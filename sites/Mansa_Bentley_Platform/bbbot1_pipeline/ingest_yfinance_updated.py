"""
yfinance data ingestion module - writes to prices_daily table
Updated to match new Airbyte raw table schema
"""

import yfinance as yf
from datetime import datetime, timedelta
from sqlalchemy import text
from .db import get_mysql_engine


def fetch_yfinance_prices(ticker, start_date=None, end_date=None):
    """
    Fetch price data from yfinance
    
    Args:
        ticker (str): Stock ticker symbol
        start_date (str): Start date (YYYY-MM-DD)
        end_date (str): End date (YYYY-MM-DD)
    
    Returns:
        pd.DataFrame: Price data
    """
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Fetching yfinance data for {ticker} from {start_date} to {end_date}...")
    
    ticker_obj = yf.Ticker(ticker)
    df = ticker_obj.history(start=start_date, end=end_date)
    
    if df.empty:
        print(f"⚠️ No data returned for {ticker}")
        return None
    
    # Reset index to get date as column
    df = df.reset_index()
    
    print(f"✅ Fetched {len(df)} records for {ticker}")
    
    return df


def insert_price_data(ticker, df):
    """
    Insert price data into prices_daily table
    
    Args:
        ticker (str): Stock ticker symbol
        df (pd.DataFrame): Price data from yfinance
    """
    engine = get_mysql_engine()
    
    insert_query = text("""
    INSERT INTO prices_daily (
        ticker,
        date,
        open,
        high,
        low,
        close,
        volume,
        adj_close,
        source
    ) VALUES (
        :ticker,
        :date,
        :open,
        :high,
        :low,
        :close,
        :volume,
        :adj_close,
        :source
    )
    ON DUPLICATE KEY UPDATE
        open = VALUES(open),
        high = VALUES(high),
        low = VALUES(low),
        close = VALUES(close),
        volume = VALUES(volume),
        adj_close = VALUES(adj_close),
        updated_at = CURRENT_TIMESTAMP
    """)
    
    records_inserted = 0
    
    with engine.connect() as conn:
        for idx, row in df.iterrows():
            params = {
                'ticker': ticker,
                'date': row['Date'].date() if hasattr(row['Date'], 'date') else row['Date'],
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume']),
                'adj_close': float(row['Close']),  # yfinance doesn't separate adj_close in history
                'source': 'yfinance'
            }
            
            conn.execute(insert_query, params)
            records_inserted += 1
        
        conn.commit()
    
    print(f"✅ Inserted {records_inserted} price records for {ticker}")
    return records_inserted


def run_yfinance_ingestion(tickers=None, days_back=365):
    """
    Main function to fetch and store yfinance price data
    
    Args:
        tickers (list): List of ticker symbols
        days_back (int): Number of days of historical data to fetch
    """
    if tickers is None:
        tickers = ['IONQ', 'QBTS', 'SOUN', 'RGTI', 'AMZN', 'MSFT', 'GOOGL']
    
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Starting yfinance ingestion for {len(tickers)} tickers...")
    print(f"Date range: {start_date} to {end_date}")
    
    successful = []
    failed = []
    total_records = 0
    
    for ticker in tickers:
        try:
            # Fetch data
            df = fetch_yfinance_prices(ticker, start_date, end_date)
            
            if df is not None:
                # Insert into database
                records = insert_price_data(ticker, df)
                total_records += records
                successful.append(ticker)
            else:
                failed.append(ticker)
                
        except Exception as e:
            print(f"❌ Error processing {ticker}: {str(e)}")
            failed.append(ticker)
    
    # Summary
    print(f"\n{'='*50}")
    print(f"yfinance Ingestion Complete")
    print(f"✅ Successful: {len(successful)} - {successful}")
    print(f"📊 Total records inserted: {total_records}")
    if failed:
        print(f"❌ Failed: {len(failed)} - {failed}")
    print(f"{'='*50}\n")
    
    return {'successful': successful, 'failed': failed, 'total_records': total_records}


# Alias for backward compatibility
run_yf = run_yfinance_ingestion


if __name__ == "__main__":
    # Test the ingestion
    run_yfinance_ingestion(['IONQ', 'AMZN'], days_back=30)
