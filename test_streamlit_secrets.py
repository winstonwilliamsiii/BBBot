"""
Test Streamlit Secrets Loading
Verifies that Streamlit can read secrets.toml correctly
"""

import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("🔍 STREAMLIT SECRETS vs ENVIRONMENT VARIABLES TEST")
print("=" * 70)

# Test environment variables
print("\n📋 ENVIRONMENT VARIABLES (.env file):")
print(f"   PLAID_CLIENT_ID: {os.getenv('PLAID_CLIENT_ID', 'NOT FOUND')[:8]}...")
print(f"   ALPACA_API_KEY: {os.getenv('ALPACA_API_KEY', 'NOT FOUND')[:8]}...")

# Test Streamlit secrets
print("\n📋 STREAMLIT SECRETS (.streamlit/secrets.toml):")

try:
    # Try nested format
    if hasattr(st, 'secrets') and 'plaid' in st.secrets:
        print(f"   st.secrets.plaid.PLAID_CLIENT_ID: {st.secrets.plaid.PLAID_CLIENT_ID[:8]}...")
        print(f"   Format: NESTED ([plaid] section)")
    # Try flat format
    elif hasattr(st, 'secrets') and 'PLAID_CLIENT_ID' in st.secrets:
        print(f"   st.secrets.PLAID_CLIENT_ID: {st.secrets.PLAID_CLIENT_ID[:8]}...")
        print(f"   Format: FLAT (root level)")
    else:
        print("   ❌ Plaid secrets not found in either format")
        if hasattr(st, 'secrets'):
            print(f"   Available top-level keys: {list(st.secrets.keys())}")
except Exception as e:
    print(f"   ❌ Error reading secrets: {e}")

try:
    if hasattr(st, 'secrets') and 'alpaca' in st.secrets:
        print(f"   st.secrets.alpaca.ALPACA_API_KEY: {st.secrets.alpaca.ALPACA_API_KEY[:8]}...")
        print(f"   Format: NESTED ([alpaca] section)")
    elif hasattr(st, 'secrets') and 'ALPACA_API_KEY' in st.secrets:
        print(f"   st.secrets.ALPACA_API_KEY: {st.secrets.ALPACA_API_KEY[:8]}...")
        print(f"   Format: FLAT (root level)")
    else:
        print("   ❌ Alpaca secrets not found")
except Exception as e:
    print(f"   ❌ Error reading secrets: {e}")

# Test the get_secret function
print("\n📋 TESTING get_secret() FUNCTION:")

def get_secret(key: str, default: str = None) -> str:
    """Get a secret value from Streamlit secrets or environment"""
    # Try Streamlit secrets first (flat)
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    
    # Try nested format (key like "plaid.PLAID_CLIENT_ID")
    try:
        if hasattr(st, 'secrets'):
            parts = key.split('.')
            if len(parts) == 2:
                section, var = parts
                if section in st.secrets and var in st.secrets[section]:
                    return str(st.secrets[section][var])
    except Exception:
        pass
    
    # Fall back to environment variables
    return os.getenv(key, default)

# Test different access patterns
print(f"   get_secret('PLAID_CLIENT_ID'): {get_secret('PLAID_CLIENT_ID', 'NOT FOUND')[:8]}...")
print(f"   get_secret('plaid.PLAID_CLIENT_ID'): {get_secret('plaid.PLAID_CLIENT_ID', 'NOT FOUND')[:8] if get_secret('plaid.PLAID_CLIENT_ID', 'NOT FOUND') != 'NOT FOUND' else 'NOT FOUND'}")
print(f"   get_secret('ALPACA_API_KEY'): {get_secret('ALPACA_API_KEY', 'NOT FOUND')[:8]}...")

print("\n" + "=" * 70)
print("✅ TEST COMPLETE")
print("=" * 70)

st.write("# Streamlit Secrets Test")
st.write("Check your terminal/console for test results!")

# Show in app
if hasattr(st, 'secrets'):
    st.write("## Available Secrets Sections:")
    st.write(list(st.secrets.keys()))
    
    if 'plaid' in st.secrets:
        st.success("✅ Plaid secrets found (nested format)")
        st.code(f"PLAID_CLIENT_ID: {st.secrets.plaid.PLAID_CLIENT_ID[:8]}...")
    
    if 'alpaca' in st.secrets:
        st.success("✅ Alpaca secrets found (nested format)")
        st.code(f"ALPACA_API_KEY: {st.secrets.alpaca.ALPACA_API_KEY[:8]}...")
else:
    st.error("❌ st.secrets not available")
