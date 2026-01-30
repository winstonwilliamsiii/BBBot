#!/usr/bin/env python3
"""
Test Alpaca API connection and provide diagnostics for production issues.
"""

import os
import sys
from dotenv import load_dotenv
import requests

# Load environment
load_dotenv()

def test_alpaca_credentials():
    """Test Alpaca API credentials and endpoint connectivity."""
    
    print("=" * 60)
    print("🔍 ALPACA CONNECTION DIAGNOSTIC")
    print("=" * 60)
    
    api_key = os.getenv('ALPACA_API_KEY', '').strip()
    secret_key = os.getenv('ALPACA_SECRET_KEY', '').strip()
    paper_trading = os.getenv('ALPACA_PAPER', 'true').lower() == 'true'
    
    print("\n1️⃣ CREDENTIALS LOADED")
    print("-" * 60)
    print(f"  API Key (first 8 chars): {api_key[:8] if api_key else 'NOT SET'}...")
    print(f"  Secret Key (first 8 chars): {secret_key[:8] if secret_key else 'NOT SET'}...")
    print(f"  Paper Trading: {paper_trading}")
    
    if not api_key or not secret_key:
        print("\n❌ ERROR: Credentials not found in environment!")
        return False
    
    print("\n2️⃣ API ENDPOINT TEST")
    print("-" * 60)
    
    base_url = "https://paper-api.alpaca.markets" if paper_trading else "https://api.alpaca.markets"
    endpoint = f"{base_url}/v2/account"
    
    print(f"  Endpoint: {endpoint}")
    
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': secret_key,
    }
    
    print(f"  Headers: APCA-API-KEY-ID={api_key[:8]}..., APCA-API-SECRET-KEY={secret_key[:8]}...")
    
    try:
        print(f"\n  📡 Sending GET request to Alpaca API...")
        response = requests.get(endpoint, headers=headers, timeout=10)
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("  ✅ SUCCESS: Connected to Alpaca API!")
            account = response.json()
            print(f"\n  Account Details:")
            print(f"    - Account ID: {account.get('id')}")
            print(f"    - Portfolio Value: ${float(account.get('portfolio_value', 0)):,.2f}")
            print(f"    - Cash: ${float(account.get('cash', 0)):,.2f}")
            print(f"    - Buying Power: ${float(account.get('buying_power', 0)):,.2f}")
            print(f"    - Status: {account.get('status')}")
            return True
        
        elif response.status_code == 401:
            print("  ❌ ERROR 401: Unauthorized")
            print("     Possible causes:")
            print("     - API Key is expired or invalid")
            print("     - Secret Key is incorrect")
            print("     - Headers not properly formatted")
            print(f"     Response: {response.text}")
            return False
        
        elif response.status_code == 403:
            print("  ❌ ERROR 403: Forbidden")
            print("     Possible causes:")
            print("     - Account is not approved for paper trading")
            print("     - Permissions not configured")
            print(f"     Response: {response.text}")
            return False
        
        elif response.status_code == 404:
            print("  ❌ ERROR 404: Not Found")
            print("     Possible causes:")
            print("     - Account does not exist")
            print("     - Endpoint URL is incorrect")
            print(f"     Response: {response.text}")
            return False
        
        else:
            print(f"  ❌ ERROR {response.status_code}: Unexpected response")
            print(f"     Response: {response.text}")
            return False
    
    except requests.exceptions.Timeout:
        print("  ❌ ERROR: Request timeout (10 seconds)")
        print("     Check your internet connection and Alpaca API availability")
        return False
    
    except requests.exceptions.ConnectionError as e:
        print(f"  ❌ ERROR: Connection failed")
        print(f"     {str(e)}")
        print("     Check your internet connection")
        return False
    
    except Exception as e:
        print(f"  ❌ ERROR: Unexpected error")
        print(f"     {str(e)}")
        return False


def test_streamlit_secrets():
    """Test if credentials can be loaded via Streamlit."""
    print("\n3️⃣ STREAMLIT SECRETS TEST")
    print("-" * 60)
    
    try:
        import streamlit as st
        
        # Try to get secrets
        try:
            api_key = st.secrets.get("ALPACA_API_KEY", "")
            secret_key = st.secrets.get("ALPACA_SECRET_KEY", "")
            
            print("  ✅ Streamlit secrets loaded successfully")
            print(f"    - API Key: {api_key[:8] if api_key else 'NOT SET'}...")
            print(f"    - Secret Key: {secret_key[:8] if secret_key else 'NOT SET'}...")
            
        except Exception as e:
            print(f"  ⚠️  Could not load Streamlit secrets: {e}")
            print("     This is expected if running outside of Streamlit context")
    
    except ImportError:
        print("  ⚠️  Streamlit not imported (expected in this context)")


if __name__ == "__main__":
    success = test_alpaca_credentials()
    test_streamlit_secrets()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED - Your Alpaca connection is working!")
    else:
        print("❌ TESTS FAILED - Check the errors above")
        print("\nNext Steps:")
        print("1. Verify API keys at: https://app.alpaca.markets/")
        print("2. Check that account has paper trading enabled")
        print("3. Ensure credentials are set in Streamlit Cloud secrets")
        print("4. Contact Alpaca support if issue persists")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
