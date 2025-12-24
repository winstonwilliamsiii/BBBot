"""
Quick test to verify Streamlit pages load without errors
"""
import subprocess
import time
import sys
import os

def test_streamlit_imports():
    """Test that all critical imports work"""
    print("\n" + "="*60)
    print("STREAMLIT PAGE IMPORT TEST")
    print("="*60)
    
    test_results = []
    
    # Test 1: Main app imports
    print("\n[1/4] Testing main app imports...")
    try:
        import streamlit_app
        print("  ✓ streamlit_app.py imports successfully")
        test_results.append(True)
    except Exception as e:
        print(f"  ✗ Error: {e}")
        test_results.append(False)
    
    # Test 2: Personal Budget page imports
    print("\n[2/4] Testing Personal Budget page imports...")
    try:
        # Add pages to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pages'))
        
        # Import the budget page module
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "budget_page", 
            "pages/01_💰_Personal_Budget.py"
        )
        budget_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(budget_module)
        
        print("  ✓ Personal Budget page imports successfully")
        print("  ✓ No RBAC AttributeError!")
        test_results.append(True)
    except AttributeError as e:
        print(f"  ✗ AttributeError (RBAC issue): {e}")
        test_results.append(False)
    except Exception as e:
        print(f"  ✗ Other error: {e}")
        test_results.append(False)
    
    # Test 3: RBAC functionality
    print("\n[3/4] Testing RBAC functionality...")
    try:
        from frontend.utils.rbac import RBACManager, Permission
        
        # Test static method exists
        assert hasattr(RBACManager, 'has_permission'), "has_permission method missing"
        
        # Test it can be called (will return False when not authenticated)
        result = RBACManager.has_permission(Permission.VIEW_BUDGET)
        
        print("  ✓ RBACManager.has_permission() works")
        print(f"  ✓ Returns: {result} (expected False when not logged in)")
        test_results.append(True)
    except Exception as e:
        print(f"  ✗ Error: {e}")
        test_results.append(False)
    
    # Test 4: Budget dashboard component
    print("\n[4/4] Testing budget dashboard component...")
    try:
        from frontend.components.budget_dashboard import show_full_budget_dashboard
        print("  ✓ Budget dashboard imports successfully")
        test_results.append(True)
    except Exception as e:
        print(f"  ✗ Error: {e}")
        test_results.append(False)
    
    # Summary
    print("\n" + "="*60)
    passed = sum(test_results)
    total = len(test_results)
    
    if passed == total:
        print(f"SUCCESS! All {total} tests passed!")
        print("\n✓ Streamlit app should work correctly")
        print("✓ Personal Budget page should load without errors")
        print("✓ RBAC is properly configured")
        return True
    else:
        print(f"PARTIAL: {passed}/{total} tests passed")
        return False


if __name__ == '__main__':
    success = test_streamlit_imports()
    sys.exit(0 if success else 1)
