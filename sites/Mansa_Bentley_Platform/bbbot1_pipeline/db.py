"""
Database utilities for BentleyBot pipeline
Handles MySQL connections and common database operations
"""

import os
import pymysql
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), 'config.env'))


def get_mysql_connection():
    """
    Get a raw PyMySQL connection to MySQL database
    
    Returns:
        pymysql.Connection: Database connection object
    """
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST', '127.0.0.1'),
        port=int(os.getenv('MYSQL_PORT', 3307)),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', 'root'),
        database=os.getenv('MYSQL_DATABASE', 'bbbot1'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def get_mysql_engine():
    """
    Get SQLAlchemy engine for pandas DataFrame operations
    
    Returns:
        sqlalchemy.engine.Engine: SQLAlchemy engine
    """
    host = os.getenv('MYSQL_HOST', '127.0.0.1')
    port = os.getenv('MYSQL_PORT', 3307)
    user = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', 'root')
    database = os.getenv('MYSQL_DATABASE', 'bbbot1')
    
    connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    return create_engine(connection_string)


def insert_stock_prices(df, table_name='stock_prices_yf', if_exists='append'):
    """
    Insert stock price data into MySQL
    
    Args:
        df (pd.DataFrame): DataFrame with columns: ticker, date, open, high, low, close, volume, adj_close
        table_name (str): Target table name
        if_exists (str): How to behave if table exists ('append', 'replace', 'fail')
    
    Returns:
        int: Number of rows inserted
    """
    engine = get_mysql_engine()
    rows_inserted = df.to_sql(table_name, con=engine, if_exists=if_exists, index=False)
    return rows_inserted


def query_latest_prices(ticker, days=30):
    """
    Get latest stock prices for a ticker
    
    Args:
        ticker (str): Stock ticker symbol
        days (int): Number of days to look back
    
    Returns:
        list: List of dictionaries with price data
    """
    conn = get_mysql_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT ticker, date, open, high, low, close, volume, adj_close
            FROM stock_prices_yf
            WHERE ticker = %s
            ORDER BY date DESC
            LIMIT %s
            """
            cursor.execute(sql, (ticker, days))
            return cursor.fetchall()
    finally:
        conn.close()


def query_fundamentals(ticker):
    """
    Get fundamental data for a ticker (placeholder for future implementation)
    
    Args:
        ticker (str): Stock ticker symbol
    
    Returns:
        dict: Fundamental data
    """
    # TODO: Implement when fundamentals table is created
    conn = get_mysql_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT * FROM stock_fundamentals
            WHERE ticker = %s
            ORDER BY report_date DESC
            LIMIT 1
            """
            cursor.execute(sql, (ticker,))
            return cursor.fetchone()
    finally:
        conn.close()


def create_fundamentals_table():
    """
    Create table for storing fundamental data (Alpha Vantage, etc.)
    """
    conn = get_mysql_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            CREATE TABLE IF NOT EXISTS stock_fundamentals (
                id INT AUTO_INCREMENT,
                ticker VARCHAR(10) NOT NULL,
                report_date DATE NOT NULL,
                market_cap BIGINT,
                pe_ratio DECIMAL(10, 2),
                eps DECIMAL(10, 4),
                revenue BIGINT,
                net_income BIGINT,
                total_assets BIGINT,
                total_liabilities BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (ticker, report_date),
                UNIQUE KEY id (id),
                INDEX idx_ticker (ticker),
                INDEX idx_date (report_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            cursor.execute(sql)
            conn.commit()
            print("✓ Created stock_fundamentals table")
    finally:
        conn.close()


if __name__ == "__main__":
    # Test database connection
    print("Testing MySQL connection...")
    try:
        conn = get_mysql_connection()
        print(f"✓ Connected to MySQL: {os.getenv('MYSQL_DATABASE')}")
        conn.close()
        
        engine = get_mysql_engine()
        print(f"✓ SQLAlchemy engine created")
        
        # Create fundamentals table if needed
        create_fundamentals_table()
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
