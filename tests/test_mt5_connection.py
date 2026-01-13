"""
Test script for MT5 REST API connection
Quick test to verify MT5 integration is working
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_import():
    """Test if MT5 connector can be imported"""
    print("=" * 60)
    print("TEST 1: Import MT5 Connector")
    print("=" * 60)
    
    try:
        from frontend.utils.mt5_connector import MT5Connector, quick_connect, MT5Account, MT5Position
        print("✅ MT5 connector imported successfully")
        print(f"   - MT5Connector: {MT5Connector}")
        print(f"   - quick_connect: {quick_connect}")
        print(f"   - MT5Account: {MT5Account}")
        print(f"   - MT5Position: {MT5Position}")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_health_check():
    """Test MT5 API server health check"""
    print("\n" + "=" * 60)
    print("TEST 2: Health Check")
    print("=" * 60)
    
    try:
        from frontend.utils.mt5_connector import MT5Connector
        
        base_url = os.getenv("MT5_API_URL", "http://localhost:8000")
        print(f"Testing connection to: {base_url}")
        
        connector = MT5Connector(base_url)
        
        if connector.health_check():
            print("✅ MT5 API server is healthy and reachable")
            return True
        else:
            print("⚠️  MT5 API server is not responding")
            print("   This is expected if you haven't set up the server yet")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_connection():
    """Test MT5 account connection"""
    print("\n" + "=" * 60)
    print("TEST 3: MT5 Connection")
    print("=" * 60)
    
    user = os.getenv("MT5_USER")
    password = os.getenv("MT5_PASSWORD")
    host = os.getenv("MT5_HOST")
    port = int(os.getenv("MT5_PORT", "443"))
    base_url = os.getenv("MT5_API_URL", "http://localhost:8000")
    
    if not all([user, password, host]):
        print("⚠️  MT5 credentials not configured in .env")
        print("   Please set: MT5_USER, MT5_PASSWORD, MT5_HOST")
        return False
    
    try:
        from frontend.utils.mt5_connector import MT5Connector
        
        print(f"Connecting to MT5 account: {user}")
        print(f"Broker server: {host}:{port}")
        
        connector = MT5Connector(base_url)
        
        if connector.connect(user, password, host, port):
            print("✅ MT5 connection successful!")
            
            # Test account info
            account_info = connector.get_account_info()
            if account_info:
                print(f"   Balance: ${account_info.get('balance', 0):,.2f}")
                print(f"   Equity: ${account_info.get('equity', 0):,.2f}")
            
            connector.disconnect()
            return True
        else:
            print("❌ MT5 connection failed")
            print("   Check your credentials and MT5 API server")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def test_streamlit_component():
    """Test if Streamlit component can be imported"""
    print("\n" + "=" * 60)
    print("TEST 4: Streamlit Component")
    print("=" * 60)
    
    try:
        from frontend.components.mt5_dashboard import render_mt5_dashboard
        print("✅ MT5 Streamlit component imported successfully")
        print(f"   - render_mt5_dashboard: {render_mt5_dashboard}")
        return True
    except ImportError as e:
        print(f"❌ Component import failed: {e}")
        return False


def print_setup_instructions():
    """Print setup instructions"""
    print("\n" + "=" * 60)
    print("SETUP INSTRUCTIONS")
    print("=" * 60)
    print("\n📋 To complete MT5 integration:")
    print("\n1. Set up MT5 REST API Server")
    print("   - You need a server that implements the MT5 REST API endpoints")
    print("   - Server should run on port 8000 (or configure MT5_API_URL)")
    print("\n2. Configure environment variables in .env:")
    print("   MT5_API_URL=http://localhost:8000")
    print("   MT5_USER=your_account_number")
    print("   MT5_PASSWORD=your_password")
    print("   MT5_HOST=broker_server.com")
    print("   MT5_PORT=443")
    print("\n3. Test the connection:")
    print("   python test_mt5_connection.py")
    print("\n4. Run Streamlit app:")
    print("   streamlit run streamlit_app.py")
    print("   Navigate to '🔌 MT5 Trading' page")
    print("\n5. Or run examples:")
    print("   python examples/mt5_usage_examples.py")
    print("\n📚 Documentation: docs/MT5_INTEGRATION.md")
    print("=" * 60)


def main():
    """Run all tests"""
    print("\n" + "╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "MT5 INTEGRATION TEST" + " " * 23 + "║")
    print("╚" + "=" * 58 + "╝")
    
    results = []
    
    # Run tests
    results.append(("Import Test", test_import()))
    results.append(("Streamlit Component", test_streamlit_component()))
    results.append(("Health Check", test_health_check()))
    results.append(("MT5 Connection", test_connection()))
    
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
    
    if passed == total:
        print("\n🎉 All tests passed! MT5 integration is ready.")
    elif passed >= 2:
        print("\n⚠️  Basic setup complete, but connection tests failed.")
        print("This is normal if you haven't set up the MT5 API server yet.")
    else:
        print("\n❌ Some tests failed. Check error messages above.")
    
    # Print setup instructions
    print_setup_instructions()


if __name__ == "__main__":
    main()
