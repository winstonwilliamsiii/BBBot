import streamlit as st
import sys
import os
from datetime import datetime

st.set_page_config(page_title="BBBot Health Check", page_icon="🏥", layout="wide")

def check_system():
    checks = {}
    
    # Python environment
    checks["Python Version"] = sys.version.split()[0]
    checks["Working Directory"] = os.getcwd()
    checks["Virtual Environment"] = "Active" if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else "Not Active"
    
    # Dependencies
    try:
        import streamlit
        checks["Streamlit"] = f"✅ v{streamlit.__version__}"
    except ImportError:
        checks["Streamlit"] = "❌ Missing"
    
    try:
        import yfinance
        checks["YFinance"] = "✅ Available"
    except ImportError:
        checks["YFinance"] = "⚠️ Missing (optional)"
    
    try:
        import pandas as pd
        checks["Pandas"] = f"✅ v{pd.__version__}"
    except ImportError:
        checks["Pandas"] = "❌ Missing"
    
    # BBBot modules
    try:
        import streamlit_app
        checks["Main App"] = "✅ Loads successfully"
    except ImportError as e:
        checks["Main App"] = f"❌ Error: {str(e)}"
    
    return checks

def main():
    st.title("🏥 BentleyBudgetBot Health Check")
    st.write(f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    checks = check_system()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 System Info")
        for key, value in list(checks.items())[:4]:
            st.write(f"**{key}:** {value}")
    
    with col2:
        st.subheader("📦 Dependencies")
        for key, value in list(checks.items())[4:]:
            st.write(f"**{key}:** {value}")
    
    # Test main app
    if st.button("🧪 Test Main App"):
        try:
            import streamlit_app
            st.success("✅ Main application loads successfully!")
        except Exception as e:
            st.error(f"❌ Main application error: {str(e)}")
    
    st.markdown("---")
    st.info("If all checks pass, run: `streamlit run streamlit_app.py`")

if __name__ == "__main__":
    main()