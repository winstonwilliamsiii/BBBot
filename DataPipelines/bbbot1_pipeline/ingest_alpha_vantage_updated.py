"""
Alpha Vantage data ingestion module - writes to fundamentals_raw table
Updated to match new Airbyte raw table schema
"""

import os
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import text
from .db import get_mysql_engine

# Load environment variables
load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')


def fetch_company_overview(ticker):
    """
    Fetch company overview/fundamentals from Alpha Vantage
    
    Args:
        ticker (str): Stock ticker symbol
    
    Returns:
        dict: Company fundamental data
    """
    if ALPHA_VANTAGE_API_KEY == 'demo':
        print("⚠️ Using demo API key - data will be limited")
    
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
    
    return data


def insert_fundamental_data(ticker, data):
    """
    Insert fundamental data into fundamentals_raw table
    
    Args:
        ticker (str): Stock ticker symbol
        data (dict): Fundamental data from Alpha Vantage
    """
    engine = get_mysql_engine()
    
    # Map Alpha Vantage fields to our schema
    insert_query = text("""
    INSERT INTO fundamentals_raw (
        ticker,
        report_date,
        fiscal_period,
        revenue,
        gross_profit,
        operating_income,
        net_income,
        ebit,
        ebitda,
        eps,
        total_assets,
        total_equity,
        total_liabilities,
        cash_and_equivalents,
        shares_outstanding,
        market_cap,
        source
    ) VALUES (
        :ticker,
        :report_date,
        :fiscal_period,
        :revenue,
        :gross_profit,
        :operating_income,
        :net_income,
        :ebit,
        :ebitda,
        :eps,
        :total_assets,
        :total_equity,
        :total_liabilities,
        :cash_and_equivalents,
        :shares_outstanding,
        :market_cap,
        :source
    )
    ON DUPLICATE KEY UPDATE
        revenue = VALUES(revenue),
        gross_profit = VALUES(gross_profit),
        operating_income = VALUES(operating_income),
        net_income = VALUES(net_income),
        ebit = VALUES(ebit),
        ebitda = VALUES(ebitda),
        eps = VALUES(eps),
        total_assets = VALUES(total_assets),
        total_equity = VALUES(total_equity),
        total_liabilities = VALUES(total_liabilities),
        cash_and_equivalents = VALUES(cash_and_equivalents),
        shares_outstanding = VALUES(shares_outstanding),
        market_cap = VALUES(market_cap),
        updated_at = CURRENT_TIMESTAMP
    """)
    
    # Helper function to safely convert to float
    def safe_float(value, default=None):
        try:
            return float(value) if value and value != 'None' else default
        except (ValueError, TypeError):
            return default
    
    # Prepare data
    params = {
        'ticker': ticker,
        'report_date': datetime.now().date(),  # Use current date as report date
        'fiscal_period': 'FY',  # Default to fiscal year
        'revenue': safe_float(data.get('RevenueTTM')),
        'gross_profit': safe_float(data.get('GrossProfitTTM')),
        'operating_income': safe_float(data.get('OperatingIncomeTTM')),
        'net_income': safe_float(data.get('NetIncomeTTM')),
        'ebit': safe_float(data.get('EBITDA')),  # Alpha Vantage doesn't separate EBIT
        'ebitda': safe_float(data.get('EBITDA')),
        'eps': safe_float(data.get('EPS')),
        'total_assets': safe_float(data.get('TotalAssets')),
        'total_equity': safe_float(data.get('ShareholderEquity')),
        'total_liabilities': safe_float(data.get('TotalLiabilities')),
        'cash_and_equivalents': safe_float(data.get('CashAndCashEquivalentsAtCarryingValue')),
        'shares_outstanding': int(safe_float(data.get('SharesOutstanding'), 0)),
        'market_cap': safe_float(data.get('MarketCapitalization')),
        'source': 'alphavantage'
    }
    
    # Validate required fields
    required_fields = ['net_income', 'ebit', 'ebitda', 'total_assets', 'total_equity', 
                       'total_liabilities', 'cash_and_equivalents', 'shares_outstanding']
    
    missing_fields = [field for field in required_fields if params[field] is None]
    
    if missing_fields:
        print(f"⚠️ Warning: Missing required fields for {ticker}: {missing_fields}")
        # Set defaults for missing required fields
        for field in missing_fields:
            if field == 'shares_outstanding':
                params[field] = 1  # Minimum value to avoid division by zero
            else:
                params[field] = 0.0
    
    # Execute insert
    with engine.connect() as conn:
        result = conn.execute(insert_query, params)
        conn.commit()
        print(f"✅ Inserted/updated fundamental data for {ticker}")
    
    return True


def run_alpha_vantage(tickers=None):
    """
    Main function to fetch and store Alpha Vantage data
    
    Args:
        tickers (list): List of ticker symbols to fetch
    """
    if tickers is None:
        tickers = ['IONQ', 'QBTS', 'SOUN', 'RGTI', 'AMZN', 'MSFT', 'GOOGL']
    
    print(f"Starting Alpha Vantage ingestion for {len(tickers)} tickers...")
    
    successful = []
    failed = []
    
    for ticker in tickers:
        try:
            # Fetch data
            data = fetch_company_overview(ticker)
            
            # Insert into database
            insert_fundamental_data(ticker, data)
            
            successful.append(ticker)
            
            # Rate limiting - Alpha Vantage allows 5 calls/minute on free tier
            if len(successful) < len(tickers):
                print("Waiting 12 seconds (rate limiting)...")
                time.sleep(12)
                
        except Exception as e:
            print(f"❌ Error processing {ticker}: {str(e)}")
            failed.append(ticker)
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Alpha Vantage Ingestion Complete")
    print(f"✅ Successful: {len(successful)} - {successful}")
    if failed:
        print(f"❌ Failed: {len(failed)} - {failed}")
    print(f"{'='*50}\n")
    
    return {'successful': successful, 'failed': failed}


if __name__ == "__main__":
    # Test the ingestion
    run_alpha_vantage(['IONQ', 'AMZN'])
