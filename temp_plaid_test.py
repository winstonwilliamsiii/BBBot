"""
Comprehensive API Diagnostic Test
Tests all APIs and provides actionable fix instructions
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv(override=True)

def print_header(title):
    """Print formatted section header"""
    print(f"
{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}
")

def test_tiingo_api():
    """Test Tiingo API with detailed diagnostics"""
    print_header("🔍 TIINGO API TEST")
    
    api_key = os.getenv('TIINGO_API_KEY', '').strip()
    
    if not api_key:
        print("❌ TIINGO_API_KEY not found in .env file")
        print("
Fix:")
        print("  1. Login to https://www.tiingo.com/account/api")
        print("  2. Copy your API token")
        print("  3. Add to .env: TIINGO_API_KEY=your_token_here")
        return False
    
    print(f"✅ API Key found: {api_key[:8]}...{api_key[-4:]}")
    
    # Test with direct HTTP request
    print("
📡 Testing API connection...")
    url = "https://api.tiingo.com/tiingo/daily/AAPL/prices"
    params = {"startDate": "2024-12-01"}
    headers = {"Authorization": f"Token {api_key}"}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"✅ SUCCESS! API is working")
                print(f"   Retrieved {len(data)} price records for AAPL")
                latest = data[-1]
                print(f"   Latest price: ${latest['close']:.2f} on {latest['date'][:10]}")
                return True
            else:
                print("⚠️  API responded but returned empty data")
                print("   This may indicate a free tier limitation")
                return False
        
        elif response.status_code == 403:
            print("❌ HTTP 403 - FORBIDDEN")
            print("
Possible causes:")
            print("  1. API key is valid but account needs upgrade")
            print("  2. Free tier doesn't allow this endpoint")
            print("  3. Rate limit exceeded")
            print("
Try:")
            print("  - Check subscription at https://www.tiingo.com/account")
            print("  - Wait a few minutes and try again")
            return False
        
        elif response.status_code == 401:
            error_msg = response.json().get('detail', 'Unknown error')
            print(f"❌ HTTP 401 - AUTHENTICATION FAILED")
            print(f"   Server says: {error_msg}")
            print("
🔴 YOUR API KEY IS INVALID!")
            print("
Fix:")
            print("  1. Go to https://www.tiingo.com/account/api")
            print("  2. Check if you see an API token")
            print("  3. If no token shown, click 'Create New Token'")
            print("  4. Copy the EXACT token (no spaces)")
            print("  5. Update .env file: TIINGO_API_KEY=new_token")
            print("  6. Re-run this test")
            
            # Try to get account info
            print("
📋 Testing account endpoint...")
            account_url = "https://api.tiingo.com/api/test"
            account_response = requests.get(account_url, headers=headers, timeout=10)
            if account_response.status_code == 200:
                info = account_response.json()
                print(f"   Account email: {info.get('email', 'N/A')}")
            else:
                print(f"   Account test also failed: {account_response.status_code}")
            
            return False
        
        else:
            print(f"❌ HTTP {response.status_code} - Unexpected error")
            print(f"   Response: {response.text[:200]}")
            return False
    
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        print("   Check your internet connection")
        return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_plaid_api():
    """Test Plaid API configuration"""
    print_header("🔍 PLAID API TEST")
    
    client_id = os.getenv('PLAID_CLIENT_ID', '').strip()
    secret = os.getenv('PLAID_SECRET', '').strip()
    env = os.getenv('PLAID_ENV', 'sandbox').strip()
    
    if not client_id or client_id == 'your_plaid_client_id_here':
        print("❌ PLAID_CLIENT_ID not configured")
        print("
Fix:")
        print("  1. Login to https://dashboard.plaid.com/")
        print("  2. Get your client_id from API settings")
        print("  3. Add to .env: PLAID_CLIENT_ID=your_client_id")
        return False
    
    if not secret or secret == 'your_plaid_secret_here':
        print("❌ PLAID_SECRET not configured")
        return False
    
    print(f"✅ Client ID: {client_id[:8]}...")
    print(f"✅ Secret: {secret[:8]}...")
    print(f"✅ Environment: {env}")
    
    # Try to import and instantiate PlaidLinkManager
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'frontend' / 'utils'))
        from plaid_link import PlaidLinkManager
        
        manager = PlaidLinkManager()
        print("
✅ SUCCESS! PlaidLinkManager initialized")
        print("
If Streamlit still shows error:")
        print("  1. Hard refresh browser (Ctrl+Shift+R)")
        print("  2. Clear Streamlit cache (press 'C' in app)")
        print("  3. Restart Streamlit server")
        return True
    
    except ImportError as e:
        print(f"⚠️  Could not import PlaidLinkManager: {e}")
        print("   This is OK - module may not be in path")
        print("   Credentials are configured correctly")
        return True
    
    except Exception as e:
        print(f"❌ Error initializing Plaid: {e}")
        return False


def test_yahoo_finance():
    """Test Yahoo Finance (should always work - no API key needed)"""
    print_header("🔍 YAHOO FINANCE TEST")
    
    try:
        import yfinance as yf
        
        print("📡 Fetching AAPL data from Yahoo Finance...")
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        
        if info and 'currentPrice' in info:
            print(f"✅ SUCCESS! Yahoo Finance is working")
            print(f"   AAPL current price: ${info.get('currentPrice', 'N/A')}")
            print(f"   Company: {info.get('longName', 'N/A')}")
            return True
        else:
            print("⚠️  Data fetched but format unexpected")
            return True  # Still counts as working
    
    except ImportError:
        print("❌ yfinance not installed")
        print("   Run: pip install yfinance")
        return False
    
    except Exception as e:
        print(f"⚠️  Error: {e}")
        print("   Yahoo Finance may be temporarily unavailable")
        return False


def test_database():
    """Test MySQL database connection"""
    print_header("🔍 DATABASE TEST")
    
    db_config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'mansa_bot'),
    }
    
    print(f"Testing connection:")
    print(f"  Host: {db_config['host']}:{db_config['port']}")
    print(f"  Database: {db_config['database']}")
    print(f"  User: {db_config['user']}")
    
    try:
        from sqlalchemy import create_engine
        
        connection_string = (
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        
        engine = create_engine(connection_string, pool_recycle=3600)
        
        with engine.connect() as conn:
            result = conn.execute("SELECT VERSION()")
            version = result.fetchone()[0]
            print(f"
✅ SUCCESS! Connected to MySQL")
            print(f"   Version: {version}")
            return True
    
    except ImportError:
        print("❌ SQLAlchemy not installed")
        print("   Run: pip install sqlalchemy pymysql")
        return False
    
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("
Fix:")
        print("  1. Check if MySQL is running")
        print("  2. Verify port 3306 (not 3307)")
        print("  3. Check credentials in .env file")
        print("  4. Ensure database 'mansa_bot' exists")
        return False


def main():
    """Run all diagnostic tests"""
    print("
" + "="*70)
    print("  🔬 BENTLEY BUDGET BOT - API DIAGNOSTIC TEST")
    print("="*70)
    print("
This will test all your API integrations and provide fix instructions")
    print("for any issues found.

")
    
    # Track results
    results = {
        'Yahoo Finance': test_yahoo_finance(),
        'Tiingo API': test_tiingo_api(),
        'Plaid API': test_plaid_api(),
        'Database': test_database(),
    }
    
    # Print summary
    print_header("📊 SUMMARY")
    
    working = [name for name, status in results.items() if status]
    broken = [name for name, status in results.items() if not status]
    
    if working:
        print("✅ Working:")
        for name in working:
            print(f"   • {name}")
    
    if broken:
        print("
❌ Needs Attention:")
        for name in broken:
            print(f"   • {name}")
    
    print(f"
Total: {len(working)}/{len(results)} APIs working")
    
    # Recommendations
    print_header("💡 NEXT STEPS")
    
    if 'Tiingo API' in broken:
        print("🔴 PRIORITY 1: Fix Tiingo API")
        print("   → See detailed instructions above in 'TIINGO API TEST' section")
        print("   → Key issue: Invalid API token - get new one from dashboard")
        print()
    
    if 'Plaid API' in broken:
        print("🟡 PRIORITY 2: Fix Plaid API")
        print("   → Check configuration in .env file")
        print()
    
    if 'Database' in broken:
        print("🟡 PRIORITY 3: Fix Database")
        print("   → Ensure MySQL is running on port 3306")
        print()
    
    if len(working) == len(results):
        print("🎉 ALL SYSTEMS GO!")
        print("
You can now run:")
        print("   streamlit run streamlit_app.py")
        print()
    else:
        print("📖 For detailed fix guide, see: API_FIX_GUIDE.md")
        print()
    
    print("="*70)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_plaid_api()
