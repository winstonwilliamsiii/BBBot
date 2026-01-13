"""Quick test of the budget page imports and RBAC"""
import sys
import os

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("Testing Budget Page RBAC...")

try:
    from frontend.utils.rbac import RBACManager, Permission, show_login_form, show_user_info
    print("[OK] RBAC imports successful")
    
    from frontend.components.budget_dashboard import show_full_budget_dashboard
    print("[OK] Budget dashboard import successful")
    
    # Test static method
    print(f"[OK] has_permission exists: {hasattr(RBACManager, 'has_permission')}")
    
    # Test calling it (should return False when not authenticated)
    result = RBACManager.has_permission(Permission.VIEW_BUDGET)
    print(f"[OK] has_permission(VIEW_BUDGET) = {result}")
    
    print("\n SUCCESS - All imports and methods work!")
    
except Exception as e:
    print(f"\n FAILED: {e}")
    import traceback
    traceback.print_exc()
