"""
Multi-Broker Trading Hub Page
Unified interface for MT5, Alpaca, and IBKR
"""

import streamlit as st
from frontend.components.multi_broker_dashboard import render_multi_broker_dashboard
from frontend.utils.rbac import RBACManager, Permission, show_login_form, show_user_info

st.set_page_config(
    page_title="Multi-Broker Trading - Bentley Bot",
    page_icon="🌐",
    layout="wide"
)
RBACManager.init_session_state()
show_user_info()
if not RBACManager.is_authenticated() or not RBACManager.has_permission(Permission.VIEW_TRADING_BOT):
    st.error("🚫 ADMIN access required")
    show_login_form()
    st.stop()
render_multi_broker_dashboard()
