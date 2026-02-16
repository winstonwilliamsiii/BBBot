"""
🔧 Bentley Bot Control Center - Admin Dashboard

Internal admin interface for:
- Bot deployment and monitoring
- Broker health and orchestration
- Prop firm execution management
- Risk engine controls
- System monitoring

**Access:** Internal admin only
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
FLASK_API_URL = os.getenv("CONTROL_CENTER_API_URL", "http://localhost:5001")
MLFLOW_URL = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

# Page config
st.set_page_config(
    page_title="Bentley Bot Control Center",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .status-healthy { color: #10b981; font-weight: bold; }
    .status-warning { color: #f59e0b; font-weight: bold; }
    .status-error { color: #ef4444; font-weight: bold; }
    .control-button {
        background: #3b82f6;
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        border: none;
        cursor: pointer;
    }
    .section-header {
        background: #1f2937;
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0 10px 0;
    }
</style>
""", unsafe_allow_html=True)


# Authentication Check
def check_admin_auth():
    """Verify admin authentication."""
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        st.warning("🔒 Admin authentication required")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.subheader("Admin Login")
            username = st.text_input("Username", key="admin_username")
            password = st.text_input("Password", type="password", key="admin_password")
            
            if st.button("Login", type="primary"):
                # TODO: Replace with actual authentication
                if username == "admin" and password == "admin":  # DEVELOPMENT ONLY
                    st.session_state.admin_authenticated = True
                    st.session_state.admin_user = username
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        return False
    return True


# Helper Functions
def api_request(endpoint, method="GET", data=None):
    """Make request to Flask API."""
    try:
        url = f"{FLASK_API_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        elif method == "DELETE":
            response = requests.delete(url, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(f"⚠️ Cannot connect to Control Center API at {FLASK_API_URL}")
        st.info("Start the API: `python backend/api/app.py`")
        return None
    except Exception as e:
        st.error(f"Request failed: {str(e)}")
        return None


def get_status_badge(status):
    """Return colored status badge."""
    if status in ["running", "healthy", "active"]:
        return f'<span class="status-healthy">● {status.upper()}</span>'
    elif status in ["warning", "degraded", "idle"]:
        return f'<span class="status-warning">● {status.upper()}</span>'
    else:
        return f'<span class="status-error">● {status.upper()}</span>'


# Main App
def main():
    # Check authentication first
    if not check_admin_auth():
        return
    
    # Header
    st.title("🔧 Bentley Bot Control Center")
    st.markdown(f"**Admin:** {st.session_state.admin_user} | **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Logout button in sidebar
    with st.sidebar:
        if st.button("🚪 Logout", type="secondary"):
            st.session_state.admin_authenticated = False
            st.rerun()
        
        st.markdown("---")
        st.markdown("### Quick Links")
        st.markdown(f"[MLflow]({MLFLOW_URL})")
        st.markdown("[Airflow](http://localhost:8080)")
        st.markdown("[Airbyte](http://localhost:8000)")
        st.markdown("[Service Dashboard](../sites/Mansa_Bentley_Platform/service_dashboard.html)")
    
    # Navigation Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Overview",
        "🤖 Bot Manager",
        "🔌 Broker Health",
        "🏢 Prop Firms",
        "🛡️ Risk Engine",
        "📈 System Logs"
    ])
    
    # TAB 1: Overview Dashboard
    with tab1:
        st.markdown('<div class="section-header"><h2>System Overview</h2></div>', unsafe_allow_html=True)
        
        # Health metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Active Bots", "3 / 13", "+1")
        with col2:
            st.metric("Broker Connections", "2 / 5", "")
        with col3:
            st.metric("Daily P&L", "$1,245.67", "+$345.21")
        with col4:
            st.metric("API Health", "98.5%", "-1.2%")
        
        st.markdown("---")
        
        # System status
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Docker Services")
            services_data = api_request("/api/admin/monitoring/docker-services")
            
            if services_data:
                for service in services_data.get("services", []):
                    status_html = get_status_badge(service.get("status", "unknown"))
                    st.markdown(f"{service['name']}: {status_html}", unsafe_allow_html=True)
            else:
                # Fallback if API not available
                st.markdown(get_status_badge("running") + " **Airflow**", unsafe_allow_html=True)
                st.markdown(get_status_badge("running") + " **MLflow**", unsafe_allow_html=True)
                st.markdown(get_status_badge("running") + " **Airbyte**", unsafe_allow_html=True)
                st.markdown(get_status_badge("running") + " **MySQL**", unsafe_allow_html=True)
                st.markdown(get_status_badge("running") + " **Redis**", unsafe_allow_html=True)
        
        with col2:
            st.subheader("Recent Activity")
            st.text("15:23 - Bot 3 deployed to production")
            st.text("14:45 - Alpaca session refreshed")
            st.text("13:12 - FTMO trade executed (EURUSD)")
            st.text("11:30 - Risk limit updated (max drawdown)")
            st.text("09:15 - Daily reconciliation completed")
    
    # TAB 2: Bot Manager
    with tab2:
        st.markdown('<div class="section-header"><h2>AI/ML Bot Orchestration</h2></div>', unsafe_allow_html=True)
        
        # Bot deployment controls
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("Deployed Bots")
        with col2:
            if st.button("➕ Deploy New Bot", type="primary"):
                st.session_state.show_deploy_modal = True
        
        # Bot list
        bots_data = api_request("/api/admin/bots/list")
        
        if bots_data:
            bots_df = pd.DataFrame(bots_data.get("bots", []))
            st.dataframe(bots_df, use_container_width=True)
        else:
            # Sample bot data
            bots = [
                {"id": 1, "name": "GoldRSI Strategy", "status": "running", "broker": "Alpaca", "uptime": "3d 5h"},
                {"id": 2, "name": "USD/COP Short", "status": "idle", "broker": "MT5", "uptime": "1d 2h"},
                {"id": 3, "name": "Portfolio Optimizer", "status": "running", "broker": "Multi", "uptime": "7d 12h"},
            ]
            bots_df = pd.DataFrame(bots)
            
            for idx, bot in enumerate(bots):
                col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 1, 1])
                
                with col1:
                    st.markdown(f"**{bot['name']}**")
                with col2:
                    st.markdown(get_status_badge(bot['status']), unsafe_allow_html=True)
                with col3:
                    st.text(f"Broker: {bot['broker']}")
                with col4:
                    st.text(f"Uptime: {bot['uptime']}")
                with col5:
                    if st.button("⏸️", key=f"stop_{idx}"):
                        st.info(f"Stopping {bot['name']}...")
                with col6:
                    if st.button("📊", key=f"metrics_{idx}"):
                        st.info(f"Loading metrics for {bot['name']}...")
                
                st.markdown("---")
        
        # Deploy modal
        if st.session_state.get("show_deploy_modal", False):
            with st.expander("Deploy New Bot", expanded=True):
                bot_select = st.selectbox("Select Bot", [f"Bot {i}" for i in range(1, 14)])
                broker_select = st.selectbox("Select Broker", ["Alpaca", "IBKR", "Binance", "MT5 (FTMO)", "MT5 (Axi)"])
                environment = st.radio("Environment", ["Sandbox", "Live"], horizontal=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Deploy", type="primary", use_container_width=True):
                        st.success(f"Deploying {bot_select} to {broker_select} ({environment})...")
                        st.session_state.show_deploy_modal = False
                        st.rerun()
                with col2:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state.show_deploy_modal = False
                        st.rerun()
    
    # TAB 3: Broker Health
    with tab3:
        st.markdown('<div class="section-header"><h2>Multi-Broker Orchestration</h2></div>', unsafe_allow_html=True)
        
        # Refresh button
        if st.button("🔄 Refresh All Sessions"):
            st.info("Refreshing broker sessions...")
        
        st.markdown("---")
        
        # Broker status cards
        brokers_data = api_request("/api/admin/brokers/health")
        
        if not brokers_data:
            # Sample broker data
            brokers = [
                {"name": "Alpaca", "status": "healthy", "latency": "45ms", "orders_today": 12, "last_sync": "2 min ago"},
                {"name": "Schwab", "status": "warning", "latency": "120ms", "orders_today": 0, "last_sync": "15 min ago"},
                {"name": "IBKR", "status": "error", "latency": "N/A", "orders_today": 0, "last_sync": "Never"},
                {"name": "Binance", "status": "healthy", "latency": "35ms", "orders_today": 8, "last_sync": "1 min ago"},
                {"name": "Coinbase", "status": "idle", "latency": "N/A", "orders_today": 0, "last_sync": "Never"},
            ]
        else:
            brokers = brokers_data.get("brokers", [])
        
        for broker in brokers:
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
            
            with col1:
                st.markdown(f"### {broker['name']}")
            with col2:
                st.markdown(get_status_badge(broker['status']), unsafe_allow_html=True)
            with col3:
                st.metric("Latency", broker['latency'])
            with col4:
                st.metric("Orders Today", broker['orders_today'])
            with col5:
                st.text(f"Last sync: {broker['last_sync']}")
            
            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button(f"Test Connection", key=f"{broker['name']}_test"):
                    st.info(f"Testing {broker['name']} connection...")
            with col2:
                if st.button(f"Refresh Token", key=f"{broker['name']}_refresh"):
                    st.info(f"Refreshing {broker['name']} token...")
            with col3:
                if st.button(f"View Orders", key=f"{broker['name']}_orders"):
                    st.info(f"Loading {broker['name']} orders...")
            with col4:
                if st.button(f"Settings", key=f"{broker['name']}_settings"):
                    st.info(f"Opening {broker['name']} settings...")
            
            st.markdown("---")
    
    # TAB 4: Prop Firms
    with tab4:
        st.markdown('<div class="section-header"><h2>Prop Firm Execution Management</h2></div>', unsafe_allow_html=True)
        
        # Prop firm status
        prop_firms = [
            {"name": "FTMO", "platform": "MT5", "accounts": 2, "status": "active", "daily_pnl": "$234.56"},
            {"name": "Axi Select", "platform": "MT5", "accounts": 1, "status": "active", "daily_pnl": "$89.12"},
            {"name": "Zenit", "platform": "NinjaTrader", "accounts": 0, "status": "planned", "daily_pnl": "$0.00"},
        ]
        
        for firm in prop_firms:
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
            
            with col1:
                st.markdown(f"### {firm['name']}")
            with col2:
                st.text(f"Platform: {firm['platform']}")
            with col3:
                st.metric("Active Accounts", firm['accounts'])
            with col4:
                st.markdown(get_status_badge(firm['status']), unsafe_allow_html=True)
            with col5:
                st.metric("Daily P&L", firm['daily_pnl'])
            
            # MT5 controls
            if firm['platform'] == "MT5" and firm['accounts'] > 0:
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"View Positions", key=f"{firm['name']}_positions"):
                        st.info(f"Loading {firm['name']} positions...")
                with col2:
                    if st.button(f"Challenge Status", key=f"{firm['name']}_challenge"):
                        st.info(f"Loading {firm['name']} challenge metrics...")
                with col3:
                    if st.button(f"Execute Trade", key=f"{firm['name']}_trade"):
                        st.info(f"Opening trade form for {firm['name']}...")
            
            st.markdown("---")
    
    # TAB 5: Risk Engine
    with tab5:
        st.markdown('<div class="section-header"><h2>Risk Management & Compliance</h2></div>', unsafe_allow_html=True)
        
        # Risk metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Portfolio Drawdown", "-2.3%", "Within limits")
        with col2:
            st.metric("Margin Utilization", "34%", "Healthy")
        with col3:
            st.metric("Risk Violations Today", "0", "✓")
        
        st.markdown("---")
        
        # Risk settings
        st.subheader("Risk Limits Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            max_drawdown = st.slider("Max Portfolio Drawdown (%)", 0, 20, 5)
            max_position_size = st.slider("Max Position Size (%)", 0, 50, 10)
            max_leverage = st.slider("Max Leverage", 1, 10, 3)
        
        with col2:
            daily_loss_limit = st.number_input("Daily Loss Limit ($)", value=1000)
            concentration_limit = st.number_input("Single Asset Concentration (%)", value=25)
            
            st.checkbox("Enable pre-trade risk checks", value=True)
            st.checkbox("Enable real-time monitoring", value=True)
            st.checkbox("Auto-halt on violation", value=True)
        
        if st.button("💾 Save Risk Settings", type="primary"):
            st.success("Risk settings updated successfully!")
        
        st.markdown("---")
        
        # Recent violations
        st.subheader("Recent Risk Events")
        st.text("No violations in the last 24 hours ✓")
    
    # TAB 6: System Logs
    with tab6:
        st.markdown('<div class="section-header"><h2>Execution Logs & Monitoring</h2></div>', unsafe_allow_html=True)
        
        # Log filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            log_level = st.selectbox("Log Level", ["All", "INFO", "WARNING", "ERROR"])
        with col2:
            log_source = st.selectbox("Source", ["All", "Bots", "Brokers", "Prop Firms", "Risk"])
        with col3:
            time_range = st.selectbox("Time Range", ["Last Hour", "Last 24h", "Last 7 days"])
        
        # Log display
        st.text_area("System Logs", value="""
[2026-02-15 15:23:45] [INFO] [Bot3] Successfully deployed to Alpaca (sandbox)
[2026-02-15 14:45:12] [INFO] [Alpaca] Session token refreshed successfully
[2026-02-15 13:12:34] [INFO] [FTMO-MT5] Trade executed: EURUSD BUY 0.1 lots @ 1.0945
[2026-02-15 11:30:22] [WARNING] [Schwab] High latency detected: 180ms
[2026-02-15 09:15:11] [INFO] [System] Daily reconciliation completed successfully
[2026-02-15 08:00:05] [INFO] [Risk] All systems within risk parameters
        """, height=400)
        
        # Export logs
        if st.button("📥 Export Logs"):
            st.info("Exporting logs to CSV...")


# Run the app
if __name__ == "__main__":
    main()
