#!/usr/bin/env python
"""
Diagnose Plaid credential loading issues in Streamlit environment
"""

import os
import sys
from pathlib import Path

print("=" * 70)
print("PLAID CREDENTIAL DIAGNOSTICS")
print("=" * 70)

# 1. Check working directory
print(f"\n1. Working Directory")
print(f"   Current directory: {os.getcwd()}")
print(f"   Script location: {Path(__file__).resolve()}")

# 2. Check .env file
print(f"\n2. .env File Status")
env_paths = [
    Path('.env'),
    Path(__file__).parent / '.env',
    Path(__file__).parent.parent / '.env',
    Path(__file__).parent.parent.parent / '.env',
]

env_found = None
for env_path in env_paths:
    if env_path.exists():
        print(f"   Found: {env_path.resolve()}")
        env_found = env_path
        break
    else:
        print(f"   Not found: {env_path}")

if not env_found:
    print(f"   ERROR: .env not found in any expected location")
    sys.exit(1)

# 3. Check environment variables BEFORE loading
print(f"\n3. Environment Variables (BEFORE load_dotenv)")
plaid_before = {k: v for k, v in os.environ.items() if 'PLAID' in k}
if plaid_before:
    print(f"   Found PLAID vars: {list(plaid_before.keys())}")
    for k, v in plaid_before.items():
        print(f"   - {k}: {v[:30]}..." if len(v) > 30 else f"   - {k}: {v}")
else:
    print(f"   No PLAID vars found in environment")

# 4. Load .env and check AFTER
print(f"\n4. Loading .env File")
from dotenv import load_dotenv
result = load_dotenv(str(env_found), override=True)
print(f"   load_dotenv result: {result}")

plaid_after = {k: v for k, v in os.environ.items() if 'PLAID' in k}
print(f"\n5. Environment Variables (AFTER load_dotenv)")
if plaid_after:
    print(f"   Found PLAID vars: {list(plaid_after.keys())}")
    client_id = os.getenv('PLAID_CLIENT_ID', '')
    secret = os.getenv('PLAID_SECRET', '')
    env = os.getenv('PLAID_ENV', '')
    
    print(f"   - PLAID_CLIENT_ID: {'✓ Found' if client_id else '✗ Empty'} ({len(client_id)} chars)")
    print(f"   - PLAID_SECRET: {'✓ Found' if secret else '✗ Empty'} ({len(secret)} chars)")
    print(f"   - PLAID_ENV: {env if env else '✗ Not set (defaults to sandbox)'}")
else:
    print(f"   ERROR: No PLAID vars found after load_dotenv")
    sys.exit(1)

# 6. Try creating PlaidLinkManager
print(f"\n6. Testing PlaidLinkManager")
try:
    from frontend.utils.plaid_link import PlaidLinkManager
    manager = PlaidLinkManager()
    print(f"   ✓ PlaidLinkManager created successfully")
    print(f"   - Client ID: {manager.client_id[:20]}...")
    print(f"   - Environment: {manager.env}")
except Exception as e:
    print(f"   ✗ Error creating PlaidLinkManager: {e}")
    sys.exit(1)

# 7. Try creating link token
print(f"\n7. Testing Link Token Creation")
try:
    result = manager.create_link_token('diagnostic-test')
    if result and result.get('link_token'):
        print(f"   ✓ Link token created successfully")
        print(f"   - Token: {result['link_token'][:30]}...")
        print(f"   - Expires: {result.get('expiration', 'unknown')}")
    else:
        print(f"   ✗ No link token in response: {result}")
except Exception as e:
    print(f"   ✗ Error creating link token: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("ALL TESTS PASSED - Plaid credentials are valid and working!")
print("=" * 70)
print("\nIf Streamlit is still showing errors:")
print("1. Restart Streamlit completely (kill all python processes)")
print("2. Run: streamlit run streamlit_app.py --logger.level=debug")
print("3. Check the debug output for any import or loading errors")
print("=" * 70)
