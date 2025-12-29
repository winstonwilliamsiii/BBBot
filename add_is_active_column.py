#!/usr/bin/env python3
"""
Add is_active column to plaid_items table in Railway MySQL
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def add_is_active_column():
    """Add is_active column to plaid_items table"""
    
    # Connect to MySQL
    try:
        conn = pymysql.connect(
            host=os.getenv('MYSQL_HOST', '127.0.0.1'),
            port=int(os.getenv('MYSQL_PORT', '3306')),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', 'root'),
            database=os.getenv('MYSQL_DATABASE', 'mydb')
        )
        
        cursor = conn.cursor()
        
        # Check if plaid_items table exists
        print("Checking for plaid_items table...")
        cursor.execute("SHOW TABLES LIKE 'plaid_items'")
        result = cursor.fetchall()
        
        if not result:
            print("❌ plaid_items table not found!")
            print("   Available tables:")
            cursor.execute("SHOW TABLES")
            for table in cursor.fetchall():
                print(f"   - {table[0]}")
            cursor.close()
            conn.close()
            return False
        
        print("✅ plaid_items table found")
        
        # Check if is_active column already exists
        print("Checking if is_active column exists...")
        cursor.execute("DESCRIBE plaid_items")
        columns = [row[0] for row in cursor.fetchall()]
        
        if 'is_active' in columns:
            print("✅ is_active column already exists!")
            cursor.close()
            conn.close()
            return True
        
        # Add is_active column
        print("Adding is_active column...")
        cursor.execute("""
            ALTER TABLE plaid_items 
            ADD COLUMN is_active TINYINT(1) DEFAULT 1
        """)
        conn.commit()
        
        print("✅ Successfully added is_active column to plaid_items table")
        
        # Verify
        cursor.execute("DESCRIBE plaid_items")
        print("\nUpdated table structure:")
        for row in cursor.fetchall():
            print(f"  {row[0]} - {row[1]} - NULL:{row[2]} - Default:{row[4]}")
        
        cursor.close()
        conn.close()
        return True
        
    except pymysql.MySQLError as e:
        print(f"❌ MySQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("Adding is_active column to plaid_items table")
    print("=" * 70)
    
    success = add_is_active_column()
    
    if success:
        print("\n🎉 Column added successfully!")
    else:
        print("\n⚠️  Operation failed - check errors above")
