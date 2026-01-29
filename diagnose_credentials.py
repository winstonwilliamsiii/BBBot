"""
Quick Diagnostic - Shows current credential status
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("🔍 CREDENTIAL DIAGNOSTIC REPORT")
print("=" * 70)

# Plaid Check
print("\n" + "─" * 70)
print("📊 PLAID CREDENTIALS")
print("─" * 70)

plaid_client_id = os.getenv('PLAID_CLIENT_ID', '')
plaid_secret = os.getenv('PLAID_SECRET', '')
plaid_env = os.getenv('PLAID_ENV', 'sandbox')

if plaid_client_id:
    print(f"✅ PLAID_CLIENT_ID found")
    print(f"   Value: {plaid_client_id[:8]}...")
    print(f"   Length: {len(plaid_client_id)} characters")
    
    if len(plaid_client_id) == 24:
        print(f"   ✅ Length is correct (24 characters)")
    else:
        print(f"   ❌ WRONG LENGTH! Expected 24, got {len(plaid_client_id)}")
        print(f"   ⚠️  This will cause: 'client_id must be a properly formatted, non-empty string'")
else:
    print("❌ PLAID_CLIENT_ID not found")
    print("   ⚠️  This will cause: 'client_id must be a properly formatted, non-empty string'")

if plaid_secret:
    print(f"✅ PLAID_SECRET found")
    print(f"   Value: {plaid_secret[:8]}...")
    print(f"   Length: {len(plaid_secret)} characters")
else:
    print("❌ PLAID_SECRET not found")

print(f"ℹ️  Environment: {plaid_env}")

# Plaid Verdict
print("\n🔍 PLAID DIAGNOSIS:")
if not plaid_client_id or len(plaid_client_id) != 24:
    print("   ❌ PLAID WILL FAIL - Invalid or missing client_id")
    print("   📝 Action: Run 'python fix_credentials.py' and select option 1")
elif not plaid_secret:
    print("   ❌ PLAID WILL FAIL - Missing secret")
    print("   📝 Action: Run 'python fix_credentials.py' and select option 1")
else:
    print("   ✅ PLAID credentials look valid")
    print("   📝 If still failing, verify at: https://dashboard.plaid.com/")

# Alpaca Check
print("\n" + "─" * 70)
print("📊 ALPACA CREDENTIALS")
print("─" * 70)

alpaca_api_key = os.getenv('ALPACA_API_KEY', '')
alpaca_secret = os.getenv('ALPACA_SECRET_KEY', '')
alpaca_paper = os.getenv('ALPACA_PAPER', 'true')

if alpaca_api_key:
    print(f"✅ ALPACA_API_KEY found")
    print(f"   Value: {alpaca_api_key[:8]}...")
    print(f"   Length: {len(alpaca_api_key)} characters")
    
    if alpaca_api_key.startswith('PK'):
        print(f"   ℹ️  Key Type: PAPER TRADING (starts with 'PK')")
    elif alpaca_api_key.startswith('AK'):
        print(f"   ℹ️  Key Type: LIVE TRADING (starts with 'AK')")
    else:
        print(f"   ❌ UNKNOWN key type (starts with '{alpaca_api_key[:2]}')")
else:
    print("❌ ALPACA_API_KEY not found")

if alpaca_secret:
    print(f"✅ ALPACA_SECRET_KEY found")
    print(f"   Value: {alpaca_secret[:8]}...")
    print(f"   Length: {len(alpaca_secret)} characters")
else:
    print("❌ ALPACA_SECRET_KEY not found")

paper_mode = alpaca_paper.lower() == 'true'
print(f"\n🎯 Trading Mode: {'PAPER (virtual money)' if paper_mode else 'LIVE (real money)'}")

# Alpaca Verdict
print("\n🔍 ALPACA DIAGNOSIS:")
if not alpaca_api_key or not alpaca_secret:
    print("   ❌ ALPACA WILL FAIL - Missing credentials")
    print("   📝 Action: Run 'python fix_credentials.py' and select option 2")
elif alpaca_api_key.startswith('PK') and not paper_mode:
    print("   ❌ CONFIGURATION MISMATCH!")
    print("   ⚠️  You have PAPER keys (PK) but ALPACA_PAPER=false")
    print("   📝 Action: Either get live keys (AK) or set ALPACA_PAPER=true")
elif alpaca_api_key.startswith('AK') and paper_mode:
    print("   ⚠️  CONFIGURATION WARNING!")
    print("   ⚠️  You have LIVE keys (AK) but ALPACA_PAPER=true")
    print("   📝 This will try to use paper endpoint with live keys (will fail)")
    print("   📝 Action: Set ALPACA_PAPER=false to use live trading")
elif alpaca_api_key.startswith('PK') and paper_mode:
    print("   ✅ PAPER TRADING configured correctly")
    print("   ℹ️  To use production, get live keys from Alpaca dashboard")
elif alpaca_api_key.startswith('AK') and not paper_mode:
    print("   ✅ LIVE TRADING configured correctly")
    print("   ⚠️  WARNING: This uses real money! Ensure account is funded.")
else:
    print("   ⚠️  Unknown configuration")

# Summary
print("\n" + "=" * 70)
print("📋 SUMMARY")
print("=" * 70)

issues = []

if not plaid_client_id or len(plaid_client_id) != 24:
    issues.append("Plaid Client ID invalid/missing")
if not plaid_secret:
    issues.append("Plaid Secret missing")
if not alpaca_api_key or not alpaca_secret:
    issues.append("Alpaca credentials missing")
if alpaca_api_key and alpaca_api_key.startswith('PK') and not paper_mode:
    issues.append("Alpaca paper/live mismatch")
if alpaca_api_key and alpaca_api_key.startswith('AK') and paper_mode:
    issues.append("Alpaca live/paper mismatch")

if issues:
    print(f"\n❌ Found {len(issues)} issue(s):")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")
    print("\n📝 RECOMMENDED ACTION:")
    print("   Run: python fix_credentials.py")
    print("   This will guide you through fixing all issues")
else:
    print("\n✅ All credentials look good!")
    print("\n📝 NEXT STEPS:")
    print("   1. Test Plaid: python test_plaid_streamlit.py")
    print("   2. Test Alpaca: python tests/test_alpaca_connection.py")
    print("   3. Run app: streamlit run streamlit_app.py")

print("\n" + "=" * 70)
