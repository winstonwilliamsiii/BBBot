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
import json
import subprocess
import sys
import os
from pathlib import Path
from urllib.parse import urlparse

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from bbbot1_pipeline.mlflow_config import (
        get_mlflow_tracking_uri,
        get_mlflow_server_url,
        get_mlflow_backend_store_uri,
    )
except Exception:
    def get_mlflow_tracking_uri():
        return os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

    def get_mlflow_server_url():
        return os.getenv("MLFLOW_SERVER_URL", "http://localhost:5000")

    def get_mlflow_backend_store_uri():
        return os.getenv("MLFLOW_BACKEND_STORE_URI", "not-configured")

try:
    from frontend.utils.bot_fund_mapping import get_bot_catalog_rows
except Exception:
    def get_bot_catalog_rows():
        return [
            {
                "bot": "Titan",
                "fund": "Mansa Tech",
                "strategy": "ML Ensemble - CNN with Deep Learning approaches for further accuracy",
            },
            {"bot": "Vega", "fund": "Mansa Retail", "strategy": "Multi-timeframe Strategy"},
            {"bot": "Draco", "fund": "Mansa Money Bag", "strategy": "Sentiment Analyzer"},
            {"bot": "Altair", "fund": "Mansa AI", "strategy": "News Trading"},
            {"bot": "Procryon", "fund": "Crypto Fund", "strategy": "Crypto Arbitrage"},
            {"bot": "Hydra", "fund": "Mansa Health", "strategy": "Momentum Strategy"},
            {
                "bot": "Triton",
                "fund": "Mansa Transportation",
                "strategy": "Portfolio Optimizer",
            },
            {
                "bot": "Dione",
                "fund": "Mansa Diversify Dominance",
                "strategy": "Technical Indicator Bot",
            },
            {"bot": "Dogon", "fund": "Mansa ETF", "strategy": "USD/COP Short"},
            {"bot": "Cephei", "fund": "Mansa Shorts", "strategy": "Mean Reversion"},
            {"bot": "Rigel", "fund": "Mansa FOREX", "strategy": "GoldRSI Strategy"},
            {"bot": "Orion", "fund": "Mansa Minerals", "strategy": "Options Strategy"},
            {"bot": "Rhea", "fund": "Mansa Real Estate", "strategy": "Pairs Trading"},
            {
                "bot": "Jupicita",
                "fund": "Mansa_Smalls",
                "strategy": "Small-cap alpha forecasting with liquidity-aware execution",
            },
        ]

# Configuration
DEFAULT_CONTROL_CENTER_URL = os.getenv("CONTROL_CENTER_API_URL", "http://localhost:5001")
MLFLOW_TRACKING_URI = get_mlflow_tracking_uri()
MLFLOW_URL = get_mlflow_server_url()


def probe_mlflow_server(base_url: str):
    """Probe MLflow endpoint and return (confirmed, host_reachable, note)."""
    checks = [
        ("GET", "/health", None),
        ("GET", "/version", None),
        ("POST", "/api/2.0/mlflow/experiments/search", {"max_results": 1}),
        ("GET", "/", None),
    ]

    host_reachable = False

    for method, path, payload in checks:
        try:
            url = f"{base_url}{path}"
            if method == "POST":
                response = requests.post(url, json=payload, timeout=3)
            else:
                response = requests.get(url, timeout=3)

            status = response.status_code
            if status < 500:
                host_reachable = True

            if path in ("/health", "/version") and status == 200:
                return True, host_reachable, f"MLflow endpoint {path} responded with HTTP {status}."

            if path == "/api/2.0/mlflow/experiments/search" and status in (200, 400, 401, 403):
                return True, host_reachable, "MLflow REST API is reachable."

            if path == "/" and status == 200 and "mlflow" in response.text.lower():
                return True, host_reachable, "MLflow UI page responded successfully."

        except requests.exceptions.RequestException:
            continue

    return False, host_reachable, "No MLflow endpoints were detected at this URL."


def resolve_control_center_api_url():
    """Resolve a reachable Control Center API URL with localhost fallbacks."""
    cached_url = st.session_state.get("resolved_control_center_api_url")
    if cached_url:
        return cached_url

    candidate_urls = [DEFAULT_CONTROL_CENTER_URL]
    if DEFAULT_CONTROL_CENTER_URL != "http://localhost:5001":
        candidate_urls.append("http://localhost:5001")
    if DEFAULT_CONTROL_CENTER_URL != "http://localhost:5000":
        candidate_urls.append("http://localhost:5000")

    for base_url in candidate_urls:
        try:
            response = requests.get(f"{base_url}/health", timeout=1.5)
            if response.status_code == 200:
                st.session_state.resolved_control_center_api_url = base_url
                return base_url
        except requests.exceptions.RequestException:
            continue

    st.session_state.resolved_control_center_api_url = DEFAULT_CONTROL_CENTER_URL
    return DEFAULT_CONTROL_CENTER_URL


def show_control_center_api_notice_once(reason: str = "unavailable"):
    """Show a single non-blocking notice when API data cannot be loaded."""
    if st.session_state.get("control_center_api_notice_shown"):
        return

    configured_url = st.session_state.get(
        "resolved_control_center_api_url",
        DEFAULT_CONTROL_CENTER_URL,
    )
    st.warning(
        f"Control Center API is {reason} at {configured_url}. Showing fallback data where available."
    )
    st.info("Start the API with: `python backend/api/app.py`")
    st.session_state.control_center_api_notice_shown = True

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
    .stApp {
        background: radial-gradient(circle at top left, #111827 0%, #0b1220 55%, #030712 100%);
        color: #e5e7eb;
    }
    [data-testid="stHeader"], [data-testid="stSidebar"] {
        background: #0b1220;
    }
    [data-testid="stSidebar"] {
        border-right: 1px solid #1f2937;
    }
    .metric-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
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
        background: #111827;
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0 10px 0;
        border: 1px solid #374151;
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
        flask_api_url = resolve_control_center_api_url()
        normalized = endpoint if str(endpoint).startswith("/") else f"/{endpoint}"
        endpoint_variants = [normalized]

        # Local Flask app currently exposes `/admin/*`; some clients use `/api/admin/*`.
        if normalized.startswith("/api/"):
            endpoint_variants.append(normalized[4:])
        elif normalized.startswith("/admin/"):
            endpoint_variants.append(f"/api{normalized}")

        last_status = None
        for path in endpoint_variants:
            url = f"{flask_api_url}{path}"
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=5)
            elif method == "DELETE":
                response = requests.delete(url, timeout=5)
            else:
                return None

            last_status = response.status_code
            if response.status_code == 200:
                return response.json()

            # Try alternate route shape before surfacing non-connectivity notice.
            if response.status_code in (404, 405):
                continue

            show_control_center_api_notice_once(
                f"returning HTTP {response.status_code}"
            )
            return None

        # All route variants were not implemented; rely on page fallback data silently.
        if last_status in (404, 405):
            return None

        show_control_center_api_notice_once(
            f"returning HTTP {last_status or 'unknown'}"
        )
        return None
    except requests.exceptions.ConnectionError:
        show_control_center_api_notice_once("unreachable")
        return None
    except Exception:
        show_control_center_api_notice_once("temporarily unavailable")
        return None


def get_status_badge(status):
    """Return colored status badge."""
    if status in ["running", "healthy", "active"]:
        return f'<span class="status-healthy">● {status.upper()}</span>'
    elif status in ["warning", "degraded", "idle"]:
        return f'<span class="status-warning">● {status.upper()}</span>'
    else:
        return f'<span class="status-error">● {status.upper()}</span>'


def get_vega_ibkr_schedule_status() -> dict:
    """Return task scheduler metadata for the Vega IBKR 9:30 automation task."""
    task_name = "Bentley-Vega-IBKR-930"
    cmd = ["schtasks", "/query", "/tn", task_name, "/fo", "LIST", "/v"]
    try:
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )
        if result.returncode != 0:
            return {
                "exists": False,
                "task_name": task_name,
                "error": (result.stderr or result.stdout or "Task not found").strip(),
            }

        info = {
            "exists": True,
            "task_name": task_name,
            "next_run": "Unknown",
            "last_run": "Unknown",
            "last_result": "Unknown",
            "status": "Unknown",
        }
        for line in (result.stdout or "").splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            k = key.strip().lower()
            v = value.strip()
            if k == "next run time":
                info["next_run"] = v
            elif k == "last run time":
                info["last_run"] = v
            elif k == "last result":
                info["last_result"] = v
            elif k == "status":
                info["status"] = v
        return info
    except Exception as exc:
        return {
            "exists": False,
            "task_name": task_name,
            "error": str(exc),
        }


def get_last_bot_mode_event() -> dict | None:
    """Load latest launcher event produced by start_bot_mode.ps1."""
    repo_root = Path(__file__).resolve().parents[1]
    latest_path = repo_root / "logs" / "last_bot_mode_event.json"
    if not latest_path.exists():
        return None

    try:
        with latest_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
            if isinstance(payload, dict):
                return payload
    except Exception:
        return None
    return None


def run_bot_mode(bot_name: str, mode: str) -> dict:
    """Run start_bot_mode.ps1 and return execution result."""
    repo_root = Path(__file__).resolve().parents[1]
    launcher = repo_root / "start_bot_mode.ps1"

    if not launcher.exists():
        return {
            "ok": False,
            "output": f"Launcher not found: {launcher}",
        }

    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(launcher),
        "-Bot",
        bot_name,
        "-Mode",
        mode,
        "-Broker",
        "IBKR",
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        merged = "\n".join(
            part for part in [result.stdout.strip(), result.stderr.strip()] if part
        )
        return {
            "ok": result.returncode == 0,
            "output": merged or "No output",
        }
    except Exception as exc:
        return {"ok": False, "output": str(exc)}


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
        st.markdown("### 🔗 Quick Links")
        st.markdown("#### External Services")
        st.markdown(f"[MLflow UI]({MLFLOW_URL})")
        st.markdown("[Airflow](http://localhost:8080)")
        st.markdown("[Airbyte](http://localhost:8000)")
        st.markdown("[Service Dashboard](../sites/Mansa_Bentley_Platform/service_dashboard.html)")
    
    # Navigation Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Overview",
        "🤖 Bot Manager",
        "🔌 Broker Health",
        "🏢 Prop Firms",
        "🛡️ Risk Engine",
        "🧠 MLflow",
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

        catalog_rows = get_bot_catalog_rows()
        st.caption(
            "Focus: alpha generation via price forecasting and portfolio optimization, "
            "including simulated rebalancing guidance and execution-aware deployment."
        )
        st.caption(
            "Jupicita strategy is set as a proposed default and can be overridden "
            "once you finalize the exact production label."
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Mansa Funds", str(len(catalog_rows)))
        with c2:
            st.metric("Configured Bots", str(len(catalog_rows)))
        with c3:
            st.metric("Orchestration Scope", "Forecast + Rebalance")

        st.markdown("**Mansa Capital Fund/Bot Strategy Catalog**")
        catalog_df = pd.DataFrame(catalog_rows).rename(columns={
            "bot": "Bot Name",
            "fund": "Mansa Fund",
            "strategy": "Proposed Strategy",
        })
        st.dataframe(catalog_df, use_container_width=True, hide_index=True)
        st.markdown("---")

        st.subheader("Vega IBKR 9:30 Automation")
        schedule = get_vega_ibkr_schedule_status()
        last_event = get_last_bot_mode_event()

        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("Task", "Configured" if schedule.get("exists") else "Missing")
        with col_b:
            st.metric("Next Run", schedule.get("next_run", "Unknown"))
        with col_c:
            st.metric("Last Result", schedule.get("last_result", "Unknown"))
        with col_d:
            event_status = (last_event or {}).get("status", "n/a")
            st.metric("Last Vega Status", str(event_status))

        btn_on, btn_off = st.columns(2)
        with btn_on:
            if st.button("Vega ON", type="primary", use_container_width=True):
                with st.spinner("Running Vega ON..."):
                    execution = run_bot_mode("Vega", "ON")
                st.session_state["vega_mode_output"] = execution["output"]
                if execution["ok"]:
                    st.success("Vega ON completed.")
                else:
                    st.error("Vega ON failed.")
                st.rerun()
        with btn_off:
            if st.button("Vega OFF", use_container_width=True):
                with st.spinner("Running Vega OFF..."):
                    execution = run_bot_mode("Vega", "OFF")
                st.session_state["vega_mode_output"] = execution["output"]
                if execution["ok"]:
                    st.success("Vega OFF completed.")
                else:
                    st.error("Vega OFF failed.")
                st.rerun()

        if schedule.get("exists"):
            st.caption(
                f"Task {schedule.get('task_name')} status: {schedule.get('status', 'Unknown')}"
            )
        else:
            st.warning(
                "Vega 9:30 task is not configured yet. "
                "Run setup from terminal to register Bentley-Vega-IBKR-930."
            )

        if last_event:
            st.caption("Latest launcher event (from logs/last_bot_mode_event.json)")
            st.json(last_event)

        vega_output = st.session_state.get("vega_mode_output")
        if vega_output:
            with st.expander("Last Vega Command Output", expanded=False):
                st.code(vega_output, language="text")

        st.markdown("---")
        
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
            if not bots_df.empty:
                if "bot_name" not in bots_df.columns and "name" in bots_df.columns:
                    bots_df["bot_name"] = bots_df["name"]
                if "mansa_fund" not in bots_df.columns:
                    bots_df["mansa_fund"] = "Mansa Fund"

                # Normalize displayed bot names for known Mansa fund strategies.
                fund_to_bot = {
                    "mansa minerals - gold strategy": "Orion",
                    "mansa_minerals": "Orion",
                    "mansa minerals": "Orion",
                }

                def normalize_bot_name(row):
                    fund_value = str(row.get("mansa_fund", "")).strip().lower()
                    if fund_value in fund_to_bot:
                        return fund_to_bot[fund_value]
                    return row.get("bot_name", "")

                bots_df["bot_name"] = bots_df.apply(normalize_bot_name, axis=1)

                display_cols = [
                    "bot_name",
                    "mansa_fund",
                    "status",
                    "broker",
                    "uptime",
                ]
                available_cols = [col for col in display_cols if col in bots_df.columns]
                display_df = bots_df[available_cols].copy()
                display_df = display_df.rename(columns={
                    "bot_name": "Bot Name",
                    "mansa_fund": "Mansa Fund",
                    "status": "Status",
                    "broker": "Broker",
                    "uptime": "Uptime",
                })
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("No bots returned from API.")
        else:
            # Sample bot data
            bots = [
                {"id": 1, "bot_name": "Orion", "mansa_fund": "Mansa Minerals - Gold Strategy", "status": "running", "broker": "Alpaca", "uptime": "3d 5h"},
                {"id": 2, "bot_name": "Portfolio Optimizer", "mansa_fund": "Mansa Fund", "status": "running", "broker": "Multi", "uptime": "7d 12h"},
            ]
            st.dataframe(
                pd.DataFrame(bots).rename(columns={
                    "bot_name": "Bot Name",
                    "mansa_fund": "Mansa Fund",
                    "status": "Status",
                    "broker": "Broker",
                    "uptime": "Uptime",
                })[["Bot Name", "Mansa Fund", "Status", "Broker", "Uptime"]],
                use_container_width=True,
                hide_index=True,
            )
            
            for idx, bot in enumerate(bots):
                col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 1, 1])
                
                with col1:
                    st.markdown(f"**{bot['bot_name']}**")
                with col2:
                    st.markdown(get_status_badge(bot['status']), unsafe_allow_html=True)
                with col3:
                    st.text(f"Broker: {bot['broker']}")
                with col4:
                    st.text(f"Uptime: {bot['uptime']}")
                with col5:
                    if st.button("⏸️", key=f"stop_{idx}"):
                        st.info(f"Stopping {bot['bot_name']}...")
                with col6:
                    if st.button("📊", key=f"metrics_{idx}"):
                        st.info(f"Loading metrics for {bot['bot_name']}...")
                
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
        st.caption(
            "Portfolio optimization lens: monitor liquidity, drawdown, and concentration "
            "to inform fund-level repositioning and rebalance cadence."
        )
        
        # Risk metrics (Row 1)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Portfolio Drawdown", "-2.3%", "Within limits")
        with col2:
            st.metric("Margin Utilization", "34%", "Healthy")
        with col3:
            st.metric("Risk Violations Today", "0", "✓")
        with col4:
            # NEW: Trade Liquidity Ratio
            liquidity_ratio = 26.5  # Example: 26.5% cash available
            ratio_delta = "+3.2%" if liquidity_ratio >= 20 else "-Warning"
            ratio_color = "normal" if liquidity_ratio >= 20 else "inverse"
            st.metric("Trade Liquidity Ratio", f"{liquidity_ratio}%", ratio_delta, delta_color=ratio_color)
        
        st.markdown("---")
        
        # NEW: Liquidity Management Section
        st.markdown('<div class="section-header"><h3>💧 Liquidity & Dry Powder Management</h3></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("**Automatic Trade Liquidity Settings**")
            st.caption("Ensure sufficient cash reserves for alternative opportunities and market mobility")
            
            # Cash Reserve Buffer
            liquidity_buffer = st.slider(
                "Cash Reserve Buffer (%)", 
                min_value=10, 
                max_value=50, 
                value=25, 
                step=5,
                help="Recommended: 20-30% for optimal liquidity and opportunity capture"
            )
            
            # Profit Benchmark
            profit_benchmark = st.number_input(
                "Profit Benchmark for Liquidity Release (%)", 
                min_value=0.0, 
                max_value=100.0, 
                value=15.0, 
                step=0.5,
                help="When trades reach this profit %, release funds back to liquidity pool"
            )
            
            # Auto-rebalance
            auto_rebalance = st.checkbox(
                "Auto-rebalance to maintain liquidity buffer", 
                value=True,
                help="Automatically adjust positions to maintain target cash reserve"
            )
        
        with col2:
            st.markdown("**💰 Available Dry Powder**")
            
            # Sample calculations (replace with actual portfolio data)
            total_portfolio_value = 100000  # Example
            current_cash = total_portfolio_value * (liquidity_ratio / 100)
            target_cash = total_portfolio_value * (liquidity_buffer / 100)
            available_for_trades = max(0, current_cash - target_cash)
            
            st.metric("Total Cash", f"${current_cash:,.0f}")
            st.metric("Reserved Buffer", f"${target_cash:,.0f}")
            st.metric("Available Now", f"${available_for_trades:,.0f}", 
                     "Ready for deployment" if available_for_trades > 0 else "At limit")
            
            # Liquidity health indicator
            if liquidity_ratio >= liquidity_buffer:
                st.success("✅ Healthy liquidity position")
            elif liquidity_ratio >= (liquidity_buffer - 5):
                st.warning("⚠️ Approaching liquidity minimum")
            else:
                st.error("🔴 Below liquidity buffer")
        
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
            st.info(f"Liquidity buffer set to {liquidity_buffer}% | Profit benchmark at {profit_benchmark}%")
        
        st.markdown("---")
        
        # Liquidity deployment strategy
        with st.expander("📊 Liquidity Deployment Strategy"):
            st.markdown("""
            **How the Trade Liquidity Ratio works:**
            
            1. **Cash Reserve Buffer**: Maintains {buffer}% cash for rapid deployment on opportunities
            2. **Profit Benchmark**: When positions hit {benchmark}% profit, reallocate to liquidity pool
            3. **Auto-Rebalance**: System automatically adjusts to maintain target liquidity
            4. **Dry Powder Calculation**: `Available = Current Cash - Reserved Buffer`
            
            **Example:**
            - Portfolio Value: $100,000
            - Target Buffer: 25% → $25,000 reserved
            - Current Cash: 26.5% → $26,500
            - **Available Dry Powder: $1,500** for new opportunities
            
            This ensures you always have capital ready for:
            - Alternative trading opportunities
            - Market volatility response
            - Quick position adjustments
            - Opportunistic entries
            """.format(buffer=liquidity_buffer, benchmark=profit_benchmark))
        
        st.markdown("---")
        
        # Recent violations
        st.subheader("Recent Risk Events")
        st.text("No violations in the last 24 hours ✓")
    
    # TAB 6: MLflow Integration
    with tab6:
        st.markdown('<div class="section-header"><h2>🧠 MLflow Experiment Tracking</h2></div>', unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("🔌 MLflow Server Status")
            mlflow_scheme = urlparse(MLFLOW_URL).scheme.lower()
            if mlflow_scheme not in ("http", "https"):
                st.warning(f"⚠️ MLflow UI URL must be HTTP/HTTPS. Current value: {MLFLOW_URL}")
                st.info("Set `MLFLOW_SERVER_URL` to your tracking server URL, e.g. `http://localhost:5000`")
            else:
                connected, host_reachable, probe_note = probe_mlflow_server(MLFLOW_URL)
                if connected:
                    st.success(f"✅ MLflow server reachable at {MLFLOW_URL}")
                    st.caption(probe_note)
                elif host_reachable:
                    st.warning(f"⚠️ Host is reachable at {MLFLOW_URL}, but MLflow endpoints were not detected.")
                    st.info("Verify `MLFLOW_SERVER_URL` points to the MLflow server and not another service.")
                else:
                    st.error(f"❌ Cannot connect to MLflow server at {MLFLOW_URL}")
                    backend_store_uri = get_mlflow_backend_store_uri()
                    st.info(
                        "Start MLflow: "
                        f"`python -m mlflow server --backend-store-uri \"{backend_store_uri}\" --host 0.0.0.0 --port 5000`"
                    )

        with col2:
            st.subheader("🔗 Quick Actions")
            if st.button("🔄 Refresh MLflow Data", type="primary", use_container_width=True):
                st.rerun()
            if st.button("🌐 Open MLflow UI", use_container_width=True):
                st.markdown(f"[Open MLflow UI]({MLFLOW_URL})")

        st.markdown("---")
        st.subheader("📋 Recent Experiments")

        try:
            import mlflow
            from mlflow.tracking import MlflowClient

            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            client = MlflowClient()
            experiments = client.search_experiments()

            exp_rows = []
            total_runs = 0
            finished_runs = 0

            for exp in experiments[:25]:
                runs = mlflow.search_runs(experiment_ids=[exp.experiment_id], max_results=200)
                run_count = len(runs)
                total_runs += run_count
                if not runs.empty and "status" in runs.columns:
                    finished_runs += len(runs[runs["status"] == "FINISHED"])

                last_updated = "N/A"
                if not runs.empty and "start_time" in runs.columns:
                    ts = pd.to_datetime(runs["start_time"]).max()
                    if pd.notna(ts):
                        last_updated = ts.strftime('%Y-%m-%d %H:%M:%S')

                exp_rows.append({
                    "Experiment": exp.name,
                    "Experiment ID": exp.experiment_id,
                    "Lifecycle Stage": exp.lifecycle_stage,
                    "Runs": run_count,
                    "Last Updated": last_updated,
                })

            success_rate = (finished_runs / total_runs * 100) if total_runs > 0 else 0.0

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Active Experiments", len(experiments), "")
            with m2:
                st.metric("Total Runs", total_runs, "")
            with m3:
                st.metric("Finished Runs", finished_runs, "")
            with m4:
                st.metric("Success Rate", f"{success_rate:.1f}%", "")

            if exp_rows:
                st.dataframe(pd.DataFrame(exp_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No experiments found.")

        except Exception as e:
            error_text = str(e)
            st.error(f"❌ Failed to load experiments: {error_text}")
            if "Can't locate revision identified by" in error_text:
                st.warning("⚠️ MLflow database migrations are out of sync.")
                st.code(f"mlflow db upgrade \"{get_mlflow_backend_store_uri()}\"", language="bash")
            else:
                st.info("Make sure MLflow server is running and tracking URI points to the server URL.")

        st.markdown("---")
        with st.expander("⚙️ MLflow Configuration"):
            st.code(f"""
# MLflow Configuration
TRACKING_URI: {MLFLOW_TRACKING_URI}
SERVER_URL: {MLFLOW_URL}
BACKEND_STORE_URI: {get_mlflow_backend_store_uri()}

# Notes
- MLflow Training dashboard is merged into this ACC tab.
- Use SERVER_URL for web health checks/UI.
- Use BACKEND_STORE_URI for `mlflow db upgrade`.
            """, language="text")
    
    # TAB 7: System Logs
    with tab7:
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
