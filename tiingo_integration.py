"""
Tiingo API Integration for Equity Data
Fetches fundamentals, technical data, and price history for stock analysis

Usage:
    python tiingo_integration.py --fetch prices --tickers AAPL MSFT GOOGL
    python tiingo_integration.py --fetch fundamentals --tickers AAPL
    python tiingo_integration.py --fetch all --tickers IONQ QBTS SOUN RGTI
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import requests
import pandas as pd
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

TIINGO_API_KEY = os.getenv('TIINGO_API_KEY')
TIINGO_BASE_URL = "https://api.tiingo.com"

# Default tickers for quantum computing and AI stocks
DEFAULT_TICKERS = ['IONQ', 'QBTS', 'SOUN', 'RGTI', 'AAPL', 'MSFT', 'GOOGL', 'AMZN']


class TiingoAPIClient:
    """Client for Tiingo API integration"""
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("TIINGO_API_KEY not found in environment variables")
        
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {api_key}"
        }
    
    def fetch_daily_prices(
        self,
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Fetch daily OHLCV price data for a ticker
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date (default: 2 years ago)
            end_date: End date (default: today)
            
        Returns:
            DataFrame with columns: date, open, high, low, close, volume, adj_*
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=730)  # 2 years
        if not end_date:
            end_date = datetime.now()
        
        url = f"{TIINGO_BASE_URL}/tiingo/daily/{ticker}/prices"
        params = {
            "startDate": start_date.strftime('%Y-%m-%d'),
            "endDate": end_date.strftime('%Y-%m-%d')
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                print(f"⚠️  No data returned for {ticker}")
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            
            # Parse date and set as index
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            
            # Rename columns for consistency
            df = df.rename(columns={
                'adjOpen': 'adj_open',
                'adjHigh': 'adj_high',
                'adjLow': 'adj_low',
                'adjClose': 'adj_close',
                'adjVolume': 'adj_volume',
                'splitFactor': 'split_factor'
            })
            
            df['ticker'] = ticker
            
            print(f"✅ {ticker}: Fetched {len(df)} price records")
            return df
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"❌ {ticker}: Ticker not found")
            elif e.response.status_code == 403:
                print(f"⚠️  {ticker}: Access denied (may require premium subscription)")
            else:
                print(f"❌ {ticker}: HTTP error {e.response.status_code}")
            return pd.DataFrame()
        except Exception as e:
            print(f"❌ {ticker}: Error - {e}")
            return pd.DataFrame()
    
    def fetch_ticker_metadata(self, ticker: str) -> Dict:
        """
        Fetch metadata and fundamental information for a ticker
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with company information
        """
        url = f"{TIINGO_BASE_URL}/tiingo/daily/{ticker}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ {ticker}: Fetched metadata")
            return data
            
        except requests.exceptions.HTTPError as e:
            print(f"❌ {ticker}: HTTP error {e.response.status_code}")
            return {}
        except Exception as e:
            print(f"❌ {ticker}: Error - {e}")
            return {}
    
    def fetch_intraday_prices(
        self,
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        resample_freq: str = '5min'
    ) -> pd.DataFrame:
        """
        Fetch intraday price data (requires premium subscription)
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date (default: today)
            end_date: End date (default: today)
            resample_freq: Resampling frequency (1min, 5min, 15min, 30min, 1hour)
            
        Returns:
            DataFrame with intraday OHLCV data
        """
        if not start_date:
            start_date = datetime.now().replace(hour=0, minute=0, second=0)
        if not end_date:
            end_date = datetime.now()
        
        url = f"{TIINGO_BASE_URL}/iex/{ticker}/prices"
        params = {
            "startDate": start_date.strftime('%Y-%m-%d'),
            "endDate": end_date.strftime('%Y-%m-%d'),
            "resampleFreq": resample_freq
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                print(f"⚠️  No intraday data for {ticker}")
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            df['ticker'] = ticker
            
            print(f"✅ {ticker}: Fetched {len(df)} intraday records")
            return df
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"⚠️  {ticker}: Intraday data requires premium subscription")
            else:
                print(f"❌ {ticker}: HTTP error {e.response.status_code}")
            return pd.DataFrame()
        except Exception as e:
            print(f"❌ {ticker}: Error - {e}")
            return pd.DataFrame()
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators from price data
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added technical indicators
        """
        if df.empty:
            return df
        
        # Simple Moving Averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # Exponential Moving Averages
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # Volume Moving Average
        df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
        
        # Average True Range (ATR)
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(14).mean()
        
        return df


def save_to_mysql(df: pd.DataFrame, table_name: str, db_config: Optional[Dict] = None):
    """
    Save DataFrame to MySQL database
    
    Args:
        df: DataFrame to save
        table_name: Target table name
        db_config: Database configuration (default from env vars)
    """
    try:
        from sqlalchemy import create_engine
        
        if db_config is None:
            db_config = {
                'host': os.getenv('MYSQL_HOST', 'localhost'),
                'port': int(os.getenv('MYSQL_PORT', 3306)),
                'user': os.getenv('MYSQL_USER', 'root'),
                'password': os.getenv('MYSQL_PASSWORD', ''),
                'database': os.getenv('MYSQL_DATABASE', 'bbbot1'),
            }
        
        connection_string = (
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        
        engine = create_engine(connection_string, pool_recycle=3600)
        
        # Reset index to include date as column
        df_save = df.reset_index()
        
        # Save to database (replace if exists)
        df_save.to_sql(table_name, engine, if_exists='append', index=False)
        
        print(f"✅ Saved {len(df)} records to {table_name}")
        
    except Exception as e:
        print(f"❌ Failed to save to MySQL: {e}")


def save_to_csv(df: pd.DataFrame, filename: str, output_dir: str = "data"):
    """
    Save DataFrame to CSV file
    
    Args:
        df: DataFrame to save
        filename: Output filename
        output_dir: Output directory
    """
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filepath = output_path / filename
        df.to_csv(filepath, index=True)
        
        print(f"✅ Saved to {filepath}")
        
    except Exception as e:
        print(f"❌ Failed to save CSV: {e}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Tiingo API Integration for Equity Data"
    )
    parser.add_argument(
        '--fetch',
        choices=['prices', 'metadata', 'intraday', 'all'],
        default='prices',
        help='Type of data to fetch'
    )
    parser.add_argument(
        '--tickers',
        nargs='+',
        default=DEFAULT_TICKERS,
        help='List of ticker symbols'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=730,
        help='Number of days of historical data (default: 730 = 2 years)'
    )
    parser.add_argument(
        '--technical',
        action='store_true',
        help='Calculate technical indicators'
    )
    parser.add_argument(
        '--save-db',
        action='store_true',
        help='Save to MySQL database'
    )
    parser.add_argument(
        '--save-csv',
        action='store_true',
        help='Save to CSV file'
    )
    parser.add_argument(
        '--output-dir',
        default='data',
        help='Output directory for CSV files'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("TIINGO API INTEGRATION - EQUITY DATA FETCHER")
    print("=" * 70)
    
    # Check API key
    if not TIINGO_API_KEY:
        print("\n❌ ERROR: TIINGO_API_KEY not found in environment variables")
        print("\nPlease set your Tiingo API key:")
        print("  1. Create a .env file in the project root")
        print("  2. Add: TIINGO_API_KEY=your_api_key_here")
        print("  3. Or export: export TIINGO_API_KEY=your_api_key_here")
        sys.exit(1)
    
    print(f"\n✅ API Key found: {TIINGO_API_KEY[:8]}...")
    print(f"📊 Tickers: {', '.join(args.tickers)}")
    print(f"📅 Lookback: {args.days} days")
    print(f"🔧 Technical Indicators: {'Yes' if args.technical else 'No'}")
    print()
    
    # Initialize client
    client = TiingoAPIClient(TIINGO_API_KEY)
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    
    all_data = []
    
    # Fetch data for each ticker
    for ticker in args.tickers:
        print(f"\n{'=' * 70}")
        print(f"Processing: {ticker}")
        print(f"{'=' * 70}")
        
        if args.fetch in ['metadata', 'all']:
            metadata = client.fetch_ticker_metadata(ticker)
            if metadata:
                print(f"  Name: {metadata.get('name', 'N/A')}")
                print(f"  Exchange: {metadata.get('exchangeCode', 'N/A')}")
                print(f"  Start Date: {metadata.get('startDate', 'N/A')}")
        
        if args.fetch in ['prices', 'all']:
            df = client.fetch_daily_prices(ticker, start_date, end_date)
            
            if not df.empty:
                # Calculate technical indicators if requested
                if args.technical:
                    print(f"  Calculating technical indicators...")
                    df = client.calculate_technical_indicators(df)
                
                all_data.append(df)
                
                # Save individual ticker data
                if args.save_csv:
                    filename = f"{ticker}_prices_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
                    save_to_csv(df, filename, args.output_dir)
        
        if args.fetch == 'intraday':
            df = client.fetch_intraday_prices(ticker, start_date, end_date)
            if not df.empty:
                all_data.append(df)
                
                if args.save_csv:
                    filename = f"{ticker}_intraday_{datetime.now().strftime('%Y%m%d')}.csv"
                    save_to_csv(df, filename, args.output_dir)
    
    # Combine all data and save to database
    if all_data and args.save_db:
        print(f"\n{'=' * 70}")
        print("Saving to MySQL Database")
        print(f"{'=' * 70}")
        
        combined_df = pd.concat(all_data, ignore_index=False)
        
        table_name = 'stock_prices_tiingo'
        if args.technical:
            table_name = 'stock_prices_tiingo_technical'
        
        save_to_mysql(combined_df, table_name)
    
    print(f"\n{'=' * 70}")
    print("COMPLETE!")
    print(f"{'=' * 70}")
    print(f"✅ Processed {len(args.tickers)} tickers")
    print(f"✅ Total records: {sum(len(df) for df in all_data)}")
    
    if args.save_csv:
        print(f"✅ CSV files saved to: {args.output_dir}/")
    
    if args.save_db:
        print(f"✅ Data saved to MySQL table: {table_name}")
    
    print("\n💡 Next steps:")
    print("  1. View data in Streamlit: streamlit run 'pages/01_📈_Investment_Analysis.py'")
    print("  2. Query database: mysql -u user -p bbbot1")
    print(f"  3. Check CSV files: ls {args.output_dir}/")


if __name__ == "__main__":
    main()
