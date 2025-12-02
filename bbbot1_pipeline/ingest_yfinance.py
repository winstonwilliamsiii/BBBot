"""
yfinance data ingestion module
Fetches stock prices from Yahoo Finance and stores in MySQL
"""

import os
import datetime as dt
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from .db import get_mysql_engine, insert_stock_prices

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), 'config.env'))


def fetch_yfinance_prices(ticker, start_date, end_date):
    """
    Fetch stock price data from Yahoo Finance for a single ticker
    
    Args:
        ticker (str): Stock ticker symbol
        start_date (str or datetime): Start date for data fetch
        end_date (str or datetime): End date for data fetch
    
    Returns:
        pd.DataFrame: DataFrame with columns: ticker, date, open, high, low, close, adj_close, volume
    """
    print(f"Fetching {ticker} from {start_date} to {end_date}...")
    
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    
    if data.empty:
        print(f"⚠ No data returned for {ticker}")
        return pd.DataFrame()
    
    data = data.reset_index()
    
    # Rename columns to match database schema
    data.rename(columns={
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume"
    }, inplace=True)
    
    data["ticker"] = ticker
    
    # Ensure date is in correct format
    data["date"] = pd.to_datetime(data["date"]).dt.date
    
    print(f"✓ Fetched {len(data)} records for {ticker}")
    
    return data[["ticker", "date", "open", "high", "low", "close", "adj_close", "volume"]]


def fetch_yfinance_batch(tickers, start_date, end_date):
    """
    Fetch stock prices for multiple tickers in batch
    
    Args:
        tickers (list): List of ticker symbols
        start_date (str or datetime): Start date
        end_date (str or datetime): End date
    
    Returns:
        pd.DataFrame: Combined DataFrame with all tickers
    """
    all_data = []
    
    for ticker in tickers:
        try:
            df = fetch_yfinance_prices(ticker, start_date, end_date)
            if not df.empty:
                all_data.append(df)
        except Exception as e:
            print(f"✗ Error fetching {ticker}: {e}")
            continue
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame()


def run_yfinance_ingestion(tickers, lookback_days=None, table_name='stock_prices_yf'):
    """
    Main function to run yfinance ingestion for multiple tickers
    
    Args:
        tickers (list): List of ticker symbols
        lookback_days (int): Number of days to look back (default from config)
        table_name (str): Target MySQL table name
    
    Returns:
        int: Number of records inserted
    """
    if lookback_days is None:
        lookback_days = int(os.getenv('DEFAULT_LOOKBACK_DAYS', 730))
    
    end_date = dt.date.today()
    start_date = end_date - dt.timedelta(days=lookback_days)
    
    print(f"\n{'='*60}")
    print(f"yfinance Ingestion Started")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Period: {start_date} to {end_date} ({lookback_days} days)")
    print(f"Target Table: {table_name}")
    print(f"{'='*60}\n")
    
    # Fetch data
    df = fetch_yfinance_batch(tickers, start_date, end_date)
    
    if df.empty:
        print("⚠ No data fetched. Exiting.")
        return 0
    
    # Store in MySQL
    try:
        rows_inserted = insert_stock_prices(df, table_name=table_name, if_exists='append')
        print(f"\n✓ Successfully inserted {len(df)} records into {table_name}")
        
        # Summary by ticker
        print("\nSummary by ticker:")
        for ticker in tickers:
            count = len(df[df['ticker'] == ticker])
            if count > 0:
                print(f"  {ticker}: {count} records")
        
        return rows_inserted
        
    except Exception as e:
        print(f"✗ Error inserting data: {e}")
        return 0


if __name__ == "__main__":
    # Example: Fetch quantum computing stocks
    tickers = ["RGTI", "QBTS", "IONQ", "SOUN"]
    
    # Run ingestion for 2 years of data
    run_yfinance_ingestion(tickers, lookback_days=730)
