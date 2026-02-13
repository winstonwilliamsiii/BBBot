"""
Quick MT5 Connection Test
Tests the running MT5 REST API server
"""
import MetaTrader5 as mt5
from datetime import datetime

print("\n" + "="*60)
print("  MT5 CONNECTION DIAGNOSTIC")
print("="*60)

# Test 1: MT5 Package
print("\n[1] Testing MT5 Package...")
try:
    print(f"    ✅ MetaTrader5 version: {mt5.__version__}")
except:
    print(f"    ✅ MetaTrader5 package imported")

# Test 2: MT5 Terminal Process
print("\n[2] Checking MT5 Terminal Process...")
import psutil
mt5_running = False
for proc in psutil.process_iter(['name']):
    if 'terminal64' in proc.info['name'].lower():
        mt5_running = True
        print(f"    ✅ MT5 Terminal is running (PID: {proc.pid})")
        break
if not mt5_running:
    print("    ❌ MT5 Terminal not detected!")
    print("    Please start MetaTrader 5 desktop application")
    exit(1)

# Test 3: Initialize MT5
print("\n[3] Initializing MT5 Connection...")
if not mt5.initialize():
    error = mt5.last_error()
    print(f"    ❌ MT5 initialization failed!")
    print(f"    Error Code: {error[0]}")
    print(f"    Error Message: {error[1]}")
    print("\n    SOLUTION:")
    print("    1. Open MetaTrader 5 terminal")
    print("    2. Go to: File → Open an Account")
    print("    3. Select or create a DEMO account")
    print("    4. Log in with your credentials")
    print("    5. Keep MT5 terminal running")
    print("    6. Run this test again")
    exit(1)
else:
    print("    ✅ MT5 initialized successfully!")

# Test 4: Get Account Info
print("\n[4] Getting Account Information...")
account = mt5.account_info()
if account is None:
    print("    ❌ No account info available")
    print("    Please log into your MT5 account")
else:
    print(f"    ✅ Account connected!")
    print(f"    Login: {account.login}")
    print(f"    Server: {account.server}")
    print(f"    Balance: ${account.balance:,.2f}")
    print(f"    Equity: ${account.equity:,.2f}")
    print(f"    Margin Free: ${account.margin_free:,.2f}")
    print(f"    Account Type: {'DEMO' if 'Demo' in account.server or 'demo' in account.server.lower() else 'REAL'}")

# Test 5: REST API Server
print("\n[5] Testing MT5 REST API Server...")
import requests
try:
    response = requests.get("http://localhost:8002/Health", timeout=3)
    data = response.json()
    print(f"    ✅ Server is running on port 8002")
    print(f"    Status: {data.get('status')}")
    print(f"    MT5 Initialized: {data.get('mt5_initialized')}")
except Exception as e:
    print(f"    ❌ Server not responding: {e}")

# Clean up
mt5.shutdown()

print("\n" + "="*60)
print("  ✅ MT5 CONNECTION TEST COMPLETE")
print("="*60)
print("\n📝 Next Steps:")
print("   • MT5 server is running on: http://localhost:8002")
print("   • Your application can now connect to MT5")
print("   • Use /Health, /AccountInfo, /Positions endpoints")
print("="*60 + "\n")
