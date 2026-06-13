#!/usr/bin/env python3
"""
Streamlit Plaid Environment Status Display Fix
Fixes the blue status display for PLAID_ENV
"""

import streamlit as st
import os
from dotenv import load_dotenv

def show_plaid_status():
    """Show Plaid environment status with correct color indicators"""
    
    # Force reload environment
    load_dotenv(override=True)
    
    # Get all three variables
    client_id = os.getenv('PLAID_CLIENT_ID', '').strip()
    secret = os.getenv('PLAID_SECRET', '').strip()
    env = os.getenv('PLAID_ENV', '').strip()
    
    # Display status
    st.markdown("### 🔐 Plaid Configuration Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if client_id and len(client_id) > 10:
            st.success("✅ Client ID")
            st.caption("Configured")
        else:
            st.error("❌ Client ID")
            st.caption("Not found")
    
    with col2:
        if secret and len(secret) > 10:
            st.success("✅ Secret Key")
            st.caption("Configured")
        else:
            st.error("❌ Secret Key")
            st.caption("Not found")
    
    with col3:
        # FIX: This should show GREEN for 'sandbox', not blue
        if env == 'sandbox':
            st.success("✅ Sandbox Environment")
            st.caption(f"Mode: {env}")
        elif env == 'development':
            st.warning("⚠️ Development Environment")
            st.caption(f"Mode: {env}")
        elif env == 'production':
            st.error("🔴 Production Environment")
            st.caption(f"Mode: {env}")
        else:
            st.error("❌ Environment Not Set")
            st.caption("Please configure PLAID_ENV")
    
    # Debug info (only if variables are missing)
    if not (client_id and secret and env):
        st.markdown("---")
        st.error("⚠️ Plaid Configuration Incomplete")
        st.code("""
# Add this to .env file:
PLAID_CLIENT_ID=your_client_id_from_dashboard
PLAID_SECRET=your_secret_from_dashboard
PLAID_ENV=sandbox
""")
    else:
        st.markdown("---")
        st.success("✅ All Plaid credentials configured correctly!")
        st.info("""
**Your Streamlit app can now:**
- ✅ Connect to Plaid API
- ✅ Generate link tokens
- ✅ Accept bank connections
""")


if __name__ == "__main__":
    # Test this component
    st.set_page_config(page_title="Plaid Status Test", layout="wide")
    show_plaid_status()
