"""
Example usage of MT5 REST API Connector
Demonstrates all major functionality
"""

import os
from dotenv import load_dotenv
from frontend.utils.mt5_connector import MT5Connector, quick_connect

load_dotenv()


def example_basic_connection():
    """Example 1: Basic connection"""
    print("=" * 60)
    print("Example 1: Basic MT5 Connection")
    print("=" * 60)
    
    # Method 1: Using MT5Connector class
    connector = MT5Connector(base_url="http://localhost:8000")
    
    if connector.connect(
        user=os.getenv("MT5_USER", "123456"),
        password=os.getenv("MT5_PASSWORD", "password"),
        host=os.getenv("MT5_HOST", "broker.com"),
        port=int(os.getenv("MT5_PORT", "443"))
    ):
        print("✅ Connected successfully!")
        
        # Get account info
        account_info = connector.get_account_info()
        if account_info:
            print(f"\nAccount Balance: ${account_info.get('balance', 0):,.2f}")
            print(f"Account Equity: ${account_info.get('equity', 0):,.2f}")
            print(f"Margin Used: ${account_info.get('margin', 0):,.2f}")
        
        connector.disconnect()
    else:
        print("❌ Connection failed")
    
    print()


def example_quick_connect():
    """Example 2: Quick connect helper"""
    print("=" * 60)
    print("Example 2: Quick Connect")
    print("=" * 60)
    
    # Method 2: Using quick_connect helper
    mt5 = quick_connect(
        base_url="http://localhost:8000",
        user=os.getenv("MT5_USER", "123456"),
        password=os.getenv("MT5_PASSWORD", "password"),
        host=os.getenv("MT5_HOST", "broker.com")
    )
    
    if mt5:
        print("✅ Quick connect successful!")
        mt5.disconnect()
    else:
        print("❌ Quick connect failed")
    
    print()


def example_market_data():
    """Example 3: Fetch market data"""
    print("=" * 60)
    print("Example 3: Market Data")
    print("=" * 60)
    
    mt5 = quick_connect(
        base_url="http://localhost:8000",
        user=os.getenv("MT5_USER"),
        password=os.getenv("MT5_PASSWORD"),
        host=os.getenv("MT5_HOST")
    )
    
    if mt5:
        # Get EURUSD market data
        print("Fetching EURUSD H1 data...")
        market_data = mt5.get_market_data(symbol="EURUSD", timeframe="H1", count=10)
        
        if market_data:
            print(f"✅ Retrieved {len(market_data.get('bars', []))} bars")
            
            # Get current symbol info
            symbol_info = mt5.get_symbol_info("EURUSD")
            if symbol_info:
                print(f"\nEURUSD Current Prices:")
                print(f"  Bid: {symbol_info.get('bid', 0):.5f}")
                print(f"  Ask: {symbol_info.get('ask', 0):.5f}")
                print(f"  Spread: {symbol_info.get('spread', 0)} points")
        
        mt5.disconnect()
    
    print()


def example_positions():
    """Example 4: View and manage positions"""
    print("=" * 60)
    print("Example 4: Position Management")
    print("=" * 60)
    
    mt5 = quick_connect(
        base_url="http://localhost:8000",
        user=os.getenv("MT5_USER"),
        password=os.getenv("MT5_PASSWORD"),
        host=os.getenv("MT5_HOST")
    )
    
    if mt5:
        positions = mt5.get_positions()
        
        if positions:
            print(f"✅ Found {len(positions)} open positions:")
            for pos in positions:
                print(f"\n  Ticket: {pos.ticket}")
                print(f"  Symbol: {pos.symbol}")
                print(f"  Type: {pos.type}")
                print(f"  Volume: {pos.volume} lots")
                print(f"  Profit: ${pos.profit:.2f}")
        else:
            print("No open positions")
        
        mt5.disconnect()
    
    print()


def example_place_trade():
    """Example 5: Place a trade (demo/test only)"""
    print("=" * 60)
    print("Example 5: Place Trade Order")
    print("=" * 60)
    print("⚠️  This is a DEMO - Uncomment to actually place trades!")
    
    mt5 = quick_connect(
        base_url="http://localhost:8000",
        user=os.getenv("MT5_USER"),
        password=os.getenv("MT5_PASSWORD"),
        host=os.getenv("MT5_HOST")
    )
    
    if mt5:
        # UNCOMMENT BELOW TO ACTUALLY PLACE TRADE
        """
        result = mt5.place_trade(
            symbol="EURUSD",
            order_type="BUY",
            volume=0.01,  # Minimum lot size
            sl=1.0800,    # Stop loss
            tp=1.0900,    # Take profit
            comment="Test trade from Python"
        )
        
        if result and result.get('success'):
            print(f"✅ Trade placed! Ticket: {result.get('ticket')}")
        else:
            print(f"❌ Trade failed: {result.get('error') if result else 'Unknown error'}")
        """
        
        print("Trade placement code is commented out for safety")
        mt5.disconnect()
    
    print()


def example_modify_position():
    """Example 6: Modify position SL/TP"""
    print("=" * 60)
    print("Example 6: Modify Position")
    print("=" * 60)
    print("⚠️  This is a DEMO - Uncomment to actually modify positions!")
    
    mt5 = quick_connect(
        base_url="http://localhost:8000",
        user=os.getenv("MT5_USER"),
        password=os.getenv("MT5_PASSWORD"),
        host=os.getenv("MT5_HOST")
    )
    
    if mt5:
        positions = mt5.get_positions()
        
        if positions:
            # UNCOMMENT BELOW TO ACTUALLY MODIFY POSITION
            """
            ticket = positions[0].ticket  # First position
            
            success = mt5.modify_position(
                ticket=ticket,
                sl=1.0850,  # New stop loss
                tp=1.0950   # New take profit
            )
            
            if success:
                print(f"✅ Position {ticket} modified successfully")
            else:
                print(f"❌ Failed to modify position {ticket}")
            """
            
            print(f"Found {len(positions)} positions (modification code commented out)")
        else:
            print("No positions to modify")
        
        mt5.disconnect()
    
    print()


def example_webhooks():
    """Example 7: Setup webhooks"""
    print("=" * 60)
    print("Example 7: Webhook Configuration")
    print("=" * 60)
    
    mt5 = quick_connect(
        base_url="http://localhost:8000",
        user=os.getenv("MT5_USER"),
        password=os.getenv("MT5_PASSWORD"),
        host=os.getenv("MT5_HOST")
    )
    
    if mt5:
        # Setup webhook for trade and position events
        webhook_url = os.getenv("MT5_WEBHOOK_URL", "https://your-server.com/webhook")
        events = ['trade', 'position', 'account']
        
        print(f"Setting up webhook to: {webhook_url}")
        print(f"Events: {', '.join(events)}")
        
        # UNCOMMENT TO ACTUALLY SETUP WEBHOOK
        """
        success = mt5.setup_webhook(webhook_url, events)
        
        if success:
            print("✅ Webhook configured successfully")
        else:
            print("❌ Failed to setup webhook")
        """
        
        print("Webhook setup code is commented out")
        mt5.disconnect()
    
    print()


def example_health_check():
    """Example 8: Health check"""
    print("=" * 60)
    print("Example 8: Health Check")
    print("=" * 60)
    
    connector = MT5Connector(base_url="http://localhost:8000")
    
    if connector.health_check():
        print("✅ MT5 REST API server is healthy and reachable")
    else:
        print("❌ MT5 REST API server is not responding")
    
    print()


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("MT5 REST API Connector - Examples")
    print("=" * 60 + "\n")
    
    # Check for environment variables
    if not os.getenv("MT5_USER"):
        print("⚠️  MT5 credentials not found in .env file")
        print("Please set MT5_USER, MT5_PASSWORD, MT5_HOST in your .env file\n")
    
    # Run examples
    example_health_check()
    example_basic_connection()
    example_quick_connect()
    example_market_data()
    example_positions()
    example_place_trade()
    example_modify_position()
    example_webhooks()
    
    print("=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
