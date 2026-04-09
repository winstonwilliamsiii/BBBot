#!/usr/bin/env python
"""Comprehensive test of all Kalshi API endpoints."""
import os
from dotenv import load_dotenv
from prediction_analytics.services.kalshi_client import KalshiClient

# Load environment variables
load_dotenv(override=True)

def test_kalshi_api():
    """Test all Kalshi API endpoints."""
    print("=" * 80)
    print("COMPREHENSIVE KALSHI API TEST")
    print("=" * 80)
    
    # Get credentials
    api_key_id = os.getenv('KALSHI_API_KEY_ID') or os.getenv('KALSHI_ACCESS_KEY')
    private_key = os.getenv('KALSHI_PRIVATE_KEY')
    
    print(f"\n1. CREDENTIALS CHECK")
    print(f"   API Key ID: {'✓ Loaded' if api_key_id else '✗ Missing'}")
    if api_key_id:
        print(f"   Key: {api_key_id[:20]}...")
    print(f"   Private Key: {'✓ Loaded' if private_key else '✗ Missing'}")
    
    # Initialize client
    print(f"\n2. CLIENT INITIALIZATION")
    client = KalshiClient(api_key_id=api_key_id, private_key=private_key)
    print(f"   Authenticated: {'✓ Yes' if client.authenticated else '✗ No'}")
    if client.last_error:
        print(f"   Error: {client.last_error}")
        return
    
    # Test balance
    print(f"\n3. ACCOUNT BALANCE")
    balance = client.get_user_balance()
    if balance:
        balance_dollars = balance.get('balance', 0) / 100
        portfolio_value = balance.get('portfolio_value', 0) / 100
        print(f"   ✓ Cash Balance: ${balance_dollars:.2f}")
        print(f"   ✓ Portfolio Value: ${portfolio_value:.2f}")
        print(f"   Raw: {balance}")
    else:
        print(f"   ✗ Failed to fetch balance")
    
    # Test portfolio
    print(f"\n4. PORTFOLIO POSITIONS")
    positions = client.get_user_portfolio()
    print(f"   Found {len(positions)} position(s)")
    if positions:
        for i, pos in enumerate(positions[:3], 1):
            print(f"\n   Position {i}:")
            print(f"     Contract: {pos.get('ticker', 'Unknown')}")
            print(f"     Quantity: {pos.get('position', 0)}")
            total_traded_dollars = float(pos.get('total_traded_dollars', 0)) / 100
            market_exposure_dollars = float(pos.get('market_exposure_dollars', 0)) / 100
            realized_pnl_dollars = float(pos.get('realized_pnl_dollars', 0)) / 100
            print(f"     Total Traded: ${total_traded_dollars:.2f}")
            print(f"     Market Exposure: ${market_exposure_dollars:.2f}")
            print(f"     Realized P&L: ${realized_pnl_dollars:.2f}")
    else:
        print(f"   ℹ No open positions")
    
    # Test trades/fills
    print(f"\n5. TRADE HISTORY (FILLS)")
    trades = client.get_user_trades(limit=10)
    print(f"   Found {len(trades)} trade(s)")
    if trades:
        print(f"\n   Recent Trades:")
        for i, trade in enumerate(trades[:5], 1):
            print(f"\n   Trade {i}:")
            print(f"     Ticker: {trade.get('ticker', 'Unknown')}")
            print(f"     Side: {trade.get('side', 'Unknown')}")
            print(f"     Count: {trade.get('count', 0)}")
            print(f"     Yes Price: {trade.get('yes_price', 'N/A')}")
            print(f"     No Price: {trade.get('no_price', 'N/A')}")
            print(f"     Created: {trade.get('created_time', 'Unknown')}")
    else:
        print(f"   ℹ No trade history found")
    
    # Test profile
    print(f"\n6. USER PROFILE")
    profile = client.get_user_profile()
    if profile:
        print(f"   ✓ User ID: {profile.get('user_id', 'Unknown')}")
        print(f"   Email: {profile.get('email', 'N/A')}")
        print(f"   Created: {profile.get('created_time', 'N/A')}")
    else:
        print(f"   ✗ Failed to fetch profile")
    
    # Test account history
    print(f"\n7. ACCOUNT HISTORY")
    history = client.get_account_history()
    print(f"   Found {len(history)} history item(s)")
    if history:
        for i, item in enumerate(history[:3], 1):
            print(f"\n   History {i}:")
            print(f"     Type: {item.get('type', 'Unknown')}")
            print(f"     Amount: {item.get('amount', 'N/A')}")
            print(f"     Time: {item.get('created_time', 'Unknown')}")
    
    # Test active markets
    print(f"\n8. ACTIVE MARKETS")
    markets = client.get_active_markets(limit=5)
    print(f"   Found {len(markets)} active market(s)")
    if markets:
        for i, market in enumerate(markets[:3], 1):
            print(f"\n   Market {i}:")
            print(f"     Ticker: {market.get('ticker', 'Unknown')}")
            print(f"     Title: {market.get('title', 'Unknown')}")
            print(f"     Status: {market.get('status', 'Unknown')}")
            print(f"     Close: {market.get('close_time', 'Unknown')}")
    else:
        print(f"   ℹ No active markets found")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    test_kalshi_api()
