#!/usr/bin/env python
"""
Test script to verify Kalshi and Polymarket API connections
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env.development')

from prediction_analytics.services.kalshi_client import KalshiClient
from prediction_analytics.services.polymarket_api_client import PolymarketAPIClient

def test_kalshi():
    """Test Kalshi API connection"""
    print("\n" + "="*60)
    print("🔍 TESTING KALSHI API")
    print("="*60)
    
    email = os.getenv('KALSHI_EMAIL')
    password = os.getenv('KALSHI_PASSWORD')
    
    if not email or not password:
        print("❌ KALSHI_EMAIL or KALSHI_PASSWORD not set in environment")
        return False
    
    print(f"📧 Email: {email}")
    print(f"🔐 Password: {'*' * len(password)}")
    
    try:
        client = KalshiClient(email=email, password=password)
        print(f"\n✅ Client created")
        print(f"   Authenticated: {client.authenticated}")
        print(f"   Last error: {client.last_error}")
        
        if client.authenticated:
            print("\n📊 Fetching Account Data...")
            
            # Get profile
            profile = client.get_user_profile()
            print(f"   Profile: {profile}")
            
            # Get balance
            balance = client.get_user_balance()
            print(f"   Balance: {balance}")
            
            # Get positions
            positions = client.get_user_portfolio()
            print(f"   ✅ Positions fetched: {len(positions) if positions else 0}")
            if positions:
                for i, pos in enumerate(positions[:3]):  # Show first 3
                    print(f"      [{i+1}] {pos}")
            
            # Get trades
            trades = client.get_user_trades(limit=5)
            print(f"   ✅ Trades fetched: {len(trades) if trades else 0}")
            if trades:
                for i, trade in enumerate(trades[:2]):  # Show first 2
                    print(f"      [{i+1}] {trade}")
            
            return True
        else:
            print(f"❌ Authentication failed: {client.last_error}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_polymarket():
    """Test Polymarket API connection"""
    print("\n" + "="*60)
    print("🔍 TESTING POLYMARKET API")
    print("="*60)
    
    api_key = os.getenv('POLYMARKET_API_KEY')
    secret_key = os.getenv('POLYMARKET_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("❌ POLYMARKET_API_KEY or POLYMARKET_SECRET_KEY not set in environment")
        return False
    
    print(f"🔑 API Key: {api_key[:10]}...")
    print(f"🔐 Secret Key: {secret_key[:10]}...")
    
    try:
        client = PolymarketAPIClient(api_key=api_key, secret_key=secret_key)
        print(f"\n✅ Client created")
        
        print("\n🧪 Testing connection...")
        result = client.test_connection()
        print(f"   Connection test result: {result}")
        
        print("\n📊 Fetching Data...")
        
        # Get active markets
        markets = client.get_active_markets(limit=3)
        print(f"   ✅ Markets fetched: {len(markets) if markets else 0}")
        if markets:
            for i, market in enumerate(markets[:2]):  # Show first 2
                print(f"      [{i+1}] {market}")
        
        # Get portfolio
        portfolio = client.get_user_portfolio()
        print(f"   ✅ Portfolio fetched: {len(portfolio) if portfolio else 0}")
        if portfolio:
            for i, pos in enumerate(portfolio[:2]):  # Show first 2
                print(f"      [{i+1}] {pos}")
        
        # Get balance
        balance = client.get_user_balance()
        print(f"   ✅ Balance: {balance}")
        
        # Get trades
        trades = client.get_user_trades(limit=3)
        print(f"   ✅ Trades fetched: {len(trades) if trades else 0}")
        if trades:
            for i, trade in enumerate(trades[:2]):  # Show first 2
                print(f"      [{i+1}] {trade}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 PREDICTION ANALYTICS API TEST SUITE")
    print("="*60)
    
    kalshi_ok = test_kalshi()
    polymarket_ok = test_polymarket()
    
    print("\n" + "="*60)
    print("📋 SUMMARY")
    print("="*60)
    print(f"Kalshi API:      {'✅ PASS' if kalshi_ok else '❌ FAIL'}")
    print(f"Polymarket API:  {'✅ PASS' if polymarket_ok else '❌ FAIL'}")
    print("="*60)
    
    sys.exit(0 if (kalshi_ok and polymarket_ok) else 1)
