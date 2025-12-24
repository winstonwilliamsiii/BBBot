from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.datasets import Dataset
from datetime import datetime
import requests

dataset = Dataset("mysql://mansa_bot/binance_ohlcv")

def trigger_airbyte():
    requests.post("http://localhost:8001/v1/connections/sync", json={"connectionId": "your-conn-id"})

with DAG("airbyte_sync_dag", start_date=datetime(2023, 1, 1), schedule_interval="@hourly", catchup=False) as dag:
    PythonOperator(
        task_id="trigger_airbyte",
        python_callable=trigger_airbyte,
        outlets=[dataset]
    )