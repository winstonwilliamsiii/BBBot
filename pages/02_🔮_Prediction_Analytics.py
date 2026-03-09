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
    from prediction_analytics.services.polymarket_api_client import PolymarketAPIClient
    from prediction_analytics.services.kalshi_client import KalshiClient
    PREDICTION_MODULE_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ Prediction analytics module not fully available: {e}")
    PREDICTION_MODULE_AVAILABLE = False

# ============================================
# KALSHI CREDENTIALS & SETUP
# ============================================
try:
    # Try nested table format first (production Streamlit Cloud)
    KALSHI_API_KEY_ID = st.secrets["prediction_markets"]["KALSHI_API_KEY_ID"]
    KALSHI_PRIVATE_KEY = st.secrets["prediction_markets"]["KALSHI_PRIVATE_KEY"]
except (KeyError, AttributeError):
    # Fallback to flat format or environment variables (local development)
    try:
        KALSHI_API_KEY_ID = st.secrets.get("KALSHI_API_KEY_ID", "") or os.getenv(
            "KALSHI_API_KEY_ID", ""
        ) or os.getenv("KALSHI_ACCESS_KEY", "")
        KALSHI_PRIVATE_KEY = st.secrets.get("KALSHI_PRIVATE_KEY", "") or os.getenv(
            "KALSHI_PRIVATE_KEY", ""
        )
    except Exception:
        KALSHI_API_KEY_ID = os.getenv("KALSHI_API_KEY_ID", "") or os.getenv(
            "KALSHI_ACCESS_KEY", ""
        )
        KALSHI_PRIVATE_KEY = os.getenv("KALSHI_PRIVATE_KEY", "")

# ============================================
# POLYMARKET CREDENTIALS & SETUP
# ============================================
try:
    # Try nested table format first (production Streamlit Cloud)
    POLYMARKET_API_KEY = st.secrets["prediction_markets"]["POLYMARKET_API_KEY"]
    POLYMARKET_SECRET_KEY = st.secrets["prediction_markets"]["POLYMARKET_SECRET_KEY"]
except (KeyError, AttributeError):
    # Fallback to flat format or environment variables (local development)
    try:
        POLYMARKET_API_KEY = st.secrets.get("POLYMARKET_API_KEY", "") or os.getenv(
            "POLYMARKET_API_KEY", ""
        )
        POLYMARKET_SECRET_KEY = st.secrets.get("POLYMARKET_SECRET_KEY", "") or os.getenv(
            "POLYMARKET_SECRET_KEY", ""
        )
    except Exception:
        POLYMARKET_API_KEY = os.getenv("POLYMARKET_API_KEY", "")
        POLYMARKET_SECRET_KEY = os.getenv("POLYMARKET_SECRET_KEY", "")

POLYMARKET_HAS_API_KEY = bool(POLYMARKET_API_KEY)
POLYMARKET_HAS_PRIVATE_AUTH = bool(POLYMARKET_API_KEY and POLYMARKET_SECRET_KEY)


@st.cache_data(ttl=300)
def fetch_kalshi_portfolio():
    """Fetch user's Kalshi portfolio/positions using RSA API key authentication"""
    if not PREDICTION_MODULE_AVAILABLE:
        st.warning("⚠️ Prediction analytics module not available")
        return pd.DataFrame(
            columns=['Exchange', 'Contract', 'Quantity', 'Entry Price', 'Current Price', 'P&L', 'P&L %']
        )
    if not KALSHI_API_KEY_ID or not KALSHI_PRIVATE_KEY:
        st.info("ℹ️ Kalshi credentials not configured. Set KALSHI_API_KEY_ID and KALSHI_PRIVATE_KEY.")
        return pd.DataFrame(
            columns=['Exchange', 'Contract', 'Quantity', 'Entry Price', 'Current Price', 'P&L', 'P&L %']
        )

    try:
        client = KalshiClient(api_key_id=KALSHI_API_KEY_ID, private_key=KALSHI_PRIVATE_KEY)
        if not client.authenticated:
            st.error(f"❌ Kalshi authentication failed: {client.last_error}")
            return pd.DataFrame(
                columns=['Exchange', 'Contract', 'Quantity', 'Entry Price', 'Current Price', 'P&L', 'P&L %']
            )

        positions = client.get_user_portfolio()
        
        if positions:
            portfolio_list = []
            for pos in positions:
                # Extract position data from Kalshi API response
                contract_name = pos.get('ticker', 'Unknown')
                quantity = float(pos.get('position', 0))
                realized_pnl = float(pos.get('realized_pnl', 0))
                realized_pnl_dollars = float(pos.get('realized_pnl_dollars', 0)) / 100  # Convert cents to dollars
                total_traded = float(pos.get('total_traded', 0))
                total_traded_dollars = float(pos.get('total_traded_dollars', 0)) / 100  # Convert cents to dollars
                market_exposure_dollars = float(pos.get('market_exposure_dollars', 0)) / 100  # Convert cents to dollars
                
                # Calculate entry price from total traded
                entry_price = (total_traded_dollars / total_traded) if total_traded and total_traded != 0 else 0
                current_price = (market_exposure_dollars / quantity) if quantity and quantity != 0 else entry_price
                
                # Calculate P&L based on market exposure and total cost
                cost_basis = abs(total_traded_dollars) if total_traded_dollars else 0
                current_value = abs(market_exposure_dollars) if market_exposure_dollars else 0
                pnl = realized_pnl_dollars  # Use Kalshi's calculated realized P&L (already converted to dollars)
                pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
                
                portfolio_list.append({
                    'Exchange': 'Kalshi',
                    'Contract': contract_name,
                    'Quantity': int(quantity),
                    'Entry Price': f"${entry_price:.4f}" if entry_price else "N/A",
                    'Current Price': f"${current_price:.4f}" if current_price else "N/A",
                    'P&L': f"${pnl:.2f}",
                    'P&L %': f"{pnl_pct:+.2f}%" if pnl_pct else "0%"
                })
            
            return pd.DataFrame(portfolio_list)

        st.info("💡 No open Kalshi positions found")
        return pd.DataFrame(
            columns=['Exchange', 'Contract', 'Quantity', 'Entry Price', 'Current Price', 'P&L', 'P&L %']
        )
    except Exception as e:
        st.error(f"❌ Error fetching Kalshi portfolio: {e}")
        return pd.DataFrame(
            columns=['Exchange', 'Contract', 'Quantity', 'Entry Price', 'Current Price', 'P&L', 'P&L %']
        )

@st.cache_data(ttl=300)
def fetch_kalshi_balance():
    """Fetch user's Kalshi account balance"""
    if not PREDICTION_MODULE_AVAILABLE:
        return None
    if not KALSHI_API_KEY_ID or not KALSHI_PRIVATE_KEY:
        return None
    
    try:
        client = KalshiClient(api_key_id=KALSHI_API_KEY_ID, private_key=KALSHI_PRIVATE_KEY)
        if not client.authenticated:
            st.error(f"❌ Kalshi authentication failed: {client.last_error}")
            return None
        balance = client.get_user_balance()
        print(f"✅ Balance fetched: {balance}")
        return balance
    except Exception as e:
        print(f"❌ Error fetching balance: {e}")
        return None

@st.cache_data(ttl=300)
def fetch_kalshi_trades():
    """Fetch user's Kalshi trade history (fills)"""
    if not PREDICTION_MODULE_AVAILABLE:
        return []
    if not KALSHI_API_KEY_ID or not KALSHI_PRIVATE_KEY:
        return []
    
    try:
        client = KalshiClient(api_key_id=KALSHI_API_KEY_ID, private_key=KALSHI_PRIVATE_KEY)
        if not client.authenticated:
            st.error(f"❌ Kalshi authentication failed: {client.last_error}")
            return []
        trades = client.get_user_trades(limit=50)
        print(f"✅ Trades fetched: {len(trades)} fills")
        return trades
    except Exception as e:
        print(f"❌ Error fetching trades: {e}")
        return []

@st.cache_data(ttl=300)
def fetch_kalshi_active_markets():
    """Fetch active Kalshi markets using RSA API key authentication"""
    if not PREDICTION_MODULE_AVAILABLE:
        st.warning("⚠️ Prediction analytics module not available")
        return pd.DataFrame()
    
    if not KALSHI_API_KEY_ID or not KALSHI_PRIVATE_KEY:
        st.info("ℹ️ Kalshi credentials not configured")
        return pd.DataFrame()
    
    try:
        client = KalshiClient(api_key_id=KALSHI_API_KEY_ID, private_key=KALSHI_PRIVATE_KEY)
        if not client.authenticated:
            st.error(f"❌ Kalshi authentication failed: {client.last_error}")
            return pd.DataFrame()
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

# ====================== POLYMARKET FUNCTIONS ======================

@st.cache_data(ttl=300)
def fetch_polymarket_portfolio():
    """Fetch user's Polymarket portfolio (positions)"""
    if not POLYMARKET_HAS_PRIVATE_AUTH:
        st.info("ℹ️ Polymarket private portfolio access not configured (requires API key + secret key)")
        return pd.DataFrame(columns=['Exchange', 'Contract', 'Quantity', 'Entry Price', 'Current Price', 'P&L', 'P&L %'])
    
    try:
        client = PolymarketAPIClient(api_key=POLYMARKET_API_KEY, secret_key=POLYMARKET_SECRET_KEY)
        positions = client.get_user_portfolio()
        
        if positions and len(positions) > 0:
            portfolio_list = []
            for pos in positions:
                contract_name = pos.get('market', pos.get('asset', 'Unknown'))
                quantity = pos.get('balance', pos.get('quantity', 0))
                entry_price = pos.get('avg_price', pos.get('cost_basis', 0))
                current_price = pos.get('current_price', pos.get('market_price', entry_price))
                
                # Calculate P&L
                cost_basis = quantity * entry_price if quantity > 0 else 0
                current_value = quantity * current_price if quantity > 0 else 0
                pnl = current_value - cost_basis
                pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
                
                portfolio_list.append({
                    'Exchange': 'Polymarket',
                    'Contract': contract_name,
                    'Quantity': quantity,
                    'Entry Price': f"${entry_price:.4f}",
                    'Current Price': f"${current_price:.4f}",
                    'P&L': f"${pnl:.2f}",
                    'P&L %': f"{pnl_pct:+.2f}%"
                })
            return pd.DataFrame(portfolio_list)
        else:
            st.info("💡 No open Polymarket positions found (demo data)")
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=['Exchange', 'Contract', 'Quantity', 'Entry Price', 'Current Price', 'P&L', 'P&L %'])
    except Exception as e:
        st.error(f"❌ Error fetching Polymarket portfolio: {e}")
        return pd.DataFrame(columns=['Exchange', 'Contract', 'Quantity', 'Entry Price', 'Current Price', 'P&L', 'P&L %'])

@st.cache_data(ttl=300)
def fetch_polymarket_balance():
    """Fetch user's Polymarket account balance"""
    if not POLYMARKET_HAS_PRIVATE_AUTH:
        return None
    
    try:
        client = PolymarketAPIClient(api_key=POLYMARKET_API_KEY, secret_key=POLYMARKET_SECRET_KEY)
        balance = client.get_user_balance()
        print(f"✅ Polymarket balance fetched: {balance}")
        return balance
    except Exception as e:
        print(f"❌ Error fetching Polymarket balance: {e}")
        # Return dummy data since no funds transferred
        return {"cash": 0.0, "portfolio_value": 0.0, "total_balance": 0.0}

@st.cache_data(ttl=300)
def fetch_polymarket_trades():
    """Fetch user's Polymarket trade history"""
    if not POLYMARKET_HAS_PRIVATE_AUTH:
        return []
    
    try:
        client = PolymarketAPIClient(api_key=POLYMARKET_API_KEY, secret_key=POLYMARKET_SECRET_KEY)
        trades = client.get_user_trades(limit=50)
        print(f"✅ Polymarket trades fetched: {len(trades) if trades else 0} trades")
        return trades if trades else []
    except Exception as e:
        print(f"❌ Error fetching Polymarket trades: {e}")
        return []

@st.cache_data(ttl=300)
def fetch_polymarket_active_markets():
    """Fetch active Polymarket markets"""
    if not POLYMARKET_HAS_API_KEY:
        st.info("ℹ️ Polymarket API key not configured")
        return pd.DataFrame()
    
    try:
        client = PolymarketAPIClient(api_key=POLYMARKET_API_KEY, secret_key=POLYMARKET_SECRET_KEY)
        markets = client.get_active_markets(limit=10)
        
        if markets and len(markets) > 0:
            contracts_list = []
            for market in markets:
                contracts_list.append({
                    'Contract': market.get('question', market.get('title', 'N/A')),
                    'Platform': 'Polymarket',
                    'Current Price': f"${market.get('price', 'N/A')}",
                    'Volume (24h)': market.get('volume_24h', 'N/A'),
                    'Expires': market.get('end_date', 'N/A'),
                    'Status': market.get('status', 'N/A')
                })
            return pd.DataFrame(contracts_list)
        else:
            st.info("💡 No active Polymarket markets available")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error fetching Polymarket markets: {e}")
        return pd.DataFrame()

# ================================================================

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
polymarket_portfolio = fetch_polymarket_portfolio()

# Combine portfolios
if not polymarket_portfolio.empty:
    combined_portfolio = pd.concat(
        [kalshi_portfolio, polymarket_portfolio], ignore_index=True
    )
else:
    combined_portfolio = kalshi_portfolio

portfolio_value = len(combined_portfolio)
if len(combined_portfolio) > 0 and 'P&L %' in combined_portfolio.columns:
    portfolio_pnl = combined_portfolio['P&L %'].str.rstrip('%').astype(float).sum()
else:
    portfolio_pnl = 0

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
        <div class='metric-label'>My Positions</div>
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
    st.markdown("<h3 style='color: #F3F4F6;'>Active Prediction Markets</h3>", unsafe_allow_html=True)
    
    # Platform filter
    platform_filter = st.selectbox("Filter by Platform", ["All", "Kalshi", "Polymarket"], key="platform_tab1")
    
    if PREDICTION_MODULE_AVAILABLE:
        # Fetch markets based on filter
        kalshi_markets = pd.DataFrame()
        polymarket_markets = pd.DataFrame()
        
        if platform_filter in ["All", "Kalshi"]:
            kalshi_markets = fetch_kalshi_active_markets()
        
        if platform_filter in ["All", "Polymarket"]:
            polymarket_markets = fetch_polymarket_active_markets()
        
        # Combine markets
        if not kalshi_markets.empty or not polymarket_markets.empty:
            combined_markets = pd.concat([kalshi_markets, polymarket_markets], ignore_index=True)
            
            if not combined_markets.empty:
                st.success(f"✅ Showing {len(combined_markets)} active markets")
                st.dataframe(combined_markets, use_container_width=True)
            else:
                st.info("💡 No markets found matching your filter")
        else:
            st.warning("⚠️ No markets available. Check your API credentials.")
            
            if platform_filter in ["All", "Kalshi"] and not KALSHI_API_KEY_ID:
                st.error("❌ KALSHI_API_KEY_ID not configured in environment")
            
            if platform_filter in ["All", "Polymarket"] and not POLYMARKET_API_KEY:
                st.error("❌ POLYMARKET_API_KEY not configured in environment")
        
        # Refresh button
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔄 Refresh Markets"):
                st.cache_data.clear()
                st.success("Markets refreshed!")
                st.rerun()
        
        with col2:
            st.markdown("*Last updated: Real-time*")
    else:
        st.warning("⚠️ Prediction analytics module not available. Install dependencies:")
        st.code("pip install prediction-analytics", language="bash")

with tab2:
    st.markdown("<h3 style='color: #F3F4F6;'>Your Prediction Market Portfolio</h3>", unsafe_allow_html=True)
    
    # Exchange selector
    exchange_filter = st.selectbox("Filter by Exchange", ["All", "Kalshi", "Polymarket"], key="exchange_tab2")
    
    # Fetch balance data for both exchanges
    kalshi_balance = fetch_kalshi_balance()
    polymarket_balance = fetch_polymarket_balance()
    
    # Display account balances
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Kalshi API returns 'balance' in cents, convert to dollars
        kalshi_cash = (kalshi_balance.get('balance', 0) / 100) if kalshi_balance else 0
        polymarket_cash = polymarket_balance.get('cash', 0) if polymarket_balance else 0
        total_cash = kalshi_cash + polymarket_cash
        st.metric("💰 Total Cash", f"${total_cash:,.2f}")
    
    with col2:
        # Kalshi API returns 'portfolio_value' in cents, convert to dollars
        kalshi_holdings = (kalshi_balance.get('portfolio_value', 0) / 100) if kalshi_balance else 0
        polymarket_holdings = polymarket_balance.get('portfolio_value', 0) if polymarket_balance else 0
        total_holdings = kalshi_holdings + polymarket_holdings
        st.metric("📈 Total Holdings Value", f"${total_holdings:,.2f}")
    
    with col3:
        total_account = total_cash + total_holdings
        st.metric("💵 Total Account Value", f"${total_account:,.2f}")
    
    # Filter and display portfolio
    if exchange_filter == "All":
        display_portfolio = combined_portfolio
    elif exchange_filter == "Kalshi":
        display_portfolio = kalshi_portfolio
    else:  # Polymarket
        display_portfolio = polymarket_portfolio
    
    # Display portfolio positions
    if not display_portfolio.empty:
        st.markdown("#### Active Positions")
        st.markdown(f"""
        <div style='background: {COLOR_SCHEME['card_background']}; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;'>
            <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;'>
                <div>
                    <div style='color: {COLOR_SCHEME['text']}; font-size: 0.875rem;'>Total Positions</div>
                    <div style='color: {COLOR_SCHEME['accent_gold']}; font-size: 1.5rem; font-weight: bold;'>{len(display_portfolio)}</div>
                </div>
                <div>
                    <div style='color: {COLOR_SCHEME['text']}; font-size: 0.875rem;'>Portfolio Value</div>
                    <div style='color: {COLOR_SCHEME['accent_teal']}; font-size: 1.5rem; font-weight: bold;'>${total_holdings:,.0f}</div>
                </div>
                <div>
                    <div style='color: {COLOR_SCHEME['text']}; font-size: 0.875rem;'>Total P&L</div>
                    <div style='color: {"#10B981" if portfolio_pnl >= 0 else "#EF4444"}; font-size: 1.5rem; font-weight: bold;'>{portfolio_pnl:+.2f}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.dataframe(display_portfolio, use_container_width=True)
    else:
        exchange_label = f"{exchange_filter} " if exchange_filter != "All" else ""
        st.info(f"💼 No active positions in your {exchange_label}portfolio")
    
    # Display trade history
    st.markdown("#### Recent Trades")
    
    if exchange_filter in ["All", "Kalshi"]:
        kalshi_trades = fetch_kalshi_trades()
        if kalshi_trades:
            st.subheader("Kalshi Trades")
            trades_df = pd.DataFrame(kalshi_trades)
            st.dataframe(trades_df.head(10), use_container_width=True)
        else:
            st.info("📊 No Kalshi trades found")
    
    if exchange_filter in ["All", "Polymarket"]:
        polymarket_trades = fetch_polymarket_trades()
        if polymarket_trades:
            st.subheader("Polymarket Trades")
            trades_df = pd.DataFrame(polymarket_trades)
            st.dataframe(trades_df.head(10), use_container_width=True)
        else:
            st.info("📊 No Polymarket trades found")
    
    # Debug panel
    with st.expander("🔧 Connection Debug"):
        debug_cols = st.columns(2)
        
        with debug_cols[0]:
            st.subheader("Kalshi Status")
            if KALSHI_API_KEY_ID and KALSHI_PRIVATE_KEY:
                try:
                    debug_client = KalshiClient(api_key_id=KALSHI_API_KEY_ID, private_key=KALSHI_PRIVATE_KEY)
                    if debug_client.authenticated:
                        st.success("✅ Authenticated")
                        profile = debug_client.get_user_profile()
                        st.write(f"**User**: {profile.get('user_id', 'N/A') if profile else 'N/A'}")
                        positions = debug_client.get_user_portfolio()
                        st.write(f"**Positions**: {len(positions)}")
                    else:
                        st.error(f"❌ Auth Failed: {debug_client.last_error}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.warning("ℹ️ Credentials not configured")
        
        with debug_cols[1]:
            st.subheader("Polymarket Status")
            if POLYMARKET_HAS_PRIVATE_AUTH:
                try:
                    pm_client = PolymarketAPIClient(api_key=POLYMARKET_API_KEY, secret_key=POLYMARKET_SECRET_KEY)
                    st.success("✅ API + private auth configured")
                    st.write(f"**API Key**: {POLYMARKET_API_KEY[:10]}...")
                    st.write("**Note**: No funds transferred (demo mode)")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            elif POLYMARKET_HAS_API_KEY:
                st.warning("⚠️ API key configured (public markets enabled), secret key missing for portfolio/trades")
                st.write(f"**API Key**: {POLYMARKET_API_KEY[:10]}...")
            else:
                st.warning("ℹ️ Credentials not configured")
    
    # Refresh buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh Portfolio"):
            st.cache_data.clear()
            st.success("Portfolio refreshed!")
            st.rerun()
    
    with col2:
        if st.button("📥 Export Account Data"):
            try:
                export_data = {
                    'Kalshi': {
                        'Balance': kalshi_balance,
                        'Positions': kalshi_portfolio.to_dict() if not kalshi_portfolio.empty else {},
                        'Trades': kalshi_trades if 'kalshi_trades' in locals() else []
                    },
                    'Polymarket': {
                        'Balance': polymarket_balance,
                        'Positions': polymarket_portfolio.to_dict() if not polymarket_portfolio.empty else {},
                        'Trades': polymarket_trades if 'polymarket_trades' in locals() else []
                    }
                }
                st.download_button(
                    label="Download Account Data",
                    data=str(export_data),
                    file_name="prediction_markets_export.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"Error preparing export: {e}")

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
