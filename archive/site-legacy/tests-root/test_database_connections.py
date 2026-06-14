"""
Database Connection Verification Script
Tests connectivity to all BentleyBudgetBot databases
"""

import os
import sys
from dotenv import load_dotenv
import mysql.connector
from datetime import datetime

# Load environment variables
load_dotenv(override=True)

# Database configurations
DATABASES = {
    'mydb (Budget)': {
        'host': os.getenv('BUDGET_MYSQL_HOST', '127.0.0.1'),
        'port': int(os.getenv('BUDGET_MYSQL_PORT', 3306)),
        'user': os.getenv('BUDGET_MYSQL_USER', 'root'),
        'password': os.getenv('BUDGET_MYSQL_PASSWORD', 'root'),
        'database': os.getenv('BUDGET_MYSQL_DATABASE', 'mydb'),
    },
    'mansa_bot (Metrics)': {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', 'root'),
        'database': os.getenv('MYSQL_DATABASE', 'mansa_bot'),
    },
    'mansa_quant (Quant)': {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', 'root'),
        'database': os.getenv('QUANT_MYSQL_DATABASE', 'mansa_quant'),
    },
    'mlflow_db (MLFlow)': {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', 'root'),
        'database': os.getenv('MLFLOW_MYSQL_DATABASE', 'mlflow_db'),
    },
    'mrgp_schema (Bulk)': {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', 'root'),
        'database': os.getenv('BULK_MYSQL_DATABASE', 'mrgp_schema'),
    },
}


def test_connection(name: str, config: dict) -> dict:
    """Test database connection and return status"""
    result = {
        'name': name,
        'status': 'unknown',
        'table_count': 0,
        'size_mb': 0,
        'error': None
    }
    
    try:
        # Connect to database
        conn = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            connect_timeout=5
        )
        
        cursor = conn.cursor()
        
        # Check if database exists and get table count
        cursor.execute(f"""
            SELECT COUNT(*) as table_count
            FROM information_schema.tables
            WHERE table_schema = '{config['database']}'
        """)
        table_count = cursor.fetchone()[0]
        result['table_count'] = table_count
        
        # Get database size
        cursor.execute(f"""
            SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb
            FROM information_schema.tables
            WHERE table_schema = '{config['database']}'
        """)
        size_result = cursor.fetchone()
        result['size_mb'] = float(size_result[0]) if size_result[0] else 0
        
        result['status'] = 'connected'
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as e:
        result['status'] = 'error'
        result['error'] = str(e)
    except Exception as e:
        result['status'] = 'error'
        result['error'] = f"Unexpected error: {str(e)}"
    
    return result


def main():
    print("=" * 80)
    print("DATABASE CONNECTION VERIFICATION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    for name, config in DATABASES.items():
        print(f"Testing {name}...")
        print(f"  Host: {config['host']}:{config['port']}")
        print(f"  Database: {config['database']}")
        
        result = test_connection(name, config)
        results.append(result)
        
        if result['status'] == 'connected':
            print(f"  ✅ Status: Connected")
            print(f"  📊 Tables: {result['table_count']}")
            print(f"  💾 Size: {result['size_mb']} MB")
        else:
            print(f"  ❌ Status: Failed")
            print(f"  ⚠️  Error: {result['error']}")
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    successful = [r for r in results if r['status'] == 'connected']
    failed = [r for r in results if r['status'] == 'error']
    
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    print()
    
    if successful:
        print("Connected Databases:")
        print(f"{'Database':<25} {'Tables':<10} {'Size (MB)':<10}")
        print("-" * 45)
        for r in successful:
            print(f"{r['name']:<25} {r['table_count']:<10} {r['size_mb']:<10.2f}")
        print()
    
    if failed:
        print("Failed Connections:")
        for r in failed:
            print(f"  ❌ {r['name']}")
            print(f"     Error: {r['error']}")
        print()
        
        print("Troubleshooting:")
        print("  1. Ensure MySQL is running on port 3306")
        print("  2. Verify credentials in .env file")
        print("  3. Run: mysql -u root -p -e 'SHOW DATABASES;'")
        print("  4. Check if databases exist")
        print("  5. Run init_all_databases.sql to create missing databases")
        print()
    
    # Check for deprecated bbbot1 database
    print("=" * 80)
    print("DEPRECATED DATABASE CHECK")
    print("=" * 80)
    
    try:
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', 'root'),
            connect_timeout=5
        )
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES LIKE 'bbbot1'")
        bbbot1_exists = cursor.fetchone()
        
        if bbbot1_exists:
            print("⚠️  WARNING: Deprecated 'bbbot1' database still exists!")
            print("   This database is no longer used in the new architecture.")
            print("   Consider backing up and dropping it:")
            print("   1. mysqldump -u root -p bbbot1 > backups/bbbot1_backup.sql")
            print("   2. mysql -u root -p -e 'DROP DATABASE bbbot1;'")
        else:
            print("✅ No deprecated 'bbbot1' database found (good!)")
        
        cursor.close()
        conn.close()
    except:
        print("⚠️  Could not check for bbbot1 database")
    
    print()
    
    # Exit code
    if failed:
        print("❌ Some database connections failed. Please review errors above.")
        sys.exit(1)
    else:
        print("✅ All database connections successful!")
        sys.exit(0)


if __name__ == "__main__":
    main()
