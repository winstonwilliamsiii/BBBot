from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import mlflow
from indicators import calculate_rsi, calculate_macd
from broker_api import execute_trade
from data_ingestion import fetch_market_data

# === Task Functions ===

def ingest_market_data(**kwargs):
    df = fetch_market_data(source='binance', symbol='BTCUSDT', interval='15m')
    kwargs['ti'].xcom_push(key='market_data', value=df.to_dict())

def compute_indicators(**kwargs):
    import pandas as pd
    df_dict = kwargs['ti'].xcom_pull(key='market_data', task_ids='ingest_market_data')
    df = pd.DataFrame(df_dict)
    df['RSI'] = calculate_rsi(df['close'].tolist())
    macd = calculate_macd(df['close'].tolist())
    df['MACD'] = macd['macdLine']
    df['Signal'] = macd['signalLine']
    kwargs['ti'].xcom_push(key='indicator_data', value=df.to_dict())

def train_model(**kwargs):
    import pandas as pd
    df_dict = kwargs['ti'].xcom_pull(key='indicator_data', task_ids='compute_indicators')
    df = pd.DataFrame(df_dict)

    mlflow.set_experiment("BentleyBudgetBot-Trading")
    with mlflow.start_run():
        # Dummy model: Buy if RSI < 30 and MACD > Signal
        df['prediction'] = (df['RSI'] < 30) & (df['MACD'] > df['Signal'])
        accuracy = df['prediction'].mean()
        mlflow.log_metric("buy_signal_accuracy", accuracy)
        kwargs['ti'].xcom_push(key='predictions', value=df.to_dict())

def evaluate_model(**kwargs):
    import pandas as pd
    df_dict = kwargs['ti'].xcom_pull(key='predictions', task_ids='train_model')
    df = pd.DataFrame(df_dict)
    # Log evaluation metrics
    mlflow.log_metric("total_signals", len(df))
    mlflow.log_metric("positive_signals", df['prediction'].sum())

def trigger_trade(**kwargs):
    import pandas as pd
    df_dict = kwargs['ti'].xcom_pull(key='predictions', task_ids='train_model')
    df = pd.DataFrame(df_dict)
    latest = df.iloc[-1]
    if latest['prediction']:
        execute_trade(broker='binance', symbol='BTCUSDT', side='BUY', quantity=0.01)

# === DAG Definition ===

default_args = {
    'owner': 'winston',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2025, 11, 10),
}

with DAG(
    dag_id='ml_trading_pipeline',
    default_args=default_args,
    schedule_interval='@hourly',
    catchup=False,
    tags=['trading', 'ml', 'indicators'],
) as dag:

    ingest = PythonOperator(
        task_id='ingest_market_data',
        python_callable=ingest_market_data,
    )

    indicators = PythonOperator(
        task_id='compute_indicators',
        python_callable=compute_indicators,
    )

    train = PythonOperator(
        task_id='train_model',
        python_callable=train_model,
    )

    evaluate = PythonOperator(
        task_id='evaluate_model',
        python_callable=evaluate_model,
    )

    trade = PythonOperator(
        task_id='trigger_trade',
        python_callable=trigger_trade,
    )

    ingest >> indicators >> train >> evaluate >> trade