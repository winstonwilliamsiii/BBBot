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
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from frontend.utils.cosmic_schedule import BOT_SCHEDULE, run_bot as _run_bot

logger = logging.getLogger("schedule_cosmic_signal")


def _timezone():
    name = os.getenv("COSMIC_SCHEDULE_TIMEZONE", "").strip()
    if not name:
        return datetime.now().astimezone().tzinfo
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown COSMIC_SCHEDULE_TIMEZONE: {name}") from exc


def run_bot(bot_name: str, scheduled_at: datetime | None = None) -> None:
    _run_bot(bot_name, scheduled_at.isoformat() if scheduled_at else "manual")


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
