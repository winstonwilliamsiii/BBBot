"""
MT5 Connection Test with Timeout
"""
import MetaTrader5 as mt5
import sys
from threading import Thread, Event

def test_connection(result_list, stop_event):
    """Test connection in separate thread"""
    try:
        print("Attempting MT5 initialization...")
        initialized = mt5.initialize(timeout=30000)  # 30 second timeout
        result_list.append(("init", initialized))
        
        if initialized:
            print("Getting account info...")
            account = mt5.account_info()
            result_list.append(("account", account))
            mt5.shutdown()
        else:
            error = mt5.last_error()
            result_list.append(("error", error))
    except Exception as e:
        result_list.append(("exception", str(e)))
    finally:
        stop_event.set()

print("="*60)
print("MT5 CONNECTION TEST (with 10-second timeout)")
print("="*60)

# Run test in thread with timeout
results = []
stop_event = Event()
thread = Thread(target=test_connection, args=(results, stop_event))
thread.daemon = True
thread.start()

# Wait max 10 seconds
if stop_event.wait(timeout=10):
    print("\n✅ Test completed")
    
    for result_type, result_value in results:
        if result_type == "init":
            if result_value:
                print("\n🎉 MT5 INITIALIZED SUCCESSFULLY!")
            else:
                print("\n❌ MT5 initialization failed")
        elif result_type == "account":
            if result_value:
                print(f"\n✅ ACCOUNT CONNECTED:")
                print(f"   Login: {result_value.login}")
                print(f"   Server: {result_value.server}")
                print(f"   Balance: ${result_value.balance:,.2f}")
                print(f"   Equity: ${result_value.equity:,.2f}")
            else:
                print("\n⚠️  No account info available")
        elif result_type == "error":
            print(f"\n❌ Error: {result_value}")
        elif result_type == "exception":
            print(f"\n❌ Exception: {result_value}")
else:
    print("\n⏱️  TIMEOUT: MT5 initialization took longer than 10 seconds")
    print("\n⚠️  POSSIBLE ISSUES:")
    print("   1. MT5 may be showing a dialog box - check the MT5 window")
    print("   2. MT5 may need admin approval for API access")
    print("   3. Check MT5: Tools → Options → Expert Advisors")
    print("      - Ensure 'Allow automated trading' is checked")
    print("      - Ensure 'Disable automated trading' is UNchecked")
    print("\n   4. Try closing and reopening MT5")
    print("   5. Make sure you're logged in (green bars bottom-right)")

print("\n" + "="*60)
