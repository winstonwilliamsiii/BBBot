#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diagnostic script to identify connection errors
Tests MySQL, Alpaca, MT5, and Plaid integrations

FIXED: January 17, 2026
- MySQL defaults corrected (127.0.0.1:3306/mansa_bot instead of localhost:3307/bentleybot)
- Added tests for all three MySQL instances
- Added Plaid backend health check
- Added economic data API key status
"""

import sys
import os
from pathlib import Path
import requests

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("BENTLEY BOT - INTEGRATION DIAGNOSTIC")
print("=" * 80)
print("Last Updated: January 17, 2026")
print("=" * 80)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Test 1: MySQL Connection (Main Database - Port 3306)
print("\n[1] TESTING MYSQL CONNECTION - MAIN DATABASE (3306)")
print("-" * 80)
try:
    from sqlalchemy import create_engine
    print("✅ SQLAlchemy imported")
    
    # Fixed: Use correct .env defaults
    mysql_config = {
        'host': os.getenv('MYSQL_HOST', '127.0.0.1'),  # FIXED: from 'localhost'
        'port': os.getenv('MYSQL_PORT', '3306'),        # FIXED: from '3307'
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', 'root'),
        'database': os.getenv('MYSQL_DATABASE', 'mansa_bot')  # FIXED: from 'bentleybot'
    }
    
    print(f"📍 Config: {mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}")
    
    connection_string = (
        f"mysql+pymysql://{mysql_config['user']}:{mysql_config['password']}@"
        f"{mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}"
    )
    
    engine = create_engine(connection_string, echo=False)
    conn = engine.connect()
    result = conn.execute("SELECT 1")
    print("✅ MySQL MAIN connection successful!")
    print(f"   Database: mansa_bot (general app data)")
    conn.close()
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ MySQL connection failed: {e}")

# Test 1b: MySQL Operational Database - Port 3307
print("\n[1b] TESTING MYSQL CONNECTION - OPERATIONAL DATABASE (3307)")
print("-" * 80)
try:
    from sqlalchemy import create_engine
    
    bbbot_config = {
        'host': os.getenv('BBBOT1_MYSQL_HOST', '127.0.0.1'),
        'port': os.getenv('BBBOT1_MYSQL_PORT', '3307'),
        'user': os.getenv('BBBOT1_MYSQL_USER', 'root'),
        'password': os.getenv('BBBOT1_MYSQL_PASSWORD', 'root'),
        'database': os.getenv('BBBOT1_MYSQL_DATABASE', 'bbbot1')
    }
    
    print(f"📍 Config: {bbbot_config['host']}:{bbbot_config['port']}/{bbbot_config['database']}")
    
    connection_string = (
        f"mysql+pymysql://{bbbot_config['user']}:{bbbot_config['password']}@"
        f"{bbbot_config['host']}:{bbbot_config['port']}/{bbbot_config['database']}"
    )
    
    engine = create_engine(connection_string, echo=False)
    conn = engine.connect()
    result = conn.execute("SELECT 1")
    print("✅ MySQL OPERATIONAL connection successful!")
    print(f"   Database: bbbot1 (stock data, technical analysis)")
    conn.close()
    
except Exception as e:
    print(f"⚠️  MySQL OPERATIONAL connection failed: {e}")
    print(f"   (This is expected if Docker container on port 3307 is not running)")

# Test 1c: MySQL Budget Database - Port 3306
print("\n[1c] TESTING MYSQL CONNECTION - BUDGET DATABASE (3306)")
print("-" * 80)
try:
    from sqlalchemy import create_engine
    
    budget_config = {
        'host': os.getenv('BUDGET_MYSQL_HOST', '127.0.0.1'),
        'port': os.getenv('BUDGET_MYSQL_PORT', '3306'),
        'user': os.getenv('BUDGET_MYSQL_USER', 'root'),
        'password': os.getenv('BUDGET_MYSQL_PASSWORD', 'root'),
        'database': os.getenv('BUDGET_MYSQL_DATABASE', 'mydb')
    }
    
    print(f"📍 Config: {budget_config['host']}:{budget_config['port']}/{budget_config['database']}")
    
    connection_string = (
        f"mysql+pymysql://{budget_config['user']}:{budget_config['password']}@"
        f"{budget_config['host']}:{budget_config['port']}/{budget_config['database']}"
    )
    
    engine = create_engine(connection_string, echo=False)
    conn = engine.connect()
    result = conn.execute("SELECT 1")
    print("✅ MySQL BUDGET connection successful!")
    print(f"   Database: mydb (Plaid integration)")
    conn.close()
    
except Exception as e:
    print(f"⚠️  MySQL BUDGET connection failed: {e}")
    print(f"   (This database may not exist yet)")

# Test 2: Alpaca Integration
print("\n[2] TESTING ALPACA INTEGRATION")
print("-" * 80)
try:
    from frontend.components.alpaca_connector import AlpacaConnector
    print("✅ AlpacaConnector imported")
    
    api_key = os.getenv('ALPACA_API_KEY', '')
    secret_key = os.getenv('ALPACA_SECRET_KEY', '')
    
    if api_key and secret_key:
        print(f"✅ Credentials found (key: {api_key[:10]}...)")
        alpaca = AlpacaConnector(api_key, secret_key, paper=True)
        print("✅ AlpacaConnector initialized")
    else:
        print("⚠️  No Alpaca credentials in environment")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Alpaca error: {e}")

# Test 3: MT5 Integration
print("\n[3] TESTING MT5 INTEGRATION")
print("-" * 80)
try:
    from frontend.components.mt5_connector import MT5Connector
    print("✅ MT5Connector imported")
    
    mt5_url = os.getenv('MT5_API_URL', 'http://localhost:8000')
    print(f"MT5 URL: {mt5_url}")
    
    mt5 = MT5Connector(base_url=mt5_url)
    print("✅ MT5Connector initialized")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ MT5 error: {e}")

# Test 4: Plaid Integration with Health Check
print("\n[4] TESTING PLAID INTEGRATION")
print("-" * 80)
try:
    plaid_backend_url = os.getenv('PLAID_BACKEND_URL', 'http://localhost:5001')
    plaid_client_id = os.getenv('PLAID_CLIENT_ID', '')
    plaid_secret = os.getenv('PLAID_SECRET', '')
    
    print(f"📍 Backend URL: {plaid_backend_url}")
    
    if not plaid_client_id or not plaid_secret:
        print("⚠️  Plaid credentials not fully configured in .env")
    else:
        print(f"✅ Plaid credentials found (client_id: {plaid_client_id[:10]}...)")
    
    # Try to do a health check on Plaid backend
    try:
        response = requests.get(f"{plaid_backend_url}/health", timeout=3)
        if response.status_code == 200:
            print("✅ Plaid backend is RUNNING (http://localhost:5001)")
        else:
            print(f"⚠️  Plaid backend responded with status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("⚠️  Plaid backend NOT RESPONDING (is Docker container running?)")
        print("   To start: docker-compose up -d plaid-backend")
    except Exception as e:
        print(f"⚠️  Plaid health check failed: {e}")
    
    # Try to import Plaid client
    try:
        from frontend.components.plaid_quickstart_connector import PlaidQuickstartClient
        print("✅ PlaidQuickstartClient imported successfully")
    except ImportError as e:
        print(f"❌ PlaidQuickstartClient import error: {e}")
    
except Exception as e:
    print(f"❌ Plaid error: {e}")

# Test 5: Economic Data APIs
print("\n[5] CHECKING ECONOMIC DATA API KEYS")
print("-" * 80)

economic_apis = {
    'BLS_API_KEY': 'Bureau of Labor Statistics (inflation, employment)',
    'FRED_API_KEY': 'Federal Reserve Economic Data (economic indicators)',
    'QUANDL_API_KEY': 'Quandl (alternative datasets)',
    'INFLATIONAPI_KEY': 'Inflation API (inflation data)',
    'OPENWEATHER_API_KEY': 'OpenWeather (market sentiment)',
    'NEWSAPI_KEY': 'NewsAPI (financial news)'
}

economic_configured = 0
for api_key, description in economic_apis.items():
    value = os.getenv(api_key, '')
    if value:
        display = value[:5] + '*' * (len(value) - 10) + value[-5:] if len(value) > 10 else '*' * len(value)
        print(f"✅ {api_key}: {display}")
        print(f"   └─ {description}")
        economic_configured += 1
    else:
        print(f"⚠️  {api_key}: NOT SET")
        print(f"   └─ {description}")

print(f"\nEconomic APIs Status: {economic_configured}/{len(economic_apis)} configured")

# Test 6: RBAC & New Features
print("\n[6] TESTING RBAC & NEW FEATURES")
print("-" * 80)
try:
    from frontend.utils.rbac import RBACManager, Permission
    print("✅ RBAC imported")
    
    from frontend.components.economic_calendar_widget import get_calendar_widget
    print("✅ Economic Calendar Widget imported")
    
    from frontend.components.bentley_chatbot import render_chatbot_interface
    print("✅ Bentley Chatbot imported")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"Feature error: {e}")

# Test 7: Check environment variables
print("\n[7] ENVIRONMENT VARIABLES SUMMARY")
print("-" * 80)

vars_to_check = [
    ('MYSQL_HOST', 'MySQL Host (Main)'),
    ('MYSQL_PORT', 'MySQL Port (Main)'),
    ('MYSQL_DATABASE', 'MySQL Database (Main)'),
    ('BBBOT1_MYSQL_HOST', 'MySQL Host (Operational)'),
    ('BBBOT1_MYSQL_PORT', 'MySQL Port (Operational)'),
    ('BBBOT1_MYSQL_DATABASE', 'MySQL Database (Operational)'),
    ('ALPACA_API_KEY', 'Alpaca API Key'),
    ('ALPACA_SECRET_KEY', 'Alpaca Secret Key'),
    ('MT5_API_URL', 'MT5 API URL'),
    ('PLAID_CLIENT_ID', 'Plaid Client ID'),
    ('PLAID_SECRET', 'Plaid Secret'),
    ('APPWRITE_ENDPOINT', 'Appwrite Endpoint'),
    ('APPWRITE_PROJECT_ID', 'Appwrite Project ID'),
]

print("\nCritical Environment Variables:")
for var, description in vars_to_check:
    value = os.getenv(var, '')
    if value:
        # Mask sensitive values
        if 'KEY' in var or 'SECRET' in var or 'PASSWORD' in var:
            display = value[:5] + '*' * (len(value) - 10) + value[-5:] if len(value) > 10 else '*' * len(value)
        else:
            display = value
        print(f"✅ {description}: {display}")
    else:
        print(f"⚠️  {description}: NOT SET")

# Summary Report
print("\n" + "=" * 80)
print("DIAGNOSTIC SUMMARY")
print("=" * 80)

print("\nConfiguration Status:")
print(f"  * Main MySQL: {os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DATABASE')}")
print(f"  * Operational MySQL: {os.getenv('BBBOT1_MYSQL_HOST')}:{os.getenv('BBBOT1_MYSQL_PORT')}/{os.getenv('BBBOT1_MYSQL_DATABASE')}")
print(f"  * Plaid Backend: {os.getenv('PLAID_BACKEND_URL', 'http://localhost:5001')}")
print(f"  * Economic APIs: {economic_configured}/{len(economic_apis)} configured")

print("\nKey Services:")
print(f"  * Appwrite Cloud: {os.getenv('APPWRITE_ENDPOINT', 'Not configured')}")
print(f"  * Alpaca Trading: {'Configured' if os.getenv('ALPACA_API_KEY') else 'Not configured'}")
print(f"  * MT5 Terminal: {os.getenv('MT5_API_URL', 'Not configured')}")
print(f"  * Plaid Banking: {'Configured' if os.getenv('PLAID_CLIENT_ID') else 'Not configured'}")

print("\nCommon Issues:")
print("  1. MySQL connection fails → Check docker containers are running on 3306 & 3307")
print("  2. Plaid backend down → Run: docker-compose up -d plaid-backend")
print("  3. Economic data unavailable → Add API keys to .env file")
print("  4. Appwrite errors → Verify APPWRITE_API_KEY in .env file")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
