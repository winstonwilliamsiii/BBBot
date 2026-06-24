#!/usr/bin/env python3
"""
Plaid Credentials Verification Script
Tests the updated Plaid credentials to ensure they're valid
"""

import os
import sys
from dotenv import load_dotenv

# Force reload environment variables
load_dotenv(override=True)

print("=" * 70)
print("🔍 PLAID CREDENTIALS VERIFICATION")
print("=" * 70)

# 1. Check environment variables are loaded
print("\n1️⃣  Checking Environment Variables...")
print("-" * 70)

client_id = os.getenv('PLAID_CLIENT_ID', '').strip()
secret = os.getenv('PLAID_SECRET', '').strip()
env = os.getenv('PLAID_ENV', 'sandbox').strip()

print(f"✓ PLAID_CLIENT_ID: {client_id[:8]}...{client_id[-8:] if len(client_id) > 16 else ''}")
print(f"✓ PLAID_SECRET: {secret[:8]}...{secret[-8:] if len(secret) > 16 else ''}")
print(f"✓ PLAID_ENV: {env}")

if not client_id or not secret:
    print("\n❌ ERROR: Plaid credentials not found in environment!")
    sys.exit(1)

if len(client_id) < 20:
    print(f"⚠️  WARNING: Client ID seems short ({len(client_id)} chars)")

if len(secret) < 20:
    print(f"⚠️  WARNING: Secret seems short ({len(secret)} chars)")

# 2. Test Plaid API Configuration
print("\n2️⃣  Testing Plaid API Configuration...")
print("-" * 70)

try:
    from plaid.configuration import Configuration
    from plaid.api_client import ApiClient
    from plaid.api import plaid_api
    
    print("✓ Plaid SDK imports successful")
    
    env_hosts = {
        'sandbox': 'https://sandbox.plaid.com',
        'development': 'https://development.plaid.com',
        'production': 'https://production.plaid.com'
    }
    
    host = env_hosts.get(env, 'https://sandbox.plaid.com')
    print(f"✓ Using host: {host}")
    
    configuration = Configuration(
        host=host,
        api_key={
            'clientId': client_id,
            'secret': secret,
        }
    )
    
    api_client = ApiClient(configuration)
    plaid_client = plaid_api.PlaidApi(api_client)
    
    print("✓ Plaid API client configured successfully")
    
except Exception as e:
    print(f"❌ Failed to configure Plaid API: {e}")
    sys.exit(1)

# 3. Test Link Token Creation (actual API call)
print("\n3️⃣  Testing Link Token Creation (API Call)...")
print("-" * 70)

try:
    from plaid.model.link_token_create_request import LinkTokenCreateRequest
    from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
    from plaid.model.products import Products
    from plaid.model.country_code import CountryCode
    
    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id="test_user_plaid_verify"),
        client_name="Bentley Budget Bot - Verify",
        products=[Products("transactions")],
        country_codes=[CountryCode("US")],
        language='en',
    )
    
    print("🔄 Sending request to Plaid API...")
    response = plaid_client.link_token_create(request)
    
    link_token = response['link_token']
    expiration = response['expiration']
    
    print(f"✅ SUCCESS! Link token created:")
    print(f"   Token: {link_token[:30]}...")
    print(f"   Expires: {expiration}")
    
except Exception as e:
    error_msg = str(e)
    print(f"❌ FAILED to create link token: {error_msg}")
    
    # Try to extract error details
    if "INVALID_API_KEYS" in error_msg:
        print("\n⚠️  ERROR TYPE: Invalid Plaid Credentials")
        print("   The client_id or secret provided is incorrect.")
        print("   Please verify your Plaid credentials in the dashboard:")
        print("   👉 https://dashboard.plaid.com/")
    elif "INVALID_INPUT" in error_msg:
        print("\n⚠️  ERROR TYPE: Invalid Request Input")
        print("   Check the request parameters are valid.")
    
    sys.exit(1)

# 4. Summary
print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED!")
print("=" * 70)
print("\nYour Plaid credentials are valid and working correctly.")
print("You can now use Plaid Link in your application.")
print("\nNext steps:")
print("1. Restart your Streamlit app")
print("2. Navigate to the Plaid Link section")
print("3. Click 'Connect Bank Account'")
print("4. Complete the Plaid Link flow")
print("=" * 70)
