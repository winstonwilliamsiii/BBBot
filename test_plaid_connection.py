"""
Test Plaid Connection - Diagnostic Script
Run this to check if Plaid credentials are working
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv(override=True)

print("\n" + "="*60)
print("PLAID CONNECTION DIAGNOSTIC")
print("="*60 + "\n")

# 1. Check environment variables
print("1️⃣  Checking Environment Variables...")
print("-" * 60)

plaid_client_id = os.getenv('PLAID_CLIENT_ID', '')
plaid_secret = os.getenv('PLAID_SECRET', '')
plaid_env = os.getenv('PLAID_ENV', 'sandbox')

if plaid_client_id:
    print(f"✅ PLAID_CLIENT_ID: {plaid_client_id[:10]}... (length: {len(plaid_client_id)})")
else:
    print("❌ PLAID_CLIENT_ID: NOT FOUND")

if plaid_secret:
    print(f"✅ PLAID_SECRET: {plaid_secret[:10]}... (length: {len(plaid_secret)})")
else:
    print("❌ PLAID_SECRET: NOT FOUND")

print(f"🌍 PLAID_ENV: {plaid_env}")

# 2. Test Plaid SDK Import
print("\n2️⃣  Testing Plaid SDK...")
print("-" * 60)

try:
    from plaid.api import plaid_api
    from plaid.model.link_token_create_request import LinkTokenCreateRequest
    from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
    from plaid.model.products import Products
    from plaid.model.country_code import CountryCode
    from plaid.configuration import Configuration
    from plaid.api_client import ApiClient
    print("✅ Plaid SDK imported successfully")
except Exception as e:
    print(f"❌ Failed to import Plaid SDK: {e}")
    print("   Run: pip install plaid-python")
    exit(1)

# 3. Test Plaid API Connection
print("\n3️⃣  Testing Plaid API Connection...")
print("-" * 60)

if not plaid_client_id or not plaid_secret:
    print("❌ Cannot test - credentials missing")
    print("\n📝 TO FIX:")
    print("   1. Go to: https://dashboard.plaid.com/team/keys")
    print("   2. Copy your client_id and secret (sandbox)")
    print("   3. Add to .env file:")
    print("      PLAID_CLIENT_ID=your_client_id")
    print("      PLAID_SECRET=your_secret")
    print("      PLAID_ENV=sandbox")
    exit(1)

try:
    # Configure Plaid
    env_hosts = {
        'sandbox': 'https://sandbox.plaid.com',
        'development': 'https://development.plaid.com',
        'production': 'https://production.plaid.com'
    }
    
    configuration = Configuration(
        host=env_hosts.get(plaid_env, 'https://sandbox.plaid.com'),
        api_key={
            'clientId': plaid_client_id,
            'secret': plaid_secret,
        }
    )
    
    api_client = ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)
    
    print(f"✅ Plaid API client configured for {plaid_env}")
    
    # Try to create a link token
    print("\n4️⃣  Creating Test Link Token...")
    print("-" * 60)
    
    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id="test_user_123"),
        client_name="Bentley Budget Bot Test",
        products=[Products("transactions")],
        country_codes=[CountryCode("US")],
        language='en',
    )
    
    response = client.link_token_create(request)
    link_token = response['link_token']
    
    print(f"✅ SUCCESS! Link token created:")
    print(f"   Token: {link_token[:30]}...")
    print(f"   Expires: {response.get('expiration', 'N/A')}")
    
    print("\n" + "="*60)
    print("✅ PLAID CONNECTION WORKING!")
    print("="*60)
    print("\n💡 Your Plaid integration is configured correctly.")
    print("   If the button still spins, check browser console (F12)")
    print("   for JavaScript errors.\n")
    
except Exception as e:
    error_str = str(e)
    print(f"\n❌ PLAID API ERROR:")
    print("-" * 60)
    print(error_str)
    
    print("\n🔍 COMMON ISSUES:")
    if 'INVALID_CLIENT_ID' in error_str:
        print("   • Client ID is invalid")
        print("   • Check: https://dashboard.plaid.com/team/keys")
    elif 'INVALID_SECRET' in error_str:
        print("   • Secret is invalid or doesn't match Client ID")
        print("   • Make sure you're using the correct secret for your client_id")
    elif 'UNAUTHORIZED' in error_str:
        print("   • Credentials are unauthorized")
        print("   • Regenerate keys at: https://dashboard.plaid.com/team/keys")
    else:
        print("   • Check your internet connection")
        print("   • Verify credentials at: https://dashboard.plaid.com/team/keys")
    
    print("\n")
