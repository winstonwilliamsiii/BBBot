"""Staggered Cosmic Signal Engine runs for all 15 Bentley bots.

Runs weekdays at 09:45 America/New_York. Each bot has its own sensor + task
so a failure in one bot never blocks the others. Schedule and Discord delivery
come from ``frontend.utils.cosmic_schedule`` (shared with
``scripts/schedule_cosmic_signal.py``).
"""

from datetime import datetime, timedelta

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.time_delta import TimeDeltaSensor

from frontend.utils.cosmic_schedule import BOT_SCHEDULE, run_bot

DAG_START = (9, 45)  # first slot; the DAG cron below must match
TZ = pendulum.timezone("America/New_York")


def _offset(slot) -> timedelta:
    return timedelta(
        hours=slot.hour - DAG_START[0],
        minutes=slot.minute - DAG_START[1],
        seconds=slot.second,
    )


def run_bot_task(bot_name: str, **context) -> None:
    run_bot(bot_name, schedule_label=f"airflow {context['ts']}")


with DAG(
    dag_id="cosmic_engine_staggered",
    default_args={
        "owner": "bentley",
        "depends_on_past": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=2),
    },
    description="Staggered Cosmic Signal Engine runs + Discord updates for all 15 bots",
    schedule_interval="45 9 * * 1-5",
    start_date=datetime(2026, 9, 7, tzinfo=TZ),
    catchup=False,
    max_active_runs=1,
    tags=["cosmic-signal", "discord", "bots"],
) as dag:
    for entry in BOT_SCHEDULE:
        name = entry.bot_name.lower()
        wait = TimeDeltaSensor(
            task_id=f"wait_for_{name}_slot",
            delta=_offset(entry.scheduled_at),
            mode="reschedule",
            poke_interval=10,
        )
        run = PythonOperator(
            task_id=f"run_{name}",
            python_callable=run_bot_task,
            op_kwargs={"bot_name": entry.bot_name},
        )
        wait >> run
