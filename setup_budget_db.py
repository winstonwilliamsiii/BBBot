"""
Setup Budget Database Tables
Creates all required tables for Plaid budget integration
"""
import os
import sys
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Load environment variables
load_dotenv()

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    print("Installing mysql-connector-python...")
    os.system("pip install mysql-connector-python")
    import mysql.connector
    from mysql.connector import Error

def create_budget_tables():
    """Create all budget-related tables in MySQL database"""
    
    # Get MySQL credentials from environment
    # Use BUDGET_MYSQL_* vars for budget database
    config = {
        'host': os.getenv('BUDGET_MYSQL_HOST', os.getenv('MYSQL_HOST', 'localhost')),
        'port': int(os.getenv('BUDGET_MYSQL_PORT', os.getenv('MYSQL_PORT', '3306'))),
        'user': os.getenv('BUDGET_MYSQL_USER', os.getenv('MYSQL_USER', 'root')),
        'password': os.getenv('BUDGET_MYSQL_PASSWORD', os.getenv('MYSQL_PASSWORD', '')),
        'database': os.getenv('BUDGET_MYSQL_DATABASE', 'mydb')
    }
    
    print("\n" + "="*60)
    print("BUDGET DATABASE SETUP")
    print("="*60)
    print(f"\nConnecting to MySQL:")
    print(f"  Host: {config['host']}:{config['port']}")
    print(f"  Database: {config['database']}")
    print(f"  User: {config['user']}")
    
    try:
        # Connect to MySQL with multi-statement support
        connection = mysql.connector.connect(**config, allow_local_infile=True)
        cursor = connection.cursor(buffered=True)
        
        print(f"\n✓ Connected successfully!")
        
        # Check MySQL version
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"  MySQL Version: {version}")
        
        # Read SQL schema file
        schema_file = 'scripts/setup/budget_schema_simple.sql'
        print(f"\n[Reading schema from: {schema_file}")
        
        with open(schema_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Replace USE mydb with the correct database
        sql_script = sql_script.replace('USE mydb', f"USE {config['database']}")
        
        # Split into individual statements and clean them
        raw_statements = sql_script.split(';')
        statements = []
        
        for stmt in raw_statements:
            # Clean the statement
            stmt = stmt.strip()
            # Skip empty statements, comments, and USE statements
            if not stmt or stmt.startswith('--') or stmt.startswith('/*'):
                continue
            if stmt.startswith('USE '):
                continue
            statements.append(stmt)
        
        print(f"\n🔧 Executing {len(statements)} SQL statements...")
        
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements, 1):
            try:
                # Execute statement
                cursor.execute(statement)
                connection.commit()  # Commit after each statement
                success_count += 1
                
                # Print progress for important operations
                if 'CREATE TABLE' in statement.upper():
                    # Extract table name
                    parts = statement.upper().split('CREATE TABLE')
                    if len(parts) > 1:
                        table_name = parts[1].split('(')[0].strip().split()[0]
                        if 'IF NOT EXISTS' in statement.upper():
                            table_name = parts[1].split('IF NOT EXISTS')[1].split('(')[0].strip()
                        print(f"  ✓ [{i}/{len(statements)}] Created table: {table_name}")
                elif 'ALTER TABLE' in statement.upper():
                    parts = statement.upper().split('ALTER TABLE')
                    if len(parts) > 1:
                        table_name = parts[1].split()[0].strip()
                        print(f"  ✓ [{i}/{len(statements)}] Altered table: {table_name}")
                elif 'CREATE VIEW' in statement.upper():
                    print(f"  ✓ [{i}/{len(statements)}] Created view")
                elif 'INSERT INTO' in statement.upper():
                    print(f"  ✓ [{i}/{len(statements)}] Inserted data")
                    
            except Error as e:
                error_count += 1
                # Only show errors that aren't about existing objects
                error_msg = str(e)
                if 'Duplicate column' not in error_msg and \
                   'already exists' not in error_msg and \
                   'Duplicate key' not in error_msg:
                    print(f"  ⚠ [{i}/{len(statements)}] Warning: {error_msg[:80]}...")
                    # Continue execution even with warnings
        
        connection.commit()
        
        # Verify tables were created
        print("\n📊 Verifying created tables...")
        cursor.execute("SHOW TABLES LIKE '%budget%' OR LIKE '%cash_flow%' OR LIKE '%plaid%'")
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n✓ Found {len(tables)} budget-related tables:")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"  • {table[0]} ({count} rows)")
        else:
            print("\n⚠ No budget tables found. Checking all tables...")
            cursor.execute("SHOW TABLES")
            all_tables = cursor.fetchall()
            print(f"\nAll tables in database:")
            for table in all_tables:
                print(f"  • {table[0]}")
        
        print("\n" + "="*60)
        print(f"✓ SETUP COMPLETE!")
        print(f"  Statements executed: {success_count}")
        print(f"  Warnings/skipped: {error_count}")
        print("="*60)
        
        cursor.close()
        connection.close()
        
        return True
        
    except Error as e:
        print(f"\n✗ MySQL Error: {e}")
        print(f"\nPlease check:")
        print(f"  1. MySQL is running on port {config['port']}")
        print(f"  2. Database '{config['database']}' exists")
        print(f"  3. Credentials in .env are correct")
        return False
    except FileNotFoundError:
        print(f"\n✗ File not found: {schema_file}")
        print(f"   Current directory: {os.getcwd()}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = create_budget_tables()
    sys.exit(0 if success else 1)
