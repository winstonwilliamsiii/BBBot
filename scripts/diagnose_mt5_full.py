"""
Advanced MT5 Connection Diagnostics
Checks all possible connection issues
"""
import MetaTrader5 as mt5
import os
from pathlib import Path

print("\n" + "="*60)
print("  ADVANCED MT5 DIAGNOSTICS")
print("="*60)

# Test 1: Check MT5 installation paths
print("\n[1] Checking MT5 Installation...")
common_paths = [
    r"C:\Program Files\MetaTrader 5\terminal64.exe",
    r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
    os.path.expandvars(r"%APPDATA%\MetaQuotes\Terminal\*"),
]

mt5_found = False
for path in common_paths:
    p = Path(path)
    if p.exists():
        print(f"    ✅ Found MT5 at: {path}")
        mt5_found = True
        break
    elif '*' in path:
        parent = Path(path.replace('*', '')).parent
        if parent.exists():
            print(f"    ✅ MT5 data folder: {parent}")
            
if not mt5_found:
    print("    ⚠️  Could not find standard MT5 installation")

# Test 2: Try different initialization methods
print("\n[2] Testing Initialization Methods...")

# Method 1: Default initialization
print("\n    Method 1: Default mt5.initialize()")
if mt5.initialize():
    print("    ✅ Success with default initialization!")
    account_info = mt5.account_info()
    if account_info:
        print(f"    ✅ Connected to account: {account_info.login}")
        print(f"    Server: {account_info.server}")
        print(f"    Balance: ${account_info.balance:,.2f}")
    mt5.shutdown()
else:
    error = mt5.last_error()
    print(f"    ❌ Failed: {error}")

# Method 2: Try with explicit path
print("\n    Method 2: With explicit path")
mt5_exe = r"C:\Program Files\MetaTrader 5\terminal64.exe"
if Path(mt5_exe).exists():
    if mt5.initialize(mt5_exe):
        print(f"    ✅ Success with path: {mt5_exe}")
        mt5.shutdown()
    else:
        error = mt5.last_error()
        print(f"    ❌ Failed: {error}")
else:
    print(f"    ⚠️  Path not found: {mt5_exe}")

# Method 3: Try with timeout
print("\n    Method 3: With timeout parameter")
if mt5.initialize(timeout=10000):
    print("    ✅ Success with timeout!")
    mt5.shutdown()
else:
    error = mt5.last_error()
    print(f"    ❌ Failed: {error}")

# Test 3: Check for API restrictions
print("\n[3] Checking API Settings...")
print("    ⚠️  If all initialization methods fail, check MT5 settings:")
print("    1. In MT5: Tools → Options → Expert Advisors")
print("    2. Enable: 'Allow automated trading'")
print("    3. Enable: 'Allow DLL imports'")
print("    4. Check that 'Disable automated trading' is NOT checked")
print("    5. Restart MT5 terminal after changing settings")

# Test 4: Process check
print("\n[4] MT5 Process Information...")
import psutil
for proc in psutil.process_iter(['pid', 'name', 'create_time']):
    try:
        if 'terminal64' in proc.info['name'].lower():
            print(f"    ✅ Process: {proc.info['name']}")
            print(f"    PID: {proc.info['pid']}")
            import datetime
            create_time = datetime.datetime.fromtimestamp(proc.info['create_time'])
            print(f"    Started: {create_time}")
    except:
        pass

print("\n" + "="*60)
print("  DIAGNOSTICS COMPLETE")
print("="*60)
print("\n💡 If connection still fails:")
print("   1. Close MT5 completely")
print("   2. Restart MT5 and login")
print("   3. In MT5: Tools → Options → Expert Advisors")
print("   4. Check 'Allow automated trading'")
print("   5. Uncheck 'Disable automated trading'")
print("   6. Click OK")
print("   7. Run this test again")
print("="*60 + "\n")
