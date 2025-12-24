from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook
from datetime import datetime, timedelta
import requests

# Load Tiingo API token from environment variable
import os
TIINGO_API_TOKEN = os.getenv('TIINGO_API_KEY', '')

if not TIINGO_API_TOKEN:
    raise ValueError("TIINGO_API_KEY environment variable not set")

# Tickers to fetch - Updated to include commonly available tickers for testing
TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'RGTI', 'QBTS', 'SOUN', 'IONQ']

def fetch_tiingo_data(**kwargs):
    """Fetch 2 years of OHLC data for specified tickers and store in MySQL"""

    # Calculate date range (last 2 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # ~2 years

    # Get MySQL connection
    mysql_hook = MySqlHook(mysql_conn_id='mysql_bbbot1')
    conn = mysql_hook.get_conn()
    cursor = conn.cursor()

    # Create table if not exists - Named stock_prices_tiingo for clarity
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS stock_prices_tiingo (
        id INT AUTO_INCREMENT PRIMARY KEY,
        ticker VARCHAR(10) NOT NULL,
        date DATE NOT NULL,
        open DECIMAL(18, 4),
        high DECIMAL(18, 4),
        low DECIMAL(18, 4),
        close DECIMAL(18, 4),
        volume BIGINT,
        adj_open DECIMAL(18, 4),
        adj_high DECIMAL(18, 4),
        adj_low DECIMAL(18, 4),
        adj_close DECIMAL(18, 4),
        adj_volume BIGINT,
        split_factor DECIMAL(10, 6),
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
        print(f"Fetching data for {ticker}...")

        url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices"
        headers = {"Content-Type": "application/json"}
        params = {
            "token": TIINGO_API_TOKEN,
            "startDate": start_date.strftime('%Y-%m-%d'),
            "endDate": end_date.strftime('%Y-%m-%d')
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            print(f"Received {len(data)} records for {ticker}")

            # Insert data into MySQL
            insert_sql = """
            INSERT INTO stock_prices_tiingo
            (ticker, date, open, high, low, close, volume, adj_open, adj_high, adj_low, adj_close, adj_volume, split_factor)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                open = VALUES(open),
                high = VALUES(high),
                low = VALUES(low),
                close = VALUES(close),
                volume = VALUES(volume),
                adj_open = VALUES(adj_open),
                adj_high = VALUES(adj_high),
                adj_low = VALUES(adj_low),
                adj_close = VALUES(adj_close),
                adj_volume = VALUES(adj_volume),
                split_factor = VALUES(split_factor)
            """

            for record in data:
                date_obj = datetime.strptime(record['date'][:10], '%Y-%m-%d').date()
                cursor.execute(insert_sql, (
                    ticker,
                    date_obj,
                    record.get('open'),
                    record.get('high'),
                    record.get('low'),
                    record.get('close'),
                    record.get('volume'),
                    record.get('adjOpen'),
                    record.get('adjHigh'),
                    record.get('adjLow'),
                    record.get('adjClose'),
                    record.get('adjVolume'),
                    record.get('splitFactor', 1.0)
                ))

            conn.commit()
            total_records += len(data)
            successful_tickers.append(f"{ticker}({len(data)})")
            print(f"✓ Successfully stored {len(data)} records for {ticker}")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"⚠ {ticker}: Access denied (requires premium Tiingo subscription)")
                failed_tickers.append(f"{ticker}(403-Premium)")
            else:
                print(f"✗ Error fetching {ticker}: {str(e)}")
                failed_tickers.append(f"{ticker}({e.response.status_code})")
            conn.rollback()
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
    dag_id="tiingo_data_pull",
    default_args=default_args,
    description="Pull 2 years of OHLC stock data from Tiingo (AAPL, MSFT, GOOGL, AMZN, RGTI, QBTS, SOUN, IONQ)",
    schedule_interval="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["tiingo", "finance", "quantum"],
) as dag:

    fetch_data = PythonOperator(
        task_id="fetch_tiingo_data",
        python_callable=fetch_tiingo_data,
        provide_context=True,
    )

    fetch_data
