"""
Diagnostic script to test Plaid Link initialization
"""
import os
import sys
from dotenv import load_dotenv

# Add project root to path (now in tests/ directory, need to go up one level)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Load environment
load_dotenv()

print("=" * 60)
print("PLAID LINK INITIALIZATION DIAGNOSTIC")
print("=" * 60)

# Test 1: Check credentials
print("\n[1] Checking Plaid Credentials...")
client_id = os.getenv('PLAID_CLIENT_ID', '')
secret = os.getenv('PLAID_SECRET', '')
env = os.getenv('PLAID_ENV', 'sandbox')

print(f"   PLAID_CLIENT_ID: {client_id[:20]}... (length: {len(client_id)})")
print(f"   PLAID_SECRET: {secret[:20]}... (length: {len(secret)})")
print(f"   PLAID_ENV: {env}")

if not client_id or client_id == 'your_plaid_client_id_here':
    print("   ❌ PLAID_CLIENT_ID not configured!")
    sys.exit(1)
if not secret or secret == 'your_plaid_secret_here':
    print("   ❌ PLAID_SECRET not configured!")
    sys.exit(1)
print("   ✅ Credentials found")

# Test 2: Import Plaid SDK
print("\n[2] Importing Plaid SDK...")
try:
    from plaid.api import plaid_api
    from plaid.model.link_token_create_request import LinkTokenCreateRequest
    from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
    from plaid.model.products import Products
    from plaid.model.country_code import CountryCode
    from plaid.configuration import Configuration
    from plaid.api_client import ApiClient
    print("   ✅ Plaid SDK imported successfully")
except ImportError as e:
    print(f"   ❌ Failed to import Plaid SDK: {e}")
    print("   Run: pip install plaid-python")
    sys.exit(1)

# Test 3: Initialize PlaidLinkManager
print("\n[3] Initializing PlaidLinkManager...")
try:
    from utils.plaid_link import PlaidLinkManager
    plaid_manager = PlaidLinkManager()
    print("   ✅ PlaidLinkManager initialized")
except Exception as e:
    print(f"   ❌ Failed to initialize: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Create link token
print("\n[4] Creating Link Token...")
try:
    test_user_id = "test_user_" + str(os.getpid())
    link_data = plaid_manager.create_link_token(test_user_id)
    
    if not link_data:
        print("   ❌ create_link_token returned None or empty")
        sys.exit(1)
    
    if 'link_token' not in link_data:
        print(f"   ❌ link_token not in response: {link_data}")
        sys.exit(1)
    
    link_token = link_data['link_token']
    print(f"   ✅ Link token created: {link_token[:30]}...")
    print(f"   Token length: {len(link_token)}")
    print(f"   Expiration: {link_data.get('expiration', 'N/A')}")
    
except Exception as e:
    print(f"   ❌ Failed to create link token: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Validate link token format
print("\n[5] Validating Link Token Format...")
if link_token.startswith('link-sandbox-'):
    print("   ✅ Token has correct sandbox prefix")
elif link_token.startswith('link-development-'):
    print("   ✅ Token has correct development prefix")
elif link_token.startswith('link-production-'):
    print("   ✅ Token has correct production prefix")
else:
    print(f"   ⚠️ Unexpected token prefix: {link_token[:20]}")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - Plaid Link should initialize correctly")
print("=" * 60)

# Test 6: Generate sample HTML
print("\n[6] Generating Sample HTML with Link Token...")
sample_html = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
</head>
<body>
    <button id="link-button" onclick="openPlaid()">Connect Bank</button>
    <div id="status"></div>
    
    <script>
        console.log('Initializing Plaid with token:', '{link_token}'.substring(0, 30) + '...');
        
        var linkHandler = Plaid.create({{
            token: '{link_token}',
            onSuccess: function(public_token, metadata) {{
                console.log('SUCCESS!', public_token);
                document.getElementById('status').textContent = 'Connected to ' + metadata.institution.name;
            }},
            onExit: function(err, metadata) {{
                if (err) console.error('ERROR:', err);
            }},
            onLoad: function() {{
                console.log('Plaid Link loaded!');
                document.getElementById('link-button').disabled = false;
            }}
        }});
        
        function openPlaid() {{
            linkHandler.open();
        }}
    </script>
</body>
</html>
"""

output_file = "test_plaid_link.html"
with open(output_file, 'w') as f:
    f.write(sample_html)

print(f"   Sample HTML saved to: {output_file}")
print(f"   Open this file in a browser to test Plaid Link")
print("\n" + "=" * 60)
