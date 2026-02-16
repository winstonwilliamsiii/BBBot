# 🚀 Bentley Bot Control Center - Quick Start Guide

**Purpose:** Get the admin layer foundation running in **4-6 weeks**

**Tech Stack:** Flask (backend API) + Streamlit (admin UI)

---

## Week 1-2: Control Center Dashboard Foundation

### Day 1: Create Bentley Bot Folder Structure

**First, create the organized folder structure:**

```bash
# Create main bentley-bot directory
mkdir -p bentley-bot

# Create bot modules (13 bots)
mkdir -p bentley-bot/bots
touch bentley-bot/bots/__init__.py
touch bentley-bot/bots/{bot1,bot2,bot3,bot4,bot5,bot6,bot7,bot8,bot9,bot10,bot11,bot12,bot13}.py

# Create broker clients
mkdir -p bentley-bot/brokers
touch bentley-bot/brokers/__init__.py
touch bentley-bot/brokers/{alpaca,schwab,ibkr,binance,coinbase}.py

# Create prop firm connectors
mkdir -p bentley-bot/prop_firms
touch bentley-bot/prop_firms/__init__.py
touch bentley-bot/prop_firms/{ftmo_mt5,axi_mt5,zenit_ninja}.py

# Create MLflow pipelines
mkdir -p bentley-bot/mlflow
touch bentley-bot/mlflow/__init__.py
touch bentley-bot/mlflow/{train,backtest,register}.py

# Create Streamlit UI modules
mkdir -p bentley-bot/streamlit_app
touch bentley-bot/streamlit_app/__init__.py
touch bentley-bot/streamlit_app/{admin,investor,dashboards}.py

# Create utilities
mkdir -p bentley-bot/utils
touch bentley-bot/utils/__init__.py
touch bentley-bot/utils/{risk,config,secrets}.py
```

### Day 2: Flask Admin API Setup

```bash
# Create admin API structure
mkdir -p backend/api/admin
touch backend/api/admin/__init__.py
touch backend/api/admin/bots.py
touch backend/api/admin/brokers.py
touch backend/api/admin/risk.py
touch backend/api/admin/monitoring.py
```

**File: `backend/api/admin/bots.py`**
```python
"""Bot Management API - Deploy, start, stop, monitor bots"""
from flask import Blueprint, jsonify, request
import docker

bots_bp = Blueprint('bots', __name__, url_prefix='/admin/bots')

@bots_bp.route('/list', methods=['GET'])
def list_bots():
    """List all deployed bots"""
    # TODO: Query database for registered bots
    return jsonify({"bots": []})

@bots_bp.route('/deploy/<bot_name>', methods=['POST'])
def deploy_bot(bot_name):
    """Deploy a bot to environment"""
    data = request.get_json()
    environment = data.get('environment', 'staging')
    # TODO: Copy bot code to deployment folder
    # TODO: Start bot process
    # TODO: Register in database
    return jsonify({"status": "deployed", "bot": bot_name, "env": environment})

@bots_bp.route('/start/<bot_id>', methods=['POST'])
def start_bot(bot_id):
    """Start a bot"""
    # TODO: Send start signal to bot process
    return jsonify({"status": "started", "bot_id": bot_id})

@bots_bp.route('/stop/<bot_id>', methods=['POST'])
def stop_bot(bot_id):
    """Stop a bot gracefully"""
    # TODO: Send stop signal to bot
    return jsonify({"status": "stopped", "bot_id": bot_id})

@bots_bp.route('/metrics/<bot_id>', methods=['GET'])
def get_bot_metrics(bot_id):
    """Get bot performance metrics"""
    # TODO: Query MLflow for bot metrics
    # TODO: Calculate Sharpe, drawdown, win rate
    return jsonify({"bot_id": bot_id, "metrics": {}})
```

**File: `backend/api/admin/brokers.py`**
```python
"""Broker Orchestration API - Health checks, sessions, routing"""
from flask import Blueprint, jsonify
from frontend.utils.broker_interface import create_broker_client

brokers_bp = Blueprint('brokers', __name__, url_prefix='/admin/brokers')

@brokers_bp.route('/health', methods=['GET'])
def check_all_brokers():
    """Check connection status of all brokers"""
    brokers = ['alpaca', 'mt5', 'ibkr', 'binance']
    status = {}
    
    for broker_name in brokers:
        try:
            broker = create_broker_client(broker_name)
            equity = broker.get_equity()
            status[broker_name] = {"status": "connected", "equity": equity}
        except Exception as e:
            status[broker_name] = {"status": "error", "error": str(e)}
    
    return jsonify(status)

@brokers_bp.route('/sessions', methods=['GET'])
def list_active_sessions():
    """List active broker sessions"""
    # TODO: Query database for active sessions
    return jsonify({"sessions": []})

@brokers_bp.route('/refresh/<broker>', methods=['POST'])
def refresh_broker_session(broker):
    """Refresh OAuth token or reconnect"""
    # TODO: Call broker's refresh logic
    return jsonify({"status": "refreshed", "broker": broker})

@brokers_bp.route('/latency', methods=['GET'])
def measure_latency():
    """Measure order execution latency per broker"""
    # TODO: Send test orders, measure time to fill
    return jsonify({"latencies": {}})
```

**File: `backend/api/admin/risk.py`**
```python
"""Risk Engine API - Pre-trade checks, position limits, compliance"""
from flask import Blueprint, jsonify, request

risk_bp = Blueprint('risk', __name__, url_prefix='/admin/risk')

@risk_bp.route('/validate-order', methods=['POST'])
def validate_order():
    data = request.get_json()
    symbol = data.get('symbol')
    qty = data.get('qty')
    side = data.get('side')
    account_id = data.get('account_id')
    """Run pre-trade risk checks"""
    # TODO: Check position size limits
    # TODO: Check margin requirements
    # TODO: Check concentration limits
    # TODO: Check prop firm rules
    return jsonify({"approved": True, "checks_passed": []})

@risk_bp.route('/exposure', methods=['GET'])
def get_current_exposure():
    """Get portfolio-level risk exposure"""
    # TODO: Calculate total notional exposure
    # TODO: Calculate leverage ratio
    # TODO: Calculate VaR (Value at Risk)
    return jsonify({"exposure": {}})

@risk_bp.route('/drawdown', methods=['GET'])
def get_drawdown_status():
    """Check current drawdown vs limits"""
    # TODO: Calculate current drawdown
    # TODO: Compare to prop firm limits
    # TODO: Alert if approaching limit
    return jsonify({"drawdown": 0, "limit": 0.1, "status": "ok"})

@risk_bp.route('/halt-trading', methods=['POST'])
def halt_all_trading():
    """Emergency halt all bots"""
    data = request.get_json()
    reason = data.get('reason', 'manual')
    # TODO: Send stop signals to all bots
    # TODO: Cancel all pending orders
    # TODO: Log halt event
    return jsonify({"status": "halted", "reason": reason})
```

**File: `backend/api/admin/monitoring.py`**
```python
"""Monitoring API - Logs, errors, analytics"""
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/admin/monitoring')

@monitoring_bp.route('/logs', methods=['GET'])
def get_recent_logs():
    service = request.args.get('service', 'all')
    limit = int(request.args.get('limit', 100))
    """Get recent logs from services"""
    # TODO: Query centralized log storage
    return jsonify({"logs": []})

@monitoring_bp.route('/errors', methods=['GET'])
def get_error_summary():
    """Get error summary for past N hours"""
    hours = int(request.args.get('hours', 24))
    # TODO: Query error tracking system
    return jsonify({"errors": [], "error_rate": 0})

@monitoring_bp.route('/execution-quality', methods=['GET'])
def get_execution_analytics():
    """Get execution quality metrics"""
    # TODO: Calculate average slippage
    # TODO: Calculate fill rate
    # TODO: Calculate latency percentiles
    return jsonify({
        "avg_slippage_bps": 0,
        "fill_rate": 0.99,
        "p50_latency_ms": 100,
        "p99_latency_ms": 500
    })

@monitoring_bp.route('/bot-performance', methods=['GET'])
def get_all_bot_performance():
    """Get performance summary for all bots"""
    # TODO: Query MLflow metrics
    # TODO: Calculate aggregate stats
    return jsonify({"bots": []})
```

### Day 3-4: Admin UI Setup with Streamlit

**Option 1: Streamlit Admin Dashboard (Recommended)**

**File: `pages/99_🔧_Admin_Control_Center.py`**
```python
"""Bentley Bot Control Center - Streamlit Admin Dashboard"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Bentley Bot Control Center",
    page_icon="🔧",
    layout="wide"
)

# Check admin authentication
if 'admin_authenticated' not in st.session_state:
    st.warning("⚠️ Admin access only. Please authenticate.")
    password = st.text_input("Admin Password", type="password")
    if st.button("Login"):
        if password == st.secrets.get("ADMIN_PASSWORD", "admin123"):
            st.session_state.admin_authenticated = True
            st.rerun()
        else:
            st.error("Invalid password")
    st.stop()

# Admin dashboard
st.title("🚀 Bentley Bot Control Center")
st.caption("Internal Admin Dashboard - Mansa Capital Partners")

# API base URL
API_URL = "http://localhost:5000/admin"

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview", "🤖 Bots", "🔌 Brokers", "🛡️ Risk", "📋 Logs"
])

with tab1:
    st.header("System Overview")
    
    # Service health
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Airflow", "Running", delta="✅")
    with col2:
        st.metric("MLflow", "Running", delta="✅")
    with col3:
        st.metric("Airbyte", "Running", delta="✅")
    with col4:
        st.metric("MySQL", "Connected", delta="✅")
    
    st.divider()
    
    # Broker health
    st.subheader("🔌 Broker Status")
    try:
        response = requests.get(f"{API_URL}/brokers/health", timeout=5)
        if response.ok:
            brokers = response.json()
            broker_df = pd.DataFrame([
                {"Broker": name.upper(), "Status": data.get('status', 'unknown')}
                for name, data in brokers.items()
            ])
            st.dataframe(broker_df, use_container_width=True)
        else:
            st.error("Failed to fetch broker status")
    except Exception as e:
        st.warning(f"Flask API not running: {e}")
        st.info("Start Flask API: `python backend/api/app.py`")
    
    st.divider()
    
    # Risk summary
    st.subheader("🛡️ Risk Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Drawdown", "-2.3%", delta="-0.5%")
    with col2:
        st.metric("Max DD Limit", "-10%")
    with col3:
        st.metric("Leverage", "1.2x")
    with col4:
        st.metric("Exposure", "$125,430")

with tab2:
    st.header("🤖 Bot Management")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button("🔄 Refresh Bot List", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("🚀 Deploy New Bot", use_container_width=True):
            st.session_state.show_deploy_form = True
    
    with col3:
        if st.button("🛑 Emergency Halt All", type="primary", use_container_width=True):
            try:
                response = requests.post(f"{API_URL}/risk/halt-trading", 
                                       json={"reason": "manual_halt"})
                if response.ok:
                    st.success("✅ All bots halted!")
                else:
                    st.error("Failed to halt bots")
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.divider()
    
    # Bot list (mock data)
    bots_data = [
        {"Bot Name": "GoldRSI_v1", "Status": "🟢 Running", "P&L": "+$1,234", "Trades": 45},
        {"Bot Name": "UsdCop_v2", "Status": "🔴 Stopped", "P&L": "+$567", "Trades": 23},
        {"Bot Name": "GBPJPY_MT5", "Status": "🟢 Running", "P&L": "+$890", "Trades": 34},
    ]
    
    df = pd.DataFrame(bots_data)
    st.dataframe(df, use_container_width=True)
    
    # Bot actions
    st.subheader("Bot Actions")
    selected_bot = st.selectbox("Select Bot", [b["Bot Name"] for b in bots_data])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶️ Start", use_container_width=True):
            st.success(f"Starting {selected_bot}...")
    with col2:
        if st.button("⏸️ Stop", use_container_width=True):
            st.warning(f"Stopping {selected_bot}...")
    with col3:
        if st.button("🔄 Restart", use_container_width=True):
            st.info(f"Restarting {selected_bot}...")

with tab3:
    st.header("🔌 Broker Console")
    
    # Broker health checks
    st.subheader("Connection Status")
    
    try:
        response = requests.get(f"{API_URL}/brokers/health", timeout=5)
        if response.ok:
            brokers = response.json()
            
            for broker_name, broker_data in brokers.items():
                with st.expander(f"📡 {broker_name.upper()}", expanded=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        status = broker_data.get('status', 'unknown')
                        if status == 'connected':
                            st.success(f"✅ {status.upper()}")
                        else:
                            st.error(f"❌ {status.upper()}")
                    
                    with col2:
                        if st.button("🔄 Refresh", key=f"refresh_{broker_name}"):
                            st.info(f"Refreshing {broker_name}...")
                    
                    with col3:
                        if st.button("🧪 Test", key=f"test_{broker_name}"):
                            st.info(f"Testing {broker_name}...")
                    
                    if 'equity' in broker_data:
                        st.metric("Account Equity", f"${broker_data['equity']:,.2f}")
        else:
            st.error("Unable to fetch broker status")
    except Exception as e:
        st.warning(f"Flask API not available: {e}")

with tab4:
    st.header("🛡️ Risk Monitor")
    
    # Current risk metrics
    st.subheader("Current Risk Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Portfolio Drawdown", "-2.3%", delta="-0.5%", delta_color="inverse")
    with col2:
        st.metric("Daily P&L", "+$1,234", delta="+5.2%")
    with col3:
        st.metric("Open Positions", "12")
    with col4:
        st.metric("Available Margin", "$45,230")
    
    st.divider()
    
    # Risk limits configuration
    st.subheader("⚙️ Risk Limits Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_drawdown = st.slider("Max Drawdown (%)", 0, 20, 10)
        max_position_size = st.slider("Max Position Size (%)", 0, 50, 10)
    
    with col2:
        max_leverage = st.slider("Max Leverage Ratio", 1.0, 5.0, 2.0, 0.1)
        max_concentration = st.slider("Max Concentration (%)", 0, 50, 20)
    
    if st.button("💾 Save Risk Limits", type="primary"):
        st.success("✅ Risk limits updated!")

with tab5:
    st.header("📋 Execution Logs")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        log_service = st.selectbox("Service", ["All", "Bots", "Brokers", "Risk", "System"])
    with col2:
        log_level = st.selectbox("Level", ["All", "ERROR", "WARN", "INFO", "DEBUG"])
    with col3:
        log_limit = st.number_input("Limit", min_value=10, max_value=1000, value=100)
    
    if st.button("🔄 Refresh Logs"):
        st.rerun()
    
    st.divider()
    
    # Mock logs
    logs_data = [
        {"Time": "2026-02-15 10:23:45", "Level": "INFO", "Service": "GoldRSI_v1", "Message": "Trade executed: BUY GLD @ $180.50"},
        {"Time": "2026-02-15 10:23:40", "Level": "WARN", "Service": "Risk", "Message": "Approaching drawdown limit: -8.5%"},
        {"Time": "2026-02-15 10:23:35", "Level": "INFO", "Service": "Alpaca", "Message": "Connection established"},
        {"Time": "2026-02-15 10:23:30", "Level": "ERROR", "Service": "MT5", "Message": "Connection timeout - retrying..."},
    ]
    
    df = pd.DataFrame(logs_data)
    st.dataframe(df, use_container_width=True, height=400)
    
    # Export logs
    if st.button("📥 Export Logs to CSV"):
        csv = df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            file_name=f"bentley_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# Footer
st.divider()
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    st.caption("💡 MLflow: http://localhost:5000")
with col2:
    st.caption("📊 Airflow: http://localhost:8080")
with col3:
    if st.button("🚪 Logout"):
        st.session_state.admin_authenticated = False
        st.rerun()
```

**Option 2: HTML Dashboard (If needed)**

**File: `admin_ui/dashboard.html`**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Bentley Bot Control Center</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: #0a0e27;
            color: #fff;
        }
        .container { max-width: 1600px; margin: 0 auto; padding: 20px; }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: #1a1f3a;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #2a3055;
        }
        .card h3 { 
            color: #667eea; 
            margin-bottom: 15px;
            font-size: 18px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #2a3055;
        }
        .metric:last-child { border-bottom: none; }
        .status { 
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        .status.online { background: #10b981; }
        .status.offline { background: #ef4444; }
        .status.warning { background: #f59e0b; }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }
        .btn-primary { background: #667eea; color: white; }
        .btn-danger { background: #ef4444; color: white; }
        .btn:hover { opacity: 0.8; transform: translateY(-1px); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Bentley Bot Control Center</h1>
            <p>Internal Admin Dashboard - Mansa Capital Partners</p>
        </div>

        <!-- Service Health Grid -->
        <div class="grid">
            <div class="card">
                <h3>📊 Service Health</h3>
                <div id="service-health"></div>
            </div>

            <div class="card">
                <h3>🔌 Broker Status</h3>
                <div id="broker-status"></div>
            </div>

            <div class="card">
                <h3>🤖 Active Bots</h3>
                <div id="bot-status"></div>
            </div>

            <div class="card">
                <h3>🛡️ Risk Summary</h3>
                <div id="risk-summary"></div>
            </div>
        </div>

        <!-- Bot Management Section -->
        <div class="card" style="margin-bottom: 20px;">
            <h3>🤖 Bot Management</h3>
            <div style="display: flex; gap: 10px; margin-top: 15px;">
                <button class="btn btn-primary" onclick="deployBot()">🚀 Deploy Bot</button>
                <button class="btn btn-primary" onclick="viewMLflow()">📊 MLflow Dashboard</button>
                <button class="btn btn-danger" onclick="haltAll()">🛑 Emergency Halt</button>
            </div>
        </div>

        <!-- Quick Actions -->
        <div class="card">
            <h3>⚡ Quick Actions</h3>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
                <button class="btn btn-primary" onclick="location.href='bots.html'">Manage Bots</button>
                <button class="btn btn-primary" onclick="location.href='brokers.html'">Broker Console</button>
                <button class="btn btn-primary" onclick="location.href='risk.html'">Risk Monitor</button>
                <button class="btn btn-primary" onclick="location.href='logs.html'">View Logs</button>
            </div>
        </div>
    </div>

    <script>
        // Fetch data from FastAPI backend
        async function loadDashboard() {
            // Service Health
            const services = [
                {name: 'Airflow', port: 8080, status: 'online'},
                {name: 'MLflow', port: 5000, status: 'online'},
                {name: 'Airbyte', port: 8000, status: 'online'},
                {name: 'Streamlit', port: 8501, status: 'warning'}
            ];
            
            const serviceHTML = services.map(s => `
                <div class="metric">
                    <span>${s.name} :${s.port}</span>
                    <span class="status ${s.status}">${s.status}</span>
                </div>
            `).join('');
            document.getElementById('service-health').innerHTML = serviceHTML;

            // Broker Status (fetch from API)
            try {
                const response = await fetch('http://localhost:8000/admin/brokers/health');
                const brokers = await response.json();
                
                const brokerHTML = Object.entries(brokers).map(([name, data]) => `
                    <div class="metric">
                        <span>${name.toUpperCase()}</span>
                        <span class="status ${data.status === 'connected' ? 'online' : 'offline'}">
                            ${data.status}
                        </span>
                    </div>
                `).join('');
                document.getElementById('broker-status').innerHTML = brokerHTML;
            } catch (e) {
                document.getElementById('broker-status').innerHTML = 
                    '<p style="color: #ef4444;">Unable to connect to API</p>';
            }

            // Bot Status (mock data)
            const bots = [
                {name: 'GoldRSI_v1', status: 'running', pnl: '+$1,234'},
                {name: 'UsdCop_v2', status: 'stopped', pnl: '+$567'},
                {name: 'GBPJPY_MT5', status: 'running', pnl: '+$890'}
            ];
            
            const botHTML = bots.map(b => `
                <div class="metric">
                    <div>
                        <strong>${b.name}</strong><br>
                        <small>${b.pnl}</small>
                    </div>
                    <span class="status ${b.status === 'running' ? 'online' : 'offline'}">
                        ${b.status}
                    </span>
                </div>
            `).join('');
            document.getElementById('bot-status').innerHTML = botHTML;

            // Risk Summary
            document.getElementById('risk-summary').innerHTML = `
                <div class="metric">
                    <span>Current Drawdown</span>
                    <span style="color: #10b981;">-2.3%</span>
                </div>
                <div class="metric">
                    <span>Max Drawdown Limit</span>
                    <span>-10%</span>
                </div>
                <div class="metric">
                    <span>Portfolio Exposure</span>
                    <span>$125,430</span>
                </div>
                <div class="metric">
                    <span>Leverage Ratio</span>
                    <span>1.2x</span>
                </div>
            `;
        }

        function deployBot() {
            alert('Opening Bot Deployment Manager...');
            // TODO: Open modal with bot selection + environment
        }

        function viewMLflow() {
            window.open('http://localhost:5000', '_blank');
        }

        function haltAll() {
            if (confirm('Emergency halt ALL bots? This will stop all trading immediately.')) {
                fetch('http://localhost:8000/admin/risk/halt-trading', {method: 'POST'})
                    .then(() => alert('✅ All bots halted'))
                    .catch(() => alert('❌ Failed to halt bots'));
            }
        }

        // Auto-refresh every 10 seconds
        loadDashboard();
        setInterval(loadDashboard, 10000);
    </script>
</body>
</html>
```

### Day 5: Connect to Existing Infrastructure

**Create Flask API Server: `backend/api/app.py`**
```python
from flask import Flask, jsonify
from flask_cors import CORS
from backend.api.admin.bots import bots_bp
from backend.api.admin.brokers import brokers_bp
from backend.api.admin.risk import risk_bp
from backend.api.admin.monitoring import monitoring_bp

app = Flask(__name__)

# Enable CORS for Streamlit
CORS(app, resources={r"/admin/*": {"origins": "*"}})

# Register admin blueprints
app.register_blueprint(bots_bp)
app.register_blueprint(brokers_bp)
app.register_blueprint(risk_bp)
app.register_blueprint(monitoring_bp)

@app.route('/')
def root():
    return jsonify({
        "message": "Bentley Bot Control Center API",
        "version": "1.0.0",
        "endpoints": ["/admin/bots", "/admin/brokers", "/admin/risk", "/admin/monitoring"]
    })

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

---

## Week 3-4: Broker Orchestration

### Task 1: Complete IBKR Integration

**File: `frontend/utils/broker_interface.py`** (update)
```python
class IBKRBrokerClient(BrokerClient):
    """Interactive Brokers implementation via TWS API"""
    
    def __init__(self):
        from ibapi.client import EClient
        from ibapi.wrapper import EWrapper
        
        # TODO: Initialize TWS connection
        self.client_id = 1
        self.host = "127.0.0.1"
        self.port = 7497  # TWS paper trading port
        
    def get_equity(self) -> float:
        # TODO: Request account value
        pass
    
    def get_positions(self) -> List[Position]:
        # TODO: Request positions
        pass
    
    def place_order(self, symbol, qty, side):
        # TODO: Create and submit order
        pass
```

### Task 2: Schwab OAuth Migration

**File: `backend/services/schwab_oauth.py`**
```python
"""Schwab OAuth 2.0 Authentication"""
import requests
from datetime import datetime, timedelta

class SchwabOAuth:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_url = "https://api.schwabapi.com/v1/oauth/authorize"
        self.token_url = "https://api.schwabapi.com/v1/oauth/token"
    
    def get_authorization_url(self):
        """Get URL for user to authorize"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code"
        }
        return f"{self.auth_url}?{'&'.join(f'{k}={v}' for k,v in params.items())}"
    
    def exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(self.token_url, data=data)
        return response.json()
    
    def refresh_token(self, refresh_token):
        """Refresh expired access token"""
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(self.token_url, data=data)
        return response.json()
```

---

## Quick Commands

```bash
# Start Flask API server
cd C:\Users\winst\BentleyBudgetBot
python backend/api/app.py
# API runs on http://localhost:5000

# Start Streamlit admin dashboard (in new terminal)
streamlit run streamlit_app.py
# Admin available at: http://localhost:8501
# Navigate to: Pages → 🔧 Admin Control Center

# Check broker health
curl http://localhost:5000/admin/brokers/health

# Check logs
docker logs bentley-mlflow --tail 50
```

---

## Next Steps After Week 2

1. Complete Phase 1 tasks (Week 3-6)
2. Deploy to GCP Cloud Run
3. Set up monitoring alerts
4. Begin Phase 2 (ML Bot Orchestration)

---

**Need Help?** Check [BENTLEY_BOT_CONTROL_CENTER_ARCHITECTURE.md](./BENTLEY_BOT_CONTROL_CENTER_ARCHITECTURE.md) for full roadmap.
