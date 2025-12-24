"""
Quick test to verify Plaid credentials are loading correctly
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Testing Plaid Credential Loading...\n")

# Get credentials
client_id = os.getenv('PLAID_CLIENT_ID', '').strip()
secret = os.getenv('PLAID_SECRET', '').strip()
env = os.getenv('PLAID_ENV', 'sandbox').strip()

print(f"PLAID_CLIENT_ID: {'✅ Found' if client_id and client_id != 'your_plaid_client_id_here' else '❌ Missing or placeholder'}")
if client_id:
    print(f"  Value: {client_id[:10]}... (length: {len(client_id)})")

print(f"\nPLAID_SECRET: {'✅ Found' if secret and secret != 'your_plaid_secret_here' else '❌ Missing or placeholder'}")
if secret:
    print(f"  Value: {secret[:10]}... (length: {len(secret)})")

print(f"\nPLAID_ENV: {env}")

# Test PlaidLinkManager initialization
print("\n" + "="*50)
print("Testing PlaidLinkManager initialization...")
print("="*50)

try:
    from frontend.utils.plaid_link import PlaidLinkManager
    
    manager = PlaidLinkManager()
    print("✅ SUCCESS: PlaidLinkManager initialized!")
    print(f"   Client ID: {manager.client_id[:10]}...")
    print(f"   Environment: {manager.env}")
    print(f"   Host: {manager._get_plaid_host()}")
    
except ValueError as e:
    print(f"❌ FAILED: {e}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
print("Test complete!")
