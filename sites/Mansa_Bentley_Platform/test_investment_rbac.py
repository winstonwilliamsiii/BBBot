"""
Test Script for Investment Analysis RBAC System
Verifies authentication, permissions, and data displays
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all required modules can be imported"""
    print("=" * 60)
    print("Testing Imports")
    print("=" * 60)
    
    try:
        from frontend.utils.rbac import (
            RBACManager, User, UserRole, Permission, 
            show_login_form, show_user_info
        )
        print("✅ RBAC module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import RBAC module: {e}")
        return False
    
    try:
        from frontend.utils.broker_connections import (
            BrokerConnection, BrokerConnectionManager,
            display_broker_connections
        )
        print("✅ Broker connections module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import broker connections module: {e}")
        return False
    
    print()
    return True


def test_authentication():
    """Test authentication system"""
    print("=" * 60)
    print("Testing Authentication")
    print("=" * 60)
    
    from frontend.utils.rbac import RBACManager, UserRole
    
    # Test valid credentials
    test_cases = [
        ('guest', 'guest123', UserRole.GUEST, False, False),
        ('client', 'client123', UserRole.CLIENT, True, True),
        ('investor', 'investor123', UserRole.INVESTOR, True, True),
        ('admin', 'admin123', UserRole.ADMIN, True, True),
    ]
    
    for username, password, expected_role, expected_kyc, expected_agreement in test_cases:
        user = RBACManager.authenticate(username, password)
        
        if user:
            assert user.role == expected_role, f"Role mismatch for {username}"
            assert user.kyc_completed == expected_kyc, f"KYC status mismatch for {username}"
            assert user.investment_agreement_signed == expected_agreement, f"Agreement status mismatch for {username}"
            print(f"✅ {username}: Authenticated correctly (Role: {user.role.value})")
        else:
            print(f"❌ {username}: Authentication failed")
            return False
    
    # Test invalid credentials
    user = RBACManager.authenticate('invalid', 'wrong')
    if user is None:
        print("✅ Invalid credentials correctly rejected")
    else:
        print("❌ Invalid credentials incorrectly accepted")
        return False
    
    print()
    return True


def test_permissions():
    """Test permission system"""
    print("=" * 60)
    print("Testing Permissions")
    print("=" * 60)
    
    from frontend.utils.rbac import RBACManager, UserRole, Permission
    
    test_cases = [
        ('guest', UserRole.GUEST, Permission.VIEW_PORTFOLIO, True),
        ('guest', UserRole.GUEST, Permission.VIEW_CONNECTIONS, False),
        ('client', UserRole.CLIENT, Permission.VIEW_CONNECTIONS, True),
        ('client', UserRole.CLIENT, Permission.TRADE_EXECUTION, False),
        ('investor', UserRole.INVESTOR, Permission.TRADE_EXECUTION, True),
        ('admin', UserRole.ADMIN, Permission.ADMIN_PANEL, True),
    ]
    
    for username, role, permission, expected in test_cases:
        user = RBACManager.authenticate(username, f'{username}123')
        has_perm = user.has_permission(permission)
        
        if has_perm == expected:
            status = "✅" if expected else "🚫"
            print(f"{status} {username} - {permission.value}: {has_perm}")
        else:
            print(f"❌ {username} - {permission.value}: Expected {expected}, got {has_perm}")
            return False
    
    print()
    return True


def test_connections_access():
    """Test broker connections access requirements"""
    print("=" * 60)
    print("Testing Connections Access")
    print("=" * 60)
    
    from frontend.utils.rbac import RBACManager
    
    # Guest should not have access
    guest = RBACManager.authenticate('guest', 'guest123')
    if not guest.can_view_connections():
        print("✅ Guest correctly denied connections access")
    else:
        print("❌ Guest incorrectly granted connections access")
        return False
    
    # Client with KYC should have access
    client = RBACManager.authenticate('client', 'client123')
    if client.can_view_connections():
        print("✅ Client with KYC correctly granted connections access")
    else:
        print("❌ Client with KYC incorrectly denied connections access")
        return False
    
    print()
    return True


def test_broker_data():
    """Test broker connection data structures"""
    print("=" * 60)
    print("Testing Broker Data")
    print("=" * 60)
    
    from frontend.utils.broker_connections import BrokerConnectionManager
    
    # Test demo connections
    connections = BrokerConnectionManager.get_demo_connections()
    if len(connections) > 0:
        print(f"✅ Retrieved {len(connections)} demo broker connections")
        
        total_balance = sum(conn.balance for conn in connections)
        print(f"   Total balance: ${total_balance:,.2f}")
    else:
        print("❌ No demo connections retrieved")
        return False
    
    print()
    return True


def test_data_serialization():
    """Test data serialization to dict"""
    print("=" * 60)
    print("Testing Data Serialization")
    print("=" * 60)
    
    from frontend.utils.rbac import RBACManager
    from frontend.utils.broker_connections import BrokerConnectionManager
    
    # Test user serialization
    user = RBACManager.authenticate('client', 'client123')
    user_dict = user.to_dict()
    
    if 'username' in user_dict and 'role' in user_dict:
        print("✅ User serialization works")
    else:
        print("❌ User serialization failed")
        return False
    
    # Test connection serialization
    connections = BrokerConnectionManager.get_demo_connections()
    if connections:
        conn_dict = connections[0].to_dict()
        if 'Broker' in conn_dict and 'Balance' in conn_dict:
            print("✅ Connection serialization works")
        else:
            print("❌ Connection serialization failed")
            return False
    
    print()
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("INVESTMENT ANALYSIS RBAC SYSTEM - TEST SUITE")
    print("=" * 60 + "\n")
    
    tests = [
        ("Imports", test_imports),
        ("Authentication", test_authentication),
        ("Permissions", test_permissions),
        ("Connections Access", test_connections_access),
        ("Broker Data", test_broker_data),
        ("Data Serialization", test_data_serialization),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print("-" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Run: streamlit run 'pages/01_📈_Investment_Analysis.py'")
        print("2. Login with: client / client123")
        print("3. Navigate to Broker Connections tab")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
