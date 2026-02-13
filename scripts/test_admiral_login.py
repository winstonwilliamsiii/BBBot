"""
Test MT5 connection with AdmiralsGroup demo account
"""
import MetaTrader5 as mt5

print("\n" + "="*60)
print("  TESTING ADMIRALSGROUP DEMO CONNECTION")
print("="*60)

# Initialize MT5
print("\n[1] Initializing MT5...")
if not mt5.initialize():
    print(f"❌ Initialization failed: {mt5.last_error()}")
    exit(1)
print("✅ MT5 initialized")

# Login credentials
account = 5615791854
password = "wvS7ftBb"
server = "AdmiralsGroup-Demo"

print(f"\n[2] Attempting login...")
print(f"    Account: {account}")
print(f"    Server: {server}")

# Attempt login
authorized = mt5.login(account, password=password, server=server)

if authorized:
    print("✅ Login successful!")
    
    account_info = mt5.account_info()
    if account_info:
        print(f"\n[3] Account Information:")
        print(f"    Login: {account_info.login}")
        print(f"    Name: {account_info.name}")
        print(f"    Server: {account_info.server}")
        print(f"    Balance: ${account_info.balance:,.2f}")
        print(f"    Equity: ${account_info.equity:,.2f}")
        print(f"    Margin: ${account_info.margin:,.2f}")
        print(f"    Margin Free: ${account_info.margin_free:,.2f}")
        print(f"    Leverage: 1:{account_info.leverage}")
        print(f"    Currency: {account_info.currency}")
        
        print("\n" + "="*60)
        print("  ✅ CONNECTION SUCCESSFUL - READY FOR TRADING")
        print("="*60)
else:
    error = mt5.last_error()
    print(f"❌ Login failed!")
    print(f"   Error Code: {error[0]}")
    print(f"   Error Message: {error[1]}")
    print(f"\n   Common issues:")
    print(f"   - Check server name (try 'AdmiralsGroup-Demo' vs 'AdmiralsGroup_Demo')")
    print(f"   - Verify account number is correct")
    print(f"   - Check password is correct")
    print(f"   - Ensure MT5 terminal is running")

mt5.shutdown()
print()
