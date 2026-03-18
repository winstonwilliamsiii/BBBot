"""Simple MT5 connection test - clean output"""
import MetaTrader5 as mt5

print("Testing MT5...")
result = mt5.initialize(
    login=531220202,
    password="*zH4!B5ZGB!8a",
    server="FTMO-Server3",
)

if result:
    print("\n✅ SUCCESS! MT5 Connected!")
    account = mt5.account_info()
    if account:
        print(f"\nAccount: {account.login}")
        print(f"Server: {account.server}")
        print(f"Balance: ${account.balance:,.2f}")
    mt5.shutdown()
else:
    error = mt5.last_error()
    print(f"\n❌ FAILED: {error}")
    print("\nPlease check:")
    print("1. MT5 is running")
    print("2. Logged into account")
    print("3. Tools → Options → Expert Advisors")
    print("4. 'Allow automated trading' is checked")
