from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.airbyte.operators.airbyte import AirbyteTriggerSyncOperator
from datetime import datetime, timedelta
from jinja2 import Template
import mlflow
from modules.market_data import fetch_barchart_data, fetch_polygon_data, fetch_tiingo_data, fetch_stocktwits_data, log_to_mlflow

default_args = {
    'owner': 'winston',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='stock_ingestion_pipeline',
    default_args=default_args,
    start_date=datetime(2025, 11, 1),
    schedule_interval='@hourly',
    catchup=False,
    tags=['stocks', 'mlflow', 'airbyte'],
) as dag:

    # 🔁 Airbyte syncs
    sync_barchart = AirbyteTriggerSyncOperator(
        task_id='sync_barchart',
        airbyte_conn_id='airbyte_conn',
        connection_id='{{ var.value.barchart_connection_id }}',
        asynchronous=False,
        timeout=300,
    )

    sync_polygon = AirbyteTriggerSyncOperator(
        task_id='sync_polygon',
        airbyte_conn_id='airbyte_conn',
        connection_id='{{ var.value.polygon_connection_id }}',
        asynchronous=False,
        timeout=300,
    )

    sync_tiingo = AirbyteTriggerSyncOperator(
        task_id='sync_tiingo',
        airbyte_conn_id='airbyte_conn',
        connection_id='{{ var.value.tiingo_connection_id }}',
        asynchronous=False,
        timeout=300,
    )

    sync_stocktwits = AirbyteTriggerSyncOperator(
        task_id='sync_stocktwits',
        airbyte_conn_id='airbyte_conn',
        connection_id='{{ var.value.stocktwits_connection_id }}',
        asynchronous=False,
        timeout=300,
    )

    # 📥 API fetchers
    fetch_barchart = PythonOperator(
        task_id='fetch_barchart_data',
        python_callable=fetch_barchart_data,
        op_kwargs={'ticker': 'AAPL', 'api_key': '{{ var.value.barchart_api_key }}'},
    )

    fetch_polygon = PythonOperator(
        task_id='fetch_polygon_data',
        python_callable=fetch_polygon_data,
        op_kwargs={'ticker': 'AAPL', 'date': '{{ ds }}', 'api_key': '{{ var.value.polygon_api_key }}'},
    )

    fetch_tiingo = PythonOperator(
        task_id='fetch_tiingo_data',
        python_callable=fetch_tiingo_data,
        op_kwargs={'ticker': 'AAPL', 'start_date': '{{ macros.ds_add(ds, -7) }}', 'end_date': '{{ ds }}', 'token': '{{ var.value.tiingo_token }}'},
    )

    fetch_stocktwits = PythonOperator(
        task_id='fetch_stocktwits_data',
        python_callable=fetch_stocktwits_data,
        op_kwargs={'ticker': 'AAPL'},
    )

    # 🧪 MLFlow logging
    log_barchart = PythonOperator(
        task_id='log_barchart_mlflow',
        python_callable=log_to_mlflow,
        op_kwargs={'source': 'Barchart', 'ticker': 'AAPL', 'data': '{{ ti.xcom_pull(task_ids="fetch_barchart_data") }}'},
    )

    log_polygon = PythonOperator(
        task_id='log_polygon_mlflow',
        python_callable=log_to_mlflow,
        op_kwargs={'source': 'Polygon', 'ticker': 'AAPL', 'data': '{{ ti.xcom_pull(task_ids="fetch_polygon_data") }}'},
    )

    log_tiingo = PythonOperator(
        task_id='log_tiingo_mlflow',
        python_callable=log_to_mlflow,
        op_kwargs={'source': 'Tiingo', 'ticker': 'AAPL', 'data': '{{ ti.xcom_pull(task_ids="fetch_tiingo_data") }}'},
    )

    log_stocktwits = PythonOperator(
        task_id='log_stocktwits_mlflow',
        python_callable=log_to_mlflow,
        op_kwargs={'source': 'Stocktwits', 'ticker': 'AAPL', 'data': '{{ ti.xcom_pull(task_ids="fetch_stocktwits_data") }}'},
    )

    # 🔗 Task chaining
    sync_barchart >> fetch_barchart >> log_barchart
    sync_polygon >> fetch_polygon >> log_polygon
    sync_tiingo >> fetch_tiingo >> log_tiingo
    sync_stocktwits >> fetch_stocktwits >> log_stocktwits