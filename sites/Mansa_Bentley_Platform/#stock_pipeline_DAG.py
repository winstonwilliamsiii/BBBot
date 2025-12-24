#stock_pipeline_DAG
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Import your custom modules
from bbbot1_pipeline.ingest_alpha_vantage import run_alpha_vantage
from bbbot1_pipeline.ingest_yfinance import run_yf
from bbbot1_pipeline.derive_ratios import compute_ratios
from bbbot1_pipeline.mlflow_logging import log_fundamental_ratios, train_and_log_roi_model

default_args = {
    'owner': 'winston',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='stock_pipeline_dag',
    default_args=default_args,
    description='End-to-end pipeline: fundamentals + prices + ratios + dbt + MLFlow',
    schedule_interval='@daily',
    start_date=datetime(2025, 12, 1),
    catchup=False,
    tags=['stocks', 'fundamentals', 'mlflow', 'dbt'],
) as dag:

    # Step 1: Ingest Alpha Vantage fundamentals
    alpha_ingest = PythonOperator(
        task_id='alpha_ingest',
        python_callable=run_alpha_vantage,
        op_kwargs={'tickers': ['AMZN', 'AAPL', 'MSFT']},  # extend with your quantum stocks
    )

    # Step 2: Ingest yfinance prices
    yf_ingest = PythonOperator(
        task_id='yf_ingest',
        python_callable=run_yf,
        op_kwargs={'tickers': ['AMZN', 'AAPL', 'MSFT']},
    )

    # Step 3: Derive ratios
    derive_ratios = PythonOperator(
        task_id='derive_ratios',
        python_callable=compute_ratios,
    )

    # Step 4: Run dbt transformations
    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command='cd /opt/airflow/dbt_project && dbt run',
    )

    # Step 5: Log raw ratios into MLFlow
    log_ratios = PythonOperator(
        task_id='log_ratios',
        python_callable=log_fundamental_ratios,
        op_kwargs={
            'ticker': 'AMZN',
            'report_date': '{{ ds }}',
            'ratios': '{{ ti.xcom_pull(task_ids="derive_ratios") }}'
        },
    )

    # Step 6: Train regression model predicting ROI and log to MLFlow
    train_roi_model = PythonOperator(
        task_id='train_roi_model',
        python_callable=train_and_log_roi_model,
        op_kwargs={
            'df': '{{ ti.xcom_pull(task_ids="derive_ratios") }}',
            'ticker': 'AMZN'
        },
    )

    # Task chaining
    alpha_ingest >> yf_ingest >> derive_ratios >> dbt_run >> log_ratios >> train_roi_model