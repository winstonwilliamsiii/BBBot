Updates to Airflow DAG
# file: dags/cosmic_engine_staggered.py

from datetime import datetime, timedelta
import os

from airflow import DAG
from airflow.operators.python import PythonOperator

from frontend.utils.cosmic_signal import run_cosmic_engine_for_bot
from frontend.utils.discord_notify import notify_signal

DEFAULT_ARGS = {
    "owner": "bentley",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

BOTS_SCHEDULE = [
    ("Vega",   "09:45:00"),
    ("Titan",  "09:45:20"),
    ("Rhea",   "09:45:40"),
    ("Rigel",  "10:00:00"),
    ("Altair", "10:00:20"),
]

def run_bot_task(bot_name: str, **context):
    mode = "paper" if os.getenv("LIVE_MODE", "false").lower() != "true" else "live"
    result = run_cosmic_engine_for_bot(bot_name, mode=mode)

    notify_signal(
        bot_name=bot_name,
        symbol=result["symbol"],
        decision=result["decision"],
        cosmic_score=result["cosmic_score"],
        heads=result.get("heads", []),
        mode=mode,
        extra_fields=result.get("extra_fields", []),
    )

with DAG(
    dag_id="cosmic_engine_staggered",
    default_args=DEFAULT_ARGS,
    description="Staggered Cosmic Signal Engine runs for Bentley bots",
    schedule_interval="0 9 * * 1-5",  # base daily M–F at 09:00
    start_date=datetime(2026, 9, 7),
    catchup=False,
) as dag:

    tasks = []

    for bot_name, time_str in BOTS_SCHEDULE:
        task = PythonOperator(
            task_id=f"run_{bot_name.lower()}",
            python_callable=run_bot_task,
            op_kwargs={"bot_name": bot_name},
        )
        tasks.append(task)

    for i in range(len(tasks) - 1):
        tasks[i] >> tasks[i + 1]
