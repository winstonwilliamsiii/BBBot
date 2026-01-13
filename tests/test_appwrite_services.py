"""
Test Appwrite Function Integration
Quick test script to verify service wrappers connect to Appwrite Cloud Functions
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_configuration():
    """Verify environment variables are loaded"""
    print("=== Appwrite Configuration Check ===\n")
    
    endpoint = os.getenv("APPWRITE_ENDPOINT")
    project_id = os.getenv("APPWRITE_PROJECT_ID")
    
    print(f"✓ Endpoint: {endpoint}")
    print(f"✓ Project ID: {project_id}")
    
    # Check Function IDs
    print("\n=== Streamlit Function IDs ===\n")
    functions = {
        "Get Transactions (Streamlit)": "APPWRITE_FUNCTION_ID_GET_TRANSACTIONS_STREAMLIT",
        "Add to Watchlist (Streamlit)": "APPWRITE_FUNCTION_ID_ADD_WATCHLIST_STREAMLIT",
        "Get Watchlist (Streamlit)": "APPWRITE_FUNCTION_ID_GET_WATCHLIST_STREAMLIT",
        "Get User Profile (Streamlit)": "APPWRITE_FUNCTION_ID_GET_USER_PROFILE_STREAMLIT",
    }
    
    missing = []
    for name, env_var in functions.items():
        value = os.getenv(env_var)
        if value and value != "PASTE_FUNCTION_ID_HERE":
            print(f"✓ {name}: {value}")
        else:
            print(f"✗ {name}: NOT CONFIGURED")
            missing.append(env_var)
    
    if missing:
        print(f"\n⚠️  Missing {len(missing)} Function IDs")
        print("Please update these in your .env file:")
        for var in missing:
            print(f"  - {var}")
        return False
    
    print("\n✓ All Function IDs configured!")
    return True


def test_service_imports():
    """Test if service modules import correctly"""
    print("\n=== Service Module Imports ===\n")
    
    try:
        from services.transactions import create_transaction, get_transactions
        print("✓ Transactions service imported")
    except ImportError as e:
        print(f"✗ Transactions service failed: {e}")
        return False
    
    try:
        from services.watchlist import add_to_watchlist, get_watchlist
        print("✓ Watchlist service imported")
    except ImportError as e:
        print(f"✗ Watchlist service failed: {e}")
        return False
    
    try:
        from services.user_profile import get_user_profile
        print("✓ User Profile service imported")
    except ImportError as e:
        print(f"✗ User Profile service failed: {e}")
        return False
    
    print("\n✓ All services imported successfully!")
    return True


def test_function_execution():
    """Test actual function execution (requires valid API key)"""
    print("\n=== Function Execution Test ===\n")
    
    from services.user_profile import get_user_profile
    
    # Test with a dummy user ID
    result = get_user_profile("test_user_123")
    
    if "error" in result:
        if "Missing Appwrite configuration" in result["error"]:
            print("⚠️  Configuration incomplete - cannot test execution")
            print(f"   Error: {result['error']}")
            return False
        else:
            print(f"⚠️  Function execution returned error: {result['error']}")
            print("   This is expected if you haven't added Function IDs yet")
            return False
    else:
        print("✓ Function executed successfully!")
        print(f"   Response: {result}")
        return True


if __name__ == "__main__":
    print("╔════════════════════════════════════════════════╗")
    print("║  Bentley Budget Bot - Appwrite Test Suite     ║")
    print("╚════════════════════════════════════════════════╝\n")
    
    # Run tests
    config_ok = test_configuration()
    imports_ok = test_service_imports()
    
    if config_ok and imports_ok:
        exec_ok = test_function_execution()
    
    print("\n" + "="*50)
    print("\nNext Steps:")
    print("1. Go to Appwrite Console → Functions")
    print("2. Copy each Function ID")
    print("3. Paste them into your .env file")
    print("4. Also add APPWRITE_API_KEY (server key)")
    print("5. Add APPWRITE_DATABASE_ID")
    print("6. Run this test again!")
    print("7. Then restart Streamlit: streamlit run streamlit_app.py")
    print("="*50 + "\n")
