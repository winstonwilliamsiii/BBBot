from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests

# Replace with your Tiingo API token
TIINGO_API_TOKEN = "e6c794cd1e5e48519194065a2a43b2396298288b"

def fetch_tiingo_data(**kwargs):
    url = "https://api.tiingo.com/tiingo/daily/AAPL/prices"
    headers = {"Content-Type": "application/json"}
    params = {"token": TIINGO_API_TOKEN}
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    print("Fetched Tiingo data:", data)
    # You could push to XCom, save to DB, etc.

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="tiingo_data_pull",
    default_args=default_args,
    description="Pull daily stock data from Tiingo",
    schedule_interval="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["tiingo", "finance"],
) as dag:

    fetch_data = PythonOperator(
        task_id="fetch_tiingo_data",
        python_callable=fetch_tiingo_data,
        provide_context=True,
    )

    fetch_data