#!/usr/bin/env python3
"""
Create plaid_items table with is_active column
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def create_plaid_items_table():
    """Create plaid_items table with is_active column"""
    
    try:
        conn = pymysql.connect(
            host=os.getenv('BUDGET_MYSQL_HOST', '127.0.0.1'),
            port=int(os.getenv('BUDGET_MYSQL_PORT', '3306')),
            user=os.getenv('BUDGET_MYSQL_USER', 'root'),
            password=os.getenv('BUDGET_MYSQL_PASSWORD', 'root'),
            database=os.getenv('BUDGET_MYSQL_DATABASE', 'mydb')
        )
        
        cursor = conn.cursor()
        
        # Check if plaid_items table exists
        print("Checking if plaid_items table exists...")
        cursor.execute("SHOW TABLES LIKE 'plaid_items'")
        result = cursor.fetchall()
        
        if result:
            print("✅ plaid_items table already exists")
            
            # Check if is_active column exists
            cursor.execute("DESCRIBE plaid_items")
            columns = [row[0] for row in cursor.fetchall()]
            
            if 'is_active' not in columns:
                print("Adding is_active column...")
                cursor.execute("""
                    ALTER TABLE plaid_items 
                    ADD COLUMN is_active TINYINT(1) DEFAULT 1
                """)
                conn.commit()
                print("✅ is_active column added")
            else:
                print("✅ is_active column already exists")
        else:
            print("Creating plaid_items table...")
            cursor.execute("""
                CREATE TABLE plaid_items (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    item_id VARCHAR(255) UNIQUE NOT NULL,
                    user_id INT NOT NULL,
                    access_token TEXT NOT NULL,
                    institution_id VARCHAR(255),
                    institution_name VARCHAR(255),
                    is_active TINYINT(1) DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_item_id (item_id),
                    INDEX idx_is_active (is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()
            print("✅ plaid_items table created with is_active column")
        
        # Show final structure
        cursor.execute("DESCRIBE plaid_items")
        print("\n📊 plaid_items table structure:")
        print(f"{'Column':<20} {'Type':<20} {'Null':<8} {'Key':<8} {'Default':<15}")
        print("-" * 80)
        for row in cursor.fetchall():
            print(f"{row[0]:<20} {row[1]:<20} {row[2]:<8} {row[3]:<8} {str(row[4]):<15}")
        
        cursor.close()
        conn.close()
        return True
        
    except pymysql.MySQLError as e:
        print(f"❌ MySQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("Creating plaid_items table with is_active column")
    print("=" * 80)
    
    success = create_plaid_items_table()
    
    if success:
        print("\n🎉 Success! plaid_items table is ready with is_active column")
    else:
        print("\n⚠️  Operation failed - check errors above")
