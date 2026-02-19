"""
MLflow Training Dashboard (Merged)
This page is retained for compatibility and redirects users to Admin Control Center.
"""

import streamlit as st

st.set_page_config(
    page_title="MLflow Training Dashboard (Merged)",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 MLflow Dashboard Merged")
st.info("The standalone MLflow page has been merged into Admin Control Center → 🧠 MLflow tab.")

if st.button("🔧 Open Admin Control Center", type="primary"):
    st.switch_page("pages/99_🔧_Admin_Control_Center.py")
