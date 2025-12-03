from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import pandas as pd
import mlflow
from sqlalchemy import create_engine
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === CONFIG ===
AIRBYTE_API = "http://localhost:8001"
AIRBYTE_CONNECTION_ID = "your-airbyte-connection-id"
MYSQL_CONFIG = {
    "host": "mysql",  # Docker container name
    "user": "airflow",
    "password": "airflow",
    "database": "mansa_bot"
}
MYSQL_URL = (
    f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}"
    f"@{MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}"
)
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
    r = requests.post(
        url,
        json={"connectionId": AIRBYTE_CONNECTION_ID},
        timeout=30
    )
    r.raise_for_status()


# === 2. Read MySQL Data ===
def read_mysql_data():
    engine = create_engine(MYSQL_URL)
    query = ("SELECT * FROM binance_ohlcv "
             "ORDER BY timestamp DESC LIMIT 100")
    df = pd.read_sql(query, engine)
    df.to_csv("/tmp/latest_data.csv", index=False)
    engine.dispose()


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
    df.loc[(df['RSI'] < 30) & (df['MACD'] > df['Signal']), 'trigger'] = 'BUY'
    df.loc[(df['RSI'] > 70) & (df['MACD'] < df['Signal']), 'trigger'] = 'SELL'
    df.to_csv("/tmp/indicators.csv", index=False)


# === 4. Execute Trade ===


def execute_trade():
    """
    Execute trades based on signals using real broker APIs
    Routes to appropriate broker based on symbol type
    """
    df = pd.read_csv("/tmp/indicators.csv")
    latest = df.iloc[-1]
    action = latest.get("trigger")
    
    if action in ["BUY", "SELL"]:
        # Import broker API
        from bbbot1_pipeline.broker_api import execute_trade as place_order
        
        # Determine broker based on symbol
        # Example routing logic:
        # - Crypto (ends with USDT) -> Binance
        # - Forex pairs (contains dot) -> IBKR
        # - Futures/Commodities (2-3 chars) -> IBKR
        # - Everything else -> Webull
        
        if SYMBOL.endswith("USDT"):
            # Crypto -> Binance
            result = place_order("binance", SYMBOL, action, QUANTITY)
        elif "." in SYMBOL or len(SYMBOL) <= 3:
            # Forex or Futures -> IBKR
            result = place_order("ibkr", SYMBOL, action, QUANTITY, sec_type="FUT", exchange="CME")
        else:
            # Equities/ETFs -> Webull
            result = place_order("webull", SYMBOL, action, QUANTITY)
        
        logger.info(f"Trade executed: {result}")
        
        # Save trade result
        with open("/tmp/trade_result.json", "w") as f:
            import json
            json.dump(result, f, indent=2)
    else:
        logger.info("No trade triggered.")
        print("No trade triggered.")


# === 5. Log to MLFlow ===


def log_to_mlflow():
    df = pd.read_csv("/tmp/indicators.csv")
    
    # Set MLflow tracking URI (accessible within Docker network)
    mlflow.set_tracking_uri("http://mlflow:5000")
    mlflow.set_experiment("BentleyBudgetBot-Trading")
    
    with mlflow.start_run() as run:
        # Log parameters
        mlflow.log_param("data_points", len(df))
        mlflow.log_param("broker", BROKER)
        mlflow.log_param("symbol", SYMBOL)
        mlflow.log_param("quantity", QUANTITY)
        
        # Log metrics
        buy_signals = (df['trigger'] == 'BUY').sum()
        sell_signals = (df['trigger'] == 'SELL').sum()
        
        mlflow.log_metric("buy_signals", buy_signals)
        mlflow.log_metric("sell_signals", sell_signals)
        mlflow.log_metric("total_signals", buy_signals + sell_signals)
        
        # Log latest market data
        if len(df) > 0:
            latest = df.iloc[-1]
            mlflow.log_metric("latest_rsi", latest.get('RSI', 0))
            mlflow.log_metric("latest_macd", latest.get('MACD', 0))
            mlflow.log_metric("latest_close", latest.get('close', 0))
        
        # Save and log artifacts
        import os
        artifact_path = "/tmp/mlflow_artifacts"
        os.makedirs(artifact_path, exist_ok=True)
        
        # Save trading signals
        signals_file = f"{artifact_path}/trade_signals.csv"
        df.to_csv(signals_file, index=False)
        mlflow.log_artifact(signals_file)
        
        # Save trading summary
        summary = {
            "run_id": run.info.run_id,
            "timestamp": pd.Timestamp.now().isoformat(),
            "total_data_points": len(df),
            "buy_signals": int(buy_signals),
            "sell_signals": int(sell_signals),
            "last_action": (
                latest.get('trigger', 'HOLD') if len(df) > 0 else 'HOLD'
            )
        }
        
        summary_file = f"{artifact_path}/trading_summary.json"
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        mlflow.log_artifact(summary_file)
        
        print(f"✅ MLflow run completed: {run.info.run_id}")
        print(f"📊 Logged {buy_signals} BUY and {sell_signals} SELL signals")


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

