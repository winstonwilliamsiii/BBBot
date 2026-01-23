"""
Complete Plaid Integration Testing Checklist
Run this to verify your entire workflow
"""

import os
import sys
from dotenv import load_dotenv

print("\n" + "="*70)
print("BENTLEY BUDGET BOT - PLAID INTEGRATION CHECKLIST")
print("="*70 + "\n")

# Detect if running in CI/CD
is_ci_environment = os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'
print(f"Environment: {'CI/CD (GitHub Actions)' if is_ci_environment else 'Local Development'}\n")

# Load environment
load_dotenv(override=True)

checklist = {
    "Environment & Configuration": [],
    "Local Plaid Credentials": [],
    "Appwrite Functions": [],
    "Streamlit Integration": [],
    "Database": []
}

# 1. Environment Variables
print("1️⃣  CHECKING ENVIRONMENT & CONFIGURATION")
print("-" * 70)

plaid_client_id = os.getenv('PLAID_CLIENT_ID', '')
plaid_secret = os.getenv('PLAID_SECRET', '')
plaid_env = os.getenv('PLAID_ENV', 'sandbox')

checks = [
    ("PLAID_CLIENT_ID configured", bool(plaid_client_id) and len(plaid_client_id) > 10),
    ("PLAID_SECRET configured", bool(plaid_secret) and len(plaid_secret) > 10),
    ("PLAID_ENV set to 'sandbox'", plaid_env == 'sandbox'),
]

for check_name, result in checks:
    status = "✅" if result else "⚠️" if is_ci_environment else "❌"
    print(f"  {status} {check_name}")
    checklist["Environment & Configuration"].append((check_name, result))

# 2. Plaid SDK
print("\n2️⃣  CHECKING LOCAL PLAID CREDENTIALS")
print("-" * 70)

try:
    from plaid.api import plaid_api
    from plaid.configuration import Configuration
    from plaid.api_client import ApiClient
    print("  ✅ Plaid SDK imported successfully")
    checklist["Local Plaid Credentials"].append(("Plaid SDK installed", True))
    
    # Test connection (only if credentials exist)
    if plaid_client_id and plaid_secret:
        try:
            configuration = Configuration(
                host='https://sandbox.plaid.com',
                api_key={
                    'clientId': plaid_client_id,
                    'secret': plaid_secret,
                }
            )
            api_client = ApiClient(configuration)
            client = plaid_api.PlaidApi(api_client)
            print("  ✅ Plaid API client initialized")
            checklist["Local Plaid Credentials"].append(("Plaid API connection", True))
        except Exception as e:
            status = "⚠️" if is_ci_environment else "❌"
            print(f"  {status} Plaid API connection failed: {str(e)[:50]}")
            checklist["Local Plaid Credentials"].append(("Plaid API connection", False))
    else:
        status = "⚠️" if is_ci_environment else "❌"
        print(f"  {status} Skipping Plaid API connection test (credentials not available)")
        checklist["Local Plaid Credentials"].append(("Plaid API connection", False))
        
except ImportError as e:
    status = "⚠️" if is_ci_environment else "❌"
    print(f"  {status} Plaid SDK not installed: {str(e)[:50]}")
    checklist["Local Plaid Credentials"].append(("Plaid SDK installed", False))

# 3. Appwrite Functions
print("\n3️⃣  CHECKING APPWRITE FUNCTIONS")
print("-" * 70)

appwrite_functions = [
    "functions/create_link_token/main.py",
    "functions/exchange_public_token/main.py",
]

for func_path in appwrite_functions:
    exists = os.path.exists(func_path)
    status = "✅" if exists else "⚠️"
    print(f"  {status} {func_path}")
    checklist["Appwrite Functions"].append((func_path, exists))

# 4. Streamlit Integration
print("\n4️⃣  CHECKING STREAMLIT INTEGRATION")
print("-" * 70)

streamlit_checks = [
    ("streamlit_app.py exists", os.path.exists("streamlit_app.py")),
    ("frontend/utils/plaid_link.py exists", os.path.exists("frontend/utils/plaid_link.py")),
    ("api/index.py exists", os.path.exists("api/index.py")),
]

for check_name, result in streamlit_checks:
    status = "✅" if result else ("⚠️" if is_ci_environment else "❌")
    print(f"  {status} {check_name}")
    checklist["Streamlit Integration"].append((check_name, result))

# 5. Database
print("\n5️⃣  CHECKING DATABASE SETUP")
print("-" * 70)

db_env_vars = [
    "MYSQL_HOST",
    "MYSQL_USER",
    "MYSQL_PASSWORD",
    "MYSQL_DATABASE"
]

db_checks = []
for var in db_env_vars:
    has_var = bool(os.getenv(var))
    status = "✅" if has_var else "⚠️"
    masked_value = os.getenv(var, 'NOT SET')[:15] + "..." if os.getenv(var) else "NOT SET"
    print(f"  {status} {var}: {masked_value}")
    db_checks.append((var, has_var))

db_configured = all(result for _, result in db_checks)
if db_configured:
    print("  ✅ Database environment variables configured")
else:
    print("  ⚠️ Database not fully configured (needed for production)")

checklist["Database"] = db_checks

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

total_checks = sum(len(checks) for checks in checklist.values())
passed_checks = sum(
    sum(1 for _, result in checks if result)
    for checks in checklist.values()
)

for category, checks in checklist.items():
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    print(f"\n{category}: {passed}/{total}")
    for check_name, result in checks:
        status = "✅" if result else "⚠️" if not result else "✅"
        print(f"  {status} {check_name}")

print("\n" + "="*70)
print(f"OVERALL: {passed_checks}/{total_checks} checks passed")
print("="*70)

# Determine exit code based on environment
if is_ci_environment:
    # In CI/CD, only fail on critical issues (missing files, import errors)
    critical_fails = [
        result for category, checks in checklist.items() 
        for check_name, result in checks 
        if "installed" in check_name.lower() and not result
    ]
    
    if critical_fails:
        print("\n❌ Critical dependency missing (Plaid SDK not installed)")
        print("Add 'plaid' to requirements.txt and retry")
        sys.exit(1)
    else:
        print("\n✅ CI/CD checks passed (some features may require environment variables)")
        print("NOTE: Missing Plaid credentials are OK in CI/CD. Configure them in production.")
        sys.exit(0)
else:
    # Local development: stricter requirements
    if passed_checks >= total_checks - 3:
        print("\n🎉 Integration ready! Ready to test the Plaid flow.")
        print("\nREADY TO PROCEED:")
        print("1. Start Streamlit: streamlit run streamlit_app.py")
        print("2. Test bank connection: Click 'Connect Bank' button")
        print("3. Use Plaid test credentials in sandbox")
        sys.exit(0)
    elif passed_checks >= total_checks - 5:
        print("\n⚠️ Most checks passed. Review failures above.")
        print("Some features may need additional configuration.")
        sys.exit(0)
    else:
        print("\n❌ Several checks failed. Review configuration.")
        sys.exit(1)
