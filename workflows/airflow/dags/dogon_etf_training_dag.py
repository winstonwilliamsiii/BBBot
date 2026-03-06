"""Biweekly Dogon Mansa_ETF training DAG for GBT, LSTM, and TCN models."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
import os

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

from scripts.train_dogon_models import DogonTrainingConfig, train_and_evaluate


logger = logging.getLogger(__name__)


default_args = {
    "owner": "dogon",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}


def run_dogon_training(**kwargs):
    symbols = os.getenv("DOGON_ETF_SYMBOLS", "SPY,QQQ,IWM,DIA,XLK,XLF")
    config = DogonTrainingConfig(
        symbols=[s.strip().upper() for s in symbols.split(",") if s.strip()],
        days=int(os.getenv("DOGON_TRAIN_DAYS", "730")),
        sequence_window=int(os.getenv("DOGON_SEQUENCE_WINDOW", "30")),
        min_accuracy=float(os.getenv("DOGON_MIN_ACCURACY", "0.53")),
    )
    summary = train_and_evaluate(config)
    kwargs["ti"].xcom_push(key="dogon_training_summary", value=summary)
    logger.info("Dogon training summary: %s", summary)
    return summary


def enforce_promotion_gate(**kwargs):
    summary = kwargs["ti"].xcom_pull(
        task_ids="train_dogon_models",
        key="dogon_training_summary",
    )
    if not summary:
        raise ValueError("Missing Dogon training summary")

    if not bool(summary.get("promote")):
        best_accuracy = summary.get("best_accuracy")
        min_accuracy = summary.get("min_accuracy")
        raise ValueError(
            "Dogon promotion gate failed: "
            f"best_accuracy={best_accuracy} "
            f"min_accuracy={min_accuracy}"
        )

    logger.info("Dogon promotion gate passed with summary: %s", summary)


dag = DAG(
    dag_id="dogon_etf_biweekly_training",
    default_args=default_args,
    description="Biweekly Dogon Mansa_ETF model training and promotion gate",
    schedule_interval=timedelta(days=14),
    start_date=datetime(2026, 3, 4),
    catchup=False,
    tags=["dogon", "etf", "training", "mlflow", "lstm", "tcn", "xgboost"],
)


with dag:
    train_dogon_models = PythonOperator(
        task_id="train_dogon_models",
        python_callable=run_dogon_training,
    )

    promotion_gate = PythonOperator(
        task_id="promotion_gate",
        python_callable=enforce_promotion_gate,
    )

    training_complete = EmptyOperator(task_id="training_complete")

    train_dogon_models.set_downstream(promotion_gate)
    promotion_gate.set_downstream(training_complete)
