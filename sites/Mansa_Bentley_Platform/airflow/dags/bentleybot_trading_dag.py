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
default_args = {
    "owner": "bentleybot",
    "start_date": datetime(2024, 12, 1),
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False
}
dag = DAG(
    "bentleybot_dag",
    schedule_interval="@hourly",
    catchup=False,
    default_args=default_args,
    description="BentleyBot automated trading pipeline",
    tags=["trading", "crypto", "ml"]
)


# === 1. Trigger Airbyte Sync ===
def trigger_airbyte_sync():
    try:
        url = f"{AIRBYTE_API}/v1/connections/sync"
        r = requests.post(
            url,
            json={"connectionId": AIRBYTE_CONNECTION_ID},
            timeout=30
        )
        r.raise_for_status()
        logger.info(f"✅ Airbyte sync triggered successfully: {r.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to trigger Airbyte sync: {e}")
        raise


# === 2. Read MySQL Data ===
def read_mysql_data():
    engine = None
    try:
        engine = create_engine(MYSQL_URL)
        query = ("SELECT * FROM binance_ohlcv "
                "ORDER BY timestamp DESC LIMIT 100")
        df = pd.read_sql(query, engine)
        
        if df.empty:
            logger.warning("⚠️ No data retrieved from MySQL")
            # Create empty CSV with expected columns
            df = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        df.to_csv("/tmp/latest_data.csv", index=False)
        logger.info(f"✅ Retrieved {len(df)} rows from MySQL")
    except Exception as e:
        logger.error(f"❌ Failed to read MySQL data: {e}")
        raise
    finally:
        if engine:
            engine.dispose()


# === 3. RSI/MACD + Trigger Logic ===


def compute_indicators():
    try:
        df = pd.read_csv("/tmp/latest_data.csv")
        
        if df.empty or len(df) < 26:
            logger.warning("⚠️ Insufficient data for indicators calculation")
            df['RSI'] = None
            df['MACD'] = None
            df['Signal'] = None
            df['trigger'] = 'HOLD'
            df.to_csv("/tmp/indicators.csv", index=False)
            return
            
        closes = df['close'].fillna(method='ffill').tolist()

        def ema(values, period):
            if len(values) < period:
                return [None] * len(values)
            k = 2 / (period + 1)
            ema_vals = [values[0]]
            for i in range(1, len(values)):
                ema_vals.append(values[i] * k + ema_vals[i - 1] * (1 - k))
            return ema_vals

        def rsi(values, period=14):
            if len(values) <= period:
                return [None] * len(values)
            rsi_vals = [None] * period
            for i in range(period, len(values)):
                gains = losses = 0
                for j in range(i - period + 1, i + 1):
                    if j > 0:  # Avoid index error
                        delta = values[j] - values[j - 1]
                        if delta > 0:
                            gains += delta
                        else:
                            losses -= delta
                avg_gain = gains / period
                avg_loss = losses / period
                rs = avg_gain / (avg_loss if avg_loss > 0 else 1e-10)
                rsi_vals.append(100 - 100 / (1 + rs))
            return rsi_vals

        # Calculate MACD
        ema12 = ema(closes, 12)
        ema26 = ema(closes, 26)
        
        # Ensure both EMAs have the same length
        min_len = min(len(ema12), len(ema26))
        ema12 = ema12[-min_len:]
        ema26 = ema26[-min_len:]
        
        macd_line = []
        for i in range(len(ema12)):
            if ema12[i] is not None and ema26[i] is not None:
                macd_line.append(ema12[i] - ema26[i])
            else:
                macd_line.append(None)
        
        # Calculate signal line
        signal_line = ema([x for x in macd_line if x is not None], 9)
        
        # Pad arrays to match DataFrame length
        df['RSI'] = rsi(closes)
        df['MACD'] = [None] * (len(df) - len(macd_line)) + macd_line
        df['Signal'] = [None] * (len(df) - len(signal_line)) + signal_line
        df['trigger'] = 'HOLD'
        
        # Apply trading logic with null checks
        buy_condition = (
            (df['RSI'].notna()) & (df['RSI'] < 30) & 
            (df['MACD'].notna()) & (df['Signal'].notna()) & 
            (df['MACD'] > df['Signal'])
        )
        sell_condition = (
            (df['RSI'].notna()) & (df['RSI'] > 70) & 
            (df['MACD'].notna()) & (df['Signal'].notna()) & 
            (df['MACD'] < df['Signal'])
        )
        
        df.loc[buy_condition, 'trigger'] = 'BUY'
        df.loc[sell_condition, 'trigger'] = 'SELL'
        
        df.to_csv("/tmp/indicators.csv", index=False)
        logger.info(f"✅ Indicators computed for {len(df)} data points")
        
    except Exception as e:
        logger.error(f"❌ Failed to compute indicators: {e}")
        raise


# === 4. Execute Trade ===


def execute_trade():
    """
    Execute trades based on signals using real broker APIs
    Routes to appropriate broker based on symbol type
    """
    try:
        df = pd.read_csv("/tmp/indicators.csv")
        
        if df.empty:
            logger.warning("⚠️ No indicator data available for trading")
            return
            
        latest = df.iloc[-1]
        action = latest.get("trigger", "HOLD")
        
        result = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "symbol": SYMBOL,
            "action": action,
            "quantity": QUANTITY,
            "status": "simulated"
        }
        
        if action in ["BUY", "SELL"]:
            try:
                # Import broker API with fallback
                try:
                    from bbbot1_pipeline.broker_api import execute_trade as place_order
                    
                    # Determine broker based on symbol
                    if SYMBOL.endswith("USDT"):
                        # Crypto -> Binance
                        result = place_order("binance", SYMBOL, action, QUANTITY)
                    elif "." in SYMBOL or len(SYMBOL) <= 3:
                        # Forex or Futures -> IBKR
                        result = place_order("ibkr", SYMBOL, action, QUANTITY, sec_type="FUT", exchange="CME")
                    else:
                        # Equities/ETFs -> IBKR
                        result = place_order("ibkr", SYMBOL, action, QUANTITY, sec_type="STK", exchange="SMART")
                    
                    result["status"] = "executed"
                    
                except ImportError:
                    logger.warning("⚠️ Broker API not available, running in simulation mode")
                    result["status"] = "simulated"
                    result["message"] = f"Would {action} {QUANTITY} of {SYMBOL}"
                
                logger.info(f"Trade {result['status']}: {action} {QUANTITY} {SYMBOL}")
                
            except Exception as trade_error:
                logger.error(f"❌ Trade execution failed: {trade_error}")
                result["status"] = "failed"
                result["error"] = str(trade_error)
        else:
            logger.info(f"No trade triggered. Current signal: {action}")
            result["message"] = f"No action required. Signal: {action}"
        
        # Save trade result
        import json
        with open("/tmp/trade_result.json", "w") as f:
            json.dump(result, f, indent=2)
            
    except Exception as e:
        logger.error(f"❌ Failed to execute trade: {e}")
        raise


# === 5. Log to MLFlow ===


def log_to_mlflow():
    try:
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

