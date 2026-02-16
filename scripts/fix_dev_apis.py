"""
Development API Connection Fixer
=================================
Tests and fixes all API connections for localhost:8501 development environment.

This script:
1. Tests MySQL connection
2. Tests yFinance availability
3. Tests Alpaca API
4. Tests Plaid API
5. Tests AlphaVantage API
6. Verifies ML models and trading signals
7. Checks Prediction Analytics dependencies
"""

import os
import sys
from dotenv import load_dotenv

# Load .env.development
load_dotenv('.env.development', override=True)

def test_mysql():
    """Test MySQL connection"""
    print("\n" + "="*60)
    print("1️⃣  TESTING MYSQL CONNECTION")
    print("="*60)
    
    try:
        import mysql.connector
        
        config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'bentley_bot_dev')
        }
        
        print(f"   Host: {config['host']}")
        print(f"   Port: {config['port']}")
        print(f"   Database: {config['database']}")
        print(f"   User: {config['user']}")
        
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        
        print(f"✅ MySQL connected successfully!")
        print(f"   Version: {version[0]}")
        
        # Check if database exists
        cursor.execute(f"SHOW DATABASES LIKE '{config['database']}'")
        db_exists = cursor.fetchone()
        
        if not db_exists:
            print(f"⚠️  Database '{config['database']}' does not exist. Creating...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']}")
            print(f"✅ Database created!")
        
        cursor.close()
        conn.close()
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ MySQL connection failed: {err}")
        print("\n🔧 Fix:")
        print("   1. Ensure MySQL is running: Get-Service MySQL*")
        print("   2. Update .env.development with correct credentials")
        print("   3. Create database: CREATE DATABASE bentley_bot_dev;")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_yfinance():
    """Test yFinance availability"""
    print("\n" + "="*60)
    print("2️⃣  TESTING YFINANCE")
    print("="*60)
    
    try:
        import yfinance as yf
        
        # Test fetching data
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        
        if info and 'symbol' in info:
            print(f"✅ yFinance working!")
            print(f"   Test ticker: AAPL")
            print(f"   Current price: ${info.get('currentPrice', 'N/A')}")
            return True
        else:
            print("⚠️  yFinance installed but data fetch failed")
            return False
            
    except ImportError:
        print("❌ yFinance not installed")
        print("\n🔧 Fix: pip install yfinance")
        return False
    except Exception as e:
        print(f"⚠️  yFinance error: {e}")
        print("   This might be a temporary network issue")
        return False


def test_alpaca():
    """Test Alpaca API connection"""
    print("\n" + "="*60)
    print("3️⃣  TESTING ALPACA API")
    print("="*60)
    
    api_key = os.getenv('ALPACA_API_KEY', '')
    secret_key = os.getenv('ALPACA_SECRET_KEY', '')
    base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
    
    print(f"   API Key: {api_key[:10]}..." if api_key else "   API Key: NOT SET")
    print(f"   Environment: {os.getenv('ALPACA_ENVIRONMENT', 'paper')}")
    
    if not api_key or 'placeholder' in api_key:
        print("❌ Alpaca API key not configured")
        print("\n🔧 Fix:")
        print("   1. Sign up at https://alpaca.markets")
        print("   2. Get paper trading API keys")
        print("   3. Update .env.development:")
        print("      ALPACA_API_KEY=your_key")
        print("      ALPACA_SECRET_KEY=your_secret")
        return False
    
    try:
        from alpaca.trading.client import TradingClient
        
        client = TradingClient(api_key, secret_key, paper=True)
        account = client.get_account()
        
        print(f"✅ Alpaca connected successfully!")
        print(f"   Account status: {account.status}")
        print(f"   Buying power: ${float(account.buying_power):.2f}")
        return True
        
    except ImportError:
        print("❌ Alpaca SDK not installed")
        print("\n🔧 Fix: pip install alpaca-py")
        return False
    except Exception as e:
        print(f"❌ Alpaca connection failed: {e}")
        return False


def test_plaid():
    """Test Plaid API connection"""
    print("\n" + "="*60)
    print("4️⃣  TESTING PLAID API")
    print("="*60)
    
    client_id = os.getenv('PLAID_CLIENT_ID', '')
    secret = os.getenv('PLAID_SECRET', '')
    environment = os.getenv('PLAID_ENVIRONMENT', 'sandbox')
    
    print(f"   Client ID: {client_id[:10]}..." if client_id else "   Client ID: NOT SET")
    print(f"   Environment: {environment}")
    
    if not client_id or 'placeholder' in client_id:
        print("❌ Plaid credentials not configured")
        print("\n🔧 Fix:")
        print("   1. Sign up at https://plaid.com")
        print("   2. Get sandbox credentials")
        print("   3. Update .env.development:")
        print("      PLAID_CLIENT_ID=your_client_id")
        print("      PLAID_SECRET=your_secret")
        return False
    
    try:
        import plaid
        from plaid.api import plaid_api
        from plaid.model.products import Products
        from plaid.model.country_code import CountryCode
        
        print("✅ Plaid SDK installed")
        print("   Note: Full connection test requires Link token generation")
        return True
        
    except ImportError:
        print("❌ Plaid SDK not installed")
        print("\n🔧 Fix: pip install plaid-python")
        return False
    except Exception as e:
        print(f"⚠️  Error: {e}")
        return False


def test_alphavantage():
    """Test AlphaVantage API"""
    print("\n" + "="*60)
    print("5️⃣  TESTING ALPHAVANTAGE API")
    print("="*60)
    
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY', '')
    
    print(f"   API Key: {api_key[:10]}..." if api_key else "   API Key: NOT SET")
    
    if not api_key:
        print("⚠️  AlphaVantage API key not set")
        print("   This is optional - used for enhanced fundamental data")
        print("\n🔧 To enable:")
        print("   1. Get free key at https://www.alphavantage.co/support/#api-key")
        print("   2. Update .env.development:")
        print("      ALPHA_VANTAGE_API_KEY=your_key")
        return False
    
    try:
        import requests
        
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={api_key}'
        response = requests.get(url)
        data = response.json()
        
        if 'Global Quote' in data:
            print("✅ AlphaVantage connected!")
            quote = data['Global Quote']
            print(f"   Test symbol: AAPL")
            print(f"   Price: ${quote.get('05. price', 'N/A')}")
            return True
        else:
            print(f"⚠️  API response unexpected: {data}")
            return False
            
    except Exception as e:
        print(f"❌ AlphaVantage test failed: {e}")
        return False


def test_ml_signals():
    """Test ML Trading Signals"""
    print("\n" + "="*60)
    print("6️⃣  TESTING ML TRADING SIGNALS")
    print("="*60)
    
    try:
        import mlflow
        print("✅ MLflow installed")
        
        # Check if MLflow server is running
        tracking_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
        print(f"   Tracking URI: {tracking_uri}")
        
        try:
            mlflow.set_tracking_uri(tracking_uri)
            experiments = mlflow.search_experiments()
            print(f"✅ MLflow server reachable")
            print(f"   Experiments: {len(experiments)}")
            return True
        except Exception as e:
            print(f"⚠️  MLflow server not reachable: {e}")
            print("   Trading signals will use fallback mode")
            return False
            
    except ImportError:
        print("❌ MLflow not installed")
        print("\n🔧 Fix: pip install mlflow")
        return False


def test_prediction_analytics():
    """Test Prediction Analytics dependencies"""
    print("\n" + "="*60)
    print("7️⃣  TESTING PREDICTION ANALYTICS")
    print("="*60)
    
    kalshi_key = os.getenv('KALSHI_ACCESS_KEY', '')
    kalshi_private = os.getenv('KALSHI_PRIVATE_KEY', '')
    
    print(f"   Kalshi Access Key: {kalshi_key[:10]}..." if kalshi_key else "   Access Key: NOT SET")
    
    if kalshi_key and kalshi_private and 'ea376fd0' in kalshi_key:
        print("✅ Kalshi credentials configured")
        print("   Note: Prediction Analytics page requires ADMIN role")
        return True
    else:
        print("⚠️  Kalshi credentials not fully configured")
        print("   The credentials in .env.development appear to be from config")
        return False


def create_streamlit_secrets():
    """Create .streamlit/secrets.toml for local development"""
    print("\n" + "="*60)
    print("8️⃣  CREATING STREAMLIT SECRETS FILE")
    print("="*60)
    
    secrets_dir = '.streamlit'
    secrets_file = os.path.join(secrets_dir, 'secrets.toml')
    
    if not os.path.exists(secrets_dir):
        os.makedirs(secrets_dir)
        print(f"✅ Created {secrets_dir} directory")
    
    # Read current .env.development
    secrets_content = f"""# Streamlit Secrets for Local Development
# Auto-generated from .env.development
# Keep this file in .gitignore

[database]
DB_HOST = "{os.getenv('DB_HOST', 'localhost')}"
DB_PORT = "{os.getenv('DB_PORT', '3306')}"
DB_USER = "{os.getenv('DB_USER', 'root')}"
DB_PASSWORD = "{os.getenv('DB_PASSWORD', '')}"
DB_NAME = "{os.getenv('DB_NAME', 'bentley_bot_dev')}"

[alpaca]
ALPACA_API_KEY = "{os.getenv('ALPACA_API_KEY', '')}"
ALPACA_SECRET_KEY = "{os.getenv('ALPACA_SECRET_KEY', '')}"
ALPACA_BASE_URL = "{os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')}"

[plaid]
PLAID_CLIENT_ID = "{os.getenv('PLAID_CLIENT_ID', '')}"
PLAID_SECRET = "{os.getenv('PLAID_SECRET', '')}"
PLAID_ENVIRONMENT = "{os.getenv('PLAID_ENVIRONMENT', 'sandbox')}"

[alphavantage]
ALPHA_VANTAGE_API_KEY = "{os.getenv('ALPHA_VANTAGE_API_KEY', '')}"

[kalshi]
KALSHI_ACCESS_KEY = "{os.getenv('KALSHI_ACCESS_KEY', '')}"
KALSHI_PRIVATE_KEY = "{os.getenv('KALSHI_PRIVATE_KEY', '')}"
"""
    
    with open(secrets_file, 'w') as f:
        f.write(secrets_content)
    
    print(f"✅ Created {secrets_file}")
    print("   Streamlit will now read secrets from this file")


def main():
    """Run all API connection tests"""
    print("\n" + "🚀 BENTLEY BOT - DEVELOPMENT API CONNECTION CHECKER")
    print("=" * 60)
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Target: {os.getenv('DEPLOYMENT_TARGET', 'localhost')}")
    print("=" * 60)
    
    results = {
        'MySQL': test_mysql(),
        'yFinance': test_yfinance(),
        'Alpaca': test_alpaca(),
        'Plaid': test_plaid(),
        'AlphaVantage': test_alphavantage(),
        'ML Signals': test_ml_signals(),
        'Prediction Analytics': test_prediction_analytics()
    }
    
    # Create secrets file
    create_streamlit_secrets()
    
    # Summary
    print("\n" + "="*60)
    print("📊 CONNECTION SUMMARY")
    print("="*60)
    
    for service, status in results.items():
        icon = "✅" if status else "❌"
        print(f"   {icon} {service}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n   {passed}/{total} services configured")
    
    if passed < total:
        print("\n⚠️  Some services need configuration.")
        print("   Update .env.development with real API credentials")
        print("   See instructions above for each service")
    else:
        print("\n✅ All services configured!")
        print("   Ready to run: streamlit run streamlit_app.py")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
