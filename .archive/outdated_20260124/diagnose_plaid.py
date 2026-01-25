#!/usr/bin/env python3
"""
Plaid Comprehensive Diagnostic Tool
Tests credentials, identifies issues, and provides solutions
"""

import os
import sys
import json
from dotenv import load_dotenv

# Force reload environment variables
load_dotenv(override=True)

def print_section(title, level=1):
    """Print formatted section header"""
    if level == 1:
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)
    else:
        print(f"\n{level}️⃣  {title}")
        print("-" * 70)

def check_env_variables():
    """Check environment variables are loaded correctly"""
    print_section("Environment Variables Check", 2)
    
    client_id = os.getenv('PLAID_CLIENT_ID', '').strip()
    secret = os.getenv('PLAID_SECRET', '').strip()
    env = os.getenv('PLAID_ENV', 'sandbox').strip()
    
    issues = []
    
    # Check client ID
    if not client_id:
        issues.append("❌ PLAID_CLIENT_ID is empty or missing")
    elif client_id == 'your_plaid_client_id_here' or client_id.startswith('your_'):
        issues.append("❌ PLAID_CLIENT_ID appears to be a placeholder (not real credentials)")
    elif len(client_id) < 20:
        issues.append(f"⚠️  PLAID_CLIENT_ID is very short ({len(client_id)} chars) - might be invalid")
    else:
        print(f"✓ PLAID_CLIENT_ID: {client_id[:8]}...{client_id[-8:]}")
    
    # Check secret
    if not secret:
        issues.append("❌ PLAID_SECRET is empty or missing")
    elif secret == 'your_plaid_secret_here' or secret.startswith('your_'):
        issues.append("❌ PLAID_SECRET appears to be a placeholder (not real credentials)")
    elif len(secret) < 20:
        issues.append(f"⚠️  PLAID_SECRET is very short ({len(secret)} chars) - might be invalid")
    else:
        print(f"✓ PLAID_SECRET: {secret[:8]}...{secret[-8:]}")
    
    # Check environment
    valid_envs = ['sandbox', 'development', 'production']
    if env not in valid_envs:
        issues.append(f"❌ PLAID_ENV '{env}' is invalid. Must be: {', '.join(valid_envs)}")
    else:
        print(f"✓ PLAID_ENV: {env}")
    
    return issues

def check_plaid_sdk():
    """Check Plaid SDK is installed and importable"""
    print_section("Plaid SDK Check", 2)
    
    issues = []
    
    try:
        from plaid.configuration import Configuration
        from plaid.api_client import ApiClient
        from plaid.api import plaid_api
        print("✓ Plaid SDK imported successfully")
    except ImportError as e:
        issues.append(f"❌ Failed to import Plaid SDK: {e}")
    
    return issues

def check_plaid_configuration():
    """Check Plaid API configuration can be created"""
    print_section("Plaid API Configuration Check", 2)
    
    client_id = os.getenv('PLAID_CLIENT_ID', '').strip()
    secret = os.getenv('PLAID_SECRET', '').strip()
    env = os.getenv('PLAID_ENV', 'sandbox').strip()
    
    issues = []
    
    try:
        from plaid.configuration import Configuration
        from plaid.api_client import ApiClient
        from plaid.api import plaid_api
        
        env_hosts = {
            'sandbox': 'https://sandbox.plaid.com',
            'development': 'https://development.plaid.com',
            'production': 'https://production.plaid.com'
        }
        
        host = env_hosts.get(env, 'https://sandbox.plaid.com')
        print(f"✓ Using host: {host}")
        
        configuration = Configuration(
            host=host,
            api_key={
                'clientId': client_id,
                'secret': secret,
            }
        )
        
        api_client = ApiClient(configuration)
        plaid_client = plaid_api.PlaidApi(api_client)
        
        print("✓ Plaid API client configured successfully")
        return plaid_client, issues
        
    except Exception as e:
        issues.append(f"❌ Failed to configure Plaid API: {e}")
        return None, issues

def test_link_token_creation(plaid_client):
    """Test actual link token creation API call"""
    print_section("Link Token Creation Test (API Call)", 2)
    
    issues = []
    
    try:
        from plaid.model.link_token_create_request import LinkTokenCreateRequest
        from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
        from plaid.model.products import Products
        from plaid.model.country_code import CountryCode
        
        request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id="test_user_diagnostic"),
            client_name="Bentley Budget Bot - Diagnostic",
            products=[Products("transactions")],
            country_codes=[CountryCode("US")],
            language='en',
        )
        
        print("🔄 Sending request to Plaid API...")
        response = plaid_client.link_token_create(request)
        
        link_token = response['link_token']
        expiration = response['expiration']
        
        print(f"✅ Link token created successfully:")
        print(f"   Token: {link_token[:30]}...")
        print(f"   Expires: {expiration}")
        
    except Exception as e:
        error_msg = str(e)
        issues.append(f"❌ Failed to create link token:\n{error_msg}")
        
        # Detailed error analysis
        if "INVALID_API_KEYS" in error_msg:
            issues.append("\n💡 DIAGNOSIS: Invalid Plaid Credentials")
            issues.append("   Root Cause: The client_id or secret provided is incorrect/expired")
            issues.append("   Solution: Get valid credentials from https://dashboard.plaid.com/")
        elif "INVALID_INPUT" in error_msg:
            issues.append("\n💡 DIAGNOSIS: Invalid Request Input")
            issues.append("   Root Cause: The request parameters are malformed")
            issues.append("   Solution: Check user_id, client_name, and products are valid")
        elif "RATE_LIMIT_EXCEEDED" in error_msg:
            issues.append("\n💡 DIAGNOSIS: Rate Limited")
            issues.append("   Root Cause: Too many API requests in short time")
            issues.append("   Solution: Wait a few minutes and try again")
        
    return issues

def print_recommendations(all_issues):
    """Print actionable recommendations based on issues found"""
    print_section("Recommendations & Next Steps", 2)
    
    if not all_issues:
        print("✅ No issues found - your Plaid setup is working correctly!")
        print("\n Next Steps:")
        print("   1. Restart your Streamlit app")
        print("   2. Navigate to Plaid Link section")
        print("   3. Click 'Connect Bank Account'")
        print("   4. Complete the authentication flow")
        return
    
    # Check if it's credentials issue
    cred_issues = [i for i in all_issues if 'INVALID_API_KEYS' in i or 'credentials' in i.lower()]
    if cred_issues:
        print("🔴 PRIMARY ISSUE: Invalid Plaid Credentials")
        print("\n   What to do:")
        print("   1. Go to https://dashboard.plaid.com/")
        print("   2. Log in to your Plaid account")
        print("   3. Navigate to Settings → API Keys")
        print("   4. Copy your real Client ID and Secret")
        print("   5. Update .env file:")
        print("      PLAID_CLIENT_ID=<paste_from_dashboard>")
        print("      PLAID_SECRET=<paste_from_dashboard>")
        print("   6. Save and restart your app")
        print("   7. Run test_plaid_credentials.py again")
        return
    
    # Check if it's SDK issue
    sdk_issues = [i for i in all_issues if 'SDK' in i or 'import' in i.lower()]
    if sdk_issues:
        print("🔴 PRIMARY ISSUE: Plaid SDK Not Installed")
        print("\n   What to do:")
        print("   1. Install/upgrade Plaid SDK:")
        print("      pip install --upgrade plaid-python")
        print("   2. Verify installation:")
        print("      python -c 'import plaid; print(plaid.__version__)'")
        print("   3. Run test_plaid_credentials.py again")
        return
    
    # Generic issues
    print("⚠️  Multiple issues found:")
    for issue in all_issues:
        print(f"   • {issue}")

def main():
    """Run all diagnostic checks"""
    print_section("PLAID DIAGNOSTIC TOOL - Bentley Budget Bot", 1)
    
    all_issues = []
    plaid_client = None
    
    # 1. Check environment variables
    issues = check_env_variables()
    all_issues.extend(issues)
    
    if issues:
        print_section("Diagnostic Summary", 1)
        print_recommendations(all_issues)
        return 1
    
    # 2. Check Plaid SDK
    issues = check_plaid_sdk()
    all_issues.extend(issues)
    
    if issues:
        print_section("Diagnostic Summary", 1)
        print_recommendations(all_issues)
        return 1
    
    # 3. Check Plaid configuration
    plaid_client, issues = check_plaid_configuration()
    all_issues.extend(issues)
    
    if issues or not plaid_client:
        print_section("Diagnostic Summary", 1)
        print_recommendations(all_issues)
        return 1
    
    # 4. Test link token creation
    issues = test_link_token_creation(plaid_client)
    all_issues.extend(issues)
    
    # Print summary
    print_section("Diagnostic Summary", 1)
    print_recommendations(all_issues)
    
    return 1 if all_issues else 0

if __name__ == "__main__":
    sys.exit(main())
