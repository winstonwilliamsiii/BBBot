"""
MetaTrader 5 Trading Page
Standalone page for MT5 trading in Bentley Budget Bot
"""

import streamlit as st
from frontend.components.mt5_dashboard import render_mt5_dashboard

st.set_page_config(
    page_title="MT5 Trading - Bentley Bot",
    page_icon="🔌",
    layout="wide"
)

# Render MT5 dashboard
render_mt5_dashboard()
