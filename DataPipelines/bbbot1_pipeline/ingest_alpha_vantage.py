"""
Alpha Vantage data ingestion module
Fetches fundamental data and stores in MySQL
"""

import os
import requests
import time
from dotenv import load_dotenv
from .db import get_mysql_connection, create_fundamentals_table

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), 'config.env'))

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')


def fetch_company_overview(ticker):
    """
    Fetch company overview/fundamentals from Alpha Vantage
    
    Args:
        ticker (str): Stock ticker symbol
    
    Returns:
        dict: Company fundamental data
    """
    if not ALPHA_VANTAGE_API_KEY or ALPHA_VANTAGE_API_KEY == 'your_alpha_vantage_key_here':
        raise ValueError("ALPHA_VANTAGE_API_KEY not configured in config.env")
    
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "OVERVIEW",
        "symbol": ticker,
        "apikey": ALPHA_VANTAGE_API_KEY
    }
    
    print(f"Fetching Alpha Vantage overview for {ticker}...")
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    data = response.json()
    
    if "Note" in data:
        raise Exception(f"API rate limit reached: {data['Note']}")
    
    if not data or "Symbol" not in data:
        raise Exception(f"No data returned for {ticker}")
    
    print(f"✓ Fetched overview for {ticker}")
    return data


def store_fundamentals(ticker, overview_data):
    """
    Store fundamental data in MySQL
    
    Args:
        ticker (str): Stock ticker symbol
        overview_data (dict): Data from Alpha Vantage OVERVIEW
    
    Returns:
        bool: Success status
    """
    # Create table if it doesn't exist
    create_fundamentals_table()
    
    conn = get_mysql_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO stock_fundamentals 
            (ticker, report_date, market_cap, pe_ratio, eps, revenue, net_income, total_assets, total_liabilities)
            VALUES (%s, CURDATE(), %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                market_cap = VALUES(market_cap),
                pe_ratio = VALUES(pe_ratio),
                eps = VALUES(eps),
                revenue = VALUES(revenue),
                net_income = VALUES(net_income),
                total_assets = VALUES(total_assets),
                total_liabilities = VALUES(total_liabilities)
            """
            
            # Extract and convert values (handle missing data)
            def safe_int(value):
                try:
                    return int(float(value)) if value and value != 'None' else None
                except (ValueError, TypeError):
                    return None
            
            def safe_float(value):
                try:
                    return float(value) if value and value != 'None' else None
                except (ValueError, TypeError):
                    return None
            
            cursor.execute(sql, (
                ticker,
                safe_int(overview_data.get('MarketCapitalization')),
                safe_float(overview_data.get('PERatio')),
                safe_float(overview_data.get('EPS')),
                safe_int(overview_data.get('RevenueTTM')),
                safe_int(overview_data.get('NetIncome')),
                safe_int(overview_data.get('TotalAssets')),
                safe_int(overview_data.get('TotalLiabilities'))
            ))
            
            conn.commit()
            print(f"✓ Stored fundamentals for {ticker}")
            return True
            
    except Exception as e:
        print(f"✗ Error storing fundamentals for {ticker}: {e}")
        return False
    finally:
        conn.close()


def run_alpha_vantage_ingestion(tickers, delay=12):
    """
    Run Alpha Vantage ingestion for multiple tickers
    
    Args:
        tickers (list): List of ticker symbols
        delay (int): Seconds to wait between API calls (free tier: 5 calls/min)
    
    Returns:
        int: Number of tickers successfully processed
    """
    print(f"\n{'='*60}")
    print(f"Alpha Vantage Ingestion Started")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Note: Free tier limit is 5 calls/minute")
    print(f"{'='*60}\n")
    
    success_count = 0
    
    for i, ticker in enumerate(tickers):
        try:
            overview = fetch_company_overview(ticker)
            if store_fundamentals(ticker, overview):
                success_count += 1
            
            # Rate limiting: wait between calls
            if i < len(tickers) - 1:
                print(f"Waiting {delay} seconds before next call...")
                time.sleep(delay)
                
        except Exception as e:
            print(f"✗ Failed to process {ticker}: {e}")
            continue
    
    print(f"\n✓ Successfully processed {success_count}/{len(tickers)} tickers")
    return success_count


if __name__ == "__main__":
    # Example: Fetch fundamentals for quantum stocks
    tickers = ["RGTI", "QBTS", "IONQ", "SOUN"]
    
    run_alpha_vantage_ingestion(tickers)
