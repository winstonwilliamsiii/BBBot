"""
Test Multi-Broker Integration
Verify Alpaca and IBKR connectors
"""

import os
from dotenv import load_dotenv

load_dotenv()


def test_imports():
    """Test if all connectors can be imported"""
    print("=" * 60)
    print("TEST 1: Import Connectors")
    print("=" * 60)
    
    try:
        from frontend.utils.alpaca_connector import AlpacaConnector, quick_connect_alpaca
        print("✅ Alpaca connector imported")
        
        from frontend.utils.ibkr_connector import IBKRConnector, quick_connect_ibkr
        print("✅ IBKR connector imported")
        
        from frontend.utils.mt5_connector import MT5Connector
        print("✅ MT5 connector imported")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_alpaca_connection():
    """Test Alpaca connection"""
    print("\n" + "=" * 60)
    print("TEST 2: Alpaca Connection")
    print("=" * 60)
    
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    
    if not api_key or not secret_key:
        print("⚠️  Alpaca credentials not configured in .env")
        print("   Set ALPACA_API_KEY and ALPACA_SECRET_KEY")
        return False
    
    try:
        from frontend.utils.alpaca_connector import AlpacaConnector
        
        print(f"Connecting to Alpaca (Paper trading)...")
        alpaca = AlpacaConnector(api_key, secret_key, paper=True)
        
        account = alpaca.get_account()
        
        if account:
            print("✅ Alpaca connection successful!")
            print(f"   Account Status: {account['status']}")
            print(f"   Portfolio Value: ${float(account['portfolio_value']):,.2f}")
            print(f"   Buying Power: ${float(account['buying_power']):,.2f}")
            print(f"   Cash: ${float(account['cash']):,.2f}")
            
            # Test market clock
            clock = alpaca.get_clock()
            if clock:
                print(f"   Market: {'🟢 Open' if clock['is_open'] else '🔴 Closed'}")
            
            # Test positions
            positions = alpaca.get_positions()
            print(f"   Open Positions: {len(positions) if positions else 0}")
            
            return True
        else:
            print("❌ Failed to get account info")
            return False
            
    except Exception as e:
        print(f"❌ Alpaca test failed: {e}")
        return False


def test_ibkr_connection():
    """Test IBKR Gateway connection"""
    print("\n" + "=" * 60)
    print("TEST 3: IBKR Gateway Connection")
    print("=" * 60)
    
    gateway_url = os.getenv("IBKR_GATEWAY_URL", "https://localhost:5000")
    
    print(f"Connecting to IBKR Gateway: {gateway_url}")
    print("⚠️  Make sure IBKR Gateway is running!")
    
    try:
        from frontend.utils.ibkr_connector import IBKRConnector
        
        ibkr = IBKRConnector(gateway_url)
        
        if ibkr.is_authenticated():
            print("✅ IBKR Gateway connection successful!")
            
            # Get accounts
            accounts = ibkr.get_accounts()
            if accounts:
                print(f"   Accounts: {', '.join(accounts)}")
                
                # Get positions for first account
                positions = ibkr.get_positions(accounts[0])
                print(f"   Open Positions: {len(positions) if positions else 0}")
                
                if positions:
                    print("   Sample positions:")
                    for pos in positions[:3]:  # Show first 3
                        print(f"     - {pos.symbol}: {pos.position} @ ${pos.market_value:,.2f}")
            
            return True
        else:
            print("⚠️  IBKR Gateway not authenticated")
            print("   This is normal if Gateway is not running")
            print("   Start IBKR Gateway and try again")
            return False
            
    except Exception as e:
        print(f"⚠️  IBKR test skipped: {e}")
        print("   This is normal if Gateway is not running")
        return False


def test_mt5_connection():
    """Test MT5 connection"""
    print("\n" + "=" * 60)
    print("TEST 4: MT5 Connection")
    print("=" * 60)
    
    base_url = os.getenv("MT5_API_URL", "http://localhost:8000")
    user = os.getenv("MT5_USER")
    
    if not user:
        print("⚠️  MT5 credentials not configured")
        return False
    
    try:
        from frontend.utils.mt5_connector import MT5Connector
        
        connector = MT5Connector(base_url)
        
        # Test health check
        if connector.health_check():
            print("✅ MT5 REST API server is healthy")
            
            # Try to connect
            if connector.connect(
                user=user,
                password=os.getenv("MT5_PASSWORD", ""),
                host=os.getenv("MT5_HOST", ""),
                port=int(os.getenv("MT5_PORT", "443"))
            ):
                print("✅ MT5 connection successful!")
                
                account = connector.get_account_info()
                if account:
                    print(f"   Balance: ${account.get('balance', 0):,.2f}")
                    print(f"   Equity: ${account.get('equity', 0):,.2f}")
                
                connector.disconnect()
                return True
            else:
                print("⚠️  MT5 connection failed")
                return False
        else:
            print("⚠️  MT5 REST API server not responding")
            return False
            
    except Exception as e:
        print(f"⚠️  MT5 test skipped: {e}")
        return False


def test_multi_broker_dashboard():
    """Test multi-broker dashboard component"""
    print("\n" + "=" * 60)
    print("TEST 5: Multi-Broker Dashboard")
    print("=" * 60)
    
    try:
        from frontend.components.multi_broker_dashboard import render_multi_broker_dashboard
        print("✅ Multi-broker dashboard imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Dashboard import failed: {e}")
        return False


def print_setup_guide():
    """Print setup instructions"""
    print("\n" + "=" * 60)
    print("SETUP GUIDE")
    print("=" * 60)
    
    print("\n📋 Broker Setup Instructions:\n")
    
    print("1️⃣  ALPACA (Stocks & Crypto)")
    print("   • Sign up: https://alpaca.markets/")
    print("   • Get API keys from dashboard")
    print("   • Add to .env:")
    print("     ALPACA_API_KEY=your_key")
    print("     ALPACA_SECRET_KEY=your_secret")
    print("     ALPACA_PAPER=true")
    
    print("\n2️⃣  IBKR (Multi-Asset)")
    print("   • Download Gateway: https://www.interactivebrokers.com/")
    print("   • Install and run Gateway")
    print("   • Enable API (port 5000)")
    print("   • Add to .env:")
    print("     IBKR_GATEWAY_URL=https://localhost:5000")
    
    print("\n3️⃣  MT5 (FOREX & Futures)")
    print("   • Open MT5 account with broker")
    print("   • Set up MT5 REST API server")
    print("   • Add to .env:")
    print("     MT5_API_URL=http://localhost:8000")
    print("     MT5_USER=your_account")
    print("     MT5_PASSWORD=your_password")
    print("     MT5_HOST=broker.com")
    
    print("\n4️⃣  Run Streamlit App")
    print("   streamlit run streamlit_app.py")
    print("   Navigate to: 🌐 Multi-Broker Trading")
    
    print("\n📚 Documentation:")
    print("   • Multi-Broker: docs/MULTI_BROKER_GUIDE.md")
    print("   • MT5 Only: docs/MT5_INTEGRATION.md")
    print("=" * 60)


def main():
    """Run all tests"""
    print("\n" + "╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "MULTI-BROKER INTEGRATION TEST" + " " * 17 + "║")
    print("╚" + "=" * 58 + "╝")
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Multi-Broker Dashboard", test_multi_broker_dashboard()))
    results.append(("Alpaca Connection", test_alpaca_connection()))
    results.append(("IBKR Connection", test_ibkr_connection()))
    results.append(("MT5 Connection", test_mt5_connection()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10s} - {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed >= 2:
        print("\n🎉 Core components installed successfully!")
        print("Connection tests may fail if brokers are not configured yet.")
    else:
        print("\n⚠️  Some core components failed. Check errors above.")
    
    # Print setup guide
    print_setup_guide()


if __name__ == "__main__":
    main()
