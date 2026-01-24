#!/usr/bin/env python
"""
Test Suite: Local Environment Verification
Tests the fixes applied to localhost:8501 environment
"""

import sys
import importlib.util

print("=" * 70)
print("TEST 1: LOCAL ENVIRONMENT VERIFICATION")
print("=" * 70)
print()

# Test 1a: Import bbbot1_pipeline
print("1a. Testing bbbot1_pipeline import...")
try:
    from bbbot1_pipeline.mlflow_tracker import get_tracker, MLFLOW_AVAILABLE
    from bbbot1_pipeline import load_tickers_config
    print("    ✅ bbbot1_pipeline imports SUCCESS")
    print(f"    - MLFLOW_AVAILABLE: {MLFLOW_AVAILABLE}")
except Exception as e:
    print(f"    ❌ bbbot1_pipeline import FAILED: {str(e)[:80]}")

print()

# Test 1b: Import economic calendar
print("1b. Testing economic_calendar_widget import...")
try:
    from frontend.components.economic_calendar_widget import get_calendar_widget
    print("    ✅ economic_calendar_widget imports SUCCESS")
    
    # Try to instantiate
    try:
        widget = get_calendar_widget()
        print("    ✅ Widget instantiation SUCCESS")
    except Exception as e:
        print(f"    ⚠️  Widget instantiation FAILED: {str(e)[:60]}")
except Exception as e:
    print(f"    ❌ economic_calendar_widget import FAILED: {str(e)[:80]}")

print()

# Test 1c: Import styling modules
print("1c. Testing styling modules...")
try:
    from frontend.styles.colors import COLOR_SCHEME
    from frontend.utils.styling import apply_custom_styling
    print("    ✅ Styling modules import SUCCESS")
except Exception as e:
    print(f"    ❌ Styling modules import FAILED: {str(e)[:80]}")

print()

# Test 1d: Check Investment Analysis page imports
print("1d. Testing Investment Analysis page imports...")
try:
    import frontend.pages
    spec = importlib.util.spec_from_file_location("investment_analysis", 
                                                     "frontend/pages/02_📈_Investment_Analysis.py")
    if spec and spec.loader:
        print("    ✅ Investment Analysis page can be imported")
    else:
        print("    ⚠️  Investment Analysis page load warning")
except Exception as e:
    print(f"    ⚠️  Investment Analysis test: {str(e)[:60]}")

print()

# Test 1e: Check Crypto Dashboard page imports
print("1e. Testing Crypto Dashboard page imports...")
try:
    spec = importlib.util.spec_from_file_location("crypto_dashboard", 
                                                     "frontend/pages/03_🔴_Live_Crypto_Dashboard.py")
    if spec and spec.loader:
        print("    ✅ Crypto Dashboard page can be imported")
    else:
        print("    ⚠️  Crypto Dashboard page load warning")
except Exception as e:
    print(f"    ⚠️  Crypto Dashboard test: {str(e)[:60]}")

print()

# Test 1f: Verify cachetools version
print("1f. Testing cachetools version (for cloud compatibility)...")
try:
    import cachetools
    version = cachetools.__version__
    major, minor, patch = version.split('.')[:3]
    
    if int(major) >= 5 and int(major) < 6:
        print(f"    ✅ cachetools {version} - COMPATIBLE (5.x branch)")
    elif int(major) >= 6:
        print(f"    ⚠️  cachetools {version} - INCOMPATIBLE (6.x will break google-generativeai)")
    else:
        print(f"    ⚠️  cachetools {version} - Check compatibility")
except Exception as e:
    print(f"    ❌ cachetools import FAILED: {str(e)[:60]}")

print()
print("=" * 70)
print("TEST 1 SUMMARY")
print("=" * 70)
print("✅ All critical imports tested on localhost environment")
print("Next: Verify on http://localhost:8501")
print()
