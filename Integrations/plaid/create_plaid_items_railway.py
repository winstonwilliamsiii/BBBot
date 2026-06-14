"""
Create plaid_items table on Railway MySQL (Production)
This ensures Streamlit Cloud can use the new table structure
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def create_plaid_items_on_railway():
    """Create plaid_items table on Railway production database"""
    
    # Railway connection details (from your secrets)
    railway_config = {
        'host': os.getenv('RAILWAY_MYSQL_HOST', 'nozomi.proxy.rlwy.net'),
        'port': int(os.getenv('RAILWAY_MYSQL_PORT', '54537')),
        'user': os.getenv('RAILWAY_MYSQL_USER', 'root'),
        'password': os.getenv('RAILWAY_MYSQL_PASSWORD'),
        'database': os.getenv('RAILWAY_MYSQL_DATABASE', 'railway')
    }
    
    print("🚀 Connecting to Railway MySQL...")
    print(f"   Host: {railway_config['host']}")
    print(f"   Port: {railway_config['port']}")
    print(f"   Database: {railway_config['database']}")
    
    try:
        conn = pymysql.connect(**railway_config)
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute("SHOW TABLES LIKE 'plaid_items'")
        exists = cursor.fetchone()
        
        if exists:
            print("\n⚠️  plaid_items table already exists on Railway")
            cursor.execute("DESCRIBE plaid_items")
            columns = cursor.fetchall()
            print("\n   Current columns:")
            for col in columns:
                print(f"      {col[0]} - {col[1]}")
            
            # Check if is_active column exists
            has_is_active = any(col[0] == 'is_active' for col in columns)
            if not has_is_active:
                print("\n   ⚠️  Missing is_active column - adding it now...")
                cursor.execute("""
                    ALTER TABLE plaid_items 
                    ADD COLUMN is_active TINYINT(1) DEFAULT 1,
                    ADD INDEX idx_is_active (is_active)
                """)
                conn.commit()
                print("   ✅ Added is_active column")
            else:
                print("   ✅ is_active column already exists")
        else:
            print("\n📝 Creating plaid_items table on Railway...")
            create_table_sql = """
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
                INDEX idx_is_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            cursor.execute(create_table_sql)
            conn.commit()
            print("   ✅ plaid_items table created successfully!")
            
            # Verify creation
            cursor.execute("DESCRIBE plaid_items")
            columns = cursor.fetchall()
            print("\n   Created columns:")
            for col in columns:
                print(f"      {col[0]} - {col[1]}")
        
        # Check if user_plaid_tokens exists and has data
        cursor.execute("SHOW TABLES LIKE 'user_plaid_tokens'")
        old_table_exists = cursor.fetchone()
        
        if old_table_exists:
            cursor.execute("SELECT COUNT(*) FROM user_plaid_tokens")
            old_count = cursor.fetchone()[0]
            print(f"\n📊 Old table (user_plaid_tokens) has {old_count} records")
            
            if old_count > 0:
                print("   ℹ️  Consider migrating data from user_plaid_tokens to plaid_items")
                print("   Run: python migrate_plaid_tokens.py")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Railway database is ready!")
        print("   Streamlit Cloud will now use plaid_items table")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("CREATE PLAID_ITEMS TABLE ON RAILWAY (PRODUCTION)")
    print("=" * 60)
    create_plaid_items_on_railway()
