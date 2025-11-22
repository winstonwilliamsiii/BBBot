from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
import requests
import pandas as pd
import mlflow
import mysql.connector

# === CONFIG ===
AIRBYTE_API = "http://localhost:8001"
AIRBYTE_CONNECTION_ID = "your-airbyte-connection-id"
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "your_user",
    "password": "your_pass",
    "database": "mansa_bot"
}
BROKER = "binance"
SYMBOL = "BTCUSDT"
QUANTITY = 0.01

# === DAG ===
default_args = {"start_date": datetime(2023, 1, 1)}
dag = DAG(
    "bentleybot_dag",
    schedule_interval="@hourly",
    catchup=False,
    default_args=default_args
)

# === 1. Trigger Airbyte Sync ===
def trigger_airbyte_sync():
    url = f"{AIRBYTE_API}/v1/connections/sync"
    r = requests.post(url, json={"connectionId": AIRBYTE_CONNECTION_ID})
    r.raise_for_status()

# === 2. Read MySQL Data ===
def read_mysql_data():
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    query = (
        "SELECT * FROM binance_ohlcv "
        "ORDER BY timestamp DESC LIMIT 100"
    )
    df = pd.read_sql(query, conn)
    df.to_csv("/tmp/latest_data.csv", index=False)
    conn.close()

# === 3. RSI/MACD + Trigger Logic ===
def compute_indicators():
    df = pd.read_csv("/tmp/latest_data.csv")
    closes = df['close'].tolist()

    def ema(values, period):
        k = 2 / (period + 1)
        ema_vals = [values[0]]
        for i in range(1, len(values)):
            ema_vals.append(values[i] * k + ema_vals[i - 1] * (1 - k))
        return ema_vals

    def rsi(values, period=14):
        rsi = [None] * period
        for i in range(period, len(values)):
            gains = losses = 0
            for j in range(i - period + 1, i + 1):
                delta = values[j] - values[j - 1]
                if delta > 0:
                    gains += delta
                else:
                    losses -= delta
            rs = gains / (losses or 1e-10)
            rsi.append(100 - 100 / (1 + rs))
        return rsi

    macd_line = [s - l for s, l in zip(ema(closes, 12), ema(closes, 26))]
    signal_line = ema(macd_line[14:], 9)
    df['RSI'] = rsi(closes)
    df['MACD'] = [None] * (len(df) - len(macd_line)) + macd_line
    df['Signal'] = [None] * (len(df) - len(signal_line)) + signal_line
    df['trigger'] = None
    buy_condition = (df['RSI'] < 30) & (df['MACD'] > df['Signal'])
    sell_condition = (df['RSI'] > 70) & (df['MACD'] < df['Signal'])
    df.loc[buy_condition, 'trigger'] = 'BUY'
    df.loc[sell_condition, 'trigger'] = 'SELL'
    df.to_csv("/tmp/indicators.csv", index=False)

# === 4. Execute Trade ===
def execute_trade():
    df = pd.read_csv("/tmp/indicators.csv")
    latest = df.iloc[-1]
    action = latest.get("trigger")
    if action in ["BUY", "SELL"]:
        # Replace with your broker API logic
        msg = f"{action} order placed for {SYMBOL} qty {QUANTITY}"
        print(msg)
    else:
        print("No trade triggered.")

# === 5. Log to MLFlow ===
def log_to_mlflow():
    df = pd.read_csv("/tmp/indicators.csv")
    # Use container name in Docker network, localhost outside
    mlflow.set_tracking_uri("http://mlflow:5000")
    mlflow.set_experiment("BentleyBudgetBot-Trading")
    with mlflow.start_run():
        buy_count = (df['trigger'] == 'BUY').sum()
        sell_count = (df['trigger'] == 'SELL').sum()
        mlflow.log_metric("buy_signals", buy_count)
        mlflow.log_metric("sell_signals", sell_count)
        df.to_csv("trade_signals.csv", index=False)
        mlflow.log_artifact("trade_signals.csv")

# === Airflow Tasks ===
t1 = PythonOperator(
    task_id="trigger_airbyte",
    python_callable=trigger_airbyte_sync,
    dag=dag
)
t2 = PythonOperator(
    task_id="read_mysql",
    python_callable=read_mysql_data,
    dag=dag
)
t3 = PythonOperator(
    task_id="compute_indicators",
    python_callable=compute_indicators,
    dag=dag
)
t4 = PythonOperator(
    task_id="execute_trade",
    python_callable=execute_trade,
    dag=dag
)
t5 = PythonOperator(
    task_id="log_mlflow",
    python_callable=log_to_mlflow,
    dag=dag
)

t1 >> t2 >> t3 >> t4 >> t5