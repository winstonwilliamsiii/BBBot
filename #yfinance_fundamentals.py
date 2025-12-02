#yfinance_fundamentals

import datetime as dt
import pandas as pd
import yfinance as yf
from db import get_engine

def fetch_prices(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    data = data.reset_index()
    data.rename(columns={
        "Date":"date","Open":"open","High":"high","Low":"low","Close":"close",
        "Adj Close":"adj_close","Volume":"volume"
    }, inplace=True)
    data["ticker"] = ticker
    return data[["ticker","date","open","high","low","close","adj_close","volume"]]

def run_yf(tickers):
    end = dt.date.today()
    start = end - dt.timedelta(days=365*3)
    engine = get_engine()
    for t in tickers:
        df = fetch_prices(t, start, end)
        df.to_sql("prices_daily", con=engine, if_exists="append", index=False)

if __name__ == "__main__":
    tickers = ["AMZN","AAPL"]
    run_yf(tickers)

# In your Airflow DAG
from bbbot1_pipeline.ingest_yfinance import fetch_prices
from bbbot1_pipeline.derive_ratios import calculate_pe_ratio

# Fetch data
fetch_prices(['RGTI', 'QBTS'])

# Calculate metrics
pe_ratio = calculate_pe_ratio('RGTI')