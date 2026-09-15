#Python_AI Schedule advise
# file: cosmic_scheduler.py

import os
import time
import threading
from datetime import datetime, timedelta

from frontend.utils.cosmic_signal import run_cosmic_engine_for_bot  # you implement this
from frontend.utils.discord_notify import notify_signal

BOTS_SCHEDULE = [
    ("Vega",   "09:45:00"),
    ("Hydra",  "09:45:20"),
    ("Triton", "09:45:40"),
    ("Dione",  "10:00:00"),
    ("Cephei", "10:00:20"),
]

TIMEZONE_OFFSET_HOURS = 0  # adjust if needed from server time to EST


def parse_time_str(t_str: str) -> datetime:
    today = datetime.now()
    h, m, s = map(int, t_str.split(":"))
    dt = today.replace(hour=h, minute=m, second=s, microsecond=0)
    return dt


def seconds_until(target: datetime) -> float:
    now = datetime.now()
    if target < now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def run_bot(bot_name: str):
    try:
        mode = "paper" if os.getenv("LIVE_MODE", "false").lower() != "true" else "live"
        result = run_cosmic_engine_for_bot(bot_name, mode=mode)
        # result should contain: symbol, decision, cosmic_score, heads, extra_fields
        notify_signal(
            bot_name=bot_name,
            symbol=result["symbol"],
            decision=result["decision"],
            cosmic_score=result["cosmic_score"],
            heads=result.get("heads", []),
            mode=mode,
            extra_fields=result.get("extra_fields", []),
        )
        print(f"[{datetime.now()}] Cosmic Engine run OK for {bot_name}")
    except Exception as exc:
        print(f"[{datetime.now()}] Cosmic Engine run FAILED for {bot_name}: {exc}")


def schedule_bot(bot_name: str, time_str: str):
    target = parse_time_str(time_str)
    delay = seconds_until(target)
    print(f"Scheduling {bot_name} at {time_str}, in {delay:.1f} seconds")
    time.sleep(delay)
    run_bot(bot_name)


def main():
    threads = []
    for bot_name, time_str in BOTS_SCHEDULE:
        t = threading.Thread(target=schedule_bot, args=(bot_name, time_str), daemon=True)
        t.start()
        threads.append(t)

    # keep main thread alive
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
