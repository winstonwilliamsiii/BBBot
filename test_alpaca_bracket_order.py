#!/usr/bin/env python3
"""
Test Alpaca Bracket Orders with Stop Loss and Take Profit
This script demonstrates how to place orders with automatic risk management
"""

import os
from dotenv import load_dotenv
from frontend.components.alpaca_connector import AlpacaConnector

# Load environment variables
load_dotenv()

def main():
    print("=" * 70)
    print("🎯 ALPACA BRACKET ORDER TEST")
    print("=" * 70)
    
    # Initialize Alpaca connection
    api_key = os.getenv('ALPACA_API_KEY', '').strip()
    secret_key = os.getenv('ALPACA_SECRET_KEY', '').strip()
    paper_trading = os.getenv('ALPACA_PAPER', 'true').lower() == 'true'
    
    if not api_key or not secret_key:
        print("❌ ERROR: Missing Alpaca credentials in environment!")
        print("   Set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env file")
        return
    
    alpaca = AlpacaConnector(api_key, secret_key, paper=paper_trading)
    
    print(f"\n{'PAPER' if paper_trading else 'LIVE'} Trading Mode\n")
    
    # Get account info
    account = alpaca.get_account()
    if not account:
        print("❌ Failed to connect to Alpaca API")
        return
    
    print(f"✅ Connected to Alpaca!")
    print(f"   Account: {account.get('id', 'Unknown')[:8]}...")
    print(f"   Portfolio Value: ${float(account.get('portfolio_value', 0)):,.2f}")
    print(f"   Buying Power: ${float(account.get('buying_power', 0)):,.2f}")
    print(f"   Cash: ${float(account.get('cash', 0)):,.2f}")
    
    # Get current positions
    print(f"\n📊 Current Positions:")
    positions = alpaca.get_positions()
    if positions:
        for pos in positions:
            print(f"   {pos.symbol}: {pos.qty} shares @ ${pos.current_price:.2f}")
            print(f"      P/L: ${pos.unrealized_pl:,.2f} ({pos.unrealized_plpc*100:.2f}%)")
    else:
        print("   No open positions")
    
    # Example: Place a bracket order
    print("\n" + "=" * 70)
    print("📝 BRACKET ORDER EXAMPLE")
    print("=" * 70)
    
    symbol = "SPY"  # Popular ETF for testing
    qty = 1  # Buy 1 share
    
    # Get current price
    try:
        quote = alpaca.get_latest_quote(symbol)
        current_price = float(quote['quote']['ap'])  # Ask price
        print(f"\n💰 Current {symbol} Price: ${current_price:.2f}")
    except Exception as e:
        print(f"❌ Could not get current price: {e}")
        return
    
    # Calculate stop loss and take profit
    # For BUY orders:
    # - Take Profit should be ABOVE current price
    # - Stop Loss should be BELOW current price
    take_profit_price = round(current_price * 1.02, 2)  # 2% profit target
    stop_loss_price = round(current_price * 0.99, 2)    # 1% stop loss
    
    print(f"\n🎯 Order Setup:")
    print(f"   Symbol: {symbol}")
    print(f"   Quantity: {qty} shares")
    print(f"   Side: BUY")
    print(f"   Entry: MARKET (~${current_price:.2f})")
    print(f"   Take Profit: ${take_profit_price:.2f} (+${take_profit_price - current_price:.2f})")
    print(f"   Stop Loss: ${stop_loss_price:.2f} (-${current_price - stop_loss_price:.2f})")
    print(f"   Risk/Reward Ratio: {(take_profit_price - current_price) / (current_price - stop_loss_price):.2f} to 1")
    
    # Ask for confirmation
    print(f"\n⚠️  This will place a REAL order on your {'PAPER' if paper_trading else 'LIVE'} account!")
    response = input("   Proceed? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n❌ Order cancelled by user")
        return
    
    # Place bracket order
    print("\n🚀 Placing bracket order...")
    order = alpaca.place_bracket_order(
        symbol=symbol,
        qty=qty,
        side="buy",
        order_type="market",
        take_profit_limit_price=take_profit_price,
        stop_loss_stop_price=stop_loss_price,
        time_in_force="gtc"  # Good til cancelled
    )
    
    if order:
        print("\n✅ SUCCESS! Bracket order placed:")
        print(f"   Order ID: {order.get('id')}")
        print(f"   Symbol: {order.get('symbol')}")
        print(f"   Status: {order.get('status')}")
        print(f"   Filled Qty: {order.get('filled_qty', 0)}")
        
        # Display the legs of the bracket order
        if 'legs' in order:
            print(f"\n   📋 Order Legs:")
            for leg in order['legs']:
                leg_type = leg.get('order_class', 'unknown')
                if 'take_profit' in str(leg).lower():
                    print(f"      ✅ Take Profit: ${leg.get('limit_price', 'N/A')} (Leg ID: {leg.get('id')[:8]}...)")
                elif 'stop_loss' in str(leg).lower() or leg.get('stop_price'):
                    print(f"      🛑 Stop Loss: ${leg.get('stop_price', 'N/A')} (Leg ID: {leg.get('id')[:8]}...)")
        
        print(f"\n💡 TIP: Monitor your position in the Alpaca dashboard")
        print(f"   The stop loss and take profit will execute automatically!")
    else:
        print("\n❌ Failed to place bracket order")
        print("   Check logs above for error details")
    
    print("\n" + "=" * 70)
    print("📊 CHECKING OPEN ORDERS")
    print("=" * 70)
    
    # Check open orders
    orders = alpaca.get_orders(status="open")
    if orders:
        print(f"\n✅ You have {len(orders)} open order(s):")
        for ord in orders[:5]:  # Show first 5
            print(f"\n   Order ID: {ord.get('id')[:12]}...")
            print(f"   Symbol: {ord.get('symbol')}")
            print(f"   Side: {ord.get('side').upper()}")
            print(f"   Qty: {ord.get('qty')}")
            print(f"   Type: {ord.get('type')}")
            print(f"   Status: {ord.get('status')}")
            if ord.get('order_class') == 'bracket':
                print(f"   🎯 BRACKET ORDER (includes stop loss & take profit)")
    else:
        print("\n   No open orders")
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
