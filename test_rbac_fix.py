"""
RBAC Fix Verification Test
===========================
Tests the Personal Budget RBAC permissions fix

Run this after the RBAC AttributeError fix to verify:
1. RBACManager.has_permission() method exists
2. User.user_id property exists
3. All user roles have budget permissions
4. Session state initialization works
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from frontend.utils.rbac import RBACManager, Permission, UserRole, User
from datetime import datetime


def test_has_permission_method():
    """Test that RBACManager.has_permission() static method exists"""
    print("\n" + "="*60)
    print("TEST 1: RBACManager.has_permission() Method")
    print("="*60)
    
    try:
        # Check method exists
        assert hasattr(RBACManager, 'has_permission'), "has_permission method missing!"
        
        # Test with no authentication (should return False)
        result = RBACManager.has_permission(Permission.VIEW_BUDGET)
        assert result == False, "Should return False when not authenticated"
        
        print("✅ has_permission() method exists and works correctly")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_user_id_property():
    """Test that User class has user_id property"""
    print("\n" + "="*60)
    print("TEST 2: User.user_id Property")
    print("="*60)
    
    try:
        # Create test user
        user = User(
            username="test_user",
            role=UserRole.CLIENT,
            kyc_completed=True,
            investment_agreement_signed=True,
        )
        
        # Check user_id exists
        assert hasattr(user, 'user_id'), "user_id property missing!"
        assert user.user_id is not None, "user_id should not be None"
        assert isinstance(user.user_id, int), "user_id should be an integer"
        
        print(f"✅ User has user_id property: {user.user_id}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_budget_permissions():
    """Test that all relevant roles have budget permissions"""
    print("\n" + "="*60)
    print("TEST 3: Budget Permissions by Role")
    print("="*60)
    
    try:
        test_cases = [
            (UserRole.GUEST, Permission.VIEW_BUDGET, False),
            (UserRole.CLIENT, Permission.VIEW_BUDGET, True),
            (UserRole.CLIENT, Permission.MANAGE_BUDGET, False),
            (UserRole.CLIENT, Permission.CONNECT_BANK, True),
            (UserRole.INVESTOR, Permission.VIEW_BUDGET, True),
            (UserRole.INVESTOR, Permission.MANAGE_BUDGET, True),
            (UserRole.INVESTOR, Permission.CONNECT_BANK, True),
            (UserRole.ADMIN, Permission.VIEW_BUDGET, True),
            (UserRole.ADMIN, Permission.MANAGE_BUDGET, True),
            (UserRole.ADMIN, Permission.CONNECT_BANK, True),
        ]
        
        all_passed = True
        for role, permission, expected in test_cases:
            user = User(username=f"test_{role.value}", role=role)
            result = user.has_permission(permission)
            
            status = "✅" if result == expected else "❌"
            print(f"{status} {role.value:10s} - {permission.value:20s} = {result} (expected {expected})")
            
            if result != expected:
                all_passed = False
        
        if all_passed:
            print("\n✅ All budget permission tests passed!")
            return True
        else:
            print("\n❌ Some permission tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_session_state_init():
    """Test that session state initialization works"""
    print("\n" + "="*60)
    print("TEST 4: Session State Initialization")
    print("="*60)
    
    try:
        # This should not raise an error
        RBACManager.init_session_state()
        
        print("✅ Session state initialization works (no errors)")
        print("   Note: Full test requires Streamlit runtime")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_user_serialization():
    """Test that User can be serialized/deserialized with user_id"""
    print("\n" + "="*60)
    print("TEST 5: User Serialization with user_id")
    print("="*60)
    
    try:
        # Create test user
        original_user = User(
            username="serialization_test",
            role=UserRole.INVESTOR,
            kyc_completed=True,
            investment_agreement_signed=True,
            email="test@example.com",
            user_id=12345
        )
        
        # Serialize
        user_dict = original_user.to_dict()
        assert 'user_id' in user_dict, "user_id missing from serialized dict"
        assert user_dict['user_id'] == 12345, "user_id value incorrect"
        
        # Deserialize
        restored_user = User.from_dict(user_dict)
        assert restored_user.user_id == 12345, "user_id not restored correctly"
        
        print(f"✅ User serialization/deserialization works")
        print(f"   Original user_id: {original_user.user_id}")
        print(f"   Restored user_id: {restored_user.user_id}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_demo_user_authentication():
    """Test authentication with demo users and check user_id assignment"""
    print("\n" + "="*60)
    print("TEST 6: Demo User Authentication")
    print("="*60)
    
    try:
        test_users = ['guest', 'client', 'investor', 'admin']
        passwords = ['guest123', 'client123', 'investor123', 'admin123']
        
        all_passed = True
        for username, password in zip(test_users, passwords):
            user = RBACManager.authenticate(username, password)
            
            if user is None:
                print(f"❌ Authentication failed for {username}")
                all_passed = False
                continue
            
            if not hasattr(user, 'user_id') or user.user_id is None:
                print(f"❌ User {username} missing user_id")
                all_passed = False
                continue
            
            print(f"✅ {username:10s} authenticated (user_id: {user.user_id})")
        
        if all_passed:
            print("\n✅ All authentication tests passed!")
            return True
        else:
            print("\n❌ Some authentication tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def run_all_tests():
    """Run all RBAC verification tests"""
    print("\n" + "="*60)
    print("RBAC FIX VERIFICATION TEST SUITE")
    print("="*60)
    print("\nTesting fixes for Personal Budget AttributeError")
    print("Date: December 9, 2025")
    
    tests = [
        test_has_permission_method,
        test_user_id_property,
        test_budget_permissions,
        test_session_state_init,
        test_user_serialization,
        test_demo_user_authentication,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! RBAC fix is working correctly.")
        print("\nYou can now:")
        print("1. Run: streamlit run streamlit_app.py")
        print("2. Login with: username='client', password='client123'")
        print("3. Navigate to: Personal Budget page")
        print("4. Verify: No AttributeError, full dashboard loads")
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED. Please review the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
