# dags/airbyte_sync_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import requests

AIRBYTE_API = "http://localhost:8001"
CONNECTION_ID = "your-connection-id"

def trigger_airbyte_sync():
    url = f"{AIRBYTE_API}/v1/connections/sync"
    response = requests.post(url, json={"connectionId": CONNECTION_ID})
    response.raise_for_status()

def wait_for_completion():
    # Optional: poll Airbyte for sync status
    pass

with DAG("airbyte_sync_dag", start_date=datetime(2023, 1, 1), schedule_interval="@hourly", catchup=False) as dag:

    sync_airbyte = PythonOperator(
        task_id="trigger_airbyte_sync",
        python_callable=trigger_airbyte_sync
    )

    wait_sync = PythonOperator(
        task_id="wait_for_completion",
        python_callable=wait_for_completion
    )

    sync_airbyte >> wait_sync