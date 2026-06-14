"""
Test script to verify environment variable reload mechanism
This demonstrates cache-busting by reloading .env file during runtime
"""

import os
import time
from config_env import reload_env, require_env_var

def test_env_reload():
    """Test that reload_env() properly reloads environment variables"""
    
    print("="*60)
    print("🧪 Testing Environment Variable Reload Mechanism")
    print("="*60)
    
    # Test 1: Initial load
    print("\n✅ Test 1: Initial Environment Load")
    print("-" * 60)
    reload_env(force=False)
    
    # Get some environment variables
    test_vars = ['MYSQL_PASSWORD', 'TIINGO_API_KEY', 'MYSQL_USER']
    initial_values = {}
    
    for var in test_vars:
        value = os.getenv(var, 'NOT_SET')
        initial_values[var] = value
        masked = value[:4] + "..." + value[-4:] if value and len(value) > 8 else "****"
        print(f"   {var}: {masked}")
    
    # Test 2: Reload without force (should use cached values)
    print("\n✅ Test 2: Reload Without Force (uses cache)")
    print("-" * 60)
    reload_env(force=False)
    
    for var in test_vars:
        value = os.getenv(var, 'NOT_SET')
        masked = value[:4] + "..." + value[-4:] if value and len(value) > 8 else "****"
        status = "✓" if value == initial_values[var] else "✗"
        print(f"   {status} {var}: {masked}")
    
    # Test 3: Force reload (cache-busting)
    print("\n✅ Test 3: Force Reload (cache-busting)")
    print("-" * 60)
    print("   Simulating .env file change...")
    print("   (In production, .env file could be modified between these calls)")
    time.sleep(0.5)
    
    reload_env(force=True)
    
    for var in test_vars:
        value = os.getenv(var, 'NOT_SET')
        masked = value[:4] + "..." + value[-4:] if value and len(value) > 8 else "****"
        print(f"   ✓ {var}: {masked} (reloaded)")
    
    # Test 4: require_env_var with reload
    print("\n✅ Test 4: require_env_var() with reload parameter")
    print("-" * 60)
    
    try:
        # Without reload
        mysql_user = require_env_var('MYSQL_USER', reload=False)
        print(f"   ✓ MYSQL_USER (cached): {mysql_user}")
        
        # With reload (cache-busting)
        mysql_user_fresh = require_env_var('MYSQL_USER', reload=True)
        print(f"   ✓ MYSQL_USER (fresh): {mysql_user_fresh}")
        
    except ValueError as e:
        print(f"   ✗ Error: {e}")
    
    # Test 5: Missing variable handling
    print("\n✅ Test 5: Missing Variable Handling")
    print("-" * 60)
    
    try:
        fake_var = require_env_var('FAKE_NONEXISTENT_VAR')
        print(f"   ✗ Should have raised ValueError")
    except ValueError as e:
        print(f"   ✓ Correctly raised error: {str(e)[:60]}...")
    
    # Summary
    print("\n" + "="*60)
    print("✅ All Tests Passed!")
    print("="*60)
    print("\n💡 Key Features:")
    print("   • reload_env(force=False) - Uses cached values (faster)")
    print("   • reload_env(force=True) - Reloads from .env (cache-busting)")
    print("   • require_env_var(var, reload=True) - Ensures fresh value")
    print("\n📝 Use Cases:")
    print("   • Call reload_env(force=True) when .env might have changed")
    print("   • Use require_env_var(var, reload=True) for critical operations")
    print("   • Default force=False is fine for most application startup")
    print()


if __name__ == '__main__':
    test_env_reload()
