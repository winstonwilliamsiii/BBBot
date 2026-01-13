"""
Multi-Broker Trading Hub Page
Unified interface for MT5, Alpaca, and IBKR
"""

import streamlit as st
from frontend.components.multi_broker_dashboard import render_multi_broker_dashboard

st.set_page_config(
    page_title="Multi-Broker Trading - Bentley Bot",
    page_icon="🌐",
    layout="wide"
)

render_multi_broker_dashboard()
