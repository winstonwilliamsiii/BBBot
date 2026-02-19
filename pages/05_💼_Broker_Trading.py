"""
Broker Trading Dashboard (Unified)
This page now uses the shared Multi-Broker Trading dashboard implementation.
"""

import streamlit as st
from frontend.components.multi_broker_dashboard import render_multi_broker_dashboard
from frontend.utils.rbac import (
    RBACManager,
    Permission,
    show_login_form,
    show_user_info,
    show_permission_denied,
)

st.set_page_config(
    page_title="Broker Trading - Bentley Bot",
    page_icon="💼",
    layout="wide",
)

RBACManager.init_session_state()
show_user_info()

if not RBACManager.is_authenticated():
    st.error("🔐 Authentication Required")
    show_login_form()
    st.stop()

can_view_broker = RBACManager.has_permission(Permission.VIEW_BROKER_TRADING)
can_view_admin_trading = RBACManager.has_permission(Permission.VIEW_TRADING_BOT)

if not (can_view_broker or can_view_admin_trading):
    show_permission_denied("INVESTOR or ADMIN access")
    st.stop()

render_multi_broker_dashboard()
