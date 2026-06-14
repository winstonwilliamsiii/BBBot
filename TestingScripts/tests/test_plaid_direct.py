"""
Test Plaid Connection Directly
Bypasses Streamlit to test raw API connection
"""

import os
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

# Load environment
load_dotenv()

print("=" * 70)
print("🧪 PLAID API DIRECT TEST")
print("=" * 70)

# Get credentials
client_id = os.getenv('PLAID_CLIENT_ID', '').strip()
secret = os.getenv('PLAID_SECRET', '').strip()
env = os.getenv('PLAID_ENV', 'sandbox').strip()

print(f"\n📋 Configuration:")
print(f"   Client ID: {client_id[:8]}... (length: {len(client_id)})")
print(f"   Secret: {secret[:8]}... (length: {len(secret)})")
print(f"   Environment: {env}")

# Validate
if not client_id or len(client_id) != 24:
    print(f"\n❌ ERROR: Invalid client_id")
    print(f"   Expected: 24 characters")
    print(f"   Got: {len(client_id)} characters")
    print(f"   Value: '{client_id}'")
    exit(1)

if not secret:
    print(f"\n❌ ERROR: Missing secret")
    exit(1)

# Get host
env_hosts = {
    'sandbox': 'https://sandbox.plaid.com',
    'development': 'https://development.plaid.com',
    'production': 'https://production.plaid.com'
}
host = env_hosts.get(env, 'https://sandbox.plaid.com')

print(f"   API Host: {host}")

# Test 1: Configuration
print("\n" + "-" * 70)
print("TEST 1: Create Plaid Configuration")
print("-" * 70)

try:
    configuration = Configuration(
        host=host,
        api_key={
            'clientId': client_id,
            'secret': secret,
        }
    )
    print("✅ Configuration created successfully")
except Exception as e:
    print(f"❌ Configuration failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 2: API Client
print("\n" + "-" * 70)
print("TEST 2: Create API Client")
print("-" * 70)

try:
    api_client = ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)
    print("✅ API client created successfully")
except Exception as e:
    print(f"❌ API client creation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 3: Create Link Token (the actual API call)
print("\n" + "-" * 70)
print("TEST 3: Create Link Token (Real API Call)")
print("-" * 70)

try:
    print("   Creating link token request...")
    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id="test_user_123"),
        client_name="Bentley Budget Bot Test",
        products=[Products("transactions")],
        country_codes=[CountryCode("US")],
        language='en',
    )
    
    print("   Sending request to Plaid API...")
    print(f"   Endpoint: {host}/link/token/create")
    print(f"   Client ID: {client_id[:8]}...")
    
    response = client.link_token_create(request)
    
    print("\n✅ SUCCESS! Link token created")
    print(f"   Link Token: {response['link_token'][:20]}...")
    print(f"   Expires: {response['expiration']}")
    
    print("\n" + "=" * 70)
    print("✅ PLAID CONNECTION WORKING PERFECTLY!")
    print("=" * 70)
    print("\nYour Plaid credentials are valid and the API is responding.")
    print("If you're still seeing errors in your app, the issue is likely:")
    print("  1. Streamlit Cloud secrets not matching .env file")
    print("  2. Environment not reloaded after changing .env")
    print("  3. Different code path being used in production")
    
except Exception as e:
    print(f"\n❌ FAILED to create link token")
    print(f"\nError: {e}")
    
    # Parse the error
    error_str = str(e)
    
    if "client_id must be a properly formatted" in error_str:
        print("\n🔍 DIAGNOSIS:")
        print("   The API received an invalid/empty client_id")
        print("\n   Possible causes:")
        print("   1. Using production secret with sandbox client_id (or vice versa)")
        print("   2. Credentials from different Plaid projects")
        print("   3. API key revoked/expired")
        print("\n   ✅ FIX:")
        print("   1. Go to https://dashboard.plaid.com/")
        print("   2. Select your project")
        print("   3. Go to Team Settings → Keys")
        print("   4. Copy BOTH client_id AND secret from the SAME section")
        print(f"      (Currently using: {env})")
        print("   5. Run: python fix_credentials.py")
    
    elif "invalid_api_keys" in error_str:
        print("\n🔍 DIAGNOSIS:")
        print("   Your API keys are invalid or revoked")
        print("\n   ✅ FIX:")
        print("   1. Go to https://dashboard.plaid.com/")
        print("   2. Generate new API keys")
        print("   3. Run: python fix_credentials.py")
    
    else:
        print("\n🔍 Full error details:")
        import traceback
        traceback.print_exc()
    
    exit(1)
