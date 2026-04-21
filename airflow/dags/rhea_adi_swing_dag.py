"""
Rhea Mansa ADI Swing DAG

Pipeline checkpoints:
1) Load Rhea universe (Airbyte source config) — Aerospace/Defense/Industrials
2) Verify MySQL connectivity for Bentley Dashboard persistence
3) Log pipeline snapshot to MLflow
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator


default_args = {
    "owner": "bentleybot",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
}

RHEA_TICKERS_FALLBACK = [
    "SIDU", "AXON", "NNE", "GD", "NOC", "KTOS", "HON", "FLY", "IR", "XTIA"
]


def _repo_root() -> Path:
    explicit = os.getenv("BENTLEY_REPO_ROOT", "").strip()
    if explicit:
        return Path(explicit)
    return Path(__file__).resolve().parents[2]


def load_rhea_universe(**context):
    cfg_path = (
        _repo_root()
        / "airbyte"
        / "sources"
        / "stocktwits"
        / "rhea_mansa_config.json"
    )
    try:
        with cfg_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        tickers = [str(t).strip().upper() for t in payload.get("tickers", []) if str(t).strip()]
    except (FileNotFoundError, json.JSONDecodeError):
        tickers = RHEA_TICKERS_FALLBACK

    if not tickers:
        tickers = RHEA_TICKERS_FALLBACK

    context["task_instance"].xcom_push(key="tickers", value=tickers)
    context["task_instance"].xcom_push(key="source_config", value=str(cfg_path))
    return {
        "ticker_count": len(tickers),
        "tickers": tickers,
        "source_config": str(cfg_path),
    }


def verify_mysql_connection(**context):
    import pymysql

    connection = pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3307")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "root"),
        database=os.getenv("MYSQL_DATABASE", "bbbot1"),
        charset="utf8mb4",
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE(), VERSION()")
            database_name, version = cursor.fetchone()
        return {
            "database": database_name,
            "version": version,
            "signal_table": os.getenv("RHEA_MYSQL_SIGNAL_TABLE", "rhea_signal_events"),
        }
    finally:
        connection.close()


def log_rhea_pipeline_snapshot(**context):
    tickers = context["task_instance"].xcom_pull(
        task_ids="load_rhea_universe",
        key="tickers",
    ) or []
    source_config = context["task_instance"].xcom_pull(
        task_ids="load_rhea_universe",
        key="source_config",
    )
    mysql_status = context["task_instance"].xcom_pull(task_ids="verify_mysql_connection")

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    experiment = os.getenv("RHEA_MLFLOW_EXPERIMENT", "Rhea_Mansa_ADI")

    try:
        import mlflow
    except ImportError:
        return {
            "logged": False,
            "reason": "mlflow not installed",
            "ticker_count": len(tickers),
            "source_config": source_config,
            "mysql": mysql_status,
        }

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment)

    with mlflow.start_run(run_name=f"rhea_pipeline_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"):
        mlflow.set_tag("bot", "Rhea")
        mlflow.set_tag("fund", "Mansa ADI")
        mlflow.set_tag("pipeline", "airflow")
        mlflow.set_tag("strategy", "ADI_Divergence_Swing")
        mlflow.log_param("source_config", source_config or "")
        mlflow.log_param("airflow_dag_id", "airflow_mansa_adi")
        mlflow.log_param("mysql_signal_table", os.getenv("RHEA_MYSQL_SIGNAL_TABLE", "rhea_signal_events"))
        mlflow.log_metric("ticker_count", float(len(tickers)))

    return {
        "logged": True,
        "tracking_uri": tracking_uri,
        "experiment": experiment,
        "ticker_count": len(tickers),
        "mysql": mysql_status,
    }


with DAG(
    dag_id="airflow_mansa_adi",
    default_args=default_args,
    description="Rhea ADI Swing orchestration for Aerospace/Defense/Industrials — Airbyte universe, MySQL checks, and MLflow logging",
    schedule="30 8 * * 1-5",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["rhea", "mansa", "adi", "swing", "mlflow", "mysql"],
) as dag:
    load_universe = PythonOperator(
        task_id="load_rhea_universe",
        python_callable=load_rhea_universe,
    )

    mysql_check = PythonOperator(
        task_id="verify_mysql_connection",
        python_callable=verify_mysql_connection,
    )

    mlflow_snapshot = PythonOperator(
        task_id="log_rhea_pipeline_snapshot",
        python_callable=log_rhea_pipeline_snapshot,
    )

    load_universe >> mysql_check >> mlflow_snapshot
