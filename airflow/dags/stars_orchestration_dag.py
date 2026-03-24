"""Active Stars orchestration DAG with daily Orion training refresh."""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator, PythonOperator


REPO_ROOT = os.getenv("BENTLEY_REPO_ROOT", "/opt/bentley")
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.stars_orchestration import (  # noqa: E402
    evaluate_titan_gate,
    run_fund_bot,
    train_orion_for_refresh,
)


logger = logging.getLogger(__name__)


default_args = {
    "owner": "titan",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def titan_gate_branch(**kwargs):
    decision = evaluate_titan_gate()
    kwargs["ti"].xcom_push(key="titan_gate_decision", value=decision)
    logger.info("Titan gate decision: %s", decision)
    if decision.get("status") == "approved":
        return "run_titan"
    return "blocked_by_titan"


def run_bot(bot_name: str, **kwargs):
    result = run_fund_bot(bot_name)
    kwargs["ti"].xcom_push(key=f"{bot_name.lower()}_status", value=result)
    logger.info("Bot run status for %s: %s", bot_name, result)
    return result


def train_orion(**kwargs):
    result = train_orion_for_refresh()
    kwargs["ti"].xcom_push(key="orion_training_status", value=result)
    logger.info("Orion training status: %s", result)
    return result


dag = DAG(
    dag_id="stars_orchestration",
    default_args=default_args,
    description=(
        "Titan gate + multi-bot orchestration with 7AM Orion training refresh"
    ),
    schedule="0 7 * * 1-5",
    start_date=datetime(
        2026,
        3,
        24,
        7,
        0,
        tzinfo=ZoneInfo("America/New_York"),
    ),
    catchup=False,
    tags=["stars", "trading", "titan", "rigel", "dogon", "orion"],
)


with dag:
    titan_guard = BranchPythonOperator(
        task_id="titan_guard",
        python_callable=titan_gate_branch,
    )

    blocked_by_titan = EmptyOperator(task_id="blocked_by_titan")

    run_titan = PythonOperator(
        task_id="run_titan",
        python_callable=run_bot,
        op_kwargs={"bot_name": "Titan"},
    )

    run_rigel = PythonOperator(
        task_id="run_rigel",
        python_callable=run_bot,
        op_kwargs={"bot_name": "Rigel"},
    )

    run_dogon = PythonOperator(
        task_id="run_dogon",
        python_callable=run_bot,
        op_kwargs={"bot_name": "Dogon"},
    )

    train_orion_model = PythonOperator(
        task_id="train_orion_model",
        python_callable=train_orion,
    )

    run_orion = PythonOperator(
        task_id="run_orion",
        python_callable=run_bot,
        op_kwargs={"bot_name": "Orion"},
    )

    orchestration_done = EmptyOperator(
        task_id="orchestration_done",
        trigger_rule="none_failed_min_one_success",
    )

    titan_guard.set_downstream(blocked_by_titan)
    blocked_by_titan.set_downstream(orchestration_done)

    train_orion_model.set_downstream(orchestration_done)

    titan_guard.set_downstream(run_titan)
    run_titan.set_downstream(run_rigel)
    run_titan.set_downstream(run_dogon)
    run_titan.set_downstream(run_orion)

    run_rigel.set_downstream(orchestration_done)
    run_dogon.set_downstream(orchestration_done)
    run_orion.set_downstream(orchestration_done)
