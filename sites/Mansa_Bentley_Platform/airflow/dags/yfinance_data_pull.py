from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd

# Tickers to fetch - Quantum computing stocks
TICKERS = ['RGTI', 'QBTS', 'SOUN', 'IONQ']

def fetch_yfinance_data(**kwargs):
    """Fetch 2 years of OHLC data using yfinance and store in MySQL"""
    
    # Calculate date range (last 2 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # ~2 years
    
    # Get MySQL connection
    mysql_hook = MySqlHook(mysql_conn_id='mysql_bbbot1')
    conn = mysql_hook.get_conn()
    cursor = conn.cursor()
    
    # Create table if not exists
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS stock_prices_yf (
        id INT AUTO_INCREMENT PRIMARY KEY,
        ticker VARCHAR(10) NOT NULL,
        date DATE NOT NULL,
        open DECIMAL(18, 4),
        high DECIMAL(18, 4),
        low DECIMAL(18, 4),
        close DECIMAL(18, 4),
        volume BIGINT,
        adj_close DECIMAL(18, 4),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_ticker_date (ticker, date),
        INDEX idx_ticker (ticker),
        INDEX idx_date (date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    cursor.execute(create_table_sql)
    conn.commit()
    
    total_records = 0
    successful_tickers = []
    failed_tickers = []
    
    # Fetch data for each ticker
    for ticker in TICKERS:
        print(f"Fetching data for {ticker} from Yahoo Finance...")
        
        try:
            # Download data using yfinance
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date.strftime('%Y-%m-%d'), 
                             end=end_date.strftime('%Y-%m-%d'))
            
            if df.empty:
                print(f"⚠ No data available for {ticker}")
                failed_tickers.append(f"{ticker}(NoData)")
                continue
            
            print(f"Received {len(df)} records for {ticker}")
            
            # Insert data into MySQL
            insert_sql = """
            INSERT INTO stock_prices_yf 
            (ticker, date, open, high, low, close, volume, adj_close)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                open = VALUES(open),
                high = VALUES(high),
                low = VALUES(low),
                close = VALUES(close),
                volume = VALUES(volume),
                adj_close = VALUES(adj_close)
            """
            
            records_inserted = 0
            for date, row in df.iterrows():
                cursor.execute(insert_sql, (
                    ticker,
                    date.date(),
                    float(row['Open']) if pd.notna(row['Open']) else None,
                    float(row['High']) if pd.notna(row['High']) else None,
                    float(row['Low']) if pd.notna(row['Low']) else None,
                    float(row['Close']) if pd.notna(row['Close']) else None,
                    int(row['Volume']) if pd.notna(row['Volume']) else None,
                    float(row['Close']) if pd.notna(row['Close']) else None  # Using Close as adj_close
                ))
                records_inserted += 1
            
            conn.commit()
            total_records += records_inserted
            successful_tickers.append(f"{ticker}({records_inserted})")
            print(f"✓ Successfully stored {records_inserted} records for {ticker}")
            
        except Exception as e:
            print(f"✗ Error fetching {ticker}: {str(e)}")
            failed_tickers.append(f"{ticker}(Error)")
            conn.rollback()
    
    cursor.close()
    conn.close()
    
    print(f"\n=== Summary ===")
    print(f"Total records stored: {total_records}")
    print(f"Successful: {', '.join(successful_tickers) if successful_tickers else 'None'}")
    print(f"Failed: {', '.join(failed_tickers) if failed_tickers else 'None'}")
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    return {"total_records": total_records, "successful": len(successful_tickers), "failed": len(failed_tickers)}


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="yfinance_data_pull",
    default_args=default_args,
    description="Pull 2 years of OHLC stock data using yfinance for RGTI, QBTS, SOUN, IONQ",
    schedule_interval="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["yfinance", "finance", "quantum"],
) as dag:

    fetch_data = PythonOperator(
        task_id="fetch_yfinance_data",
        python_callable=fetch_yfinance_data,
        provide_context=True,
    )

    fetch_data
