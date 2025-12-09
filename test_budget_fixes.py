"""
Test script for Budget Database and Plaid Integration fixes
Tests: 1) Database connection, 2) Environment config, 3) Budget page components
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_environment_config():
    """Test that budget database configuration is properly loaded"""
    print("\n🔧 Test 1: Environment Configuration")
    print("=" * 60)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check budget-specific variables
    budget_vars = {
        'BUDGET_MYSQL_HOST': os.getenv('BUDGET_MYSQL_HOST'),
        'BUDGET_MYSQL_PORT': os.getenv('BUDGET_MYSQL_PORT'),
        'BUDGET_MYSQL_USER': os.getenv('BUDGET_MYSQL_USER'),
        'BUDGET_MYSQL_PASSWORD': os.getenv('BUDGET_MYSQL_PASSWORD'),
        'BUDGET_MYSQL_DATABASE': os.getenv('BUDGET_MYSQL_DATABASE'),
    }
    
    all_configured = True
    for var_name, var_value in budget_vars.items():
        status = "✅" if var_value else "❌"
        print(f"   {status} {var_name}: {var_value or '(not set)'}")
        if not var_value:
            all_configured = False
    
    # Check Plaid variables
    print("\n   Plaid Configuration:")
    plaid_vars = {
        'PLAID_CLIENT_ID': os.getenv('PLAID_CLIENT_ID'),
        'PLAID_SECRET': os.getenv('PLAID_SECRET'),
        'PLAID_ENV': os.getenv('PLAID_ENV'),
    }
    
    for var_name, var_value in plaid_vars.items():
        is_placeholder = var_value and 'your_' in var_value.lower()
        status = "⚠️" if is_placeholder else ("✅" if var_value else "❌")
        display_value = "(placeholder)" if is_placeholder else (var_value or "(not set)")
        print(f"   {status} {var_name}: {display_value}")
    
    return all_configured


def test_database_connection():
    """Test MySQL connection to budget database"""
    print("\n🗄️  Test 2: Database Connection")
    print("=" * 60)
    
    try:
        from frontend.utils.budget_analysis import BudgetAnalyzer
        
        analyzer = BudgetAnalyzer()
        print(f"   ✅ BudgetAnalyzer initialized")
        print(f"   📊 Config: {analyzer.db_config['host']}:{analyzer.db_config['port']}/{analyzer.db_config['database']}")
        
        # Test connection
        conn = analyzer._get_connection()
        if conn:
            print(f"   ✅ Database connection successful!")
            
            # Test query
            cursor = conn.cursor()
            cursor.execute("SELECT DATABASE(), VERSION()")
            db_name, version = cursor.fetchone()
            print(f"   📊 Connected to: {db_name}")
            print(f"   🔢 MySQL version: {version}")
            
            # Check tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"   📋 Tables found: {len(tables)}")
            for table in tables:
                print(f"      - {table[0]}")
            
            cursor.close()
            conn.close()
            return True
        else:
            print(f"   ❌ Database connection failed (check error message above)")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mysql_service():
    """Check if MySQL service is running on port 3306"""
    print("\n🚀 Test 3: MySQL Service Status")
    print("=" * 60)
    
    import subprocess
    
    try:
        # Check if port 3306 is listening
        result = subprocess.run(
            ['powershell', '-Command', 'netstat -an | Select-String "3306"'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if "3306" in result.stdout and "LISTENING" in result.stdout:
            print("   ✅ MySQL is listening on port 3306")
            print("\n   Port Details:")
            for line in result.stdout.strip().split('\n'):
                if '3306' in line:
                    print(f"      {line.strip()}")
            return True
        else:
            print("   ❌ Port 3306 is not listening")
            print("   💡 Start MySQL service: net start MySQL80")
            return False
            
    except Exception as e:
        print(f"   ⚠️  Could not check port status: {e}")
        return False


def test_plaid_button_logic():
    """Test Plaid button logic without Streamlit UI"""
    print("\n🔗 Test 4: Plaid Integration Logic")
    print("=" * 60)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    plaid_client_id = os.getenv('PLAID_CLIENT_ID')
    plaid_secret = os.getenv('PLAID_SECRET')
    
    print(f"   PLAID_CLIENT_ID: {plaid_client_id}")
    
    if plaid_client_id and plaid_client_id != 'your_plaid_client_id_here':
        print("   ✅ Plaid credentials are configured")
        print("   📝 Button will show: OAuth flow instructions")
        return True
    else:
        print("   ⚠️  Plaid credentials are placeholders")
        print("   📝 Button will show: Setup instructions")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 BENTLEY BUDGET BOT - DATABASE & PLAID FIXES TEST")
    print("=" * 60)
    
    results = {
        'Environment Config': test_environment_config(),
        'MySQL Service': test_mysql_service(),
        'Database Connection': test_database_connection(),
        'Plaid Logic': test_plaid_button_logic(),
    }
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\n🚀 Next Steps:")
        print("   1. Run: streamlit run streamlit_app.py")
        print("   2. Navigate to Personal Budget page")
        print("   3. Test Plaid connection button")
    else:
        print("❌ SOME TESTS FAILED")
        print("\n🔧 Troubleshooting:")
        if not results['Environment Config']:
            print("   - Check .env file has BUDGET_MYSQL_* variables")
        if not results['MySQL Service']:
            print("   - Start MySQL: net start MySQL80")
        if not results['Database Connection']:
            print("   - Run: scripts/setup/verify_budget_database.ps1")
            print("   - Or: mysql -u root -p mydb < scripts/setup/budget_schema.sql")
        if not results['Plaid Logic']:
            print("   - Sign up at: https://plaid.com/dashboard")
            print("   - Update .env with real credentials")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
