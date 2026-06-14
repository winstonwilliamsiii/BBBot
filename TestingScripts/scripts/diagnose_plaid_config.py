"""
Diagnose Plaid Configuration Issues
====================================
Checks for environment mismatches, null tokens, and credential problems.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

print("=" * 70)
print("🔍 PLAID CONFIGURATION DIAGNOSTIC")
print("=" * 70)

# Load all env files
project_root = Path(__file__).parent
env_files = [
    '.env',
    '.env.local',
    '.env.development',
    '.env.production'
]

print("\n📁 Checking environment files:")
for env_file in env_files:
    file_path = project_root / env_file
    if file_path.exists():
        print(f"   ✅ {env_file} exists")
        load_dotenv(file_path, override=True)
    else:
        print(f"   ❌ {env_file} NOT FOUND")

print("\n" + "=" * 70)
print("🔑 PLAID CREDENTIALS (from environment)")
print("=" * 70)

# Check all possible variable names
client_id_vars = ['PLAID_CLIENT_ID']
secret_vars = ['PLAID_SECRET', 'PLAID_SECRET_KEY']
env_vars = ['PLAID_ENV', 'PLAID_ENVIRONMENT']

print("\n1️⃣  Client ID:")
found_client_id = None
for var in client_id_vars:
    value = os.getenv(var)
    if value:
        print(f"   {var}: {value[:10]}... (length: {len(value)})")
        found_client_id = value
        
        # Check if it's a placeholder
        if 'placeholder' in value.lower() or 'your_' in value.lower() or 'dev_' in value.lower():
            print(f"   ⚠️  WARNING: Looks like a placeholder value!")
    else:
        print(f"   {var}: NOT SET")

print("\n2️⃣  Secret:")
found_secret = None
for var in secret_vars:
    value = os.getenv(var)
    if value:
        print(f"   {var}: {value[:10]}... (length: {len(value)})")
        found_secret = value
        
        if 'placeholder' in value.lower() or 'your_' in value.lower() or 'dev_' in value.lower():
            print(f"   ⚠️  WARNING: Looks like a placeholder value!")
    else:
        print(f"   {var}: NOT SET")

print("\n3️⃣  Environment:")
found_env = None
for var in env_vars:
    value = os.getenv(var)
    if value:
        print(f"   {var}: {value}")
        found_env = value

print("\n" + "=" * 70)
print("✅ VALIDATION RESULTS")
print("=" * 70)

issues = []

if not found_client_id:
    issues.append("❌ PLAID_CLIENT_ID is not set")
elif found_client_id.startswith('dev_') or found_client_id.startswith('your_'):
    issues.append("❌ PLAID_CLIENT_ID contains placeholder value")
else:
    print("✅ Client ID looks valid")

if not found_secret:
    issues.append("❌ PLAID_SECRET is not set")
elif found_secret.startswith('dev_') or found_secret.startswith('your_'):
    issues.append("❌ PLAID_SECRET contains placeholder value")
else:
    print("✅ Secret looks valid")

if not found_env:
    issues.append("⚠️  PLAID_ENV not set (will default to 'sandbox')")
    found_env = 'sandbox'
else:
    print(f"✅ Environment: {found_env}")

# Check environment mismatch
if found_client_id and found_env:
    print("\n" + "=" * 70)
    print("🔍 ENVIRONMENT MISMATCH CHECK")
    print("=" * 70)
    
    # Real client IDs follow these patterns
    if found_env == 'sandbox':
        if not (found_client_id.startswith('68') or found_client_id.startswith('67')):
            issues.append(f"⚠️  Client ID pattern doesn't match sandbox environment")
            print(f"   Your client ID: {found_client_id[:10]}...")
            print(f"   Environment: {found_env}")
            print(f"   ⚠️  Make sure these match!")
    elif found_env == 'production':
        print(f"   ⚠️  WARNING: Using PRODUCTION environment!")
        print(f"   This will connect to REAL bank accounts!")
        print(f"   For testing, use 'sandbox' environment.")

# Print all issues
if issues:
    print("\n" + "=" * 70)
    print("🚨 ISSUES FOUND:")
    print("=" * 70)
    for issue in issues:
        print(f"   {issue}")
else:
    print("\n✅ No configuration issues detected!")

print("\n" + "=" * 70)
print("📋 RECOMMENDATIONS")
print("=" * 70)

if issues:
    print("""
1. Update .env.local with your REAL Plaid credentials:
   
   PLAID_CLIENT_ID=68b8718ec2f428002456a84c
   PLAID_SECRET=1849c4090173dfbce2bda5453e7048
   PLAID_ENV=sandbox
   
2. Get credentials from: https://dashboard.plaid.com/team/keys

3. Make sure you're using SANDBOX credentials for testing

4. After updating, restart Streamlit:
   Get-Process -Name python* | Where-Object {$_.CommandLine -like "*streamlit*"} | Stop-Process -Force
   streamlit run streamlit_app.py --server.port=8501

5. Test link token creation in the app
""")
else:
    print("""
✅ Configuration looks good!

If you're still seeing "No link_token provided":
1. Check browser console (F12) for JavaScript errors
2. Verify domain whitelist in Plaid dashboard
3. Make sure popup blocker is disabled
4. Try opening the page in a new tab (not iframe)
""")

print("=" * 70)
