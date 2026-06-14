"""Test Plaid API initialization"""
from dotenv import load_dotenv
import os

load_dotenv(override=True)

client_id = os.getenv('PLAID_CLIENT_ID', '').strip()
secret = os.getenv('PLAID_SECRET', '').strip()
env = os.getenv('PLAID_ENV', 'sandbox').strip()

print("Plaid Configuration:")
print(f"  Client ID: {client_id[:15]}... (len: {len(client_id)})")
print(f"  Secret: {secret[:15]}... (len: {len(secret)})")
print(f"  Environment: {env}")
print()

# Test with plaid SDK
try:
    from plaid.configuration import Configuration
    from plaid.api_client import ApiClient
    from plaid.api import plaid_api
    
    print("Creating Plaid configuration...")
    
    # Determine host
    env_hosts = {
        'sandbox': 'https://sandbox.plaid.com',
        'development': 'https://development.plaid.com',
        'production': 'https://production.plaid.com'
    }
    host = env_hosts.get(env, 'https://sandbox.plaid.com')
    
    print(f"  Host: {host}")
    print(f"  Client ID type: {type(client_id)}")
    print(f"  Secret type: {type(secret)}")
    
    configuration = Configuration(
        host=host,
        api_key={
            'clientId': client_id,
            'secret': secret,
        }
    )
    
    print("✅ Configuration created successfully")
    
    api_client = ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)
    
    print("✅ Plaid client initialized")
    
    # Try to create a link token
    from plaid.model.link_token_create_request import LinkTokenCreateRequest
    from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
    from plaid.model.products import Products
    from plaid.model.country_code import CountryCode
    
    print("\nTesting link token creation...")
    
    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id="test_user"),
        client_name="Bentley Budget Bot Test",
        products=[Products("transactions")],
        country_codes=[CountryCode("US")],
        language='en',
    )
    
    response = client.link_token_create(request)
    print("✅ Link token created successfully!")
    print(f"   Token: {response['link_token'][:20]}...")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
