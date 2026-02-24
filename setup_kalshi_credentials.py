"""
Kalshi Credentials Setup Helper
================================
This script will help you quickly set up your Kalshi API credentials.

Run this after you've:
1. Generated your API keys at https://kalshi.com/account/profile
2. Downloaded your private key file
"""

import os
from pathlib import Path
import shutil


def setup_kalshi_credentials():
    """Interactive setup for Kalshi credentials"""
    print("\n" + "=" * 70)
    print("🔑 KALSHI API CREDENTIALS SETUP")
    print("=" * 70)
    
    print("\nThis script will help you configure your Kalshi API credentials.")
    print("Make sure you have already:")
    print("  1. Logged into https://kalshi.com/account/profile")
    print("  2. Created a new API key")
    print("  3. Downloaded the private key file")
    
    input("\nPress Enter to continue...")
    
    # Step 1: Get API Key ID
    print("\n" + "-" * 70)
    print("STEP 1: API Key ID")
    print("-" * 70)
    print("\nYour API Key ID looks like: a952bcbe-ec3b-4b5b-b8f9-11dae589608c")
    api_key_id = input("\nPaste your API Key ID here: ").strip()
    
    if not api_key_id:
        print("❌ ERROR: API Key ID cannot be empty")
        return False
    
    print(f"✅ API Key ID: {api_key_id[:20]}...")
    
    # Step 2: Locate Private Key File
    print("\n" + "-" * 70)
    print("STEP 2: Private Key File")
    print("-" * 70)
    print("\nWhere did you save your private key file?")
    print("Common locations:")
    print("  1. Downloads folder: C:\\Users\\winst\\Downloads\\")
    print("  2. Desktop: C:\\Users\\winst\\Desktop\\")
    print("  3. Already in project: C:\\Users\\winst\\BentleyBudgetBot-predictions\\")
    
    private_key_source = input("\nEnter the full path to your private key file: ").strip()
    
    if not private_key_source:
        print("❌ ERROR: Private key path cannot be empty")
        return False
    
    # Remove quotes if user pasted path with quotes
    private_key_source = private_key_source.strip('"').strip("'")
    
    source_path = Path(private_key_source)
    if not source_path.exists():
        print(f"❌ ERROR: File not found at: {source_path}")
        print("\nPlease check the path and try again.")
        return False
    
    # Step 3: Copy Private Key to Project
    project_root = Path(__file__).parent
    dest_path = project_root / "kalshi-private-key.key"
    
    print(f"\n📁 Copying private key to project directory...")
    print(f"   From: {source_path}")
    print(f"   To: {dest_path}")
    
    try:
        shutil.copy2(source_path, dest_path)
        print("✅ Private key file copied successfully!")
    except Exception as e:
        print(f"❌ ERROR: Failed to copy file: {e}")
        return False
    
    # Step 4: Verify Private Key Format
    print("\n🔍 Verifying private key format...")
    try:
        with open(dest_path, 'r') as f:
            content = f.read()
            if 'BEGIN RSA PRIVATE KEY' not in content and 'BEGIN PRIVATE KEY' not in content:
                print("⚠️  WARNING: File doesn't appear to be a valid RSA private key")
                print("   Expected format: -----BEGIN RSA PRIVATE KEY-----")
            else:
                print("✅ Private key format looks correct!")
    except Exception as e:
        print(f"⚠️  WARNING: Could not verify key format: {e}")
    
    # Step 5: Update .env.development
    print("\n" + "-" * 70)
    print("STEP 3: Updating .env.development")
    print("-" * 70)
    
    env_file = project_root / ".env.development"
    
    if not env_file.exists():
        print(f"❌ ERROR: .env.development not found at: {env_file}")
        return False
    
    try:
        # Read current content
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update lines
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('KALSHI_API_KEY_ID='):
                lines[i] = f'KALSHI_API_KEY_ID={api_key_id}\n'
                updated = True
                print(f"✅ Updated KALSHI_API_KEY_ID")
            elif line.startswith('KALSHI_PRIVATE_KEY_PATH='):
                lines[i] = f'KALSHI_PRIVATE_KEY_PATH=./kalshi-private-key.key\n'
                print(f"✅ Updated KALSHI_PRIVATE_KEY_PATH")
        
        # Write back
        if updated:
            with open(env_file, 'w') as f:
                f.writelines(lines)
            print("\n✅ .env.development updated successfully!")
        else:
            print("\n⚠️  WARNING: Could not find KALSHI_API_KEY_ID in .env.development")
            print("   You may need to add it manually.")
    
    except Exception as e:
        print(f"❌ ERROR: Failed to update .env.development: {e}")
        return False
    
    # Step 6: Success Message
    print("\n" + "=" * 70)
    print("🎉 SETUP COMPLETE!")
    print("=" * 70)
    print("\n✅ Your Kalshi API credentials have been configured!")
    print("\nNext steps:")
    print("  1. Run the diagnostic script to verify:")
    print("     python fix_kalshi_portfolio.py")
    print("\n  2. If successful, view your portfolio at:")
    print("     Streamlit app → Prediction Analytics page")
    print("\n  3. Refresh your browser to see updated data")
    print()
    
    return True


def main():
    """Main entry point"""
    try:
        success = setup_kalshi_credentials()
        if success:
            print("\n💡 TIP: The private key file is sensitive - it's in .gitignore")
            print("   Don't commit it to version control!")
        else:
            print("\n❌ Setup failed. Please check the errors above and try again.")
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
