"""
Quick Environment Check for Streamlit
Verifies .env loading in Streamlit context
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("ENVIRONMENT VARIABLES CHECK")
print("=" * 60)

# Check Alpaca credentials
alpaca_key = os.getenv("ALPACA_API_KEY", "")
alpaca_secret = os.getenv("ALPACA_SECRET_KEY", "")
alpaca_paper = os.getenv("ALPACA_PAPER", "")

print("\n🔍 Alpaca Configuration:")
print(f"   ALPACA_API_KEY: {'✅ Found' if alpaca_key else '❌ Missing'} ({alpaca_key[:10]}... if found)")
print(f"   ALPACA_SECRET_KEY: {'✅ Found' if alpaca_secret else '❌ Missing'} ({alpaca_secret[:10]}... if found)")
print(f"   ALPACA_PAPER: {'✅ Found' if alpaca_paper else '❌ Missing'} ({alpaca_paper})")

# Check other broker credentials
print("\n🔍 MT5 Configuration:")
mt5_url = os.getenv("MT5_API_URL", "")
mt5_user = os.getenv("MT5_USER", "")
print(f"   MT5_API_URL: {'✅ Found' if mt5_url else '❌ Missing'} ({mt5_url})")
print(f"   MT5_USER: {'✅ Found' if mt5_user else '❌ Missing'}")

print("\n🔍 IBKR Configuration:")
ibkr_url = os.getenv("IBKR_GATEWAY_URL", "")
print(f"   IBKR_GATEWAY_URL: {'✅ Found' if ibkr_url else '❌ Missing'} ({ibkr_url})")

print("\n" + "=" * 60)
print("✅ Environment check complete")
print("=" * 60)

# Show current working directory
print(f"\n📂 Current Directory: {os.getcwd()}")
print(f"📄 .env file exists: {os.path.exists('.env')}")

if os.path.exists('.env'):
    with open('.env', 'r') as f:
        lines = [line for line in f if 'ALPACA' in line and not line.strip().startswith('#')]
        print(f"📝 Alpaca lines in .env: {len(lines)}")
