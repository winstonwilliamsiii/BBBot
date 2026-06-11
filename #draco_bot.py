#draco_bot.py

import alpaca_trade_api as tradeapi
import ib_insync
import yfinance as yf
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from statsmodels.tsa.arima.model import ARIMA
from textblob import TextBlob

# --- CONFIG ---
ALPACA_API_KEY = "your_key"
ALPACA_SECRET_KEY = "your_secret"
IBKR_HOST = "127.0.0.1"
IBKR_PORT = 7497
IBKR_CLIENT_ID = 1

# --- CONNECTORS ---
def connect_alpaca():
    return tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, base_url="https://paper-api.alpaca.markets")

def connect_ibkr():
    ib = ib_insync.IB()
    ib.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID)
    return ib

# --- FUNDAMENTAL ANALYZER ---
def fundamental_analysis(ticker):
    data = yf.Ticker(ticker).info
    return {
        "pe_ratio": data.get("forwardPE"),
        "market_cap": data.get("marketCap"),
        "dividend_yield": data.get("dividendYield")
    }

# --- TECHNICAL ANALYZER ---
def technical_analysis(df):
    df['SMA_20'] = df['Close'].rolling(20).mean()
    df['SMA_50'] = df['Close'].rolling(50).mean()
    df['RSI'] = compute_rsi(df['Close'])
    return df.tail(1).to_dict()

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- SENTIMENT ANALYZER ---
def sentiment_analysis(news_headlines):
    scores = [TextBlob(headline).sentiment.polarity for headline in news_headlines]
    return np.mean(scores)

# --- ARIMA FORECASTER ---
def arima_forecast(df, column="Close"):
    series = df[column].dropna()
    model = ARIMA(series, order=(5,1,0))
    fit = model.fit()
    forecast = fit.forecast(steps=5)
    return forecast

# --- MLflow Tracking ---
def log_experiment(ticker, forecast, fundamentals, technicals, sentiment):
    with mlflow.start_run():
        mlflow.log_param("ticker", ticker)
        mlflow.log_metric("sentiment", sentiment)
        mlflow.log_metrics(fundamentals)
        mlflow.log_metrics({k: float(v) for k,v in technicals.items() if isinstance(v,(int,float))})
        mlflow.log_artifact("forecast.csv")
        
        ##FASTAPI Scaffold for the foe API endpointimport alpaca_trade_api as tradeapi
import ib_insync
import yfinance as yf
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from statsmodels.tsa.arima.model import ARIMA
from textblob import TextBlob

# --- CONFIG ---
ALPACA_API_KEY = "your_key"
ALPACA_SECRET_KEY = "your_secret"
IBKR_HOST = "127.0.0.1"
IBKR_PORT = 7497
IBKR_CLIENT_ID = 1

# --- CONNECTORS ---
def connect_alpaca():
    return tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, base_url="https://paper-api.alpaca.markets")

def connect_ibkr():
    ib = ib_insync.IB()
    ib.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID)
    return ib

# --- FUNDAMENTAL ANALYZER ---
def fundamental_analysis(ticker):
    data = yf.Ticker(ticker).info
    return {
        "pe_ratio": data.get("forwardPE"),
        "market_cap": data.get("marketCap"),
        "dividend_yield": data.get("dividendYield")
    }

# --- TECHNICAL ANALYZER ---
def technical_analysis(df):
    df['SMA_20'] = df['Close'].rolling(20).mean()
    df['SMA_50'] = df['Close'].rolling(50).mean()
    df['RSI'] = compute_rsi(df['Close'])
    return df.tail(1).to_dict()

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- SENTIMENT ANALYZER ---
def sentiment_analysis(news_headlines):
    scores = [TextBlob(headline).sentiment.polarity for headline in news_headlines]
    return np.mean(scores)

# --- ARIMA FORECASTER ---
def arima_forecast(df, column="Close"):
    series = df[column].dropna()
    model = ARIMA(series, order=(5,1,0))
    fit = model.fit()
    forecast = fit.forecast(steps=5)
    return forecast

# --- MLflow Tracking ---
def log_experiment(ticker, forecast, fundamentals, technicals, sentiment):
    with mlflow.start_run():
        mlflow.log_param("ticker", ticker)
        mlflow.log_metric("sentiment", sentiment)
        mlflow.log_metrics(fundamentals)
        mlflow.log_metrics({k: float(v) for k,v in technicals.items() if isinstance(v,(int,float))})
        mlflow.log_artifact("forecast.csv")
import alpaca_trade_api as tradeapi
import ib_insync
import yfinance as yf
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from statsmodels.tsa.arima.model import ARIMA
from textblob import TextBlob

# --- CONFIG ---
ALPACA_API_KEY = "your_key"
ALPACA_SECRET_KEY = "your_secret"
IBKR_HOST = "127.0.0.1"
IBKR_PORT = 7497
IBKR_CLIENT_ID = 1

# --- CONNECTORS ---
def connect_alpaca():
    return tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, base_url="https://paper-api.alpaca.markets")

def connect_ibkr():
    ib = ib_insync.IB()
    ib.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID)
    return ib

# --- FUNDAMENTAL ANALYZER ---
def fundamental_analysis(ticker):
    data = yf.Ticker(ticker).info
    return {
        "pe_ratio": data.get("forwardPE"),
        "market_cap": data.get("marketCap"),
        "dividend_yield": data.get("dividendYield")
    }

# --- TECHNICAL ANALYZER ---
def technical_analysis(df):
    df['SMA_20'] = df['Close'].rolling(20).mean()
    df['SMA_50'] = df['Close'].rolling(50).mean()
    df['RSI'] = compute_rsi(df['Close'])
    return df.tail(1).to_dict()

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- SENTIMENT ANALYZER ---
def sentiment_analysis(news_headlines):
    scores = [TextBlob(headline).sentiment.polarity for headline in news_headlines]
    return np.mean(scores)

# --- ARIMA FORECASTER ---
def arima_forecast(df, column="Close"):
    series = df[column].dropna()
    model = ARIMA(series, order=(5,1,0))
    fit = model.fit()
    forecast = fit.forecast(steps=5)
    return forecast

# --- MLflow Tracking ---
def log_experiment(ticker, forecast, fundamentals, technicals, sentiment):
    with mlflow.start_run():
        mlflow.log_param("ticker", ticker)
        mlflow.log_metric("sentiment", sentiment)
        mlflow.log_metrics(fundamentals)
        mlflow.log_metrics({k: float(v) for k,v in technicals.items() if isinstance(v,(int,float))})
        mlflow.log_artifact("forecast.csv")
        
# --Fast API Scaffold for the API endpoint
from fastapi import FastAPI, Query
from pydantic import BaseModel
import pandas as pd
import yfinance as yf
import mlflow
from statsmodels.tsa.arima.model import ARIMA
from textblob import TextBlob

app = FastAPI(title="Draco Bot Mansa Money Bag API",
              description="Mansa Cosmos – Fundamental, Technical, Sentiment, ARIMA Forecasting",
              version="1.0.0")

# --- MODELS ---
class ForecastRequest(BaseModel):
    ticker: str
    news_headlines: list[str] = []
    steps: int = 5

# --- ENDPOINTS ---
@app.get("/fundamental")
def get_fundamentals(ticker: str = Query(...)):
    data = yf.Ticker(ticker).info
    fundamentals = {
        "pe_ratio": data.get("forwardPE"),
        "market_cap": data.get("marketCap"),
        "dividend_yield": data.get("dividendYield")
    }
    return fundamentals

@app.get("/technical")
def get_technicals(ticker: str = Query(...)):
    df = yf.download(ticker, period="6mo", interval="1d")
    df['SMA_20'] = df['Close'].rolling(20).mean()
    df['SMA_50'] = df['Close'].rolling(50).mean()
    return df.tail(1).to_dict()

@app.post("/sentiment")
def get_sentiment(req: ForecastRequest):
    scores = [TextBlob(h).sentiment.polarity for h in req.news_headlines]
    return {"sentiment_score": sum(scores)/len(scores) if scores else 0}

@app.post("/forecast")
def forecast(req: ForecastRequest):
    df = yf.download(req.ticker, period="1y", interval="1d")
    series = df['Close'].dropna()
    model = ARIMA(series, order=(5,1,0))
    fit = model.fit()
    forecast = fit.forecast(steps=req.steps)

    # MLflow logging
    with mlflow.start_run():
        mlflow.log_param("ticker", req.ticker)
        mlflow.log_metric("sentiment", sum([TextBlob(h).sentiment.polarity for h in req.news_headlines]) / len(req.news_headlines) if req.news_headlines else 0)
        mlflow.log_artifact("forecast.csv")

    return {"forecast": forecast.tolist()}

# -- Broker Integrtion-- #
from fastapi import FastAPI, Query
from pydantic import BaseModel
import alpaca_trade_api as tradeapi
import ib_insync
import yfinance as yf
import mlflow
from statsmodels.tsa.arima.model import ARIMA
from textblob import TextBlob

# --- CONFIG ---
ALPACA_API_KEY = "your_key"
ALPACA_SECRET_KEY = "your_secret"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

IBKR_HOST = "127.0.0.1"
IBKR_PORT = 7497
IBKR_CLIENT_ID = 1

app = FastAPI(title="Draco Bot Mansa Money Bag API",
              description="Mansa Cosmos – Analysis, Forecasting, Live Trading",
              version="2.0.0")

# --- CONNECTORS ---
def connect_alpaca():
    return tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, base_url=ALPACA_BASE_URL)

def connect_ibkr():
    ib = ib_insync.IB()
    ib.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID)
    return ib

# --- MODELS ---
class TradeRequest(BaseModel):
    ticker: str
    qty: int
    side: str  # "buy" or "sell"
    broker: str  # "alpaca" or "ibkr"

# --- ENDPOINTS ---
@app.post("/trade")
def execute_trade(req: TradeRequest):
    if req.broker.lower() == "alpaca":
        api = connect_alpaca()
        order = api.submit_order(
            symbol=req.ticker,
            qty=req.qty,
            side=req.side,
            type="market",
            time_in_force="gtc"
        )
        return {"status": "submitted", "broker": "alpaca", "order": str(order)}

    elif req.broker.lower() == "ibkr":
        ib = connect_ibkr()
        contract = ib_insync.Stock(req.ticker, 'SMART', 'USD')
        if req.side.lower() == "buy":
            order = ib_insync.MarketOrder("BUY"