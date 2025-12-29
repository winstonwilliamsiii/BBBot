"""
Test complete Personal Budget page functionality:
1. Plaid connection checking with is_active column
2. Table existence verification
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def test_plaid_connection_query():
    """Test the exact SQL query used in budget_analysis.py"""
    try:
        conn = pymysql.connect(
            host=os.getenv('BUDGET_MYSQL_HOST', '127.0.0.1'),
            port=int(os.getenv('BUDGET_MYSQL_PORT', '3306')),
            user=os.getenv('BUDGET_MYSQL_USER', 'root'),
            password=os.getenv('BUDGET_MYSQL_PASSWORD', 'root'),
            database=os.getenv('BUDGET_MYSQL_DATABASE', 'mydb')
        )
        
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # This is the EXACT query from budget_analysis.py check_plaid_connection()
        query = """
            SELECT access_token, item_id 
            FROM plaid_items 
            WHERE COALESCE(is_active, 1) = 1
            ORDER BY created_at DESC 
            LIMIT 1
        """
        
        print("🔍 Testing Plaid connection query...")
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            print("✅ Query executed successfully!")
            print(f"   Found active Plaid item: {result['item_id']}")
            print(f"   Access token exists: {'Yes' if result['access_token'] else 'No'}")
        else:
            print("✅ Query executed successfully!")
            print("   No active Plaid items found (expected if no connections yet)")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Query failed: {str(e)}")
        return False

def test_table_structure():
    """Verify plaid_items has all required columns"""
    try:
        conn = pymysql.connect(
            host=os.getenv('BUDGET_MYSQL_HOST', '127.0.0.1'),
            port=int(os.getenv('BUDGET_MYSQL_PORT', '3306')),
            user=os.getenv('BUDGET_MYSQL_USER', 'root'),
            password=os.getenv('BUDGET_MYSQL_PASSWORD', 'root'),
            database=os.getenv('BUDGET_MYSQL_DATABASE', 'mydb')
        )
        
        cursor = conn.cursor()
        cursor.execute("DESCRIBE plaid_items")
        columns = {col[0]: col[1] for col in cursor.fetchall()}
        
        print("\n🔍 Verifying table structure...")
        
        required_columns = {
            'id': 'int',
            'item_id': 'varchar(255)',
            'user_id': 'int',
            'access_token': 'text',
            'is_active': 'tinyint(1)',
            'created_at': 'timestamp',
            'updated_at': 'timestamp'
        }
        
        all_present = True
        for col_name, expected_type in required_columns.items():
            if col_name in columns:
                print(f"   ✅ {col_name}: {columns[col_name]}")
            else:
                print(f"   ❌ {col_name}: MISSING")
                all_present = False
        
        cursor.close()
        conn.close()
        return all_present
        
    except Exception as e:
        print(f"❌ Table structure check failed: {str(e)}")
        return False

def test_insert_and_query():
    """Test inserting a dummy record and querying it"""
    try:
        conn = pymysql.connect(
            host=os.getenv('BUDGET_MYSQL_HOST', '127.0.0.1'),
            port=int(os.getenv('BUDGET_MYSQL_PORT', '3306')),
            user=os.getenv('BUDGET_MYSQL_USER', 'root'),
            password=os.getenv('BUDGET_MYSQL_PASSWORD', 'root'),
            database=os.getenv('BUDGET_MYSQL_DATABASE', 'mydb')
        )
        
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        print("\n🔍 Testing insert and query operations...")
        
        # Insert test record
        test_item_id = "test_item_12345"
        cursor.execute("""
            INSERT INTO plaid_items (item_id, user_id, access_token, is_active)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE is_active = VALUES(is_active)
        """, (test_item_id, 1, "test_access_token", 1))
        conn.commit()
        print("   ✅ Test record inserted")
        
        # Query it back with COALESCE
        cursor.execute("""
            SELECT * FROM plaid_items 
            WHERE COALESCE(is_active, 1) = 1 
            AND item_id = %s
        """, (test_item_id,))
        result = cursor.fetchone()
        
        if result:
            print("   ✅ Test record retrieved successfully")
            print(f"   is_active value: {result['is_active']}")
        else:
            print("   ❌ Test record not found")
        
        # Clean up
        cursor.execute("DELETE FROM plaid_items WHERE item_id = %s", (test_item_id,))
        conn.commit()
        print("   ✅ Test record cleaned up")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Insert/query test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("PERSONAL BUDGET PAGE - COMPLETE FUNCTIONALITY TEST")
    print("=" * 60)
    
    test1 = test_plaid_connection_query()
    test2 = test_table_structure()
    test3 = test_insert_and_query()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Plaid Connection Query: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Table Structure:        {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Insert/Query Test:      {'✅ PASS' if test3 else '❌ FAIL'}")
    
    if test1 and test2 and test3:
        print("\n🎉 All tests passed! Personal Budget page should work correctly.")
    else:
        print("\n⚠️  Some tests failed. Review errors above.")
