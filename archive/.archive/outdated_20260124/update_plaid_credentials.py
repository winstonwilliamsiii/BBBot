#!/usr/bin/env python3
"""
Quick Fix Script for Plaid Credentials
Interactively updates your .env file with new credentials
"""

import os
import sys
from pathlib import Path

def update_env_file(client_id, secret):
    """Update .env file with new credentials"""
    
    env_file = Path(r"C:\Users\winst\BentleyBudgetBot\.env")
    
    if not env_file.exists():
        print(f"❌ Error: .env file not found at {env_file}")
        return False
    
    # Read current content
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Replace credentials
    import re
    
    # Update PLAID_CLIENT_ID
    content = re.sub(
        r'PLAID_CLIENT_ID=.*',
        f'PLAID_CLIENT_ID={client_id}',
        content
    )
    
    # Update PLAID_SECRET
    content = re.sub(
        r'PLAID_SECRET=.*',
        f'PLAID_SECRET={secret}',
        content
    )
    
    # Update PLAID_SANDBOX_SECRET
    content = re.sub(
        r'PLAID_SANDBOX_SECRET=.*',
        f'PLAID_SANDBOX_SECRET={secret}',
        content
    )
    
    # Write back
    with open(env_file, 'w') as f:
        f.write(content)
    
    return True

def main():
    """Main interactive update flow"""
    
    print("=" * 70)
    print("  PLAID CREDENTIALS - Quick Update Tool")
    print("=" * 70)
    
    print("\n📍 Before you continue:")
    print("   1. Go to https://dashboard.plaid.com/")
    print("   2. Log in to your Plaid account")
    print("   3. Click Settings → API Keys")
    print("   4. Copy your Client ID and Secret")
    
    print("\n" + "-" * 70)
    
    # Get Client ID
    client_id = input("\n🔑 Enter your Plaid Client ID from the dashboard:\n> ").strip()
    
    if not client_id or len(client_id) < 20:
        print("❌ Invalid Client ID (should be 24+ characters)")
        return 1
    
    # Get Secret
    secret = input("\n🔑 Enter your Plaid Secret from the dashboard:\n> ").strip()
    
    if not secret or len(secret) < 20:
        print("❌ Invalid Secret (should be 30+ characters)")
        return 1
    
    # Confirm
    print("\n📋 Credentials to update:")
    print(f"   Client ID: {client_id[:8]}...{client_id[-8:]}")
    print(f"   Secret: {secret[:8]}...{secret[-8:]}")
    
    confirm = input("\n✅ Update .env file with these credentials? (yes/no)\n> ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Update cancelled")
        return 1
    
    # Update file
    if update_env_file(client_id, secret):
        print("\n✅ SUCCESS! .env file updated with new credentials")
        print("\n📝 Next steps:")
        print("   1. Run: python test_plaid_credentials.py")
        print("   2. If test passes, restart your Streamlit app")
        print("   3. Test the Plaid Link integration in your app")
        return 0
    else:
        print("❌ Failed to update .env file")
        return 1

if __name__ == "__main__":
    sys.exit(main())
