"""
StockTwits API Connection Test
==============================
This script validates the StockTwits API key by making a simple API call.

Purpose:
- Load the STOCKTWITS_API_KEY from the .env file.
- Make a request to a public StockTwits endpoint.
- Check for a 200 OK response to confirm the key is valid and active.

Usage:
  python test_stocktwits.py
"""

import os
import requests
from dotenv import load_dotenv

# Use the project's robust env loader if available
try:
    from config_env import require_env_var
    CONFIG_ENV_AVAILABLE = True
except ImportError:
    CONFIG_ENV_AVAILABLE = False
    # Fallback to basic loading if config_env is not in the path
    load_dotenv(override=True)


def test_stocktwits_connection():
    """
    Tests the connection to the StockTwits API using the configured API key.
    """
    print("========================================")
    print("🧪 Testing StockTwits API Connection...")
    print("========================================")

    try:
        # 1. Get API Key using the robust require_env_var function
        if CONFIG_ENV_AVAILABLE:
            print("- Using require_env_var to load API key...")
            api_key = require_env_var('STOCKTWITS_API_KEY', reload=True)
        else:
            print("- Using basic os.getenv to load API key...")
            api_key = os.getenv('STOCKTWITS_API_KEY')
            if not api_key or api_key.startswith('your_'):
                raise ValueError("STOCKTWITS_API_KEY not found or is a placeholder in .env file.")

        print(f"- API Key loaded: {api_key[:4]}...{api_key[-4:]}")

        # 2. Make a simple API call
        symbol = 'AAPL'
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
        params = {'access_token': api_key}
        print(f"- Making request to: {url}")

        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        print(f"\n✅ SUCCESS: StockTwits API connection is working!")
        print(f"- Status Code: {response.status_code}")
        print(f"- Successfully fetched stream for ${symbol}.")

    except (ValueError, requests.exceptions.RequestException) as e:
        print(f"\n❌ FAILED: Could not connect to StockTwits API.")
        print(f"   Error: {e}")
        print("\n   Troubleshooting:")
        print("   1. Ensure 'STOCKTWITS_API_KEY' is correctly set in your .env file.")
        print("   2. Verify your StockTwits subscription is active.")
        print("   3. Check your internet connection.")

if __name__ == "__main__":
    test_stocktwits_connection()
