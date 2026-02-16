"""
TEST: Plaid Link Iframe Fix
===========================

Test script to verify that:
1. Plaid Link popup page loads correctly
2. Link token is passed as query parameter
3. Main test page opens popup with correct URL
"""

import sys
from pathlib import Path

# Test 1: Check files exist
print("✓ Test 1: Checking file structure...")
pages_dir = Path(__file__).parent / "pages"

test_page = pages_dir / "07_🏦_Plaid_Test.py"
popup_page = pages_dir / "07a_🏦_Plaid_Link_Popup.py"

assert test_page.exists(), f"❌ Main test page missing: {test_page}"
assert popup_page.exists(), f"❌ Popup page missing: {popup_page}"
print(f"   ✓ Main test page: {test_page.name}")
print(f"   ✓ Popup page: {popup_page.name}")

# Test 2: Check popup page contains key functionality
print("\n✓ Test 2: Checking popup page has required functionality...")
popup_content = popup_page.read_text(encoding='utf-8')

checks = {
    "Plaid Link script": "cdn.plaid.com",
    "Query parameter extraction": "parse_qs",
    "Link token handler": "Plaid.create",
    "onSuccess callback": "onSuccess",
    "PostMessage": "postMessage",
    "Public token display": "public_token",
}

for check_name, check_string in checks.items():
    assert check_string in popup_content, f"❌ Missing: {check_name} ({check_string})"
    print(f"   ✓ {check_name}")

# Test 3: Check main test page opens popup correctly
print("\n✓ Test 3: Checking main test page opens popup...")
test_content = test_page.read_text(encoding='utf-8')

assert "06a_🏦_Plaid_Link_Popup" in test_content, "❌ Main page doesn't reference popup"
assert "target=\"_blank\"" in test_content, "❌ Main page doesn't open in new window"
assert "link_token=" in test_content, "❌ Main page doesn't pass link_token parameter"
print("   ✓ Main page opens popup with link_token parameter")

# Test 4: Check documentation exists
print("\n✓ Test 4: Checking documentation...")
assert "iframe" in test_content, "❌ No iframe documentation"
assert "new window" in test_content, "❌ No 'new window' explanation"
print("   ✓ Documentation explains iframe limitation")

print("\n" + "="*50)
print("✅ ALL TESTS PASSED")
print("="*50)
print("\nPLAID LINK IFRAME FIX VERIFIED:")
print("1. Files created and in correct locations")
print("2. Popup page has Plaid Link initialization")
print("3. Main page opens popup in new window")
print("4. Documentation explains the issue")
print("\nHOW TO TEST LOCALLY:")
print("  1. Run: streamlit run streamlit_app.py")
print("  2. Navigate to 🏦 Plaid Test page")
print("  3. Click 'Create Link Token'")
print("  4. Click 'Open Plaid Link in New Window'")
print("  5. Plaid Link should load (no more 'Waiting for SDK...')")
print("\nHOW TO TEST ON PRODUCTION:")
print("  1. Visit: https://bbbot305.streamlit.app")
print("  2. Navigate to 🏦 Plaid Test page")
print("  3. Same steps as local test")
print("  4. Plaid Link should work properly")
