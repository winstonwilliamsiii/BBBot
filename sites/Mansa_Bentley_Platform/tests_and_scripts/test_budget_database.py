"""Test budget database connection"""
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Testing Budget Database Connection...\n")

# Get configuration
config = {
    'host': os.getenv('BUDGET_MYSQL_HOST', '127.0.0.1'),
    'port': int(os.getenv('BUDGET_MYSQL_PORT', '3306')),
    'user': os.getenv('BUDGET_MYSQL_USER', 'root'),
    'password': os.getenv('BUDGET_MYSQL_PASSWORD', 'root'),
    'database': os.getenv('BUDGET_MYSQL_DATABASE', 'mydb'),
}

print(f"Configuration:")
print(f"  Host: {config['host']}")
print(f"  Port: {config['port']}")
print(f"  User: {config['user']}")
print(f"  Database: {config['database']}")
print()

try:
    conn = mysql.connector.connect(**config)
    print("✅ Successfully connected to database!")
    
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    print(f"\n📊 Tables in '{config['database']}':")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check if users table exists and has data
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"\n👥 Users in database: {user_count}")
    
    if user_count > 0:
        cursor.execute("SELECT username, email FROM users LIMIT 5")
        users = cursor.fetchall()
        print("\n📋 Sample users:")
        for user in users:
            print(f"  - {user[0]} ({user[1] if user[1] else 'no email'})")
    
    cursor.close()
    conn.close()
    
    print("\n✅ All tests passed!")
    
except mysql.connector.Error as err:
    print(f"❌ Connection failed: {err}")
    print("\n🔧 Troubleshooting steps:")
    print("1. Check MySQL service is running:")
    print("   netstat -an | Select-String \"3306\"")
    print("2. Verify credentials in .env file")
    print("3. Check database exists:")
    print("   CREATE DATABASE IF NOT EXISTS mydb;")
