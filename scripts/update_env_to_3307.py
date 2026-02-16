#!/usr/bin/env python3
"""
.env Configuration Updater
Updates all MySQL port references to use Port 3307 (consolidated instance)
Author: Bentley Budget Bot Development Team
"""
import os
import re
from datetime import datetime

def backup_env_file(env_path):
    """Create a timestamped backup of .env file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{env_path}.backup_{timestamp}"
    
    with open(env_path, 'r') as src:
        with open(backup_path, 'w') as dst:
            dst.write(src.read())
    
    return backup_path

def update_env_file(env_path):
    """Update .env file to use Port 3307 for all MySQL connections"""
    
    # Read current .env content
    with open(env_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Changes to make
    changes = []
    
    # 1. Update BUDGET_MYSQL_PORT from 3306 to 3307
    old_budget = "BUDGET_MYSQL_PORT=3306"
    new_budget = "BUDGET_MYSQL_PORT=3307"
    if old_budget in content:
        content = content.replace(old_budget, new_budget)
        changes.append(f"   ✅ BUDGET_MYSQL_PORT: 3306 → 3307")
    
    # 2. Update BBBOT1_MYSQL_PORT from 3306 to 3307
    old_bbbot = "BBBOT1_MYSQL_PORT=3306"
    new_bbbot = "BBBOT1_MYSQL_PORT=3307"
    if old_bbbot in content:
        content = content.replace(old_bbbot, new_bbbot)
        changes.append(f"   ✅ BBBOT1_MYSQL_PORT: 3306 → 3307")
    
    # 3. Ensure MYSQL_PORT is 3307 (should already be)
    if "MYSQL_PORT=3307" in content:
        changes.append(f"   ✓ MYSQL_PORT: Already 3307")
    
    # 4. Update BUDGET_MYSQL_DATABASE to point to consolidated instance
    # Note: mydb should now be on Port 3307 after migration
    
    # Write updated content if changes were made
    if content != original_content:
        with open(env_path, 'w') as f:
            f.write(content)
        return True, changes
    else:
        return False, ["   No changes needed - already configured correctly"]

def verify_env_configuration(env_path):
    """Verify all MySQL ports are set to 3307"""
    with open(env_path, 'r') as f:
        content = f.read()
    
    issues = []
    
    # Check for any remaining references to Port 3306
    if re.search(r'MYSQL_PORT=3306(?!\d)', content):
        issues.append("⚠️  Found MYSQL_PORT=3306")
    if "BUDGET_MYSQL_PORT=3306" in content:
        issues.append("⚠️  Found BUDGET_MYSQL_PORT=3306")
    if "BBBOT1_MYSQL_PORT=3306" in content:
        issues.append("⚠️  Found BBBOT1_MYSQL_PORT=3306")
    
    # Verify Port 3307 is configured
    configs = []
    if re.search(r'MYSQL_PORT=3307', content):
        configs.append("✅ MYSQL_PORT=3307")
    if re.search(r'BUDGET_MYSQL_PORT=3307', content):
        configs.append("✅ BUDGET_MYSQL_PORT=3307")
    if re.search(r'BBBOT1_MYSQL_PORT=3307', content):
        configs.append("✅ BBBOT1_MYSQL_PORT=3307")
    
    return issues, configs

if __name__ == "__main__":
    print("=" * 100)
    print(".ENV CONFIGURATION UPDATER")
    print("Consolidating all MySQL connections to Port 3307")
    print("=" * 100)
    print()
    
    env_path = ".env"
    
    # Check if .env exists
    if not os.path.exists(env_path):
        print(f"❌ ERROR: {env_path} not found")
        print("   Please ensure you're running this from the project root")
        exit(1)
    
    print(f"📄 Found: {env_path}")
    
    # Step 1: Create backup
    print("\n🔄 Step 1: Creating backup...")
    backup_path = backup_env_file(env_path)
    print(f"   ✅ Backup created: {backup_path}")
    
    # Step 2: Check current configuration
    print("\n🔍 Step 2: Analyzing current configuration...")
    issues_before, configs_before = verify_env_configuration(env_path)
    
    if issues_before:
        print("   Current issues:")
        for issue in issues_before:
            print(f"      {issue}")
    else:
        print("   ✅ No Port 3306 references found")
    
    if configs_before:
        print("   Current Port 3307 configs:")
        for config in configs_before:
            print(f"      {config}")
    
    # Step 3: Update configuration
    print("\n🔧 Step 3: Updating configuration...")
    updated, changes = update_env_file(env_path)
    
    if updated:
        print("   Changes applied:")
        for change in changes:
            print(change)
    else:
        print("   No changes needed")
        for msg in changes:
            print(msg)
    
    # Step 4: Verify updates
    print("\n✅ Step 4: Verifying configuration...")
    issues_after, configs_after = verify_env_configuration(env_path)
    
    if issues_after:
        print("   ⚠️  Remaining issues:")
        for issue in issues_after:
            print(f"      {issue}")
    else:
        print("   ✅ All MySQL ports configured to use 3307")
    
    if configs_after:
        print("\n   Final configuration:")
        for config in configs_after:
            print(f"      {config}")
    
    # Summary
    print("\n" + "=" * 100)
    print("📊 SUMMARY")
    print("=" * 100)
    
    if not issues_after:
        print("\n🎉 CONFIGURATION UPDATE SUCCESSFUL!")
        print("\n✅ All MySQL connections now point to Port 3307")
        print(f"💾 Backup saved: {backup_path}")
        print("\n📋 Next Steps:")
        print("   1. Restart any running services (Streamlit, APIs, etc.)")
        print("   2. Run: python test_api_connections.py")
        print("   3. Verify Plaid, Alpaca, and Tiingo connections")
    else:
        print("\n⚠️  CONFIGURATION UPDATE INCOMPLETE")
        print("   Manual review needed for remaining issues")
        print(f"\n💾 Original backed up to: {backup_path}")
        print("   To restore: cp {backup_path} .env")
    
    print("\n" + "=" * 100)
