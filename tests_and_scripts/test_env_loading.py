"""
Test if .env is being loaded in Streamlit context
"""
import os
from dotenv import load_dotenv

print("Testing .env loading...")
print("=" * 60)

# Load .env
load_dotenv()

# Check all budget MySQL variables
vars_to_check = [
    'BUDGET_MYSQL_HOST',
    'BUDGET_MYSQL_PORT',
    'BUDGET_MYSQL_USER',
    'BUDGET_MYSQL_PASSWORD',
    'BUDGET_MYSQL_DATABASE',
    'PLAID_CLIENT_ID',
    'PLAID_SECRET',
    'PLAID_ENV'
]

print("\nEnvironment Variables:")
print("-" * 60)
for var in vars_to_check:
    value = os.getenv(var)
    if var in ['BUDGET_MYSQL_PASSWORD', 'PLAID_SECRET']:
        display = '***SET***' if value else 'NOT SET'
    elif var == 'PLAID_CLIENT_ID':
        display = f"{value[:10]}..." if value else 'NOT SET'
    else:
        display = value if value else 'NOT SET'
    
    status = "✅" if value else "❌"
    print(f"{status} {var}: {display}")

print("\n" + "=" * 60)

# Test database connection
print("\nTesting MySQL Connection...")
print("-" * 60)

try:
    import mysql.connector
    
    config = {
        'host': os.getenv('BUDGET_MYSQL_HOST', '127.0.0.1'),
        'port': int(os.getenv('BUDGET_MYSQL_PORT', '3306')),
        'user': os.getenv('BUDGET_MYSQL_USER', 'root'),
        'password': os.getenv('BUDGET_MYSQL_PASSWORD', ''),
        'database': os.getenv('BUDGET_MYSQL_DATABASE', 'mydb'),
    }
    
    print(f"Connecting with:")
    print(f"  Host: {config['host']}")
    print(f"  Port: {config['port']}")
    print(f"  User: {config['user']}")
    print(f"  Password: {'***' + str(len(config['password'])) + ' chars***' if config['password'] else 'EMPTY/NOT SET'}")
    print(f"  Database: {config['database']}")
    print()
    
    conn = mysql.connector.connect(**config)
    print("✅ MySQL connection successful!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    print(f"✅ Users table accessible: {count} users")
    
    cursor.close()
    conn.close()
    
except mysql.connector.Error as err:
    print(f"❌ MySQL Error: {err}")
    print(f"   Error Code: {err.errno}")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
