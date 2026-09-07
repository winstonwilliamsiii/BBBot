"""Staggered Cosmic Signal Engine scheduler for the configured Bentley Bots.

This is intentionally implemented with the Python standard library so it can
run on a free-tier worker without Airflow or another always-on scheduler.

Run continuously:
    python scripts/schedule_cosmic_signal.py

Run one bot immediately (useful for a smoke test):
    python scripts/schedule_cosmic_signal.py --run-now Vega

The schedule uses the host's local timezone by default. Set
``COSMIC_SCHEDULE_TIMEZONE`` to an IANA timezone (for example, ``America/New_York``)
when the worker's local timezone is not the desired market timezone.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime, time as clock_time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Keep these module imports explicit: the scheduler is the integration point
# between the Cosmic Signal Engine and Discord notifications.
from frontend.utils import cosmic_signal, discord_notify

logger = logging.getLogger("schedule_cosmic_signal")


@dataclass(frozen=True)
class BotSchedule:
    bot_name: str
    scheduled_at: clock_time


# Add new bots or adjust times here. Keep at least a small gap between starts
# so free-tier workers do not initialize several ML/data clients at once.
BOT_SCHEDULE: tuple[BotSchedule, ...] = (
    BotSchedule("Vega", clock_time(9, 45, 0)),
    BotSchedule("Titan", clock_time(9, 45, 20)),
    BotSchedule("Rhea", clock_time(9, 45, 40)),
    BotSchedule("Rigel", clock_time(10, 0, 0)),
    BotSchedule("Altair", clock_time(10, 0, 20)),
)


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "y"}


def _mode() -> str:
    """Return live only when explicitly enabled; paper is the safe default."""
    return "live" if _truthy(os.getenv("LIVE_MODE")) else "paper"


def _timezone():
    name = os.getenv("COSMIC_SCHEDULE_TIMEZONE", "").strip()
    if not name:
        return datetime.now().astimezone().tzinfo
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown COSMIC_SCHEDULE_TIMEZONE: {name}") from exc


def run_bot(bot_name: str, scheduled_at: datetime | None = None) -> None:
    """Run one bot; exceptions are contained so later bots still start."""
    mode = _mode()
    result = cosmic_signal.run_cosmic_engine_for_bot(bot_name, mode=mode)
    schedule_label = scheduled_at.isoformat() if scheduled_at else "manual"
    discord_notify.notify_signal(
        bot_name=bot_name,
        symbol=result["symbol"],
        decision=result["decision"],
        cosmic_score=result["cosmic_score"],
        heads=result["heads"],
        mode=mode,
        extra_fields=result["extra_fields"] + [
            {"name": "Scheduled", "value": schedule_label, "inline": True},
        ],
    )

    # Trade notifications are emitted only for trade records returned by a
    # bot's ML/execution adapter; a signal alone is never reported as a trade.
    for trade in result.get("trades", []):
        discord_notify.notify_trade(
            bot_name=bot_name,
            symbol=str(trade.get("symbol", result["symbol"])),
            side=str(trade["side"]),
            qty=float(trade["qty"]),
            status=str(trade.get("status", "simulated")),
            mode=mode,
            ticket=trade.get("ticket"),
            broker=str(trade.get("broker", "")),
            cosmic_score=result["cosmic_score"],
        )
    logger.info("%s completed: %s %+.4f (%s)", bot_name, result["decision"], result["cosmic_score"], mode)


def _safe_run_bot(bot_name: str, scheduled_at: datetime) -> None:
    try:
        run_bot(bot_name, scheduled_at)
    except Exception:  # noqa: BLE001
        logger.exception("Cosmic Signal Engine failed for %s", bot_name)


def run_scheduler() -> None:
    """Run each daily slot in a daemon thread, isolating bot failures."""
    timezone = _timezone()
    launched: set[tuple[date, str]] = set()
    while True:
        now = datetime.now(timezone)
        for entry in BOT_SCHEDULE:
            key = (now.date(), entry.bot_name)
            due = datetime.combine(now.date(), entry.scheduled_at, tzinfo=timezone)
            slot_end = due + timedelta(seconds=2)
            if due <= now < slot_end and key not in launched:
                launched.add(key)
                threading.Thread(
                    target=_safe_run_bot,
                    args=(entry.bot_name, due),
                    name=f"cosmic-{entry.bot_name.lower()}",
                    daemon=True,
                ).start()
        # Keep the process lightweight while still honoring second-level slots.
        time.sleep(1.0)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-now", metavar="BOT", help="Run one configured bot immediately.")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    args = _parse_args()
    if args.run_now:
        names = {entry.bot_name.lower(): entry.bot_name for entry in BOT_SCHEDULE}
        bot_name = names.get(args.run_now.lower())
        if bot_name is None:
            raise SystemExit(f"Unknown bot {args.run_now!r}; choose one of {sorted(names.values())}")
        run_bot(bot_name)
        return 0
    run_scheduler()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
