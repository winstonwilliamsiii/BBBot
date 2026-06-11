"""
Interactive Credential Fix Script
Fixes both Plaid and Alpaca credential issues
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def update_env_variable(key: str, value: str) -> bool:
    """Update a single environment variable in .env file"""
    env_path = Path('.env')
    
    if not env_path.exists():
        print(f"❌ .env file not found at {env_path.absolute()}")
        return False
    
    try:
        content = env_path.read_text(encoding='utf-8')
        
        # Pattern to match the variable
        pattern = rf'^{re.escape(key)}=.*$'
        
        # Check if variable exists
        if re.search(pattern, content, re.MULTILINE):
            # Update existing variable
            content = re.sub(pattern, f'{key}={value}', content, flags=re.MULTILINE)
        else:
            # Add new variable
            content += f'\n{key}={value}\n'
        
        # Write back
        env_path.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"❌ Error updating .env: {e}")
        return False


def validate_plaid_client_id(client_id: str) -> bool:
    """Validate Plaid Client ID format"""
    # Should be 24 characters, alphanumeric
    if len(client_id) != 24:
        print(f"⚠️  Expected 24 characters, got {len(client_id)}")
        return False
    
    if not client_id.replace('_', '').isalnum():
        print(f"⚠️  Should only contain alphanumeric characters")
        return False
    
    return True


def validate_alpaca_key(api_key: str, key_type: str = 'paper') -> bool:
    """Validate Alpaca API key format"""
    expected_prefix = 'PK' if key_type == 'paper' else 'AK'
    
    if not api_key.startswith(expected_prefix):
        print(f"⚠️  {key_type.title()} key should start with '{expected_prefix}', got '{api_key[:2]}'")
        return False
    
    if len(api_key) < 20:
        print(f"⚠️  Key seems too short: {len(api_key)} characters")
        return False
    
    return True


def fix_plaid():
    """Interactive Plaid credential fix"""
    print("\n" + "=" * 70)
    print("🔧 PLAID CREDENTIALS FIX")
    print("=" * 70)
    
    print("\n📍 Steps to get your Plaid credentials:")
    print("   1. Go to: https://dashboard.plaid.com/")
    print("   2. Log in to your account")
    print("   3. Navigate to: Team Settings → Keys")
    print("   4. Copy your credentials")
    
    print("\n" + "-" * 70)
    
    # Get Client ID
    current_client_id = os.getenv('PLAID_CLIENT_ID', '')
    print(f"\nCurrent PLAID_CLIENT_ID: {current_client_id[:8]}... (length: {len(current_client_id)})")
    
    client_id = input("\n🔑 Enter your Plaid Client ID (24 characters):\n> ").strip()
    
    if not client_id:
        print("❌ Skipping Plaid Client ID (empty input)")
        return False
    
    if not validate_plaid_client_id(client_id):
        print("❌ Invalid Client ID format. Please check and try again.")
        return False
    
    # Get Secret
    current_secret = os.getenv('PLAID_SECRET', '')
    print(f"\nCurrent PLAID_SECRET: {current_secret[:8]}... (length: {len(current_secret)})")
    
    secret = input("\n🔑 Enter your Plaid Secret:\n> ").strip()
    
    if not secret:
        print("❌ Skipping Plaid Secret (empty input)")
        return False
    
    if len(secret) < 20:
        print(f"⚠️  Warning: Secret seems short ({len(secret)} characters). Are you sure this is correct?")
        confirm = input("Continue anyway? (y/n): ").lower()
        if confirm != 'y':
            return False
    
    # Get Environment
    print("\nEnvironment options:")
    print("   sandbox     - Test environment with fake banks")
    print("   development - Live environment (100 free Items)")
    print("   production  - Full production (requires approval)")
    
    env = input("\n🌍 Enter Plaid environment [sandbox]: ").strip() or 'sandbox'
    
    if env not in ['sandbox', 'development', 'production']:
        print(f"⚠️  Unknown environment '{env}', using 'sandbox'")
        env = 'sandbox'
    
    # Update .env
    print("\n📝 Updating .env file...")
    
    if update_env_variable('PLAID_CLIENT_ID', client_id):
        print("   ✅ PLAID_CLIENT_ID updated")
    else:
        print("   ❌ Failed to update PLAID_CLIENT_ID")
        return False
    
    if update_env_variable('PLAID_SECRET', secret):
        print("   ✅ PLAID_SECRET updated")
    else:
        print("   ❌ Failed to update PLAID_SECRET")
        return False
    
    if update_env_variable('PLAID_ENV', env):
        print("   ✅ PLAID_ENV updated")
    else:
        print("   ❌ Failed to update PLAID_ENV")
        return False
    
    print("\n✅ Plaid credentials updated successfully!")
    return True


def fix_alpaca():
    """Interactive Alpaca credential fix"""
    print("\n" + "=" * 70)
    print("🔧 ALPACA CREDENTIALS FIX")
    print("=" * 70)
    
    print("\n📍 Steps to get your Alpaca credentials:")
    print("   1. Go to: https://alpaca.markets/")
    print("   2. Log in to your account")
    print("   3. Navigate to: Paper Trading or Live Trading")
    print("   4. Generate/View API Keys")
    
    print("\n⚠️  IMPORTANT:")
    print("   • Paper keys start with 'PK' (unlimited virtual money)")
    print("   • Live keys start with 'AK' (real money, funded account required)")
    
    print("\n" + "-" * 70)
    
    # Ask which type
    key_type = input("\nWhich keys are you entering? [paper/live]: ").strip().lower()
    
    if key_type not in ['paper', 'live']:
        print(f"⚠️  Invalid type '{key_type}', defaulting to 'paper'")
        key_type = 'paper'
    
    # Get API Key
    current_key = os.getenv('ALPACA_API_KEY', '')
    print(f"\nCurrent ALPACA_API_KEY: {current_key[:8]}... (type: {'PK=paper' if current_key.startswith('PK') else 'AK=live'})")
    
    api_key = input(f"\n🔑 Enter your Alpaca API Key (should start with '{'PK' if key_type == 'paper' else 'AK'}'):\n> ").strip()
    
    if not api_key:
        print("❌ Skipping Alpaca API Key (empty input)")
        return False
    
    if not validate_alpaca_key(api_key, key_type):
        print(f"❌ Invalid {key_type} API key format")
        return False
    
    # Get Secret Key
    current_secret = os.getenv('ALPACA_SECRET_KEY', '')
    print(f"\nCurrent ALPACA_SECRET_KEY: {current_secret[:8]}...")
    
    secret_key = input("\n🔑 Enter your Alpaca Secret Key:\n> ").strip()
    
    if not secret_key:
        print("❌ Skipping Alpaca Secret Key (empty input)")
        return False
    
    if len(secret_key) < 30:
        print(f"⚠️  Warning: Secret key seems short ({len(secret_key)} characters)")
        confirm = input("Continue anyway? (y/n): ").lower()
        if confirm != 'y':
            return False
    
    # Update .env
    print("\n📝 Updating .env file...")
    
    if update_env_variable('ALPACA_API_KEY', api_key):
        print("   ✅ ALPACA_API_KEY updated")
    else:
        print("   ❌ Failed to update ALPACA_API_KEY")
        return False
    
    if update_env_variable('ALPACA_SECRET_KEY', secret_key):
        print("   ✅ ALPACA_SECRET_KEY updated")
    else:
        print("   ❌ Failed to update ALPACA_SECRET_KEY")
        return False
    
    # Set paper mode
    paper_mode = 'true' if key_type == 'paper' else 'false'
    if update_env_variable('ALPACA_PAPER', paper_mode):
        print(f"   ✅ ALPACA_PAPER set to {paper_mode}")
    else:
        print("   ❌ Failed to update ALPACA_PAPER")
        return False
    
    print(f"\n✅ Alpaca credentials updated successfully! (Mode: {key_type.upper()})")
    return True


def main():
    """Main execution"""
    print("=" * 70)
    print("🔧 CREDENTIAL FIX UTILITY")
    print("=" * 70)
    print("\nThis script will help you fix:")
    print("  1. Plaid connection issues (invalid client_id)")
    print("  2. Alpaca production/paper trading setup")
    
    print("\n" + "=" * 70)
    
    # Menu
    while True:
        print("\nWhat would you like to fix?")
        print("   1. Plaid credentials")
        print("   2. Alpaca credentials")
        print("   3. Both")
        print("   4. Exit")
        
        choice = input("\nEnter your choice [1-4]: ").strip()
        
        if choice == '1':
            fix_plaid()
        elif choice == '2':
            fix_alpaca()
        elif choice == '3':
            fix_plaid()
            fix_alpaca()
        elif choice == '4':
            print("\n👋 Exiting...")
            break
        else:
            print("❌ Invalid choice. Please enter 1-4.")
            continue
        
        # Test option
        print("\n" + "-" * 70)
        test = input("\nWould you like to test the connections now? (y/n): ").lower()
        
        if test == 'y':
            print("\n🧪 Testing connections...\n")
            
            if choice in ['1', '3']:
                print("Testing Plaid...")
                os.system('python test_plaid_streamlit.py')
            
            if choice in ['2', '3']:
                print("\nTesting Alpaca...")
                os.system('python tests/test_alpaca_connection.py')
        
        # Continue?
        another = input("\nFix another credential? (y/n): ").lower()
        if another != 'y':
            break
    
    print("\n" + "=" * 70)
    print("✅ CREDENTIAL FIX COMPLETE")
    print("=" * 70)
    print("\n📝 Next steps:")
    print("   1. Restart your Streamlit app")
    print("   2. Test the integrations")
    print("   3. Verify in the dashboard")
    print("\n🚀 Run: streamlit run streamlit_app.py")


if __name__ == '__main__':
    main()
