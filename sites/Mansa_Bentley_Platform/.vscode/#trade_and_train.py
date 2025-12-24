#import pandas as pd
from indicators import calculate_rsi, calculate_macd
from trigger_engine import evaluate_triggers
from broker_api import execute_trade
import mlflow

# Simulated close prices
closes = [100 + i for i in range(50)]
df = pd.DataFrame({'close': closes})

df['RSI'] = calculate_rsi(closes)
macd = calculate_macd(closes)
df['MACD'] = macd['macdLine']
df['Signal'] = macd['signalLine']

rules = [
    {"indicator": "RSI", "condition": "<", "threshold": 30, "action": "BUY", "asset": "BTCUSDT"},
    {"indicator": "RSI", "condition": ">", "threshold": 70, "action": "SELL", "asset": "BTCUSDT"}
]

df = evaluate_triggers(df, rules)

mlflow.set_tracking_uri("http://mlflow-server:5000")
mlflow.set_experiment("BentleyBudgetBot-Trading")

with mlflow.start_run():
    mlflow.log_metric("buy_signals", (df['trigger_action'] == 'BUY').sum())
    mlflow.log_metric("sell_signals", (df['trigger_action'] == 'SELL').sum())

    latest = df.iloc[-1]
    if latest['trigger_action']:
        execute_trade(broker='binance', symbol='BTCUSDT', side=latest['trigger_action'], quantity=0.01)