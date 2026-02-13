"""
BentleyBudgetBot Multi-Page Dashboard
Main entry point with navigation to all pages

Pages:
- 01_💰_Personal_Budget.py
- 02_📈_Investment_Analysis.py
- 03_🔴_Live_Crypto_Dashboard.py
- 04_💼_Broker_Trading.py
- 05_🤖_Trading_Bot.py
"""

import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except Exception:
    yf = None
    YFINANCE_AVAILABLE = False

from datetime import date, timedelta
from frontend.utils.styling import (
    apply_custom_styling,
    create_custom_card,
    create_metric_card,
    add_footer,
)
from frontend.styles.colors import COLOR_SCHEME

# Import Appwrite services for backend integration
try:
    from services.transactions import create_transaction, get_transactions
    from services.watchlist import add_to_watchlist, get_watchlist
    APPWRITE_SERVICES_AVAILABLE = True
except ImportError:
    APPWRITE_SERVICES_AVAILABLE = False

# RBAC imports
try:
    from frontend.utils.rbac import RBACManager, Permission, show_login_form, show_user_info
    RBAC_AVAILABLE = True
except ImportError:
    RBAC_AVAILABLE = False

# Configure page
st.set_page_config(
    page_title="BentleyBudgetBot",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styling
apply_custom_styling()

# Main Page Header
st.title("🏦 BentleyBudgetBot Dashboard")
st.markdown("### Your Personal Finance Command Center")

# Show RBAC Login/User Info
if RBAC_AVAILABLE:
    show_login_form()
    show_user_info()
else:
    st.warning("⚠️ RBAC not available. Running in open mode.")

st.markdown("---")

# Welcome Section
col1, col2, col3 = st.columns(3)

with col1:
    create_metric_card(
        "💰 Budget Management",
        "Track expenses & income",
        "View Budget Page →"
    )
    st.markdown("Monitor your personal finances with detailed budget analysis.")

with col2:
    create_metric_card(
        "📈 Investment Portfolio",
        "Analyze your holdings",
        "View Investments →"
    )
    st.markdown("Track stocks, ETFs, and portfolio performance.")

with col3:
    create_metric_card(
        "🔴 Live Crypto",
        "Real-time crypto tracking",
        "View Crypto →"
    )
    st.markdown("Monitor cryptocurrency prices and trends.")

st.markdown("---")

# Quick Actions Section
st.header("⚡ Quick Actions")

tab1, tab2, tab3 = st.tabs(["💸 Transactions", "📊 Watchlist", "🤖 Bot Status"])

with tab1:
    if APPWRITE_SERVICES_AVAILABLE:
        st.subheader("Recent Transactions")
        user_id = st.text_input("User ID", key="user_id_tx")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("📥 View Transactions"):
                if user_id:
                    with st.spinner("Fetching transactions..."):
                        txs = get_transactions(user_id, limit=10)
                        if txs.get("success"):
                            st.success(f"Found {len(txs.get('transactions', []))} transactions")
                            st.json(txs["transactions"])
                        else:
                            st.error(txs.get("error", "Failed to fetch transactions"))
                else:
                    st.warning("Please enter a User ID")
        
        with col_b:
            st.subheader("Add New Transaction")
            amount = st.number_input("Amount ($)", min_value=0.01, step=0.01)
            date_input = st.date_input("Date")
            description = st.text_input("Description")
            
            if st.button("➕ Add Transaction"):
                if user_id and amount:
                    result = create_transaction(user_id, amount, str(date_input))
                    if result.get("success"):
                        st.success("✅ Transaction added!")
                    else:
                        st.error(result.get("error", "Failed to add transaction"))
                else:
                    st.warning("User ID and amount required")
    else:
        st.info("💡 Appwrite services not configured. Add your Function IDs to `.env` to enable transactions.")

with tab2:
    if APPWRITE_SERVICES_AVAILABLE:
        st.subheader("Stock Watchlist")
        user_id_wl = st.text_input("User ID", key="user_id_wl")
        
        col_c, col_d = st.columns(2)
        
        with col_c:
            symbol = st.text_input("Symbol (e.g., AAPL, TSLA)")
            if st.button("➕ Add to Watchlist"):
                if user_id_wl and symbol:
                    result = add_to_watchlist(user_id_wl, symbol)
                    if result.get("success"):
                        st.success(f"✅ Added {symbol} to watchlist!")
                    else:
                        st.error(result.get("error", "Failed to add symbol"))
                else:
                    st.warning("User ID and symbol required")
        
        with col_d:
            if st.button("📋 View Watchlist"):
                if user_id_wl:
                    wl = get_watchlist(user_id_wl)
                    if wl.get("success"):
                        st.success(f"Found {len(wl.get('watchlist', []))} items")
                        st.json(wl["watchlist"])
                    else:
                        st.error(wl.get("error", "Failed to fetch watchlist"))
                else:
                    st.warning("Please enter a User ID")
    else:
        st.info("💡 Appwrite services not configured. Add your Function IDs to `.env` to enable watchlist.")

with tab3:
    st.subheader("Trading Bot Status")
    create_custom_card("🤖 Bot Status", "Visit the Trading Bot page for full controls")
    st.info("Navigate to **🤖 Trading Bot** page in the sidebar for detailed bot management.")

st.markdown("---")

# Navigation Guide
st.header("📑 Available Pages")
st.markdown("""
Navigate using the **sidebar** to access:

1. **💰 Personal Budget** - Expense tracking and budget analysis
2. **📈 Investment Analysis** - Portfolio performance and stock analysis
3. **🔴 Live Crypto Dashboard** - Real-time cryptocurrency monitoring
4. **💼 Broker Trading** - Trading account integration
5. **🤖 Trading Bot** - Automated trading strategies and controls

---

**Need Help?** Check the documentation or contact support.
""")

# Footer
add_footer()
