#Bot Signals Analytic Head API issues

#Purpose: resolving the likely break: API connectors (Plaid, FRED, Alpaca, TradingView) not populating values before signal evaluation.

# ingestion.py

import yfinance as yf
import requests

def fetch_symbol_data(symbol: str):
    try:
        data = yf.download(symbol, period="1d", interval="1m")
        if data.empty:
            raise ValueError("No data returned")
        return data
    except Exception as e:
        print(f"[ERROR] Data ingestion failed: {e}")
        return None

def compute_rsi(prices, window=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

