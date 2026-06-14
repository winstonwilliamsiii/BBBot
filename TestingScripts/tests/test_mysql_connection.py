"""
MySQL Connection Test Script
Tests direct connection to MySQL database
"""
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

def test_mysql_connection():
    """Test MySQL connection with current .env settings"""
    
    print("="*60)
    print("MySQL Connection Test")
    print("="*60)
    
    # Load config from .env
    config = {
        'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', 'root'),
        'database': os.getenv('MYSQL_DATABASE', 'mansa_bot')
    }
    
    print(f"\n📋 Connection Settings:")
    print(f"   Host: {config['host']}")
    print(f"   Port: {config['port']}")
    print(f"   User: {config['user']}")
    print(f"   Database: {config['database']}")
    print(f"   Password: {'*' * len(config['password'])}")
    
    # Test 1: Connect without database
    print(f"\n🔍 Test 1: Connect to MySQL server...")
    try:
        conn_no_db = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password']
        )
        print("   ✅ MySQL server connection successful!")
        
        # List databases
        cursor = conn_no_db.cursor()
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]
        print(f"   📁 Available databases: {', '.join(databases)}")
        
        cursor.close()
        conn_no_db.close()
        
    except Error as e:
        print(f"   ❌ Connection failed: {e}")
        print(f"\n💡 Fix:")
        print(f"   1. Check MySQL is running: Get-Service MySQL*")
        print(f"   2. Verify credentials in .env file")
        print(f"   3. Check firewall settings")
        return False
    
    # Test 2: Connect to specific database
    print(f"\n🔍 Test 2: Connect to database '{config['database']}'...")
    try:
        conn = mysql.connector.connect(**config)
        print(f"   ✅ Database connection successful!")
        
        # List tables
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        if tables:
            print(f"   📊 Tables found: {', '.join(tables)}")
        else:
            print(f"   ⚠️  No tables found in database")
            print(f"\n💡 Create tables using:")
            print(f"   mysql -u root -p {config['database']} < scripts/setup/schema.sql")
        
        cursor.close()
        conn.close()
        
    except Error as e:
        if e.errno == 1049:  # Unknown database
            print(f"   ❌ Database '{config['database']}' does not exist")
            print(f"\n💡 Create database:")
            print(f"   mysql -u root -p")
            print(f"   CREATE DATABASE {config['database']};")
            print(f"   USE {config['database']};")
            print(f"   SOURCE scripts/setup/schema.sql;")
        else:
            print(f"   ❌ Connection failed: {e}")
        return False
    
    # Test 3: Test portfolio service
    print(f"\n🔍 Test 3: Test portfolio service...")
    try:
        from services.mysql_portfolio import get_user_portfolio
        
        result = get_user_portfolio("test_user")
        
        if "error" in result:
            print(f"   ⚠️  Service returned error: {result['error']}")
        else:
            print(f"   ✅ Portfolio service working!")
            holdings = result.get('holdings', [])
            print(f"   📊 Found {len(holdings)} holdings for test_user")
            
    except ImportError:
        print(f"   ⚠️  mysql_portfolio service not found")
    except Exception as e:
        print(f"   ❌ Service test failed: {e}")
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    test_mysql_connection()
