"""
Simple Plaid Credential Test
Tests if Plaid credentials can be loaded from .env file
"""

import os
from pathlib import Path
from dotenv import load_dotenv

print("=" * 70)
print("PLAID CREDENTIAL TEST")
print("=" * 70)
print()

# Test 1: Check if .env file exists
env_file = Path.cwd() / '.env'
print(f"1. .env file location: {env_file}")
print(f"   Exists: {env_file.exists()}")
print()

# Test 2: Load environment with override
print("2. Loading .env with override=True...")
result = load_dotenv(env_file, override=True)
print(f"   Load result: {result}")
print()

# Test 3: Read Plaid credentials from os.environ
print("3. Reading from os.environ:")
client_id = os.environ.get('PLAID_CLIENT_ID', 'NOT FOUND')
secret = os.environ.get('PLAID_SECRET', 'NOT FOUND')
env = os.environ.get('PLAID_ENV', 'NOT FOUND')

print(f"   PLAID_CLIENT_ID: {client_id}")
print(f"   PLAID_SECRET: {secret}")
print(f"   PLAID_ENV: {env}")
print()

# Test 4: Read using os.getenv (should be same)
print("4. Reading using os.getenv():")
client_id_2 = os.getenv('PLAID_CLIENT_ID', 'NOT FOUND')
secret_2 = os.getenv('PLAID_SECRET', 'NOT FOUND')
env_2 = os.getenv('PLAID_ENV', 'NOT FOUND')

print(f"   PLAID_CLIENT_ID: {client_id_2}")
print(f"   PLAID_SECRET: {secret_2}")
print(f"   PLAID_ENV: {env_2}")
print()

# Test 5: Check if they match what's in file
print("5. Reading directly from .env file:")
if env_file.exists():
    with open(env_file, 'r') as f:
        plaid_lines = [line.strip() for line in f if 'PLAID' in line and not line.strip().startswith('#')]
    
    print("   Lines containing 'PLAID':")
    for line in plaid_lines:
        # Mask the actual values for security
        if '=' in line:
            key, value = line.split('=', 1)
            masked_value = value[:10] + '...' if len(value) > 10 else value
            print(f"   {key}={masked_value}")
print()

# Test 6: Try to instantiate PlaidLinkManager
print("6. Testing PlaidLinkManager instantiation:")
try:
    from frontend.utils.plaid_link import PlaidLinkManager
    manager = PlaidLinkManager()
    print("   ✅ PlaidLinkManager created successfully!")
    print(f"   Client ID configured: {manager.client_id[:10]}...")
    print(f"   Environment: {manager.env}")
except ValueError as e:
    print(f"   ❌ ValueError: {e}")
except Exception as e:
    print(f"   ❌ Error: {e}")
print()

# Summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)

if client_id != 'NOT FOUND' and client_id != '':
    print("✅ Plaid credentials ARE loaded in environment")
    print()
    print("If Streamlit still shows error, the issue is:")
    print("  1. Streamlit caching the old error message in browser")
    print("  2. PlaidLinkManager being instantiated before load_dotenv()")
    print("  3. Streamlit session state caching the error")
    print()
    print("Solution: Hard refresh browser (Ctrl+Shift+R) and restart Streamlit")
else:
    print("❌ Plaid credentials NOT found")
    print()
    print("Check:")
    print("  1. .env file exists in project root")
    print("  2. PLAID_CLIENT_ID=... line is not commented out")
    print("  3. No typos in variable names")

print()
