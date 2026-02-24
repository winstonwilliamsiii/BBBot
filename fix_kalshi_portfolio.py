"""
Kalshi Portfolio Fix - Diagnostic & Resolution Script
=====================================================
This script:
1. Checks current Kalshi credentials configuration
2. Tests authentication with Kalshi API
3. Fetches and displays portfolio data
4. Provides step-by-step fix instructions if issues found
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('.env.development', override=True)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from prediction_analytics.services.kalshi_client import KalshiClient


def check_credential_status():
    """Check if Kalshi credentials are configured"""
    print("=" * 70)
    print("🔍 STEP 1: CHECKING KALSHI CREDENTIAL CONFIGURATION")
    print("=" * 70)
    
    api_key_id = os.getenv('KALSHI_API_KEY_ID', '')
    private_key_path = os.getenv('KALSHI_PRIVATE_KEY_PATH', '')
    
    issues = []
    
    # Check API Key ID
    print(f"\n📋 API Key ID: {api_key_id[:30] + '...' if len(api_key_id) > 30 else api_key_id}")
    if not api_key_id or api_key_id == 'your-api-key-id-here':
        print("   ❌ ISSUE: API Key ID not configured or using placeholder value")
        issues.append("api_key_id")
    else:
        print("   ✅ API Key ID is configured")
    
    # Check Private Key Path
    print(f"\n📁 Private Key Path: {private_key_path}")
    if not private_key_path:
        print("   ❌ ISSUE: Private key path not configured")
        issues.append("private_key_path")
    elif not Path(private_key_path).exists():
        print(f"   ❌ ISSUE: Private key file does not exist at: {Path(private_key_path).absolute()}")
        issues.append("private_key_file_missing")
    else:
        print(f"   ✅ Private key file exists at: {Path(private_key_path).absolute()}")
        
        # Check file content
        try:
            with open(private_key_path, 'r') as f:
                content = f.read()
                if 'BEGIN RSA PRIVATE KEY' in content:
                    print("   ✅ Private key file format looks correct (RSA format)")
                else:
                    print("   ⚠️  WARNING: Private key file doesn't appear to be in RSA format")
                    issues.append("private_key_format")
        except Exception as e:
            print(f"   ❌ ERROR: Cannot read private key file: {e}")
            issues.append("private_key_unreadable")
    
    return issues


def test_authentication():
    """Test authentication with Kalshi API"""
    print("\n" + "=" * 70)
    print("🔐 STEP 2: TESTING KALSHI API AUTHENTICATION")
    print("=" * 70)
    
    api_key_id = os.getenv('KALSHI_API_KEY_ID', '')
    private_key_path = os.getenv('KALSHI_PRIVATE_KEY_PATH', '')
    
    try:
        client = KalshiClient(api_key_id=api_key_id, private_key_path=private_key_path)
        
        print(f"\n🔑 Client Initialized")
        print(f"   Authenticated: {client.authenticated}")
        
        if not client.authenticated:
            print(f"   ❌ Authentication Failed: {client.last_error}")
            return False, None
        
        print(f"   ✅ Authentication Successful!")
        return True, client
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to initialize Kalshi client")
        print(f"   Error: {e}")
        return False, None


def test_portfolio_fetch(client):
    """Test fetching portfolio data"""
    print("\n" + "=" * 70)
    print("📊 STEP 3: FETCHING PORTFOLIO DATA")
    print("=" * 70)
    
    if not client:
        print("\n⚠️  Skipping - client not authenticated")
        return None
    
    try:
        # Test 1: Get User Profile
        print("\n1️⃣ Fetching User Profile...")
        profile = client.get_user_profile()
        if profile:
            print(f"   ✅ Profile Retrieved")
            print(f"   User ID: {profile.get('user_id', 'N/A')}")
            print(f"   Email: {profile.get('email', 'N/A')}")
        else:
            print("   ❌ Failed to retrieve profile")
        
        # Test 2: Get Balance
        print("\n2️⃣ Fetching Account Balance...")
        balance = client.get_user_balance()
        if balance:
            print(f"   ✅ Balance Retrieved")
            print(f"   Balance: {balance}")
        else:
            print("   ❌ Failed to retrieve balance")
        
        # Test 3: Get Portfolio Positions (MAIN ISSUE)
        print("\n3️⃣ Fetching Portfolio Positions...")
        positions = client.get_user_portfolio()
        
        print(f"   Response Type: {type(positions)}")
        print(f"   Number of Positions: {len(positions) if positions else 0}")
        
        if positions:
            print(f"   ✅ Portfolio Retrieved Successfully!")
            print(f"\n   📈 Your Open Positions:")
            for i, pos in enumerate(positions, 1):
                print(f"\n   Position {i}:")
                for key, value in pos.items():
                    print(f"      {key}: {value}")
            return positions
        else:
            print(f"   ⚠️  No open positions found")
            
            # Check trade history to see if there are closed positions
            print("\n4️⃣ Checking Trade History (Fills)...")
            trades = client.get_user_trades(limit=10)
            if trades:
                print(f"   ✅ Found {len(trades)} recent trades")
                print(f"   Note: You may have closed positions or pending orders")
            else:
                print(f"   ℹ️  No trade history found")
            
            return []
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to fetch portfolio")
        print(f"   Error: {e}")
        import traceback
        print(f"\n   Traceback:")
        print(traceback.format_exc())
        return None


def provide_fix_instructions(issues):
    """Provide step-by-step fix instructions based on issues found"""
    print("\n" + "=" * 70)
    print("🔧 FIX INSTRUCTIONS")
    print("=" * 70)
    
    if not issues:
        print("\n✅ No configuration issues found!")
        print("   If you're still having issues viewing your portfolio,")
        print("   it may be because you have no open positions.")
        return
    
    print("\n⚠️  The following issues need to be fixed:\n")
    
    if "api_key_id" in issues:
        print("━" * 70)
        print("❌ ISSUE: Kalshi API Key ID not configured")
        print("━" * 70)
        print("\n📝 How to Fix:")
        print("   1. Go to: https://kalshi.com/account/profile")
        print("   2. Log in with your credentials:")
        print("      Email: wwilliams@mansacap.com")
        print("      Password: Cartagena57!@")
        print("   3. Find 'API Keys' section")
        print("   4. Click 'Create New API Key'")
        print("   5. Copy the 'Key ID' (looks like: a952bcbe-ec3b-4b5b-b8f9-11dae589608c)")
        print("   6. Open: .env.development")
        print("   7. Replace this line:")
        print("      KALSHI_API_KEY_ID=your-api-key-id-here")
        print("      With:")
        print("      KALSHI_API_KEY_ID=<your-actual-key-id>")
        print()
    
    if "private_key_path" in issues or "private_key_file_missing" in issues:
        print("━" * 70)
        print("❌ ISSUE: Kalshi Private Key file missing")
        print("━" * 70)
        print("\n📝 How to Fix:")
        print("   1. When you create the API key (above), Kalshi will show a private key")
        print("   2. It starts with: -----BEGIN RSA PRIVATE KEY-----")
        print("   3. Download or copy this key (YOU CANNOT RETRIEVE IT AGAIN!)")
        print("   4. Save it to: c:\\Users\\winst\\BentleyBudgetBot-predictions\\kalshi-private-key.key")
        print("   5. Make sure the file name is exactly: kalshi-private-key.key")
        print()
    
    if "private_key_format" in issues:
        print("━" * 70)
        print("❌ ISSUE: Private key file format incorrect")
        print("━" * 70)
        print("\n📝 How to Fix:")
        print("   The private key file should start with:")
        print("   -----BEGIN RSA PRIVATE KEY-----")
        print("   And end with:")
        print("   -----END RSA PRIVATE KEY-----")
        print()
    
    print("\n📚 Additional Resources:")
    print("   Full Setup Guide: KALSHI_API_SETUP.md")
    print("   Kalshi API Docs: https://kalshi.com/api/docs")
    print()


def main():
    """Main diagnostic flow"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "KALSHI PORTFOLIO DIAGNOSTIC TOOL" + " " * 21 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # Step 1: Check credentials
    issues = check_credential_status()
    
    # Step 2: Test authentication
    authenticated, client = test_authentication()
    
    # Step 3: Test portfolio fetch
    if authenticated:
        positions = test_portfolio_fetch(client)
    
    # Step 4: Provide fix instructions if needed
    provide_fix_instructions(issues)
    
    # Final summary
    print("\n" + "=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    
    if not issues and authenticated:
        print("\n✅ SUCCESS! Kalshi API is properly configured and working!")
        print("   You can now view your portfolio in the Prediction Analytics page.")
    else:
        print("\n⚠️  Issues found. Please follow the fix instructions above.")
        print("   After fixing, run this script again to verify.")
    
    print("\n💡 Tips:")
    print("   • Keep your API keys secure - never commit them to git")
    print("   • API keys bypass MFA/2FA for programmatic access")
    print("   • You can create multiple API keys for different environments")
    print()


if __name__ == "__main__":
    main()
