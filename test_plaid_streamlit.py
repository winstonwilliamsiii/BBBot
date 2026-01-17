"""
Simple test page for Plaid Link initialization
Run with: streamlit run test_plaid_streamlit.py
"""
import streamlit as st
import sys
import os

# Add frontend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frontend'))

from utils.plaid_link import render_plaid_link_button

st.set_page_config(page_title="Plaid Link Test", page_icon="🔗")

st.title("🔗 Plaid Link Integration Test")

st.write("""
This is a test page to verify Plaid Link initialization.

**Instructions:**
1. Click the "Connect Your Bank" button below
2. In the Plaid modal, search for "Sandbox"
3. Select "Plaid Sandbox"
4. Use credentials: `user_good` / `pass_good`
5. Select accounts to connect
6. Copy the public token when displayed
7. Paste it in the manual form below

**Expected Behavior:**
- Button should initialize and show "Ready to connect"
- Clicking button should open Plaid modal
- After successful connection, you'll see a green success message
- Public token will be displayed in the debug section
""")

st.markdown("---")

# Test with a dummy user ID
test_user_id = "test_user_123"

st.subheader("Plaid Link Button Component")

try:
    render_plaid_link_button(test_user_id)
    st.success("✅ Plaid Link component rendered successfully")
except Exception as e:
    st.error(f"❌ Error rendering Plaid Link: {e}")
    import traceback
    st.code(traceback.format_exc())

st.markdown("---")

st.info("""
**Debug Tips:**
- Open browser console (F12) to see Plaid initialization logs
- Look for messages starting with `[Plaid]`
- Check the "debug" line below the button for status
- If the button stays disabled, check console for SDK loading errors
""")
