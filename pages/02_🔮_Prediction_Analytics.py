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
import os

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

# Kalshi API credentials from environment
KALSHI_API_KEY = os.getenv("KALSHI_ACCESS_KEY", "")
KALSHI_PRIVATE_KEY = os.getenv("KALSHI_PRIVATE_KEY", "")

@st.cache_data(ttl=300)
def fetch_kalshi_portfolio():
    """Fetch user's Kalshi portfolio/positions"""
    if not KALSHI_API_KEY:
        return pd.DataFrame(columns=['Contract', 'Quantity', 'Entry Price', 'Current Price', 'P&L', 'P&L %'])
    
    try:
        client = KalshiClient(api_key=KALSHI_API_KEY)
        positions = client.get_user_portfolio()
        
        if positions:
            portfolio_list = []
            for pos in positions:
                # Extract position data from Kalshi API response
                contract_name = pos.get('market_title', pos.get('ticker', 'Unknown'))
                quantity = pos.get('position', 0)
                entry_price = pos.get('purchase_price', 0)
                current_price = pos.get('current_price', entry_price)
                
                # Calculate P&L
                cost_basis = quantity * entry_price
                current_value = quantity * current_price
                pnl = current_value - cost_basis
                pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
                
                portfolio_list.append({
                    'Contract': contract_name,
                    'Quantity': quantity,
                    'Entry Price': f"${entry_price:.2f}",
                    'Current Price': f"${current_price:.2f}",
                    'P&L': f"${pnl:.2f}",
                    'P&L %': f"{pnl_pct:+.2f}%"
                })
            
            return pd.DataFrame(portfolio_list)
    except Exception as e:
        st.warning(f"Could not fetch Kalshi portfolio: {e}")
    
    return pd.DataFrame(columns=['Contract', 'Quantity', 'Entry Price', 'Current Price', 'P&L', 'P&L %'])

@st.cache_data(ttl=300)
def fetch_kalshi_active_markets():
    """Fetch active Kalshi markets"""
    if not PREDICTION_MODULE_AVAILABLE:
        return pd.DataFrame()
    
    try:
        client = KalshiClient(api_key=KALSHI_API_KEY)
        markets = client.get_active_markets()
        
        if markets:
            contracts_list = []
            for market in markets[:10]:  # Limit to 10 for display
                contracts_list.append({
                    'Contract': market.get('title', 'N/A'),
                    'Platform': 'Kalshi',
                    'Current Price': market.get('close_price', 'N/A'),
                    'Volume (24h)': market.get('volume', 'N/A'),
                    'Expires': market.get('expiration_date', 'N/A'),
                    'Status': market.get('status', 'N/A')
                })
            return pd.DataFrame(contracts_list)
    except Exception as e:
        st.warning(f"Could not fetch live Kalshi data: {e}")
    
    return pd.DataFrame()

# Main content - Metrics with improved visibility
st.markdown(f"""
<style>
    .metric-container {{
        display: flex;
        gap: 1.5rem;
        margin: 1rem 0;
    }}
    .metric-card {{
        flex: 1;
        background: {COLOR_SCHEME['card_background']};
        border-radius: 0.5rem;
        padding: 1.5rem;
        border-left: 3px solid {COLOR_SCHEME['accent_teal']};
    }}
    .metric-label {{
        color: #E5E7EB;
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }}
    .metric-value {{
        color: {COLOR_SCHEME['accent_gold']};
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.25rem;
    }}
    .metric-change {{
        color: #10B981;
        font-size: 0.875rem;
    }}
    .tab-header {{
        color: #F3F4F6 !important;
        font-weight: 600;
    }}
</style>
""", unsafe_allow_html=True)

# Fetch portfolio data
kalshi_portfolio = fetch_kalshi_portfolio()
portfolio_value = len(kalshi_portfolio)
portfolio_pnl = kalshi_portfolio['P&L %'].sum() if len(kalshi_portfolio) > 0 else 0

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Active Markets</div>
        <div class='metric-value'>24</div>
        <div class='metric-change'>+3 this week</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>My Kalshi Positions</div>
        <div class='metric-value'>{portfolio_value}</div>
        <div class='metric-change'>Portfolio Active</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    pnl_color = "#10B981" if portfolio_pnl >= 0 else "#EF4444"
    pnl_sign = "+" if portfolio_pnl >= 0 else ""
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>Portfolio P&L</div>
        <div class='metric-value' style='color: {pnl_color};'>{pnl_sign}{portfolio_pnl:.1f}%</div>
        <div class='metric-change' style='color: {pnl_color};'>Real-time tracking</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Tabs for different views
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Active Markets",
    "💼 My Portfolio",
    "📈 Probability Engine",
    "💬 Sentiment Analysis"
])

with tab1:
    st.markdown("<h3 style='color: #F3F4F6;'>Polymarket & Kalshi Contracts</h3>", unsafe_allow_html=True)
    
    if PREDICTION_MODULE_AVAILABLE:
        st.info("🔄 Loading your Kalshi markets...")
        
        # Fetch live Kalshi data only
        live_kalshi = fetch_kalshi_active_markets()
        
        if not live_kalshi.empty:
            st.success(f"✅ Showing {len(live_kalshi)} active Kalshi markets")
            st.dataframe(live_kalshi, use_container_width=True)
        else:
            st.warning("⚠️ No active Kalshi markets found. Check your API credentials.")
            if not KALSHI_API_KEY:
                st.error("❌ KALSHI_ACCESS_KEY not configured in environment")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Markets"):
                st.cache_data.clear()
                st.success("Markets refreshed!")
                st.rerun()
        
        with col2:
            platform_filter = st.selectbox("Platform", ["All", "Polymarket", "Kalshi"], key="platform_tab1")
    else:
        st.warning("⚠️ Prediction analytics module not available. Install dependencies:")
        st.code("pip install prediction-analytics", language="bash")

with tab2:
    st.markdown("<h3 style='color: #F3F4F6;'>Your Kalshi Portfolio</h3>", unsafe_allow_html=True)
    
    if not kalshi_portfolio.empty:
        # Display portfolio positions
        st.markdown(f"""
        <div style='background: {COLOR_SCHEME['card_background']}; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;'>
            <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;'>
                <div>
                    <div style='color: #9CA3AF; font-size: 0.875rem;'>Total Positions</div>
                    <div style='color: {COLOR_SCHEME['accent_gold']}; font-size: 1.5rem; font-weight: bold;'>{len(kalshi_portfolio)}</div>
                </div>
                <div>
                    <div style='color: #9CA3AF; font-size: 0.875rem;'>Portfolio Value</div>
                    <div style='color: {COLOR_SCHEME['accent_teal']}; font-size: 1.5rem; font-weight: bold;'>${kalshi_portfolio['Entry Price'].sum() if 'Entry Price' in kalshi_portfolio.columns else 0:,.0f}</div>
                </div>
                <div>
                    <div style='color: #9CA3AF; font-size: 0.875rem;'>Total P&L</div>
                    <div style='color: {"#10B981" if portfolio_pnl >= 0 else "#EF4444"}; font-size: 1.5rem; font-weight: bold;'>{portfolio_pnl:+.2f}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display positions table
        st.dataframe(kalshi_portfolio, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 View Detailed P&L Analysis"):
                st.info("Detailed analysis coming soon...")
        with col2:
            if st.button("🔄 Sync Kalshi Account"):
                st.success("Account synced!")
                st.cache_data.clear()
                st.rerun()
    else:
        st.info("""
        ### 💼 Portfolio Status: Empty
        
        You haven't synced any Kalshi investments yet. To view your positions:
        1. Make sure your **KALSHI_ACCESS_KEY** is configured in your environment
        2. Click the **"🔄 Sync Kalshi Account"** button above
        3. Your positions will appear here automatically
        
        **Manual Portfolio Upload:** You can also upload a CSV file with additional portfolio data:
        """)
        
        uploaded_file = st.file_uploader("Upload Kalshi Portfolio CSV", type=['csv'])
        if uploaded_file:
            try:
                portfolio_df = pd.read_csv(uploaded_file)
                st.success("Portfolio uploaded successfully!")
                st.dataframe(portfolio_df, use_container_width=True)
                st.session_state.kalshi_portfolio = portfolio_df
            except Exception as e:
                st.error(f"Error uploading portfolio: {e}")

with tab3:
    st.markdown("<h3 style='color: #F3F4F6;'>Probability Predictions</h3>", unsafe_allow_html=True)
    
    st.info("📊 ML Probability Engine - Coming Soon")
    st.markdown("""
    <div style='color: #F3F4F6; margin-top: 1rem;'>
        <strong>Planned Features:</strong><br>
        • Machine learning predictions for market outcomes<br>
        • Confidence scores and edge detection<br>
        • Comparison with market-implied probabilities<br>
        • Arbitrage opportunity alerts
    </div>
    """, unsafe_allow_html=True)

with tab4:
    st.markdown("<h3 style='color: #F3F4F6;'>Sentiment Analysis</h3>", unsafe_allow_html=True)
    
    st.info("💬 Market Sentiment Engine - Coming Soon")
    st.markdown("""
    <div style='color: #F3F4F6; margin-top: 1rem;'>
        <strong>Planned Features:</strong><br>
        • News and social media sentiment aggregation<br>
        • On-chain activity analysis<br>
        • Sentiment strength scoring<br>
        • Multi-source data correlation
    </div>
    """, unsafe_allow_html=True)

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
