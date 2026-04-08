#triton_bot

# Triton_Bot – Mansa Transportation Fund
# Swing Trading Setup with Alpaca + IBKR, Analytics, MLFlow, ARIMA + LSTM

import os
import pandas as pd
import numpy as np
import yfinance as yf
from alpaca_trade_api import REST
import ib_insync as ib
import talib
from transformers import pipeline
from statsmodels.tsa.arima.model import ARIMA
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import mlflow
import mlflow.keras

# -------------------------------
# 1. Broker Connections
# -------------------------------

# Alpaca
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

alpaca = REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)

# IBKR
ibkr = ib.IB()
ibkr.connect('127.0.0.1', 7497, clientId=1)

# -------------------------------
# 2. Data Retrieval
# -------------------------------

def get_data(symbol="TSLA", period="6mo", interval="1d"):
    df = yf.download(symbol, period=period, interval=interval)
    return df

# -------------------------------
# 3. Analytics Pipeline
# -------------------------------

def fundamental_analysis(symbol="TSLA"):
    stock = yf.Ticker(symbol)
    return stock.info

def technical_analysis(df):
    df['RSI'] = talib.RSI(df['Close'])
    df['MACD'], df['MACD_signal'], _ = talib.MACD(df['Close'])
    return df

def sentiment_analysis(texts):
    nlp = pipeline("sentiment-analysis")
    scores = [nlp(t)[0]['score'] if nlp(t)[0]['label'] == 'POSITIVE' else -nlp(t)[0]['score'] for t in texts]
    return np.mean(scores)

# -------------------------------
# 4. Swing Trading Strategy
# -------------------------------

def swing_signal(df, sentiment_score):
    latest = df.iloc[-1]
    if latest['RSI'] < 30 and sentiment_score > 0.6:
        return "BUY"
    elif latest['RSI'] > 70 or sentiment_score < 0.4:
        return "SELL"
    return "HOLD"

# -------------------------------
# 5. MLFlow Experiment Tracking
# -------------------------------

def log_mlflow(model_name, model, metrics):
    with mlflow.start_run():
        mlflow.log_param("model", model_name)
        for k, v in metrics.items():
            mlflow.log_metric(k, v)
        if model_name == "LSTM":
            mlflow.keras.log_model(model, "lstm_model")
        else:
            mlflow.sklearn.log_model(model, f"{model_name}_model")

# -------------------------------
# 6. Prediction Models
# -------------------------------

def arima_forecast(df):
    model = ARIMA(df['Close'], order=(5,1,0))
    fit = model.fit()
    forecast = fit.forecast(steps=5)
    return forecast

def lstm_forecast(df, look_back=10):
    data = df['Close'].values.reshape(-1,1)
    X, y = [], []
    for i in range(len(data)-look_back):
        X.append(data[i:i+look_back])
        y.append(data[i+look_back])
    X, y = np