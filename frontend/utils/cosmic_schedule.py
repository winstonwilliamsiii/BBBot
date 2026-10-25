"""Shared Cosmic Signal Engine schedule and Discord delivery for all 15 bots.

Used by both ``scripts/schedule_cosmic_signal.py`` (standalone scheduler) and
``airflow/dags/cosmic_engine_staggered.py`` so the two never drift apart.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, time as clock_time
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv

    # Webhooks and LIVE_MODE live in the repo .env; never override real env vars.
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
except ImportError:  # python-dotenv is optional
    pass

from frontend.utils import cosmic_signal
from frontend.utils.webhook_router import get_webhook

logger = logging.getLogger("cosmic_schedule")


@dataclass(frozen=True)
class BotSchedule:
    bot_name: str
    scheduled_at: clock_time


# All 15 bots, staggered 20s apart in groups of three every 15 minutes so
# free-tier workers don't initialize several ML/data clients at once.
BOT_SCHEDULE: tuple[BotSchedule, ...] = (
    BotSchedule("Vega", clock_time(9, 45, 0)),
    BotSchedule("Titan", clock_time(9, 45, 20)),
    BotSchedule("Rhea", clock_time(9, 45, 40)),
    BotSchedule("Rigel", clock_time(10, 0, 0)),
    BotSchedule("Altair", clock_time(10, 0, 20)),
    BotSchedule("Dogon", clock_time(10, 0, 40)),
    BotSchedule("Orion", clock_time(10, 15, 0)),
    BotSchedule("Draco", clock_time(10, 15, 20)),
    BotSchedule("Procryon", clock_time(10, 15, 40)),
    BotSchedule("Hydra", clock_time(10, 30, 0)),
    BotSchedule("Triton", clock_time(10, 30, 20)),
    BotSchedule("Dione", clock_time(10, 30, 40)),
    BotSchedule("Cephei", clock_time(10, 45, 0)),
    BotSchedule("Jupicita", clock_time(10, 45, 20)),
    BotSchedule("Cygnus", clock_time(10, 45, 40)),
)

SCHEDULE_TIMEZONE_DEFAULT = "America/New_York"


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "y"}


def get_mode() -> str:
    """Return live only when explicitly enabled; paper is the safe default."""
    return "live" if _truthy(os.getenv("LIVE_MODE")) else "paper"


def send_discord(bot_name: str, payload: dict) -> bool:
    """Post a payload to the bot's own channel via the webhook routing map."""
    webhook = get_webhook(bot_name)
    if not webhook:
        logger.warning("No webhook configured for %s (set WEBHOOK_%s)", bot_name, bot_name.upper())
        return False
    try:
        response = requests.post(webhook, json=payload, timeout=8)
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.warning("Discord post failed for %s: %s", bot_name, exc)
        return False


def _mode_tag(mode: str) -> str:
    return "🔴 LIVE" if mode == "live" else "📄 PAPER"


def signal_payload(bot_name: str, result: dict, mode: str, schedule_label: str) -> dict:
    score = float(result["cosmic_score"])
    decision = str(result["decision"]).upper()
    color = {"BUY": 3066993, "SELL": 15158332, "HOLD": 10181046}.get(decision, 5592575)
    filled = round((score + 1) / 2 * 12)
    bar = "█" * filled + "░" * (12 - filled)
    fields = []
    if result.get("heads"):
        lines = "\n".join(
            f"`{h.get('head', '?'):20s}` {h.get('score', 0):+.3f} "
            f"× w={h.get('weight', 0):.2f} → `{h.get('score', 0) * h.get('weight', 0):+.4f}`"
            for h in result["heads"]
        )
        fields.append({"name": "🧠 Analytic Heads", "value": lines[:1024], "inline": False})
    fields.extend((result.get("extra_fields") or [])[:4])
    fields.append({"name": "Scheduled", "value": schedule_label, "inline": True})
    return {
        "embeds": [{
            "title": f"🤖 {bot_name} | Signal — {_mode_tag(mode)}",
            "description": (
                f"**Time:** {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}\n"
                f"**Symbol:** `{result['symbol']}` │ **Mode:** {_mode_tag(mode)}\n"
                f"**Cosmic Score:** `{score:+.4f}`\n"
                f"```\n[{bar}] {score:+.2f}\n```\n"
                f"**Decision:** {decision}"
            ),
            "color": color,
            "fields": fields,
            "footer": {"text": f"{bot_name} Cosmic Signal Engine | Bentley Budget Bot"},
            "timestamp": datetime.now().astimezone().isoformat(),
        }]
    }


def trade_payload(bot_name: str, result: dict, trade: dict, mode: str) -> dict:
    side = str(trade["side"]).upper()
    symbol = str(trade.get("symbol", result["symbol"]))
    status = str(trade.get("status", "simulated"))
    broker = str(trade.get("broker", ""))
    ticket = trade.get("ticket")
    description = f"**{side} {symbol}** — {float(trade['qty'])} lot(s)"
    if broker:
        description += f" via **{broker.upper()}**"
    description += f"\nStatus: {status}" + (f" │ Ticket: `{ticket}`" if ticket else "")
    return {
        "embeds": [{
            "title": f"🤖 {bot_name} | Trade — {_mode_tag(mode)}",
            "description": description,
            "color": 3447003,
            "fields": [{"name": "Cosmic Score", "value": f"{float(result['cosmic_score']):+.4f}", "inline": True}],
            "footer": {"text": f"{bot_name} | Bentley Budget Bot"},
            "timestamp": datetime.now().astimezone().isoformat(),
        }]
    }


def run_bot(bot_name: str, schedule_label: str = "manual") -> dict:
    """Scan the bot's whole universe and post the strongest signal to Discord.

    The headline is the symbol with the largest absolute cosmic score; a
    "Universe Scan" field lists every symbol evaluated.
    """
    mode = get_mode()
    override = os.getenv(f"COSMIC_SYMBOL_{bot_name.upper()}", "").strip().upper()
    symbols = [override] if override else cosmic_signal.get_bot_universe(bot_name)
    if not symbols:
        raise ValueError(
            f"No symbol universe for {bot_name}; check screener_file in "
            "bentley-bot/config/bots/"
        )

    results = []
    for symbol in symbols:
        try:
            results.append(
                cosmic_signal.run_cosmic_engine_for_bot(bot_name, mode=mode, symbol=symbol)
            )
        except Exception:  # noqa: BLE001 - one bad ticker must not drop the rest
            logger.exception("%s: cosmic run failed for %s", bot_name, symbol)
    if not results:
        raise RuntimeError(f"Cosmic Signal Engine produced no results for {bot_name}")

    best = max(results, key=lambda r: abs(float(r["cosmic_score"])))
    scan_lines = "\n".join(
        f"`{r['symbol']:<6}` {float(r['cosmic_score']):+.3f} {r['decision']}"
        for r in sorted(results, key=lambda r: -abs(float(r["cosmic_score"])))
    )
    best = {
        **best,
        "extra_fields": [
            {
                "name": f"🌐 Universe Scan ({len(results)}/{len(symbols)})",
                "value": scan_lines[:1024],
                "inline": False,
            },
            *(best.get("extra_fields") or []),
        ],
    }
    send_discord(bot_name, signal_payload(bot_name, best, mode, schedule_label))

    # A signal alone is never reported as a trade; only adapter-returned trades.
    for trade in best.get("trades", []):
        send_discord(bot_name, trade_payload(bot_name, best, trade, mode))
    logger.info(
        "%s completed: %s %s %+.4f (%s, %d symbols)",
        bot_name, best["symbol"], best["decision"], best["cosmic_score"], mode, len(results),
    )
    return best
