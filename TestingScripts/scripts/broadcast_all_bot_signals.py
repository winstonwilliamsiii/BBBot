from __future__ import annotations

import argparse
import json
import logging
import math
from pathlib import Path
import sys
from datetime import datetime
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from frontend.utils.cosmic_signal import compute_cosmic_score
from frontend.utils.discord_notify import notify_signal, notify_status
from scripts.load_screener_csv import (
    load_bot_config,
    load_screener_csv,
    resolve_screener_path,
)

logger = logging.getLogger("broadcast_all_bot_signals")

ALL_BOTS = [
    "Titan",
    "Vega",
    "Rigel",
    "Dogon",
    "Orion",
    "Draco",
    "Altair",
    "Procryon",
    "Hydra",
    "Triton",
    "Dione",
    "Cephei",
    "Rhea",
    "Jupicita",
    "Cygnus",
]

BOT_CONFIG_PATH = REPO_ROOT / "bentley-bot" / "config" / "bots"


def _load_active_bots(repo_root: Path) -> set[str]:
    cfg = repo_root / "config" / "broker_modes.json"
    if not cfg.exists():
        return set()
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
        active_bots = data.get("active_bots", {})
        return {
            str(bot)
            for bot, is_active in active_bots.items()
            if bool(is_active)
        }
    except (OSError, ValueError, TypeError) as exc:
        logger.warning("Could not read active_bots from config: %s", exc)
        return set()


def _base_context() -> dict[str, Any]:
    # Neutral baseline context; per-bot engine rules still shape final decision.
    return {
        "rsi": None,
        "momentum_1d": None,
        "sentiment_score": 0.0,
        "execution_probability": 0.5,
        "average_spread_bps": 12.0,
        "cash_ratio": 0.5,
        "is_multi_tf_aligned": True,
        "predicted_side": "buy",
    }


def _compute_rsi_from_closes(closes: list[float], window: int = 14) -> float | None:
    if len(closes) < window + 1:
        return None

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    recent = deltas[-window:]
    gains = [d for d in recent if d > 0]
    losses = [-d for d in recent if d < 0]
    avg_gain = sum(gains) / window
    avg_loss = sum(losses) / window

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _build_ingestion_context(symbol: str) -> dict[str, Any] | None:
    endpoint = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{symbol}?range=5d&interval=1h"
    )

    try:
        response = requests.get(endpoint, timeout=10)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Ingestion failed for %s: %s", symbol, exc)
        return None

    try:
        result = (
            payload.get("chart", {})
            .get("result", [])[0]
        )
        closes = (
            result.get("indicators", {})
            .get("quote", [])[0]
            .get("close", [])
        )
    except (AttributeError, IndexError, TypeError):
        closes = []

    closes = [float(v) for v in closes if v is not None]
    if not closes:
        logger.warning("Ingestion returned no data for %s", symbol)
        return None

    if len(closes) < 15:
        logger.warning("Ingestion has insufficient bars for %s: %s", symbol, len(closes))
        return None

    rsi_value = _compute_rsi_from_closes(closes, window=14)
    prev_close = closes[-2] if len(closes) >= 2 else None
    last_close = closes[-1] if closes else None
    momentum_value = None
    if prev_close and last_close is not None and prev_close != 0:
        momentum_value = (last_close - prev_close) / prev_close

    if rsi_value is None or momentum_value is None:
        logger.warning("Skipping %s: RSI or momentum is None", symbol)
        return None

    try:
        rsi_float = float(rsi_value)
        momentum_float = float(momentum_value)
    except (TypeError, ValueError):
        logger.warning("Skipping %s: RSI or momentum not numeric", symbol)
        return None

    if math.isnan(rsi_float) or math.isnan(momentum_float):
        logger.warning("Skipping %s: RSI or momentum is NaN", symbol)
        return None

    # Normalize momentum to cosmic head domain [-1, +1]
    momentum_clamped = max(-1.0, min(1.0, momentum_float))

    return {
        "rsi": rsi_float,
        "momentum_1d": momentum_clamped,
    }


def _load_bot_symbols(bot_name: str) -> list[str]:
    try:
        config = load_bot_config(bot_name, config_path=BOT_CONFIG_PATH)
        screener_path = resolve_screener_path(config, config_path=BOT_CONFIG_PATH)
        symbols = [s for s in load_screener_csv(screener_path) if s]
        return symbols
    except (FileNotFoundError, OSError, ValueError) as exc:
        logger.warning("Universe load failed for %s: %s", bot_name, exc)
        return []


def _time_slot_index(now_local: datetime) -> int:
    hour = now_local.hour
    if hour < 11:
        return 0
    if hour < 14:
        return 1
    return 2


def _pick_symbol(bot_name: str, symbols: list[str]) -> tuple[str, int, str]:
    if not symbols:
        return "", 0, "universe-missing"

    now_local = datetime.now()
    slot = _time_slot_index(now_local)
    index = (now_local.toordinal() + slot + sum(ord(c) for c in bot_name)) % len(symbols)
    return symbols[index], len(symbols), "universe"


def broadcast(mode: str, active_only: bool) -> int:
    repo_root = REPO_ROOT
    selected_bots = list(ALL_BOTS)

    if active_only:
        active = _load_active_bots(repo_root)
        selected_bots = [b for b in ALL_BOTS if b in active]

    if not selected_bots:
        notify_status(
            bot_name="ControlCenter",
            message=(
                "Scheduled all-bot signal pulse skipped: no bots selected "
                f"(active_only={active_only})."
            ),
            mode=mode,
        )
        return 0

    sent = 0
    failed = 0
    skipped_universe = 0
    skipped_ingestion = 0

    notify_status(
        bot_name="ControlCenter",
        message=(
            f"Starting scheduled all-bot signal pulse for {len(selected_bots)} bots "
            f"(mode={mode})."
        ),
        mode=mode,
    )

    for bot in selected_bots:
        try:
            bot_symbols = _load_bot_symbols(bot)
            chosen_symbol, universe_size, symbol_source = _pick_symbol(
                bot,
                bot_symbols,
            )
            if universe_size == 0 or not chosen_symbol:
                skipped_universe += 1
                logger.warning(
                    "Skipping %s: configured universe is empty (source=%s)",
                    bot,
                    symbol_source,
                )
                notify_status(
                    bot_name=bot,
                    message="Skipped signal pulse: configured universe has zero symbols.",
                    mode=mode,
                )
                continue

            ingestion_ctx = _build_ingestion_context(chosen_symbol)
            if ingestion_ctx is None:
                skipped_ingestion += 1
                logger.warning(
                    "Skipping %s/%s: missing RSI or momentum from ingestion",
                    bot,
                    chosen_symbol,
                )
                notify_status(
                    bot_name=bot,
                    message=(
                        f"Skipped signal pulse for {chosen_symbol}: missing RSI/momentum "
                        "from ingestion connectors."
                    ),
                    mode=mode,
                )
                continue

            logger.info(
                "Bot %s selected symbol %s (source=%s, universe_size=%s)",
                bot,
                chosen_symbol,
                symbol_source,
                universe_size,
            )
            context = _base_context()
            context.update(ingestion_ctx)
            snap = compute_cosmic_score(
                context,
                symbol=chosen_symbol,
                bot_name=bot,
                mode=mode,
            )
            notify_signal(
                bot_name=bot,
                symbol=chosen_symbol,
                decision=snap.decision,
                cosmic_score=snap.cosmic_score,
                heads=snap.to_dict().get("heads"),
                mode=mode,
                post_to_bot_talk_on_hold=True,
                extra_fields=[
                    {
                        "name": "Schedule",
                        "value": "All-bot pulse (3x/day)",
                        "inline": True,
                    },
                    {
                        "name": "Universe",
                        "value": f"{symbol_source} | size={universe_size}",
                        "inline": True,
                    }
                ],
            )
            sent += 1
        except Exception as exc:  # noqa: BLE001
            failed += 1
            logger.exception("Failed to send signal for %s: %s", bot, exc)

    notify_status(
        bot_name="ControlCenter",
        message=(
            f"Scheduled all-bot signal pulse complete. sent={sent}, failed={failed}, "
            f"skipped_universe={skipped_universe}, skipped_ingestion={skipped_ingestion}, "
            f"mode={mode}."
        ),
        mode=mode,
    )

    return 0 if failed == 0 else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Broadcast Discord Bot_Talk cosmic signal updates for all bots."
    )
    parser.add_argument(
        "--mode",
        choices=["paper", "live"],
        default="paper",
        help="Trading mode tag for notifications.",
    )
    parser.add_argument(
        "--active-only",
        action="store_true",
        help="Only send for bots marked active in config/broker_modes.json.",
    )
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    args = _parse_args()
    return broadcast(mode=args.mode, active_only=args.active_only)


if __name__ == "__main__":
    raise SystemExit(main())
