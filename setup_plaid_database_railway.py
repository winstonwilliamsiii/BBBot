#!/usr/bin/env python3
"""
Create missing Plaid database (mydb) on Railway MySQL
This script creates the mydb database and required tables for Plaid integration
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Railway MySQL Configuration
RAILWAY_CONFIG = {
    'host': 'nozomi.proxy.rlwy.net',
    'port': 54537,
    'user': 'root',
    'password': 'cBlIUSygvPJCgPbNKHePJekQlClRamri'
}

def create_mydb_database():
    """Create mydb database on Railway MySQL for Plaid integration"""
    print("=" * 60)
    print("🚀 Creating mydb Database on Railway MySQL")
    print("=" * 60)
    
    try:
        # Connect to Railway MySQL (without database specified)
        print(f"\n📡 Connecting to Railway MySQL...")
        print(f"   Host: {RAILWAY_CONFIG['host']}")
        print(f"   Port: {RAILWAY_CONFIG['port']}")
        
        connection = mysql.connector.connect(**RAILWAY_CONFIG)
        
        if connection.is_connected():
            print(f"✅ Connected to Railway MySQL")
            
            cursor = connection.cursor()
            
            # Check if mydb exists
            cursor.execute("SHOW DATABASES LIKE 'mydb'")
            result = cursor.fetchone()
            
            if result:
                print(f"\n⚠️  Database 'mydb' already exists")
                print(f"   Checking for required tables...")
            else:
                # Create mydb database
                print(f"\n📦 Creating database: mydb")
                cursor.execute("CREATE DATABASE mydb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"✅ Database 'mydb' created successfully")
            
            # Use the mydb database
            cursor.execute("USE mydb")
            
            # Create Plaid tables
            print(f"\n📊 Creating Plaid integration tables...")
            
            # Plaid Items table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS plaid_items (
                item_id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                institution_id VARCHAR(255),
                institution_name VARCHAR(255),
                access_token VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("   ✅ plaid_items table created")
            
            # Accounts table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_id VARCHAR(255) PRIMARY KEY,
                item_id VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                official_name VARCHAR(255),
                type VARCHAR(50),
                subtype VARCHAR(50),
                currency VARCHAR(10),
                balance_current DECIMAL(15,2),
                balance_available DECIMAL(15,2),
                balance_limit DECIMAL(15,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES plaid_items(item_id),
                INDEX idx_item_id (item_id),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("   ✅ accounts table created")
            
            # Transactions table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id VARCHAR(255) PRIMARY KEY,
                account_id VARCHAR(255) NOT NULL,
                date DATE,
                amount DECIMAL(15,2),
                name VARCHAR(255),
                merchant_name VARCHAR(255),
                category VARCHAR(100),
                category_detail VARCHAR(255),
                transaction_type VARCHAR(50),
                pending BOOLEAN DEFAULT FALSE,
                authorized_datetime DATETIME,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(account_id),
                INDEX idx_account_id (account_id),
                INDEX idx_date (date),
                INDEX idx_created_at (created_at),
                INDEX idx_category (category)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("   ✅ transactions table created")
            
            # Budget Categories table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS budget_categories (
                category_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                category_name VARCHAR(100) NOT NULL,
                budget_amount DECIMAL(15,2),
                spent_amount DECIMAL(15,2) DEFAULT 0,
                month_year VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id),
                INDEX idx_month_year (month_year)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("   ✅ budget_categories table created")
            
            # Budget Goals table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS budget_goals (
                goal_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                goal_name VARCHAR(255),
                target_amount DECIMAL(15,2),
                current_amount DECIMAL(15,2) DEFAULT 0,
                deadline DATE,
                status VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("   ✅ budget_goals table created")
            
            connection.commit()
            
            # Verify tables
            print(f"\n🔍 Verifying tables in mydb...")
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            print(f"\n📋 Tables created:")
            for table in tables:
                print(f"   - {table[0]}")
            
            cursor.close()
            connection.close()
            
            return True
        
    except Error as e:
        print(f"\n❌ Error: {e}")
        return False

def print_connection_info():
    """Print connection information for verification"""
    print("\n" + "=" * 60)
    print("✅ Database Setup Complete!")
    print("=" * 60)
    print(f"""
Streamlit Cloud Secrets Configuration:
- BUDGET_MYSQL_HOST = "nozomi.proxy.rlwy.net"
- BUDGET_MYSQL_PORT = "54537"
- BUDGET_MYSQL_USER = "root"
- BUDGET_MYSQL_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"
- BUDGET_MYSQL_DATABASE = "mydb"

Tables created:
✅ plaid_items - Plaid integration items
✅ accounts - Bank accounts from Plaid
✅ transactions - Bank transactions
✅ budget_categories - Budget categories per user
✅ budget_goals - Budget savings goals

Ready for Streamlit Cloud deployment!
""")
    print("=" * 60 + "\n")

def main():
    """Main setup function"""
    print("\n🚀 Bentley Budget Bot - Plaid Database Setup\n")
    
    # Create database
    if not create_mydb_database():
        print("\n❌ Failed to create database")
        return False
    
    # Print info
    print_connection_info()
    
    print("\n✅ Setup Complete!")
    print("\nNext steps:")
    print("1. Verify Streamlit Cloud has these secrets configured")
    print("2. Test 💰 Personal Budget page")
    print("3. Connect Plaid account to populate data\n")
    
    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
