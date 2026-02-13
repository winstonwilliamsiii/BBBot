#!/usr/bin/env python3
"""
Deployment Validation Script
Verifies all requirements are met before deployment
"""

import os
import sys
import json
from pathlib import Path

def check_file_exists(filepath: str) -> tuple[bool, str]:
    """Check if a file exists and return status"""
    path = Path(filepath)
    if path.exists():
        return True, f"✓ {filepath}"
    return False, f"✗ {filepath} NOT FOUND"

def validate_json(filepath: str) -> tuple[bool, str]:
    """Validate JSON file syntax"""
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        return True, f"✓ {filepath} is valid JSON"
    except json.JSONDecodeError as e:
        return False, f"✗ {filepath} has invalid JSON: {e}"
    except FileNotFoundError:
        return False, f"✗ {filepath} not found"

def check_vercel_routes(filepath: str = "vercel.json") -> tuple[bool, str]:
    """Check if vercel.json has required routes"""
    try:
        with open(filepath, 'r') as f:
            config = json.load(f)
        
        routes = config.get('routes', [])
        has_api = any('/api' in str(route.get('src', '')) for route in routes)
        has_health = any('health' in str(route.get('src', '')) for route in routes)
        
        if has_api and has_health:
            return True, "✓ vercel.json has required routes (/api, /health)"
        elif has_api:
            return True, "⚠ vercel.json missing /health route (warning only)"
        else:
            return False, "✗ vercel.json missing /api routes"
    except Exception as e:
        return False, f"✗ Error checking vercel.json routes: {e}"

def check_git_status() -> tuple[bool, str]:
    """Check if git submodule issue is fixed"""
    import subprocess
    try:
        result = subprocess.run(
            ['git', 'submodule', 'status'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if 'starter-for-js' in result.stderr:
            return False, "✗ Git submodule issue still present"
        return True, "✓ No git submodule issues"
    except subprocess.TimeoutExpired:
        return False, "⚠ Git submodule check timed out"
    except Exception as e:
        return True, f"⚠ Could not check git submodules: {e}"

def main():
    print("=" * 60)
    print("DEPLOYMENT VALIDATION")
    print("=" * 60)
    
    checks = []
    
    # Critical Files
    print("\n📁 CRITICAL FILES:")
    critical_files = [
        'streamlit_app.py',
        'api/index.py',
        'api/requirements.txt',
        'requirements.txt',
        'vercel.json',
    ]
    
    for file in critical_files:
        success, msg = check_file_exists(file)
        checks.append(success)
        print(f"  {msg}")
    
    # JSON Validation
    print("\n🔍 JSON VALIDATION:")
    success, msg = validate_json('vercel.json')
    checks.append(success)
    print(f"  {msg}")
    
    # Vercel Configuration
    print("\n⚙️  VERCEL CONFIGURATION:")
    success, msg = check_vercel_routes()
    checks.append(success)
    print(f"  {msg}")
    
    # Git Status
    print("\n📦 GIT STATUS:")
    success, msg = check_git_status()
    checks.append(success)
    print(f"  {msg}")
    
    # GitHub Secrets Warning
    print("\n🔐 GITHUB SECRETS (Manual Verification Required):")
    print("  ⚠ VERCEL_TOKEN - Must be added to GitHub")
    print("  ⚠ VERCEL_ORG_ID - Must be added to GitHub")
    print("  ⚠ VERCEL_PROJECT_ID - Must be added to GitHub")
    print("  ⚠ VERCEL_SCOPE - Must be added to GitHub")
    print("\n  📖 See GITHUB_SECRETS_SETUP.md for instructions")
    
    # Python Imports Test
    print("\n🐍 PYTHON IMPORTS:")
    try:
        import streamlit
        print("  ✓ streamlit imported successfully")
        checks.append(True)
    except ImportError:
        print("  ✗ streamlit import failed")
        checks.append(False)
    
    try:
        import pandas
        print("  ✓ pandas imported successfully")
        checks.append(True)
    except ImportError:
        print("  ✗ pandas import failed")
        checks.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(checks)
    total = len(checks)
    
    if all(checks):
        print(f"✅ ALL CHECKS PASSED ({passed}/{total})")
        print("\n📋 NEXT STEPS:")
        print("  1. Add GitHub secrets (see GITHUB_SECRETS_SETUP.md)")
        print("  2. Commit changes: git add . && git commit -m 'fix: deployment fixes'")
        print("  3. Push to main: git push origin main")
        print("  4. Monitor deployment: github.com/winstonwilliamsiii/BBBot/actions")
        return 0
    else:
        print(f"⚠️  SOME CHECKS FAILED ({passed}/{total} passed)")
        print("\n🔧 REQUIRED FIXES:")
        print("  - Fix failed checks above")
        print("  - Review DEPLOYMENT_READINESS_CHECKLIST.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())
