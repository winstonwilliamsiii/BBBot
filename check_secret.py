"""Check PLAID_SECRET formatting"""
from dotenv import load_dotenv
import os

load_dotenv()

secret = os.getenv('PLAID_SECRET')

print(f"PLAID_SECRET Analysis:")
print(f"  Length: {len(secret) if secret else 0}")
print(f"  Value: {repr(secret)}")
print(f"  First 10: {secret[:10] if secret else 'None'}")
print(f"  Last 10: {secret[-10:] if secret else 'None'}")
print(f"  Has spaces: {' ' in secret if secret else False}")
print(f"  Has tabs: {chr(9) in secret if secret else False}")
print(f"  Has newlines: {chr(10) in secret if secret else False}")
print(f"  Stripped length: {len(secret.strip()) if secret else 0}")
