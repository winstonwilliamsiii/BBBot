from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.datasets import Dataset
from datetime import datetime
import pandas as pd
import mlflow

dataset = Dataset("mysql://mansa_bot/binance_ohlcv")

def log_metrics():
    df = pd.read_sql("SELECT * FROM binance_ohlcv", mysql_connection)
    mlflow.set_tracking_uri("http://mlflow:5000")
    mlflow.set_experiment("BentleyBudgetBot-Trading")
    with mlflow.start_run():
        mlflow.log_metric("rows_ingested", len(df))

with DAG("mlflow_logging_dag", start_date=datetime(2023, 1, 1), schedule=[dataset], catchup=False) as dag:
    PythonOperator(
        task_id="log_to_mlflow",
        python_callable=log_metrics
    )