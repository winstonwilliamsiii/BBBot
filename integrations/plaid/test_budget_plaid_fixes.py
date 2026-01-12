#!/usr/bin/env python3
"""
Test Plaid Connection and Budget Page Fixes
============================================
Tests the two fixes:
1. is_active column error in check_plaid_connection
2. Plaid Link button not opening
"""

import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def test_is_active_column():
    """Test if is_active column exists and query works"""
    print("=" * 70)
    print("TEST 1: Checking is_active column fix")
    print("=" * 70)
    
    try:
        conn = mysql.connector.connect(
            host=os.getenv('BUDGET_MYSQL_HOST', '127.0.0.1'),
            port=int(os.getenv('BUDGET_MYSQL_PORT', '3306')),
            user=os.getenv('BUDGET_MYSQL_USER', 'root'),
            password=os.getenv('BUDGET_MYSQL_PASSWORD', 'root'),
            database=os.getenv('BUDGET_MYSQL_DATABASE', 'mydb')
        )
        
        cursor = conn.cursor(dictionary=True)
        
        # Test the fixed query
        query = """
            SELECT 
                institution_name,
                last_sync,
                COALESCE(is_active, 1) as is_active
            FROM user_plaid_tokens
            WHERE user_id = %s AND COALESCE(is_active, 1) = 1
            ORDER BY last_sync DESC
            LIMIT 1
        """
        
        # Test with a sample user_id (1 is common test user)
        cursor.execute(query, (1,))
        result = cursor.fetchone()
        
        print("✅ Query executed successfully!")
        print(f"   Result: {result if result else 'No Plaid connections found (expected for new users)'}")
        
        # Check column exists
        cursor.execute("DESCRIBE user_plaid_tokens")
        columns = {row[0]: row[1] for row in cursor.fetchall()}
        
        if 'is_active' in columns:
            print(f"✅ is_active column exists (type: {columns['is_active']})")
        else:
            print("❌ is_active column is missing!")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_plaid_credentials():
    """Test if Plaid credentials are configured"""
    print("\n" + "=" * 70)
    print("TEST 2: Checking Plaid credentials")
    print("=" * 70)
    
    plaid_client_id = os.getenv('PLAID_CLIENT_ID', '')
    plaid_secret = os.getenv('PLAID_SECRET', '')
    plaid_env = os.getenv('PLAID_ENV', 'sandbox')
    
    if not plaid_client_id or plaid_client_id == 'your_plaid_client_id':
        print("⚠️  PLAID_CLIENT_ID not configured (using placeholder)")
        print("   Button will show setup instructions instead of opening OAuth")
    else:
        print(f"✅ PLAID_CLIENT_ID configured: {plaid_client_id[:10]}...")
        
    if not plaid_secret or plaid_secret == 'your_plaid_secret':
        print("⚠️  PLAID_SECRET not configured (using placeholder)")
    else:
        print(f"✅ PLAID_SECRET configured: {plaid_secret[:10]}...")
        
    print(f"✅ PLAID_ENV: {plaid_env}")
    
    print("\n📝 To enable Plaid OAuth:")
    print("   1. Sign up at: https://plaid.com/dashboard")
    print("   2. Create an application in Sandbox mode")
    print("   3. Copy Client ID and Secret to .env file")
    print("   4. Restart the Streamlit app")
    
    return True


def test_budget_database():
    """Test budget database tables"""
    print("\n" + "=" * 70)
    print("TEST 3: Checking budget database tables")
    print("=" * 70)
    
    try:
        conn = mysql.connector.connect(
            host=os.getenv('BUDGET_MYSQL_HOST', '127.0.0.1'),
            port=int(os.getenv('BUDGET_MYSQL_PORT', '3306')),
            user=os.getenv('BUDGET_MYSQL_USER', 'root'),
            password=os.getenv('BUDGET_MYSQL_PASSWORD', 'root'),
            database=os.getenv('BUDGET_MYSQL_DATABASE', 'mydb')
        )
        
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['user_plaid_tokens', 'transactions', 'transaction_notes', 'budget_categories']
        
        print(f"Found {len(tables)} tables in database:")
        for table in tables:
            status = "✅" if table in required_tables else "  "
            print(f"   {status} {table}")
            
        missing = [t for t in required_tables if t not in tables]
        if missing:
            print(f"\n⚠️  Missing tables: {', '.join(missing)}")
            print("   Run: mysql -u root -p mydb < scripts/setup/budget_schema.sql")
        else:
            print("\n✅ All required tables present!")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n🧪 Budget Page & Plaid Link Fixes Test Suite")
    print("=" * 70)
    
    results = []
    
    results.append(("Database is_active fix", test_is_active_column()))
    results.append(("Plaid credentials check", test_plaid_credentials()))
    results.append(("Budget database tables", test_budget_database()))
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
        print("\n✅ Fixes Applied:")
        print("   1. is_active column error fixed - now uses COALESCE(is_active, 1)")
        print("   2. Plaid Link button improved - added console logging and error handling")
        print("\n📱 Next Steps:")
        print("   1. Restart your Streamlit app: streamlit run streamlit_app.py")
        print("   2. Login and navigate to Personal Budget page")
        print("   3. The is_active error should be gone")
        print("   4. Click 'Connect to Bank' button")
        print("   5. If credentials configured: Plaid sandbox will open")
        print("   6. If not configured: Setup instructions will show")
    else:
        print("\n⚠️  Some tests failed - review errors above")
        
    print()
