#alphavantage_fundamentals
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def get_engine():
    # mysql+pymysql://user:pass@host:3306/bbbot1
    return create_engine("mysql+pymysql://user:pass@localhost:3306/bbbot1", pool_recycle=3600)

def get_session():
    engine = get_engine()
    return sessionmaker(bind=engine)()

import os
import requests
import datetime as dt
from db import get_engine
import pandas as pd

ALPHA_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
BASE = "https://www.alphavantage.co/query"

def fetch_income_statement(ticker):
    url = f"{BASE}?function=INCOME_STATEMENT&symbol={ticker}&apikey={ALPHA_KEY}"
    r = requests.get(url, timeout=30); r.raise_for_status()
    return r.json()

def fetch_balance_sheet(ticker):
    url = f"{BASE}?function=BALANCE_SHEET&symbol={ticker}&apikey={ALPHA_KEY}"
    r = requests.get(url, timeout=30); r.raise_for_status()
    return r.json()

def fetch_cashflow(ticker):
    url = f"{BASE}?function=CASH_FLOW&symbol={ticker}&apikey={ALPHA_KEY}"
    r = requests.get(url, timeout=30); r.raise_for_status()
    return r.json()

def normalize_fundamentals(ticker, inc, bal):
    # take annual reports for last 3 years
    inc_reports = inc.get("annualReports", [])[:3]
    bal_reports = bal.get("annualReports", [])[:3]
    by_date = {}
    for r in inc_reports:
        d = r.get("fiscalDateEnding")
        by_date.setdefault(d, {}).update({
            "net_income": float(r.get("netIncome", "0") or 0),
            "ebit": float(r.get("ebit", "0") or 0),
            "ebitda": float(r.get("ebitda", "0") or 0),
            "fiscal_period": r.get("reportedCurrency"),
            "currency": r.get("reportedCurrency"),
            "fiscal_year": int(d[:4]) if d else None
        })
    for r in bal_reports:
        d = r.get("fiscalDateEnding")
        by_date.setdefault(d, {}).update({
            "total_assets": float(r.get("totalAssets", "0") or 0),
            "total_liabilities": float(r.get("totalLiabilities", "0") or 0),
            "total_equity": float(r.get("totalShareholderEquity", "0") or 0),
            "cash_and_equivalents": float(r.get("cashAndCashEquivalentsAtCarryingValue", "0") or 0),
            "shares_outstanding": float(r.get("commonStockSharesOutstanding", "0") or 0),
        })
    rows = []
    for d, vals in by_date.items():
        rows.append({
            "ticker": ticker,
            "report_date": d,
            **vals
        })
    return pd.DataFrame(rows)

def upsert_fundamentals(df):
    engine = get_engine()
    df.to_sql("fundamentals_raw", con=engine, if_exists="append", index=False)
    # optional: add ON DUPLICATE KEY via sqlalchemy core if needed

def run_alpha_vantage(tickers):
    for t in tickers:
        inc = fetch_income_statement(t)
        bal = fetch_balance_sheet(t)
        df = normalize_fundamentals(t, inc, bal)
        upsert_fundamentals(df)

if __name__ == "__main__":
    quantum_tickers = ["AMZN","AAPL"]  # add your quantum stocks list
    run_alpha_vantage(quantum_tickers)

# In your Airflow DAG
from bbbot1_pipeline.ingest_yfinance import fetch_prices
from bbbot1_pipeline.derive_ratios import calculate_pe_ratio

# Fetch data
fetch_prices(['RGTI', 'QBTS'])

# Calculate metrics
pe_ratio = calculate_pe_ratio('RGTI')