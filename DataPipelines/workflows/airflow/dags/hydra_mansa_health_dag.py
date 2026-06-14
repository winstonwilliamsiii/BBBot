from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator


REPO_ROOT = os.getenv("BENTLEY_REPO_ROOT", "/opt/bentley")
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from hydra_bot import HydraBot, HydraConfig  # noqa: E402


logger = logging.getLogger(__name__)


default_args = {
    "owner": "hydra",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def _scan_tickers() -> list[str]:
    raw = os.getenv("HYDRA_SCAN_TICKERS", "")
    if raw.strip():
        return [
            ticker.strip().upper()
            for ticker in raw.split(",")
            if ticker.strip()
        ]
    return list(HydraConfig.from_env().default_universe)


def trigger_hydra_airbyte_sync(**kwargs):
    connection_id = os.getenv("HYDRA_AIRBYTE_CONNECTION_ID", "").strip()
    if not connection_id:
        result = {
            "status": "skipped",
            "reason": "HYDRA_AIRBYTE_CONNECTION_ID is not configured",
        }
        kwargs["ti"].xcom_push(key="airbyte_sync", value=result)
        return result

    base_url = os.getenv(
        "HYDRA_AIRBYTE_API_BASE",
        "http://localhost:8001/api/v1",
    ).rstrip("/")
    response = requests.post(
        f"{base_url}/connections/sync",
        json={"connectionId": connection_id},
        timeout=30,
    )
    response.raise_for_status()
    result = {
        "status": "triggered",
        "connection_id": connection_id,
        "response": response.json(),
    }
    kwargs["ti"].xcom_push(key="airbyte_sync", value=result)
    return result


def run_hydra_scan(**kwargs):
    bot = HydraBot()
    results = bot.scan_universe(_scan_tickers(), log_to_mlflow=False)
    summary = {
        "status": "completed",
        "buy": [
            result["ticker"]
            for result in results
            if result["action"] == "BUY"
        ],
        "sell": [
            result["ticker"]
            for result in results
            if result["action"] == "SELL"
        ],
        "hold": [
            result["ticker"]
            for result in results
            if result["action"] == "HOLD"
        ],
        "count": len(results),
    }
    kwargs["ti"].xcom_push(key="hydra_scan_summary", value=summary)
    logger.info("Hydra scan summary: %s", summary)
    return summary


def log_hydra_scan_to_mlflow(**kwargs):
    bot = HydraBot()
    summary = kwargs["ti"].xcom_pull(
        task_ids="run_hydra_scan",
        key="hydra_scan_summary",
    ) or {}
    if not summary:
        return {"logged": False, "reason": "Hydra scan summary missing"}

    payload = {
        "ticker": "UNIVERSE",
        "action": "SCAN",
        "composite_score": float(summary.get("count", 0)),
        "momentum": {"score": float(len(summary.get("buy", [])))},
        "fundamental": {"score": float(len(summary.get("hold", [])))},
        "technical": {"score": float(len(summary.get("sell", [])))},
        "sentiment": {"score": 0.0},
    }
    result = bot.log_signal_run(
        payload,
        run_name="hydra_daily_scan",
        tags={"source": "airflow", "dag_id": bot.config.airflow_dag_id},
    )
    kwargs["ti"].xcom_push(key="hydra_mlflow", value=result)
    return result


dag = DAG(
    dag_id="hydra_mansa_health",
    default_args=default_args,
    description=(
        "Hydra Mansa Health orchestration with Airbyte sync and "
        "MLflow logging"
    ),
    schedule="30 8 * * 1-5",
    start_date=datetime(
        2026,
        4,
        8,
        8,
        30,
        tzinfo=ZoneInfo("America/New_York"),
    ),
    catchup=False,
    tags=["hydra", "mansa", "health", "airbyte", "mlflow"],
)


with dag:
    airbyte_sync = PythonOperator(
        task_id="trigger_hydra_airbyte_sync",
        python_callable=trigger_hydra_airbyte_sync,
    )

    hydra_scan = PythonOperator(
        task_id="run_hydra_scan",
        python_callable=run_hydra_scan,
    )

    hydra_mlflow = PythonOperator(
        task_id="log_hydra_scan_to_mlflow",
        python_callable=log_hydra_scan_to_mlflow,
    )

    airbyte_sync >> hydra_scan >> hydra_mlflow
