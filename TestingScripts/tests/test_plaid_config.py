"""
Test Plaid Configuration
Verifies that Plaid credentials are properly loaded from .env
"""
import os
from dotenv import load_dotenv

# Reload environment with force=True
load_dotenv(override=True)

print("\n" + "="*60)
print("PLAID CONFIGURATION TEST")
print("="*60)

# Check Plaid environment variables
plaid_vars = {
    'PLAID_CLIENT_ID': os.getenv('PLAID_CLIENT_ID'),
    'PLAID_SECRET': os.getenv('PLAID_SECRET'),
    'PLAID_ENV': os.getenv('PLAID_ENV')
}

print("\n[Checking Plaid Environment Variables]")
for var, value in plaid_vars.items():
    if value:
        masked = value[:8] + "..." if len(value) > 8 else "****"
        print(f"  ✓ {var}: {masked}")
    else:
        print(f"  ✗ {var}: NOT SET")

# Check if all required vars are set
all_set = all(plaid_vars.values())

print("\n" + "="*60)
if all_set:
    print("✓ ALL PLAID CREDENTIALS CONFIGURED!")
    print("\nYou can now use Plaid Link in the app.")
    print("Using environment:", plaid_vars['PLAID_ENV'])
else:
    print("✗ MISSING PLAID CREDENTIALS")
    print("\nTo fix:")
    print("1. Open .env file")
    print("2. Ensure these lines exist:")
    print("   PLAID_CLIENT_ID=your_client_id")
    print("   PLAID_SECRET=your_secret")
    print("   PLAID_ENV=sandbox")
print("="*60)
