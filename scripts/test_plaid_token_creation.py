"""
Test Plaid Link Token Creation
===============================
Tests if link_token can be created successfully.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env.local
load_dotenv('.env.local', override=True)

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("🔍 TESTING PLAID LINK TOKEN CREATION")
print("=" * 70)

# Check credentials
client_id = os.getenv('PLAID_CLIENT_ID')
secret = os.getenv('PLAID_SECRET')
env = os.getenv('PLAID_ENV', 'sandbox')

print(f"\n📋 Configuration:")
print(f"   Client ID: {client_id[:15]}...")
print(f"   Secret: {secret[:15]}...")
print(f"   Environment: {env}")

print(f"\n🔗 Creating link token...")

try:
    from plaid.api import plaid_api
    from plaid.model.link_token_create_request import LinkTokenCreateRequest
    from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
    from plaid.model.products import Products
    from plaid.model.country_code import CountryCode
    from plaid.configuration import Configuration
    from plaid.api_client import ApiClient
    
    # Configure client
    env_hosts = {
        'sandbox': 'https://sandbox.plaid.com',
        'development': 'https://development.plaid.com',
        'production': 'https://production.plaid.com'
    }
    
    configuration = Configuration(
        host=env_hosts.get(env, 'https://sandbox.plaid.com'),
        api_key={
            'clientId': client_id,
            'secret': secret,
        }
    )
    
    api_client = ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)
    
    # Create link token
    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id="test_user_001"),
        client_name="BBBot Test",
        products=[Products("transactions")],
        country_codes=[CountryCode("US")],
        language='en',
    )
    
    print(f"   Sending request to: {env_hosts.get(env)}...")
    response = client.link_token_create(request)
    
    link_token = response['link_token']
    expiration = response['expiration']
    
    print(f"\n✅ SUCCESS!")
    print(f"   Link Token: {link_token[:30]}...")
    print(f"   Expiration: {expiration}")
    print(f"   Token Length: {len(link_token)}")
    
    # Validate token format
    if link_token.startswith('link-sandbox-'):
        print(f"   ✅ Token format: SANDBOX (correct for environment: {env})")
    elif link_token.startswith('link-development-'):
        print(f"   ⚠️  Token format: DEVELOPMENT (environment: {env})")
    elif link_token.startswith('link-production-'):
        print(f"   ⚠️  Token format: PRODUCTION (environment: {env})")
    else:
        print(f"   ❌ Token format: UNKNOWN")
    
    print(f"\n" + "=" * 70)
    print(f"✅ PLAID LINK TOKEN CREATION WORKS!")
    print(f"=" * 70)
    print(f"\nThe issue is NOT with token creation.")
    print(f"The problem is HOW the token is passed to the frontend.\n")
    print(f"Next steps:")
    print(f"1. Make sure Streamlit uses .env.local (not .env.development)")
    print(f"2. Test opening Plaid Link in NEW window (not iframe)")
    print(f"3. Check browser console for JavaScript errors")
    
except Exception as e:
    print(f"\n❌ FAILED TO CREATE LINK TOKEN")
    print(f"   Error: {e}")
    print(f"\n   Possible causes:")
    print(f"   1. Invalid credentials (check Plaid dashboard)")
    print(f"   2. Environment mismatch (sandbox vs production)")
    print(f"   3. Network issue (firewall/proxy)")
    
    import traceback
    print(f"\n📋 Full error:")
    traceback.print_exc()

print("=" * 70)
