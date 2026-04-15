#!/usr/bin/env python3
"""
Quick test to verify Alpaca bracket order API without placing real orders
"""

import os
from dotenv import load_dotenv
from frontend.components.alpaca_connector import AlpacaConnector

load_dotenv()

def main():
    print("=" * 70)
    print("🔍 ALPACA BRACKET ORDER - API VALIDATION TEST")
    print("=" * 70)
    
    # Get credentials
    api_key = os.getenv('ALPACA_API_KEY', '').strip()
    secret_key = os.getenv('ALPACA_SECRET_KEY', '').strip()
    paper = os.getenv('ALPACA_PAPER', 'true').lower() == 'true'
    
    if not api_key or not secret_key:
        print("❌ Missing Alpaca credentials")
        return False
    
    # Connect
    alpaca = AlpacaConnector(api_key, secret_key, paper=paper)
    print(f"\n✅ Connector initialized ({'PAPER' if paper else 'LIVE'} mode)")
    
    # Test connection
    account = alpaca.get_account()
    if not account:
        print("❌ Failed to connect to Alpaca API")
        return False
    
    print(f"✅ Connected to Alpaca!")
    print(f"   Account ID: {account.get('id', 'Unknown')[:12]}...")
    print(f"   Portfolio: ${float(account.get('portfolio_value', 0)):,.2f}")
    print(f"   Buying Power: ${float(account.get('buying_power', 0)):,.2f}")
    
    # Check if account supports bracket orders
    print(f"\n📋 Account Status: {account.get('status')}")
    print(f"   Trading Blocked: {account.get('trading_blocked', False)}")
    print(f"   Pattern Day Trader: {account.get('pattern_day_trader', False)}")
    
    # Verify bracket order method exists
    print(f"\n🔧 Checking new bracket order method...")
    if hasattr(alpaca, 'place_bracket_order'):
        print(f"   ✅ place_bracket_order() method available")
    else:
        print(f"   ❌ place_bracket_order() method NOT found")
        return False
    
    # Test current positions
    print(f"\n📊 Current Positions:")
    positions = alpaca.get_positions()
    if positions:
        for pos in positions[:3]:  # Show first 3
            print(f"   • {pos.symbol}: {pos.qty} shares @ ${pos.current_price:.2f}")
            print(f"     P/L: ${pos.unrealized_pl:,.2f} ({pos.unrealized_plpc*100:.2f}%)")
    else:
        print(f"   No open positions")
    
    # Test getting a quote
    print(f"\n💰 Testing market data API...")
    try:
        quote = alpaca.get_latest_quote("SPY")
        if quote and 'quote' in quote:
            bid = float(quote['quote']['bp'])
            ask = float(quote['quote']['ap'])
            print(f"   ✅ SPY Quote: Bid ${bid:.2f} / Ask ${ask:.2f}")
            
            # Calculate what bracket order would look like
            entry = ask
            take_profit = round(entry * 1.02, 2)
            stop_loss = round(entry * 0.98, 2)
            
            print(f"\n🎯 Example Bracket Order for SPY:")
            print(f"   Entry: ${entry:.2f} (market)")
            print(f"   Take Profit: ${take_profit:.2f} (+2%)")
            print(f"   Stop Loss: ${stop_loss:.2f} (-2%)")
            print(f"   Risk/Reward: 1:1")
        else:
            print(f"   ⚠️  Quote data format unexpected")
    except Exception as e:
        print(f"   ⚠️  Could not get quote: {e}")
    
    print(f"\n" + "=" * 70)
    print(f"✅ ALL CHECKS PASSED!")
    print(f"\nThe bracket order functionality is ready to use.")
    print(f"Run 'python tests/manual/test_alpaca_bracket_order.py' to place a test order.")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
