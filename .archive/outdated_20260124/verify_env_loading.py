"""Quick diagnostic to verify .env is loading correctly"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Find .env
root = Path(__file__).parent
env_file = root / '.env'

print(f"Looking for .env at: {env_file}")
print(f"Exists: {env_file.exists()}")

if env_file.exists():
    # Check file size
    size = env_file.stat().st_size
    print(f"File size: {size} bytes")
    
    # Load it
    load_dotenv(str(env_file), override=True)
    
    # Check what loaded
    plaid_id = os.getenv('PLAID_CLIENT_ID', 'NOT_SET')
    plaid_secret = os.getenv('PLAID_SECRET', 'NOT_SET')
    alpaca_key = os.getenv('ALPACA_API_KEY', 'NOT_SET')
    alpaca_secret = os.getenv('ALPACA_SECRET_KEY', 'NOT_SET')
    mysql_host = os.getenv('MYSQL_HOST', 'NOT_SET')
    mysql_port = os.getenv('MYSQL_PORT', 'NOT_SET')
    bbbot_host = os.getenv('BBBOT1_MYSQL_HOST', 'NOT_SET')
    bbbot_port = os.getenv('BBBOT1_MYSQL_PORT', 'NOT_SET')
    mlflow_uri = os.getenv('MLFLOW_TRACKING_URI', 'NOT_SET')
    
    print(f"\n✅ After load_dotenv:")
    print(f"   PLAID_CLIENT_ID: {plaid_id[:20] if plaid_id != 'NOT_SET' else '❌ EMPTY'}")
    print(f"   PLAID_SECRET: {plaid_secret[:20] if plaid_secret != 'NOT_SET' else '❌ EMPTY'}")
    print(f"   ALPACA_API_KEY: {alpaca_key[:20] if alpaca_key != 'NOT_SET' else '❌ EMPTY'}")
    print(f"   ALPACA_SECRET_KEY: {alpaca_secret[:20] if alpaca_secret != 'NOT_SET' else '❌ EMPTY'}")
    print(f"   MYSQL_HOST: {mysql_host} (Port: {mysql_port})")
    print(f"   BBBOT1_MYSQL_HOST: {bbbot_host} (Port: {bbbot_port})")
    print(f"   MLFLOW_TRACKING_URI: {mlflow_uri}")
    
    # Check raw file
    print(f"\n📄 Raw .env file (credentials section):")
    with open(env_file, 'r') as f:
        in_credentials = False
        for i, line in enumerate(f):
            if 'Financial Data APIs' in line or 'PLAID' in line or 'ALPACA' in line:
                in_credentials = True
            if in_credentials and line.strip() and not line.startswith('#'):
                key = line.split('=')[0]
                value = line.split('=')[1] if '=' in line else ''
                if value and value != '':
                    print(f"   ✅ {key}={value[:15]}...")
                else:
                    print(f"   ❌ {key}=(empty)")
            if i > 160:
                break
else:
    print("❌ .env file NOT FOUND")
    print(f"   Current directory: {os.getcwd()}")
    print(f"   Expected location: {env_file}")

print("\n" + "="*60)

# Now test MySQL connection specifically
print("\n🔗 Testing MySQL connections...")
try:
    import mysql.connector
    
    # Test MYSQL_PORT (3306)
    try:
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', '127.0.0.1'),
            port=int(os.getenv('MYSQL_PORT', '3306')),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', 'root'),
            database=os.getenv('MYSQL_DATABASE', 'mansa_bot')
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        print(f"   ✅ MYSQL_PORT (3306): Connected to {os.getenv('MYSQL_DATABASE')}")
        conn.close()
    except Exception as e:
        print(f"   ⚠️ MYSQL_PORT (3306): {str(e)[:60]}")
    
    # Test BBBOT1_MYSQL_PORT (3307)
    try:
        conn = mysql.connector.connect(
            host=os.getenv('BBBOT1_MYSQL_HOST', '127.0.0.1'),
            port=int(os.getenv('BBBOT1_MYSQL_PORT', '3307')),
            user=os.getenv('BBBOT1_MYSQL_USER', 'root'),
            password=os.getenv('BBBOT1_MYSQL_PASSWORD', 'root'),
            database=os.getenv('BBBOT1_MYSQL_DATABASE', 'bbbot1')
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        print(f"   ✅ BBBOT1_MYSQL_PORT (3307): Connected to {os.getenv('BBBOT1_MYSQL_DATABASE')}")
        conn.close()
    except Exception as e:
        print(f"   ⚠️ BBBOT1_MYSQL_PORT (3307): {str(e)[:60]}")
        
except ImportError:
    print("   ⚠️ mysql.connector not installed. Run: pip install mysql-connector-python")

print("\n" + "="*60)
