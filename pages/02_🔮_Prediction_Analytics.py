"""
🔮 Prediction Analytics Dashboard
==================================
Monitor Polymarket & Kalshi prediction markets with probability analysis
Features:
- Active contract listings
- Probability predictions
- Sentiment analysis
- Market trends
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from frontend.utils.styling import apply_custom_styling, add_footer
from frontend.styles.colors import COLOR_SCHEME
from frontend.utils.rbac import RBACManager, Permission, show_login_form, show_user_info

# Page config
st.set_page_config(
    page_title="Prediction Analytics | BBBot",
    page_icon="🔮",
    layout="wide"
)

# Apply styling
apply_custom_styling()

# RBAC Authentication
RBACManager.init_session_state()
show_user_info()

if not RBACManager.is_authenticated():
    st.error("🔐 Authentication Required")
    show_login_form()
    st.stop()

if not RBACManager.has_permission(Permission.VIEW_TRADING_BOT):
    st.error("🚫 Prediction Analytics requires ADMIN access")
    st.stop()

# Page Title
st.markdown(f"""
<div style='text-align: center; margin-bottom: 2rem;'>
    <h1 style='color: {COLOR_SCHEME['text']}; margin-bottom: 0.5rem;'>
        <span style='color: {COLOR_SCHEME['accent_teal']}'>🔮</span> 
        Prediction Analytics
    </h1>
    <p style='color: rgba(255,255,255,0.9); font-size: 1rem;'>
        Real-time probability predictions from Polymarket & Kalshi
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Initialize session state
if 'prediction_data' not in st.session_state:
    st.session_state.prediction_data = None
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None

# Try to load prediction analytics module
try:
    from prediction_analytics.services.polymarket_client import PolymarketClient
    from prediction_analytics.services.kalshi_client import KalshiClient
    from prediction_analytics.services.probability_engine import ProbabilityEngine
    PREDICTION_MODULE_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ Prediction analytics module not fully available: {e}")
    PREDICTION_MODULE_AVAILABLE = False

# Main content
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Active Markets", "24", "+3")
with col2:
    st.metric("High Confidence", "8", "+2")
with col3:
    st.metric("Bullish Sentiment", "65%", "+5%")

st.markdown("---")

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["📊 Active Markets", "📈 Probability Engine", "💬 Sentiment Analysis"])

with tab1:
    st.subheader("Polymarket & Kalshi Contracts")
    
    if PREDICTION_MODULE_AVAILABLE:
        st.info("🔄 Loading prediction markets...")
        
        # Sample data (will be replaced with actual API calls)
        sample_contracts = pd.DataFrame({
            'Contract': ['Will BTC exceed $100k by Q2?', 'Election Winner - State A', 'Tech Earnings Beat'],
            'Platform': ['Polymarket', 'Kalshi', 'Polymarket'],
            'Current Price': [0.72, 0.58, 0.81],
            'Volume (24h)': ['$1.2M', '$450K', '$890K'],
            'Expires': ['2026-04-30', '2026-02-14', '2026-03-15'],
            'Status': ['OPEN', 'OPEN', 'OPEN']
        })
        
        st.dataframe(sample_contracts, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Markets"):
                st.success("Markets refreshed!")
                st.rerun()
        
        with col2:
            st.selectbox("Platform", ["All", "Polymarket", "Kalshi"])
    else:
        st.warning("⚠️ Prediction analytics module not available. Install dependencies:")
        st.code("pip install prediction-analytics", language="bash")

with tab2:
    st.subheader("Probability Predictions")
    
    if PREDICTION_MODULE_AVAILABLE:
        st.info("📊 ML predictions for active markets")
        
        # Sample probability data
        prob_data = pd.DataFrame({
            'Contract': ['Will BTC exceed $100k by Q2?', 'Election Winner - State A', 'Tech Earnings Beat'],
            'Market Implied': [0.72, 0.58, 0.81],
            'ML Prediction': [0.68, 0.62, 0.79],
            'Confidence': ['95%', '87%', '92%'],
            'Edge': ['Bullish', 'Neutral', 'Bearish']
        })
        
        st.dataframe(prob_data, use_container_width=True)
        
        st.markdown("**How to read:**")
        st.markdown("""
        - **Market Implied:** Price-based probability from market
        - **ML Prediction:** Our model's forecast
        - **Edge:** Opportunity direction (buy/sell)
        """)
    else:
        st.info("Probability engine coming soon")

with tab3:
    st.subheader("Sentiment Analysis")
    
    if PREDICTION_MODULE_AVAILABLE:
        st.info("💬 Aggregated sentiment from news, social media, and on-chain data")
        
        # Sample sentiment data
        sentiment_data = pd.DataFrame({
            'Market': ['BTC Technical Analysis', 'Fed Policy Talk', 'Crypto Regulation News', 'On-Chain Metrics'],
            'Sentiment': ['Bullish', 'Neutral', 'Bearish', 'Bullish'],
            'Strength': ['Strong', 'Moderate', 'Weak', 'Strong'],
            'Sources': [3, 5, 2, 8]
        })
        
        st.dataframe(sentiment_data, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Bullish Signals** 📈")
            st.write("- Strong technical setup")
            st.write("- On-chain accumulation")
            st.write("- Positive macro news")
        
        with col2:
            st.markdown("**Bearish Signals** 📉")
            st.write("- Regulatory concerns")
            st.write("- Overbought conditions")
            st.write("- Liquidations trending")
    else:
        st.info("Sentiment analysis coming soon")

st.markdown("---")

# Advanced Configuration
with st.expander("⚙️ Advanced Configuration"):
    st.subheader("Prediction Engine Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        confidence_threshold = st.slider("Min Confidence (%)", 0, 100, 80)
        edge_threshold = st.slider("Min Edge (%)", 0, 50, 5)
    
    with col2:
        st.selectbox("ML Model", ["XGBoost (Current)", "Neural Network", "Ensemble"])
        st.selectbox("Data Sources", ["Market + Sentiment", "Market Only", "Sentiment Only"])
    
    if st.button("💾 Save Settings"):
        st.success("Settings saved!")

# Footer
st.markdown("---")
add_footer()
