"""
Quick test to verify Streamlit can load environment variables
Run this to confirm .env loading works in Streamlit context
"""

import os
from pathlib import Path
from dotenv import load_dotenv

print("=" * 60)
print("STREAMLIT ENVIRONMENT TEST")
print("=" * 60)

# Method 1: Default load_dotenv()
print("\n1️⃣ Testing default load_dotenv():")
load_dotenv()
api_key_1 = os.getenv("ALPACA_API_KEY", "")
print(f"   Result: {'✅ Found' if api_key_1 else '❌ Not Found'} ({api_key_1[:10]}... if found)")

# Method 2: Explicit path (simulating Streamlit pages/ subdirectory)
print("\n2️⃣ Testing with explicit path (pages/ context):")
# Simulate being in pages/ directory
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)
api_key_2 = os.getenv("ALPACA_API_KEY", "")
print(f"   .env path: {env_path}")
print(f"   .env exists: {env_path.exists()}")
print(f"   Result: {'✅ Found' if api_key_2 else '❌ Not Found'} ({api_key_2[:10]}... if found)")

# Method 3: Force reload with override
print("\n3️⃣ Testing with override=True:")
load_dotenv(override=True)
api_key_3 = os.getenv("ALPACA_API_KEY", "")
print(f"   Result: {'✅ Found' if api_key_3 else '❌ Not Found'} ({api_key_3[:10]}... if found)")

print("\n" + "=" * 60)
if api_key_2:
    print("✅ SUCCESS: Explicit path method works!")
    print("   This is what Streamlit pages should use.")
else:
    print("❌ FAILED: Check .env file location")
print("=" * 60)
