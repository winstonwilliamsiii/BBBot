#!/usr/bin/env python3
"""
Test the updated Gold RSI trading script with bracket orders
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from frontend.components.alpaca_connector import AlpacaConnector

load_dotenv()

def test_bracket_functionality():
    """Test that bracket orders work with small position"""
    
    print("=" * 70)
    print("TESTING ALPACA BRACKET ORDER INTEGRATION")
    print("=" * 70)
    
    # Get credentials
    api_key = os.getenv('ALPACA_API_KEY', '').strip()
    secret_key = os.getenv('ALPACA_SECRET_KEY', '').strip()
    
    if not api_key or not secret_key:
        print("❌ Missing credentials")
        return False
    
    # Initialize
    alpaca = AlpacaConnector(api_key, secret_key, paper=True)
    
    # Get account
    account = alpaca.get_account()
    if not account:
        print("❌ Could not connect")
        return False
    
    print(f"\n✅ Connected to Alpaca (PAPER mode)")
    print(f"   Portfolio: ${float(account.get('portfolio_value', 0)):,.2f}")
    print(f"   Buying Power: ${float(account.get('buying_power', 0)):,.2f}")
    
    # Test with small SPY order
    symbol = "SPY"
    qty = 1
    
    # Get price
    try:
        # Use latest trade price, not quote (bid/ask can have wide spreads)
        trade = alpaca.get_latest_trade(symbol)
        current_price = float(trade['trade']['p'])
        print(f"\n   Current {symbol} price: ${current_price:.2f}")
    except Exception as e:
        print(f"❌ Could not get price: {e}")
        return False
    
    # Calculate bracket prices
    stop_loss = round(current_price * 0.98, 2)
    take_profit = round(current_price * 1.04, 2)
    
    print(f"\n📋 TEST ORDER DETAILS:")
    print(f"   Symbol: {symbol}")
    print(f"   Qty: {qty} share")
    print(f"   Entry: ~${current_price:.2f}")
    print(f"   Stop Loss: ${stop_loss:.2f} (-2%)")
    print(f"   Take Profit: ${take_profit:.2f} (+4%)")
    print(f"   Risk: ${current_price - stop_loss:.2f}")
    print(f"   Reward: ${take_profit - current_price:.2f}")
    print(f"   R/R Ratio: {(take_profit - current_price)/(current_price - stop_loss):.2f}:1")
    
    # Confirm
    print(f"\n⚠️  This will place a REAL bracket order on your PAPER account")
    response = input("   Continue? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n❌ Test cancelled")
        return False
    
    # Place order
    print("\n🚀 Placing bracket order...")
    order = alpaca.place_bracket_order(
        symbol=symbol,
        qty=qty,
        side="buy",
        order_type="market",
        take_profit_limit_price=take_profit,
        stop_loss_stop_price=stop_loss,
        time_in_force="gtc"
    )
    
    if not order:
        print("❌ Order failed")
        return False
    
    print(f"\n✅ SUCCESS! Order placed:")
    print(f"   Order ID: {order.get('id')}")
    print(f"   Status: {order.get('status')}")
    print(f"   Symbol: {order.get('symbol')}")
    print(f"   Qty: {order.get('qty')}")
    
    # Check for legs
    if 'legs' in order and order['legs']:
        print(f"\n   📋 Bracket Legs:")
        for leg in order['legs']:
            if leg.get('stop_price'):
                print(f"      🛑 Stop Loss: ${leg.get('stop_price')}")
            if leg.get('limit_price'):
                print(f"      ✅ Take Profit: ${leg.get('limit_price')}")
    
    print(f"\n💡 The position is now protected:")
    print(f"   • Will automatically sell if price drops to ${stop_loss}")
    print(f"   • Will automatically sell if price rises to ${take_profit}")
    
    # Show open orders
    print(f"\n📊 Checking open orders...")
    orders = alpaca.get_orders(status="open")
    if orders:
        print(f"   Found {len(orders)} open order(s)")
        for ord in orders[:3]:
            print(f"   • {ord.get('symbol')}: {ord.get('side')} {ord.get('qty')} ({ord.get('status')})")
            if ord.get('order_class') == 'bracket':
                print(f"     🎯 BRACKET ORDER with stop loss & take profit")
    
    print(f"\n" + "=" * 70)
    print(f"✅ BRACKET ORDER TEST PASSED!")
    print(f"=" * 70)
    
    return True


if __name__ == "__main__":
    success = test_bracket_functionality()
    sys.exit(0 if success else 1)
