"""
Test Alpaca Connection Script
Validates Alpaca API credentials and connection status
"""
    
import os
import sys
import pathlib
# Ensure project root is in sys.path for import
project_root = pathlib.Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
from dotenv import load_dotenv
        
# Load environment variables
load_dotenv()
        
print("=" * 60)
print("ALPACA CONNECTION TEST")
print("=" * 60)
        
# Import connector
try:
    from frontend.components.alpaca_connector import AlpacaConnector
    print("✅ Alpaca connector imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Alpaca connector: {e}")
    sys.exit(1)
        
# Get credentials from environment
api_key = os.getenv("ALPACA_API_KEY", "")
secret_key = os.getenv("ALPACA_SECRET_KEY", "")
paper = os.getenv("ALPACA_PAPER", "true").lower() == "true"
        
print("\n" + "=" * 60)
print("STEP 1: Environment Configuration")
print("=" * 60)
    
if not api_key:
    print("❌ ALPACA_API_KEY not found in .env")
    sys.exit(1)
else:
    print(f"✅ ALPACA_API_KEY found: {api_key[:8]}...")
    
if not secret_key:
    print("❌ ALPACA_SECRET_KEY not found in .env")
    sys.exit(1)
else:
    print(f"✅ ALPACA_SECRET_KEY found: {secret_key[:8]}...")
    
print(f"✅ Trading Mode: {'PAPER' if paper else 'LIVE'}")

# Initialize connector
print("\n" + "=" * 60)
print("STEP 2: Initialize Connector")
print("=" * 60)

try:
    alpaca = AlpacaConnector(api_key, secret_key, paper)
    print("✅ Alpaca connector initialized")
except Exception as e:
    print(f"❌ Failed to initialize connector: {e}")
    sys.exit(1)

# Test authentication
print("\n" + "=" * 60)
print("STEP 3: Test Authentication")
print("=" * 60)

try:
    account = alpaca.get_account()
    
    if account:
        print("✅ Authentication successful!")
        print("\n📊 Account Summary:")
        print(f"   Account ID: {account.get('id', 'N/A')}")
        print(f"   Status: {account.get('status', 'N/A')}")
        print(f"   Currency: {account.get('currency', 'N/A')}")
        print(f"   Buying Power: ${float(account.get('buying_power', 0)):,.2f}")
        print(f"   Cash: ${float(account.get('cash', 0)):,.2f}")
        print(f"   Portfolio Value: ${float(account.get('portfolio_value', 0)):,.2f}")
        print(f"   Equity: ${float(account.get('equity', 0)):,.2f}")
        
        # Trading status
        print("\n🔒 Trading Status:")
        print(f"   Trading Blocked: {account.get('trading_blocked', 'N/A')}")
        print(f"   Account Blocked: {account.get('account_blocked', 'N/A')}")
        print(f"   Pattern Day Trader: {account.get('pattern_day_trader', 'N/A')}")
        
        # Check if ready to trade
        trading_blocked = account.get('trading_blocked', False)
        account_blocked = account.get('account_blocked', False)
        
        if not trading_blocked and not account_blocked:
            print("\n✅ READY TO TRADE!")
        else:
            print("\n⚠️ TRADING RESTRICTED")
    else:
        print("❌ Failed to retrieve account information")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Authentication test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test market clock
print("\n" + "=" * 60)
print("STEP 4: Market Status")
print("=" * 60)

try:
    clock = alpaca.get_clock()
    if clock:
        is_open = clock.get('is_open', False)
        next_open = clock.get('next_open', 'N/A')
        next_close = clock.get('next_close', 'N/A')
        
        print(f"   Market Open: {'🟢 YES' if is_open else '🔴 NO'}")
        print(f"   Next Open: {next_open}")
        print(f"   Next Close: {next_close}")
    else:
        print("⚠️ Could not fetch market clock")
except Exception as e:
    print(f"⚠️ Market clock error: {e}")

# Test positions
print("\n" + "=" * 60)
print("STEP 5: Current Positions")
print("=" * 60)

try:
    positions = alpaca.get_positions()
    
    if positions is not None:
        if len(positions) > 0:
            print(f"✅ Found {len(positions)} position(s):")
            for pos in positions[:5]:  # Show first 5
                print(f"\n   {pos.symbol}:")
                print(f"      Qty: {pos.qty}")
                print(f"      Side: {pos.side}")
                print(f"      Market Value: ${pos.market_value:,.2f}")
                print(f"      P/L: ${pos.unrealized_pl:,.2f} ({pos.unrealized_plpc*100:.2f}%)")
        else:
            print("ℹ️  No open positions")
    else:
        print("⚠️ Could not fetch positions")
except Exception as e:
    print(f"⚠️ Positions error: {e}")

# Test orders
print("\n" + "=" * 60)
print("STEP 6: Open Orders")
print("=" * 60)

try:
    orders = alpaca.get_orders(status="open")
    
    if orders is not None:
        if len(orders) > 0:
            print(f"✅ Found {len(orders)} open order(s)")
            for order in orders[:5]:  # Show first 5
                print(f"\n   Order ID: {order.get('id', 'N/A')[:8]}...")
                print(f"      Symbol: {order.get('symbol', 'N/A')}")
                print(f"      Side: {order.get('side', 'N/A')}")
                print(f"      Type: {order.get('type', 'N/A')}")
                print(f"      Status: {order.get('status', 'N/A')}")
        else:
            print("ℹ️  No open orders")
    else:
        print("⚠️ Could not fetch orders")
except Exception as e:
    print(f"⚠️ Orders error: {e}")

# Final summary
print("\n" + "=" * 60)
print("✅ CONNECTION TEST COMPLETE")
print("=" * 60)

print("\n" + "=" * 60)
print("STEP 7: Place SUPX Buy Order @ $16.50")
print("=" * 60)
try:
    order = alpaca.place_order(
        symbol="SUPX",
        qty=1,
        side="buy",
        order_type="limit",
        time_in_force="day",
        limit_price=16.50
    )
    if order:
        print(f"✅ Order placed! ID: {order.get('id', 'N/A')}")
        print(f"   Symbol: {order.get('symbol', 'N/A')}")
        print(f"   Side: {order.get('side', 'N/A')}")
        print(f"   Type: {order.get('type', 'N/A')}")
        print(f"   Limit Price: {order.get('limit_price', 'N/A')}")
        print(f"   Status: {order.get('status', 'N/A')}")
        # Send Discord notification
        try:
            from frontend.utils.discord_alpaca import send_discord_trade_notification
            sent = send_discord_trade_notification(
                symbol=order.get('symbol', 'SUPX'),
                side=order.get('side', 'buy'),
                qty=order.get('qty', 1),
                order_type=order.get('type', 'limit'),
                limit_price=order.get('limit_price', 16.50),
                status=order.get('status', 'pending_new')
            )
            if sent:
                print("✅ Discord notification sent.")
            else:
                print("⚠️ Discord notification failed (check webhook URL)")
        except Exception as e:
            print(f"⚠️ Discord notification error: {e}")
    else:
        print("❌ Order failed (no response)")
except Exception as e:
    print(f"❌ Order error: {e}")

print("\nAlpaca is ready for:")
print("  ✅ Bentley Bot Investment Page")
print("  ✅ Brokerage Dashboard")
print("  ✅ Multi-Broker Trading Hub")
print("\nNext integrations planned:")
print("  🔜 IBKR via QuantConnect")
print("  🔜 Think or Swim (Charles Schwab Dev)")
print("  🔜 NinjaTrader (Futures & FOREX)")
print("  🔜 Binance (Production)")
print("\nRun: streamlit run streamlit_app.py")
print("Navigate to: 🌐 Multi-Broker Trading Hub")
print("=" * 60)
