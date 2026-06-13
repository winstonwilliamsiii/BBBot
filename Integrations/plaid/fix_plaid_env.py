#!/usr/bin/env python3
"""
Plaid Environment Variable Fix for Streamlit
Diagnoses and fixes PLAID_ENV blue status issue
"""

import os
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

def diagnose_plaid_env():
    """Diagnose PLAID_ENV loading issue"""
    print("\n" + "="*70)
    print("PLAID ENVIRONMENT DIAGNOSTIC")
    print("="*70 + "\n")
    
    # 1. Check .env file exists
    env_file = Path('.env')
    print(f"1️⃣  Checking .env file...")
    if env_file.exists():
        print(f"   ✅ .env file found at: {env_file.absolute()}")
    else:
        print(f"   ❌ .env file NOT FOUND")
        print(f"   Expected location: {env_file.absolute()}")
        return False
    
    # 2. Read raw .env content
    print(f"\n2️⃣  Reading .env content...")
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Check for PLAID_ENV line
    lines = content.split('\n')
    plaid_env_line = None
    for line in lines:
        if line.startswith('PLAID_ENV'):
            plaid_env_line = line
            break
    
    if plaid_env_line:
        print(f"   ✅ Found line: {plaid_env_line}")
    else:
        print(f"   ❌ PLAID_ENV line NOT FOUND in .env")
        return False
    
    # 3. Parse with python-dotenv
    print(f"\n3️⃣  Parsing with python-dotenv...")
    env_dict = dotenv_values('.env')
    
    if 'PLAID_ENV' in env_dict:
        value = env_dict['PLAID_ENV']
        print(f"   ✅ PLAID_ENV value: '{value}'")
        if value.strip() == '':
            print(f"   ⚠️  WARNING: Value is empty!")
            return False
    else:
        print(f"   ❌ PLAID_ENV not in parsed dict")
        print(f"   Available keys: {list(env_dict.keys())}")
        return False
    
    # 4. Test with os.getenv after load_dotenv
    print(f"\n4️⃣  Testing with load_dotenv(override=True)...")
    load_dotenv(override=True)
    
    plaid_client_id = os.getenv('PLAID_CLIENT_ID', 'NOT_SET').strip()
    plaid_secret = os.getenv('PLAID_SECRET', 'NOT_SET').strip()
    plaid_env = os.getenv('PLAID_ENV', 'NOT_SET').strip()
    
    print(f"   PLAID_CLIENT_ID: {plaid_client_id[:10]}... (length: {len(plaid_client_id)})")
    print(f"   PLAID_SECRET: {plaid_secret[:10]}... (length: {len(plaid_secret)})")
    print(f"   PLAID_ENV: '{plaid_env}' (length: {len(plaid_env)})")
    
    if plaid_env == 'NOT_SET':
        print(f"\n   ❌ PLAID_ENV still NOT SET after load_dotenv!")
        return False
    elif plaid_env == '':
        print(f"\n   ❌ PLAID_ENV is EMPTY!")
        return False
    elif plaid_env not in ['sandbox', 'development', 'production']:
        print(f"\n   ⚠️  WARNING: PLAID_ENV '{plaid_env}' is not recognized!")
        print(f"      Valid values: sandbox, development, production")
        return False
    
    print(f"\n   ✅ All variables loaded successfully!")
    return True


def fix_plaid_env():
    """Fix PLAID_ENV in .env file"""
    print("\n" + "="*70)
    print("PLAID ENVIRONMENT FIX")
    print("="*70 + "\n")
    
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    # Read current content
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Find or create PLAID_ENV line
    plaid_env_index = None
    for i, line in enumerate(lines):
        if line.startswith('PLAID_ENV'):
            plaid_env_index = i
            break
    
    # Prepare fix
    print("Current status:")
    if plaid_env_index is not None:
        current_line = lines[plaid_env_index].strip()
        print(f"  Found: {current_line}")
        
        # Check if value is missing
        if '=' not in current_line or current_line.split('=')[1].strip() == '':
            print(f"  ❌ Value is empty or missing!")
            lines[plaid_env_index] = 'PLAID_ENV=sandbox\n'
            print(f"  ✅ Fixed to: PLAID_ENV=sandbox")
        else:
            print(f"  ✅ Already configured: {current_line}")
    else:
        print(f"  ❌ PLAID_ENV line not found")
        print(f"  Adding PLAID_ENV=sandbox")
        
        # Add after PLAID_SECRET line or at end
        secret_index = None
        for i, line in enumerate(lines):
            if line.startswith('PLAID_SECRET'):
                secret_index = i
                break
        
        if secret_index is not None:
            lines.insert(secret_index + 1, 'PLAID_ENV=sandbox\n')
        else:
            lines.append('\n')
            lines.append('# Plaid Configuration\n')
            lines.append('PLAID_ENV=sandbox\n')
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"\n✅ .env file updated!")
    
    # Verify fix
    load_dotenv(override=True)
    plaid_env = os.getenv('PLAID_ENV', 'NOT_SET').strip()
    
    if plaid_env == 'sandbox':
        print(f"✅ Verification: PLAID_ENV = '{plaid_env}'")
        return True
    else:
        print(f"❌ Verification failed: PLAID_ENV = '{plaid_env}'")
        return False


def main():
    """Main function"""
    # Run diagnostic
    success = diagnose_plaid_env()
    
    if success:
        print("\n" + "="*70)
        print("✅ ALL PLAID ENVIRONMENT VARIABLES CONFIGURED CORRECTLY")
        print("="*70)
        print("\nNext steps:")
        print("1. Save your Streamlit app")
        print("2. Restart Streamlit: streamlit run streamlit_app.py")
        print("3. The PLAID_ENV status should now show GREEN")
        return 0
    else:
        print("\n" + "="*70)
        print("❌ PLAID ENVIRONMENT ISSUE DETECTED")
        print("="*70)
        print("\nAttempting automatic fix...")
        
        if fix_plaid_env():
            print("\n✅ Fix applied successfully!")
            print("\nNext steps:")
            print("1. Restart Streamlit: streamlit run streamlit_app.py")
            print("2. The PLAID_ENV status should now show GREEN")
            return 0
        else:
            print("\n❌ Automatic fix failed!")
            print("\nManual fix:")
            print("1. Open .env file")
            print("2. Find the line: PLAID_ENV=...")
            print("3. Ensure it says: PLAID_ENV=sandbox")
            print("4. Save and restart Streamlit")
            return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
