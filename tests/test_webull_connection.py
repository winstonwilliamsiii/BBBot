"""
Test script for Webull API integration
Run this to verify your Webull credentials and API connection
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.webull_client import create_webull_client


def test_connection():
    """Test basic Webull API connection"""
    print("=" * 60)
    print("WEBULL API CONNECTION TEST")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Check for credentials
    app_key = os.getenv("WEBULL_APP_KEY")
    app_secret = os.getenv("WEBULL_APP_SECRET")
    
    if not app_key or not app_secret:
        print("❌ ERROR: Webull credentials not found in .env file")
        print("\nPlease add the following to your .env file:")
        print("WEBULL_APP_KEY=your_app_key_here")
        print("WEBULL_APP_SECRET=your_app_secret_here")
        return False
    
    print(f"✅ Credentials found")
    print(f"   App Key: {app_key[:8]}...{app_key[-4:]}")
    print(f"   App Secret: {app_secret[:8]}...{app_secret[-4:]}")
    print()
    
    try:
        # Initialize client (use test environment)
        print("🔄 Initializing Webull client (TEST environment)...")
        client = create_webull_client(use_production=False)
        print("✅ Client initialized successfully")
        print()
        
        # Test: Get accounts
        print("📋 Testing: Get Accounts...")
        accounts = client.get_accounts()
        print(f"✅ Found {len(accounts)} account(s)")
        
        if accounts:
            for i, acc in enumerate(accounts, 1):
                print(f"   Account {i}: {acc.get('account_id', 'N/A')}")
            print()
            
            # Get default account
            default_account = client.get_default_account_id()
            print(f"🎯 Default Account ID: {default_account}")
            print()
            
            # Test: Get balance
            print("💰 Testing: Get Account Balance...")
            balance = client.get_account_balance()
            print("✅ Balance retrieved:")
            print(f"   Total Value: ${balance.get('net_liquidation_value', 0):,.2f}")
            print(f"   Cash: ${balance.get('cash_balance', 0):,.2f}")
            print(f"   Buying Power: ${balance.get('buying_power', 0):,.2f}")
            print()
            
            # Test: Get positions
            print("📈 Testing: Get Positions...")
            positions = client.get_account_positions()
            print(f"✅ Found {len(positions) if positions else 0} position(s)")
            
            if positions:
                for pos in positions:
                    print(f"   {client.format_position_for_display(pos)}")
            else:
                print("   (No positions)")
            print()
            
            # Test: Get open orders
            print("📋 Testing: Get Open Orders...")
            orders = client.get_open_orders()
            print(f"✅ Found {len(orders) if orders else 0} open order(s)")
            
            if orders:
                for order in orders:
                    print(f"   {order.get('symbol', 'N/A')} - {order.get('side', 'N/A')} {order.get('quantity', 0)}")
            else:
                print("   (No open orders)")
            print()
            
            # Test: Portfolio summary
            print("📊 Testing: Portfolio Summary...")
            summary = client.get_portfolio_summary()
            print("✅ Portfolio summary:")
            print(f"   Account ID: {summary['account_id']}")
            print(f"   Total Value: ${summary['total_value']:,.2f}")
            print(f"   Cash Balance: ${summary['cash_balance']:,.2f}")
            print(f"   Buying Power: ${summary['buying_power']:,.2f}")
            print(f"   Positions: {summary['total_positions']}")
            print(f"   Timestamp: {summary['timestamp']}")
            print()
            
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nYour Webull integration is working correctly!")
        print("You can now use the Webull Trading dashboard in Streamlit.")
        print("\nTo launch the dashboard, run:")
        print("   streamlit run pages/webull_trading.py")
        print()
        
        return True
        
    except Exception as e:
        print("=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Verify your API credentials are correct")
        print("2. Check that you're using test environment credentials")
        print("3. Ensure your Webull account has API access enabled")
        print("4. Check your internet connection")
        print()
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
