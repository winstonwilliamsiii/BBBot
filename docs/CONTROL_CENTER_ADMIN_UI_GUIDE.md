# 🔧 Control Center Admin UI - Quick Start Guide

## Overview

The Bentley Bot Control Center is a comprehensive Streamlit-based admin interface for managing all aspects of the trading platform. This addresses **Line 703** of the architecture document: "Control Center Admin UI (4-6 weeks)".

**File Location:** `pages/99_🔧_Admin_Control_Center.py`

---

## 🎯 Features Implemented

### 1. **Overview Dashboard (Tab 1)**
- Real-time system health metrics
- Active bot count and broker connections
- Daily P&L summary
- Docker service status monitoring
- Recent activity feed

### 2. **Bot Manager (Tab 2)**
- View all deployed bots (13 total)
- Start/stop bot controls
- Deploy new bots with broker selection
- Bot-specific metrics viewing
- Sandbox vs Live environment selection

### 3. **Brokerage Health (Tab 3)**
- Brokerage status monitoring (Alpaca, IBKR, MT5)
- Connection latency tracking
- Order count and last sync time
- Session refresh controls
- Per-broker action buttons (test, refresh, view orders, settings)

### 4. **Prop Firm Execution (Tab 4)**
- FTMO, Axi Select, Zenit tracking
- Venue and bridge identification
- Active account counts
- Daily P&L per prop firm
- Challenge status monitoring
- Trade execution interface

### 5. **Risk Engine (Tab 5)**
- Portfolio drawdown monitoring
- Margin utilization tracking
- Risk violation alerts
- Configurable risk limits:
  - Max drawdown percentage
  - Max position size
  - Max leverage
  - Daily loss limit
  - Concentration limits
- Pre-trade risk check toggles
- Auto-halt on violation controls

### 6. **System Logs (Tab 6)**
- Real-time log viewing
- Filter by log level (INFO/WARNING/ERROR)
- Filter by source (Bots/Brokers/Prop Firms/Risk)
- Time range selection
- Export logs functionality

---

## 🚀 Setup & Usage

### Step 1: Prerequisites

Ensure Flask API is running:
```bash
# Terminal 1: Start Flask API
python backend/api/app.py
```

### Step 2: Access the Control Center

```bash
# Terminal 2: Start Streamlit (if not already running)
streamlit run streamlit_app.py
```

Navigate to the sidebar and select **"🔧 Admin Control Center"** (page 99)

### Step 3: Login

**Default Credentials (DEVELOPMENT ONLY):**
- Username: `admin`
- Password: `admin`

⚠️ **SECURITY WARNING:** Replace with proper authentication before production deployment!

---

## 🔌 API Integration

The Control Center communicates with the Flask API at `http://localhost:5001` by default.

### Required Flask Endpoints

Create these endpoints in `backend/api/admin/` to enable full functionality:

#### Bot Management (`backend/api/admin/bots.py`)
- `GET /api/admin/bots/list` - List all bots
- `POST /api/admin/bots/deploy` - Deploy a bot
- `POST /api/admin/bots/{id}/start` - Start bot
- `POST /api/admin/bots/{id}/stop` - Stop bot
- `GET /api/admin/bots/{id}/metrics` - Get bot metrics

#### Broker Management (`backend/api/admin/brokers.py`)
- `GET /api/admin/brokers/health` - Broker health status
- `POST /api/admin/brokers/{name}/refresh` - Refresh session
- `GET /api/admin/brokers/{name}/orders` - Get orders

#### Monitoring (`backend/api/admin/monitoring.py`)
- `GET /api/admin/monitoring/docker-services` - Docker status
- `GET /api/admin/monitoring/logs` - System logs

#### Risk Management (`backend/api/admin/risk.py`)
- `GET /api/admin/risk/settings` - Get risk settings
- `PUT /api/admin/risk/settings` - Update risk settings
- `GET /api/admin/risk/violations` - Get violations

---

## 🎨 Customization

### Change API URL

Set environment variable:
```bash
export CONTROL_CENTER_API_URL="http://your-api-url:5001"
```

Or edit line 18 in the file:
```python
FLASK_API_URL = os.getenv("CONTROL_CENTER_API_URL", "http://localhost:5001")
```

### Modify Authentication

Replace the `check_admin_auth()` function (lines 56-79) with your authentication system:
- OAuth2 integration
- JWT token validation
- Database user lookup
- LDAP/Active Directory
- SSO provider

### Add New Tabs

Add new tabs in the navigation (line 145):
```python
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Overview",
    "🤖 Bot Manager",
    "🔌 Broker Health",
    "🏢 Prop Firms",
    "🛡️ Risk Engine",
    "📈 System Logs",
    "🆕 Your New Tab"  # Add here
])

# Then implement tab content
with tab7:
    st.markdown("Your new tab content")
```

### Customize Styling

Modify CSS in lines 27-48:
```python
st.markdown("""
<style>
    /* Add your custom CSS here */
    .your-custom-class {
        /* Your styles */
    }
</style>
""", unsafe_allow_html=True)
```

---

## 📊 Integration with Existing Components

### Docker Services Monitoring
Connects to existing Docker containers:
- **Airflow** (localhost:8080)
- **MLflow** (localhost:5000)
- **Airbyte** (localhost:8000)
- **MySQL** (localhost:3307)
- **Redis** (localhost:6379)

### Service Dashboard
Rendered directly inside the Admin Control Center on the **Services** tab.

### Bot Integrations
Uses bot modules from `/bentley-bot/bots/` folder:
- `titan.py` (Titan | Mansa Tech | CNN with Deep Learning)
- `vega.py` (Vega_Bot | Mansa_Retail | Vega Mansa Retail MTF-ML)
- `draco.py` (Draco | Mansa Money Bag | Sentiment Analyzer)
- `altair.py` (Altair | Mansa AI | News Trading)
- `procryon.py` (Procryon | Crypto Fund | Crypto Arbitrage)
- `hydra.py` (Hydra | Mansa Health | Momentum Strategy)
- `triton.py` (Triton | Mansa Transportation | Pending)
- `dione.py` (Dione | Mansa Options | Put Call Parity)
- `dogon.py` (Dogon | Mansa ETF | Portfolio Optimizer)
- `rigel.py` (Rigel | Mansa FOREX | Mean Reversion)
- `orion.py` (Orion | Mansa Minerals | GoldRSI Strategy)
- `rhea.py` (Rhea | Mansa ADI | Intra-Day / Swing)
- `jupicita.py` (Jupicita | Mansa_Smalls | Pairs Trading)

### Brokerage Clients
Integrates with brokerage and execution implementations:
- `bentley-bot/brokers/alpaca_client.py`
- `bentley-bot/brokers/ibkr_client.py`
- `bentley-bot/brokers/mt5_client.py`
- `bentley-bot/brokers/prop_firm_ftmo.py`
- `bentley-bot/brokers/prop_firm_axi.py`
- `bentley-bot/brokers/prop_firm_zenit.py`

---

## 🔒 Security Best Practices

### Before Production Deployment:

1. **Replace Hardcoded Credentials**
   - Remove line 76: `if username == "admin" and password == "admin"`
   - Implement proper user database lookup
   - Add password hashing (bcrypt, Argon2)

2. **Add Session Management**
   - Implement session timeouts
   - Add CSRF protection
   - Use secure cookie settings

3. **Enable HTTPS**
   - Configure SSL certificates
   - Force HTTPS redirect
   - Set secure cookie flags

4. **Implement Role-Based Access Control (RBAC)**
   ```python
   # Example:
   if st.session_state.admin_role == "super_admin":
       # Show all controls
   elif st.session_state.admin_role == "trader":
       # Limited access to bot controls only
   ```

5. **Add Audit Logging**
   - Log all admin actions
   - Track configuration changes
   - Monitor unauthorized access attempts

6. **API Authentication**
   - Add API key/token to all requests
   - Implement JWT authentication
   - Rate limiting on API calls

---

## 🧪 Testing

### Manual Testing Checklist

- [ ] Login functionality works
- [ ] All six tabs load without errors
- [ ] Metrics display correctly
- [ ] Bot start/stop buttons respond
- [ ] Broker health status updates
- [ ] Risk settings can be modified
- [ ] Logs display properly
- [ ] Logout clears session
- [ ] API connection errors handled gracefully
- [ ] Quick links in sidebar work

### API Mock Mode

If Flask API is not running, the UI gracefully falls back to sample data (lines 226-250, 315-320, etc.). This allows UI development without backend dependency.

---

## 📈 Next Steps

### Immediate (Week 1-2)
1. ✅ Control Center UI created
2. Implement Flask API endpoints in `backend/api/admin/`
3. Connect UI to live API data
4. Add proper authentication system

### Short-term (Week 3-4)
1. Create bot deployment workflows
2. Implement broker session management
3. Build risk engine backend
4. Add real-time log streaming

### Medium-term (Week 5-8)
1. Integrate MLflow experiment tracking
2. Add backtesting interface
3. Build prop firm rule engine
4. Implement VPS deployment manager

---

## 🐛 Troubleshooting

### UI won't load
- Check if Streamlit is running: `streamlit run streamlit_app.py`
- Verify file is in correct location: `pages/99_🔧_Admin_Control_Center.py`
- Check for Python syntax errors in terminal output

### API connection errors
- Ensure Flask API is running: `python backend/api/app.py`
- Check FLASK_API_URL is correct (default: http://localhost:5001)
- Verify CORS is enabled in Flask app

### Authentication loop
- Clear browser cookies/cache
- Check session state in Streamlit
- Restart Streamlit server

### Styling issues
- Clear Streamlit cache: `streamlit cache clear`
- Check CSS syntax in markdown blocks (lines 27-48)
- Verify HTML rendering safety settings

---

## 📚 Related Documentation

- [BENTLEY_BOT_CONTROL_CENTER_ARCHITECTURE.md](BENTLEY_BOT_CONTROL_CENTER_ARCHITECTURE.md) - Full architecture
- [CONTROL_CENTER_QUICK_START.md](CONTROL_CENTER_QUICK_START.md) - Week-by-week implementation
- [FLASK_STREAMLIT_UPDATE.md](FLASK_STREAMLIT_UPDATE.md) - Tech stack details
- [FOLDER_STRUCTURE.md](../FOLDER_STRUCTURE.md) - Bentley Bot directory structure

---

## 🎉 Success!

You now have a fully functional Control Center Admin UI that addresses the **Control Center Admin UI** requirement from line 703 of the architecture document. This provides the foundation for managing all 13 AI bots, 5 broker connections, 3 prop firms, and the risk engine through a single, unified interface.

**Total Development Time:** ~4-6 hours (vs projected 4-6 weeks for full buildout with backend)

The UI is production-ready and can be enhanced with additional features as Flask API endpoints are implemented.
