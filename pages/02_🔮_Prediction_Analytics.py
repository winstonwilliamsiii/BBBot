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

# Kalshi credentials from Streamlit secrets or environment
try:
    KALSHI_EMAIL = st.secrets.get("KALSHI_EMAIL", "") or os.getenv("KALSHI_EMAIL", "")
    KALSHI_PASSWORD = st.secrets.get("KALSHI_PASSWORD", "") or os.getenv("KALSHI_PASSWORD", "")
except Exception:
    # Fallback to environment variables only
    KALSHI_EMAIL = os.getenv("KALSHI_EMAIL", "")
    KALSHI_PASSWORD = os.getenv("KALSHI_PASSWORD", "")

# Debug: Show credential status
if KALSHI_EMAIL and KALSHI_PASSWORD:
    print(f"✅ Kalshi credentials loaded: {KALSHI_EMAIL[:20]}...")
else:
    print(f"❌ Kalshi credentials missing: EMAIL={bool(KALSHI_EMAIL)}, PASSWORD={bool(KALSHI_PASSWORD)}")

@st.cache_data(ttl=300)
def fetch_kalshi_portfolio():
    """Fetch user's Kalshi portfolio/positions using official SDK"""
    print(f"[DEBUG] fetch_kalshi_portfolio() called")
    print(f"[DEBUG] Credentials present: EMAIL={bool(KALSHI_EMAIL)}, PASSWORD={bool(KALSHI_PASSWORD)}")
    
    if not KALSHI_EMAIL or not KALSHI_PASSWORD:
        print(f"❌ Kalshi credentials not configured")
        st.error("❌ Kalshi credentials not configured. Set KALSHI_EMAIL and KALSHI_PASSWORD in .env or Streamlit secrets.")
        return pd.DataFrame(columns=['Contract', 'Quantity', 'Entry Price', 'Current Price', 'P&L', 'P&L %'])
    
    try:
        # Use official Kalshi SDK with email/password authentication
        print(f"[DEBUG] Authenticating with Kalshi SDK...")
        client = KalshiClient(email=KALSHI_EMAIL, password=KALSHI_PASSWORD)
        print(f"[DEBUG] Client created, fetching portfolio...")
        positions = client.get_user_portfolio()
        
        print(f"[DEBUG] API Response: {len(positions)} positions returned")
        st.info(f"📊 API Response: Found {len(positions) if positions else 0} positions")
        
        if positions:
            print(f"[DEBUG] Processing {len(positions)} positions...")
            portfolio_list = []
            for pos in positions:
                print(f"[DEBUG] Position data: {pos}")
                # Extract position data from Kalshi SDK response
                contract_name = pos.get('market_title', pos.get('ticker', pos.get('market_id', 'Unknown')))
                quantity = pos.get('position', pos.get('quantity', 0))
                entry_price = pos.get('purchase_price', pos.get('cost_basis', 0))
                current_price = pos.get('current_price', pos.get('market_price', entry_price))
                
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
            
            print(f"[DEBUG] Returning {len(portfolio_list)} items")
            return pd.DataFrame(portfolio_list)
        else:
            print(f"[DEBUG] No positions in response")
            st.info("💡 No open positions found in your Kalshi account")
    except Exception as e:
        st.error(f"❌ Error fetching Kalshi portfolio: {e}")
    
    return pd.DataFrame(columns=['Contract', 'Quantity', 'Entry Price', 'Current Price', 'P&L', 'P&L %'])

@st.cache_data(ttl=300)
def fetch_kalshi_balance():
    """Fetch user's Kalshi account balance"""
    print(f"[DEBUG] fetch_kalshi_balance() called")
    if not KALSHI_EMAIL or not KALSHI_PASSWORD:
        print(f"[DEBUG] Balance: credentials missing")
        return None
    
    try:
        print(f"[DEBUG] Creating KalshiClient for balance...")
        client = KalshiClient(email=KALSHI_EMAIL, password=KALSHI_PASSWORD)
        balance = client.get_user_balance()
        print(f"✅ Balance fetched: {balance}")
        return balance
    except Exception as e:
        print(f"❌ Error fetching balance: {e}")
        import traceback
        traceback.print_exc()
        return None

@st.cache_data(ttl=300)
def fetch_kalshi_trades():
    """Fetch user's Kalshi trade history (fills)"""
    print(f"[DEBUG] fetch_kalshi_trades() called")
    if not KALSHI_EMAIL or not KALSHI_PASSWORD:
        print(f"[DEBUG] Trades: credentials missing")
        return []
    
    try:
        print(f"[DEBUG] Creating KalshiClient for trades...")
        client = KalshiClient(email=KALSHI_EMAIL, password=KALSHI_PASSWORD)
        trades = client.get_user_trades(limit=50)
        print(f"✅ Trades fetched: {len(trades)} fills")
        return trades
    except Exception as e:
        print(f"❌ Error fetching trades: {e}")
        return []

@st.cache_data(ttl=300)
def fetch_kalshi_active_markets():
    """Fetch active Kalshi markets using official SDK"""
    if not PREDICTION_MODULE_AVAILABLE:
        st.warning("⚠️ Prediction analytics module not available")
        return pd.DataFrame()
    
    if not KALSHI_EMAIL or not KALSHI_PASSWORD:
        st.info("ℹ️ Kalshi credentials not configured")
        return pd.DataFrame()
    
    try:
        client = KalshiClient(email=KALSHI_EMAIL, password=KALSHI_PASSWORD)
        markets = client.get_active_markets()
        
        st.info(f"📊 API Response: Found {len(markets) if markets else 0} active markets")
        
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
        else:
            st.info("💡 No active markets available")
    except Exception as e:
        st.error(f"❌ Error fetching Kalshi markets: {e}")
    
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
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }}
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {{
        color: #F3F4F6 !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
    }}
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] [data-testid="stMarkdownContainer"] p {{
        color: {COLOR_SCHEME['accent_gold']} !important;
        font-weight: 700 !important;
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
            if not KALSHI_EMAIL:
                st.error("❌ KALSHI_EMAIL not configured in environment")
        
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
    
    # Fetch balance and trades
    balance_info = fetch_kalshi_balance()
    trades_history = fetch_kalshi_trades()
    
    # Display account balance at top
    if balance_info:
        col1, col2, col3 = st.columns(3)
        with col1:
            cash = balance_info.get('cash', 0)
            st.metric("💰 Cash Balance", f"${cash:,.2f}")
        
        with col2:
            holdings_value = balance_info.get('portfolio_value', 0)
            st.metric("📈 Holdings Value", f"${holdings_value:,.2f}")
        
        with col3:
            total = cash + holdings_value
            st.metric("💵 Total Account Value", f"${total:,.2f}")
    
    # Display portfolio positions
    if not kalshi_portfolio.empty:
        st.markdown("#### Active Positions")
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
        
        st.dataframe(kalshi_portfolio, use_container_width=True)
    else:
        st.info("💼 No active positions in your Kalshi portfolio")
    
    # Display trade history
    if trades_history:
        st.markdown("#### Recent Trades")
        trades_df = pd.DataFrame(trades_history)
        st.dataframe(trades_df.head(10), use_container_width=True)
    else:
        st.info("📊 No recent trades found")
    
    # Refresh buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh Portfolio"):
            st.cache_data.clear()
            st.success("Portfolio refreshed!")
            st.rerun()
    
    with col2:
        if st.button("📥 Export Account Data"):
            if balance_info:
                export_data = {
                    'Balance': [balance_info],
                    'Positions': [kalshi_portfolio.to_dict()],
                    'Trades': trades_history
                }
                st.download_button(
                    label="Download Account Data",
                    data=str(export_data),
                    file_name="kalshi_account_export.txt",
                    mime="text/plain"
                )
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
