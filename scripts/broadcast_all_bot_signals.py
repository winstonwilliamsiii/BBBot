from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from frontend.utils.cosmic_signal import compute_cosmic_score
from frontend.utils.discord_notify import notify_signal, notify_status

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
        "rsi": 50.0,
        "momentum_1d": 0.0,
        "sentiment_score": 0.0,
        "execution_probability": 0.5,
        "average_spread_bps": 12.0,
        "cash_ratio": 0.5,
        "is_multi_tf_aligned": True,
        "predicted_side": "buy",
    }


def broadcast(mode: str, symbol: str, active_only: bool) -> int:
    repo_root = Path(__file__).resolve().parents[1]
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

    notify_status(
        bot_name="ControlCenter",
        message=(
            f"Starting scheduled all-bot signal pulse for {len(selected_bots)} bots "
            f"(mode={mode}, symbol={symbol})."
        ),
        mode=mode,
    )

    for bot in selected_bots:
        try:
            snap = compute_cosmic_score(
                _base_context(),
                symbol=symbol,
                bot_name=bot,
                mode=mode,
            )
            notify_signal(
                bot_name=bot,
                symbol=symbol,
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
            f"mode={mode}, symbol={symbol}."
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
        "--symbol",
        default="SPY",
        help="Symbol shown in scheduled signal notifications.",
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
    return broadcast(mode=args.mode, symbol=args.symbol, active_only=args.active_only)


if __name__ == "__main__":
    raise SystemExit(main())
