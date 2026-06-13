"""
DCF Database Setup Script
Executes SQL setup file to create DCF tables and sample data
"""

import mysql.connector
from pathlib import Path
import os
from dotenv import load_dotenv
import getpass

# Load environment variables from .env if it exists
load_dotenv()

# Database connection details
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", os.getenv("DB_HOST", "127.0.0.1")),
    "port": int(os.getenv("MYSQL_PORT", os.getenv("DB_PORT", "3306"))),
    "user": os.getenv("MYSQL_USER", os.getenv("DB_USER", "root")),
    "password": os.getenv("MYSQL_PASSWORD", os.getenv("DB_PASSWORD", "")),  # Will prompt if empty
    "database": os.getenv("MYSQL_DATABASE", os.getenv("DB_NAME", "mansa_bot"))
}

def get_password():
    """Get MySQL password from environment or prompt user"""
    print(f"Please enter MySQL password for user '{DB_CONFIG['user']}'")
    print(f"(or press Enter if no password is set)")
    password = getpass.getpass("MySQL Password: ")
    return password

def run_sql_setup():
    """Execute the DCF database setup SQL file"""
    sql_file = Path(__file__).parent.parent / "sql_scripts" / "setup_dcf_database.sql"
    
    if not sql_file.exists():
        print(f"❌ ERROR: SQL file not found at {sql_file}")
        return False
    
    try:
        # Connect to database
        print(f"🔌 Connecting to MySQL database '{DB_CONFIG['database']}' on {DB_CONFIG['host']}:{DB_CONFIG['port']}...")
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Read SQL file
        print(f"📄 Reading SQL file: {sql_file.name}")
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Split by semicolons and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        print(f"⚡ Executing {len(statements)} SQL statements...")
        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    normalized = statement.strip().lower()

                    # Keep setup scoped to the configured target database.
                    if normalized.startswith("use "):
                        cursor.execute(f"USE `{DB_CONFIG['database']}`")
                    else:
                        cursor.execute(statement)

                    # Consume result sets from verification SELECT statements
                    # so mysql-connector doesn't raise "Unread result found".
                    if getattr(cursor, "with_rows", False):
                        cursor.fetchall()

                    print(f"  ✅ Statement {i}/{len(statements)} executed")
                except mysql.connector.Error as e:
                    print(f"  ⚠️  Statement {i} warning: {e}")
        
        # Commit changes
        conn.commit()
        
        # Verify tables were created
        cursor.execute("SHOW TABLES LIKE 'fundamentals_annual'")
        fundamentals_exists = cursor.fetchone() is not None
        
        cursor.execute("SHOW TABLES LIKE 'prices_latest'")
        prices_exists = cursor.fetchone() is not None
        
        if fundamentals_exists and prices_exists:
            # Check row counts
            cursor.execute("SELECT COUNT(*) FROM fundamentals_annual")
            fund_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM prices_latest")
            price_count = cursor.fetchone()[0]
            
            print(f"\n✅ SUCCESS! DCF Database Setup Complete")
            print(f"   📊 fundamentals_annual: {fund_count} rows")
            print(f"   💰 prices_latest: {price_count} rows")
            
            # Show sample data
            cursor.execute("SELECT DISTINCT ticker FROM fundamentals_annual ORDER BY ticker")
            tickers = [row[0] for row in cursor.fetchall()]
            print(f"   🎯 Sample tickers available: {', '.join(tickers)}")
            
            return True
        else:
            print(f"\n❌ ERROR: Tables not created properly")
            print(f"   fundamentals_annual: {'EXISTS' if fundamentals_exists else 'MISSING'}")
            print(f"   prices_latest: {'EXISTS' if prices_exists else 'MISSING'}")
            return False
            
    except mysql.connector.Error as e:
        print(f"\n❌ MySQL Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            print("\n🔌 Database connection closed")

if __name__ == "__main__":
    print("=" * 60)
    print("DCF DATABASE SETUP")
    print("=" * 60)
    success = run_sql_setup()
    print("=" * 60)
    exit(0 if success else 1)
