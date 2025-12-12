"""
Quick Test Script for Tiingo API Integration
Tests connection and fetches sample data to verify setup
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tiingo_integration import TiingoAPIClient
from dotenv import load_dotenv

# Load environment with cache-busting
load_dotenv(override=True)

# Try to use config_env reload if available
try:
    from config_env import reload_env
    reload_env(force=True)
except ImportError:
    pass

def test_tiingo_connection():
    """Test Tiingo API connection and data fetching"""
    
    print("=" * 70)
    print("TIINGO API CONNECTION TEST")
    print("=" * 70)
    print()
    
    # Check API key
    api_key = os.getenv('TIINGO_API_KEY')
    
    if not api_key:
        print("❌ TIINGO_API_KEY not found in environment variables")
        print()
        print("To fix:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your Tiingo API key: TIINGO_API_KEY=your_key_here")
        print("  3. Get a free key at: https://www.tiingo.com/")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    print()
    
    # Initialize client
    try:
        client = TiingoAPIClient(api_key)
        print("✅ Tiingo client initialized")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Test tickers (mix of common and quantum computing stocks)
    test_tickers = ['AAPL', 'MSFT', 'IONQ', 'QBTS']
    
    print("Testing with sample tickers:")
    print(f"  {', '.join(test_tickers)}")
    print()
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # Last 30 days
    
    results = {
        'success': [],
        'failed': [],
        'premium_required': []
    }
    
    for ticker in test_tickers:
        print(f"Testing {ticker}...")
        
        try:
            # Test metadata fetch
            metadata = client.fetch_ticker_metadata(ticker)
            
            if metadata:
                print(f"  ✅ Metadata: {metadata.get('name', 'N/A')}")
            else:
                print(f"  ⚠️  No metadata returned")
            
            # Test price data fetch
            df = client.fetch_daily_prices(ticker, start_date, end_date)
            
            if not df.empty:
                print(f"  ✅ Prices: {len(df)} records")
                print(f"     Latest: ${df['close'].iloc[-1]:.2f} on {df.index[-1].date()}")
                results['success'].append(ticker)
            else:
                print(f"  ⚠️  No price data returned")
                results['failed'].append(ticker)
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            
            if "403" in str(e) or "premium" in str(e).lower():
                results['premium_required'].append(ticker)
            else:
                results['failed'].append(ticker)
        
        print()
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    print(f"\n✅ Successful: {len(results['success'])}")
    if results['success']:
        print(f"   {', '.join(results['success'])}")
    
    print(f"\n⚠️  Premium Required: {len(results['premium_required'])}")
    if results['premium_required']:
        print(f"   {', '.join(results['premium_required'])}")
        print("   These tickers may require a premium Tiingo subscription")
    
    print(f"\n❌ Failed: {len(results['failed'])}")
    if results['failed']:
        print(f"   {', '.join(results['failed'])}")
    
    print()
    
    if results['success']:
        print("🎉 SUCCESS! Your Tiingo API is working correctly.")
        print()
        print("Next steps:")
        print("  1. Run full data fetch:")
        print("     python tiingo_integration.py --fetch all --technical --save-csv")
        print()
        print("  2. Fetch specific tickers:")
        print("     python tiingo_integration.py --tickers IONQ QBTS SOUN --technical")
        print()
        print("  3. Save to database:")
        print("     python tiingo_integration.py --fetch prices --save-db")
        print()
        print("  4. View in Streamlit:")
        print("     streamlit run 'pages/01_📈_Investment_Analysis.py'")
        return True
    else:
        print("⚠️  No successful data fetches. Please check:")
        print("  1. API key is valid")
        print("  2. Internet connection is working")
        print("  3. Tickers are valid symbols")
        return False


def test_database_connection():
    """Test MySQL database connection"""
    
    print()
    print("=" * 70)
    print("DATABASE CONNECTION TEST")
    print("=" * 70)
    print()
    
    try:
        from sqlalchemy import create_engine
        
        db_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', 'root'),
            'database': os.getenv('MYSQL_DATABASE', 'mansa_bot'),
        }
        
        print(f"Testing connection to:")
        print(f"  Host: {db_config['host']}:{db_config['port']}")
        print(f"  Database: {db_config['database']}")
        print(f"  User: {db_config['user']}")
        print()
        
        connection_string = (
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        
        engine = create_engine(connection_string, pool_recycle=3600)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            result.fetchone()
        
        print("✅ Database connection successful!")
        print()
        print("You can now use --save-db flag to save data to MySQL")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print()
        print("To fix:")
        print("  1. Ensure MySQL is running on port 3307")
        print("  2. Check database credentials in .env file")
        print("  3. Create database if needed: mysql -e 'CREATE DATABASE mansa_bot'")
        print("  4. Verify connection: mysql -u root -p -h localhost -P 3307")
        print()
        print("Note: CSV export will still work without database")
        return False


if __name__ == "__main__":
    print()
    print("🔬 TIINGO API SETUP TEST")
    print("=" * 70)
    print()
    
    # Test API connection
    api_ok = test_tiingo_connection()
    
    # Test database connection (optional)
    db_ok = test_database_connection()
    
    print()
    print("=" * 70)
    print("OVERALL STATUS")
    print("=" * 70)
    print()
    
    if api_ok:
        print("✅ Tiingo API: READY")
    else:
        print("❌ Tiingo API: NOT CONFIGURED")
    
    if db_ok:
        print("✅ Database: READY")
    else:
        print("⚠️  Database: NOT CONFIGURED (CSV export still available)")
    
    print()
    
    if api_ok:
        print("🚀 You're ready to fetch equity data!")
    else:
        print("⚠️  Please configure your Tiingo API key before proceeding")
    
    print()
