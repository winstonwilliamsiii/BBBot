t"""
RBAC Page Access Test - December 9, 2025
========================================
Tests updated RBAC system with correct page access:

Page Structure:
1. Bentley Dashboard (Home)
2. Personal Budget
3. Investment Analysis
4. Live Crypto Dashboard
5. Broker Trading
6. Trading Bot

Access Rules:
- Admin: Full RW access to ALL pages (1-6)
- Client: Pages 1-4 (KYC + Asset Management Agreement)
- Investor: Pages 1-5 (KYC + Investor Management/PPM)
- Guest: Dev/Testing - Full access during development

Credentials:
- Dev/Testing: guest/guest123
- Production: admin/admin123 (for patches)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from frontend.utils.rbac import RBACManager, Permission, UserRole, User
from datetime import datetime


def test_page_access_permissions():
    """Test page access for all user roles"""
    print("\n" + "="*70)
    print("TEST: Page Access Permissions")
    print("="*70)
    
    # Page structure
    pages = {
        1: "Bentley Dashboard (Home)",
        2: "Personal Budget",
        3: "Investment Analysis",
        4: "Live Crypto Dashboard",
        5: "Broker Trading",
        6: "Trading Bot",
    }
    
    # Expected access
    expected_access = {
        'guest': [1, 2, 3, 4, 5, 6],  # Dev/Testing: All pages
        'client': [1, 2, 3, 4],        # Pages 1-4
        'investor': [1, 2, 3, 4, 5],   # Pages 1-5
        'admin': [1, 2, 3, 4, 5, 6],   # All pages
    }
    
    all_passed = True
    
    for username in ['guest', 'client', 'investor', 'admin']:
        user = RBACManager.authenticate(username, f'{username}123')
        
        if not user:
            print(f"❌ Failed to authenticate {username}")
            all_passed = False
            continue
        
        print(f"\n{username.upper()} (Role: {user.role.value})")
        print(f"Agreement: {user.agreement_type}")
        print(f"Expected Access: Pages {expected_access[username]}")
        print("-" * 70)
        
        for page_num in range(1, 7):
            can_access = user.can_access_page(page_num)
            expected = page_num in expected_access[username]
            status = "✅" if can_access == expected else "❌"
            access_str = "✅ Allow" if can_access else "❌ Deny"
            
            print(f"{status} Page {page_num}: {pages[page_num]:30s} {access_str}")
            
            if can_access != expected:
                all_passed = False
                print(f"   ⚠️  Expected: {expected}, Got: {can_access}")
    
    if all_passed:
        print("\n" + "="*70)
        print("✅ ALL PAGE ACCESS TESTS PASSED!")
        print("="*70)
        return True
    else:
        print("\n" + "="*70)
        print("❌ SOME PAGE ACCESS TESTS FAILED!")
        print("="*70)
        return False


def test_permission_mapping():
    """Test permission mapping for all roles"""
    print("\n" + "="*70)
    print("TEST: Permission Mapping")
    print("="*70)
    
    test_cases = [
        # Guest (Dev/Testing)
        ('guest', Permission.VIEW_DASHBOARD, True),
        ('guest', Permission.VIEW_BUDGET, True),
        ('guest', Permission.VIEW_ANALYSIS, True),
        ('guest', Permission.VIEW_CRYPTO, True),
        ('guest', Permission.VIEW_BROKER_TRADING, True),
        ('guest', Permission.VIEW_TRADING_BOT, True),
        
        # Client (Pages 1-4)
        ('client', Permission.VIEW_DASHBOARD, True),
        ('client', Permission.VIEW_BUDGET, True),
        ('client', Permission.VIEW_ANALYSIS, True),
        ('client', Permission.VIEW_CRYPTO, True),
        ('client', Permission.VIEW_BROKER_TRADING, False),
        ('client', Permission.VIEW_TRADING_BOT, False),
        ('client', Permission.CONNECT_BANK, True),
        ('client', Permission.MANAGE_BUDGET, False),
        
        # Investor (Pages 1-5)
        ('investor', Permission.VIEW_DASHBOARD, True),
        ('investor', Permission.VIEW_BUDGET, True),
        ('investor', Permission.VIEW_ANALYSIS, True),
        ('investor', Permission.VIEW_CRYPTO, True),
        ('investor', Permission.VIEW_BROKER_TRADING, True),
        ('investor', Permission.VIEW_TRADING_BOT, False),
        ('investor', Permission.MANAGE_BUDGET, True),
        ('investor', Permission.TRADE_EXECUTION, True),
        
        # Admin (All pages)
        ('admin', Permission.VIEW_DASHBOARD, True),
        ('admin', Permission.VIEW_BUDGET, True),
        ('admin', Permission.VIEW_ANALYSIS, True),
        ('admin', Permission.VIEW_CRYPTO, True),
        ('admin', Permission.VIEW_BROKER_TRADING, True),
        ('admin', Permission.VIEW_TRADING_BOT, True),
        ('admin', Permission.ADMIN_PANEL, True),
        ('admin', Permission.MANAGE_BUDGET, True),
        ('admin', Permission.TRADE_EXECUTION, True),
    ]
    
    all_passed = True
    for username, permission, expected in test_cases:
        user = RBACManager.authenticate(username, f'{username}123')
        result = user.has_permission(permission)
        status = "✅" if result == expected else "❌"
        
        print(f"{status} {username:10s} - {permission.value:25s} = {result} (expected {expected})")
        
        if result != expected:
            all_passed = False
    
    if all_passed:
        print("\n✅ All permission mapping tests passed!")
        return True
    else:
        print("\n❌ Some permission mapping tests failed!")
        return False


def test_agreement_types():
    """Test agreement type tracking"""
    print("\n" + "="*70)
    print("TEST: Agreement Type Tracking")
    print("="*70)
    
    expected_agreements = {
        'guest': 'dev_testing',
        'client': 'asset_mgmt',
        'investor': 'investor_mgmt',
        'admin': 'admin',
    }
    
    all_passed = True
    for username, expected_type in expected_agreements.items():
        user = RBACManager.authenticate(username, f'{username}123')
        
        if user.agreement_type == expected_type:
            print(f"✅ {username:10s} - Agreement: {expected_type}")
        else:
            print(f"❌ {username:10s} - Expected: {expected_type}, Got: {user.agreement_type}")
            all_passed = False
    
    if all_passed:
        print("\n✅ All agreement type tests passed!")
        return True
    else:
        print("\n❌ Some agreement type tests failed!")
        return False


def test_compliance_requirements():
    """Test KYC and agreement compliance"""
    print("\n" + "="*70)
    print("TEST: Compliance Requirements")
    print("="*70)
    
    test_cases = [
        ('guest', True, True),     # Dev/testing has KYC + agreement
        ('client', True, True),    # Client requires KYC + Asset Mgmt
        ('investor', True, True),  # Investor requires KYC + Investor Mgmt/PPM
        ('admin', True, True),     # Admin has all compliance
    ]
    
    all_passed = True
    for username, expected_kyc, expected_agreement in test_cases:
        user = RBACManager.authenticate(username, f'{username}123')
        
        kyc_status = "✅" if user.kyc_completed == expected_kyc else "❌"
        agreement_status = "✅" if user.investment_agreement_signed == expected_agreement else "❌"
        
        print(f"{username:10s} - KYC: {kyc_status} | Agreement: {agreement_status} | Type: {user.agreement_type}")
        
        if user.kyc_completed != expected_kyc or user.investment_agreement_signed != expected_agreement:
            all_passed = False
    
    if all_passed:
        print("\n✅ All compliance tests passed!")
        return True
    else:
        print("\n❌ Some compliance tests failed!")
        return False


def test_credentials():
    """Test login credentials"""
    print("\n" + "="*70)
    print("TEST: Login Credentials")
    print("="*70)
    
    credentials = [
        ('guest', 'guest123', 'Development/Testing'),
        ('client', 'client123', 'Client User'),
        ('investor', 'investor123', 'Investor User'),
        ('admin', 'admin123', 'Production Admin (GCP patches)'),
    ]
    
    all_passed = True
    for username, password, description in credentials:
        user = RBACManager.authenticate(username, password)
        
        if user:
            print(f"✅ {description:35s} - {username}/{password}")
        else:
            print(f"❌ {description:35s} - {username}/{password} FAILED")
            all_passed = False
    
    if all_passed:
        print("\n✅ All credential tests passed!")
        return True
    else:
        print("\n❌ Some credential tests failed!")
        return False


def run_all_tests():
    """Run all RBAC page access tests"""
    print("\n" + "="*70)
    print("RBAC PAGE ACCESS TEST SUITE")
    print("="*70)
    print("\nTesting updated RBAC system with page-based access control")
    print("Date: December 9, 2025")
    
    tests = [
        ("Credentials", test_credentials),
        ("Agreement Types", test_agreement_types),
        ("Compliance Requirements", test_compliance_requirements),
        ("Permission Mapping", test_permission_mapping),
        ("Page Access Permissions", test_page_access_permissions),
    ]
    
    results = []
    for test_name, test_func in tests:
        results.append(test_func())
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! RBAC page access is correctly configured.")
        print("\n📋 Access Summary:")
        print("   • Guest (Dev/Testing): Pages 1-6")
        print("   • Client (Asset Mgmt): Pages 1-4")
        print("   • Investor (Investor Mgmt/PPM): Pages 1-5")
        print("   • Admin (Production): Pages 1-6 + Admin panel")
        print("\n🔐 Production Credentials:")
        print("   • Development: guest/guest123")
        print("   • GCP Patches: admin/admin123")
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED. Please review the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
