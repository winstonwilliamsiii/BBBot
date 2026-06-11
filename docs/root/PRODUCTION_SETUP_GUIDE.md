"""
Production Environment Setup Guide

For running Bentley Budget Bot with multiple brokers in Live/Paper modes.

This guide covers:
1. Setting up broker credentials in Streamlit Cloud
2. Configuring Live/Paper mode for each broker
3. Selecting which bots run and which accounts they use
4. Monitoring and switching modes from Dashboard
"""

# PRODUCTION SETUP FOR BENTLEY BUDGET BOT

## 1. Streamlit Cloud Secrets Configuration

### Location
Settings → Secrets (in Streamlit Cloud app dashboard)

### Step 1: Paste your broker credentials

Copy the following template into Streamlit Cloud Secrets and replace `YOUR_*_HERE` with actual credentials:

```toml
# Alpaca Markets - Stock/ETF/Crypto Trading
[alpaca]
ALPACA_PAPER = "true"  # "true" for paper trading, "false" for live
ALPACA_PAPER_API_KEY = "YOUR_ALPACA_PAPER_API_KEY_HERE"
ALPACA_PAPER_SECRET_KEY = "YOUR_ALPACA_PAPER_SECRET_KEY_HERE"
ALPACA_LIVE_API_KEY = "YOUR_ALPACA_LIVE_API_KEY_HERE"    # Optional, only if live trading
ALPACA_LIVE_SECRET_KEY = "YOUR_ALPACA_LIVE_SECRET_KEY_HERE"  # Optional

# MetaTrader 5 / AXI / FTMO - Forex & Commodities
[mt5]
MT5_USER = "YOUR_MT5_ACCOUNT_NUMBER"
MT5_PASSWORD = "YOUR_MT5_PASSWORD"
MT5_SERVER = "Axi-US51-Live"  # Or FTMO server name
MT5_PORT = "443"               # Usually 443

# AXI-specific settings (if using AXI)
[axi]
AXI_MT5_USER = "YOUR_AXI_ACCOUNT_NUMBER"
AXI_MT5_PASSWORD = "YOUR_AXI_PASSWORD"
AXI_MT5_SERVER = "Axi-US51-Live"  # AXI live server (or demo)
AXI_MT5_PORT = "443"

# IBKR (Interactive Brokers) - Coming soon
[ibkr]
IBKR_HOST = "127.0.0.1"
IBKR_PORT = "7496"
IBKR_CLIENT_ID = "1"

# MySQL Database (if using cloud database)
[mysql]
MYSQL_HOST = "your-db-host.railway.app"
MYSQL_PORT = "3306"
MYSQL_USER = "root"
MYSQL_PASSWORD = "YOUR_MYSQL_PASSWORD"
MYSQL_DATABASE = "bbbot1"

# MLflow Tracking
[mlflow]
MLFLOW_TRACKING_URI = "http://localhost:5000"
```

### Step 2: Get your broker credentials

#### Alpaca Markets
1. Go to https://alpaca.markets/
2. Create Paper Trading Account (free):
   - Copy "Paper API Key" → `ALPACA_PAPER_API_KEY`
   - Copy "Secret Key" → `ALPACA_PAPER_SECRET_KEY`
3. (Optional) Create Live Trading Account if you want real money trading:
   - Copy "Live API Key" → `ALPACA_LIVE_API_KEY`
   - Copy "Secret Key" → `ALPACA_LIVE_SECRET_KEY`

#### AXI / FTMO MetaTrader 5
1. Get your MT5 account details from your AXI/FTMO account page
2. Account number, password, and server name are typically in account settings
3. Common servers:
   - AXI Live: `Axi-US51-Live` or `Axi-US51-Demo`
   - FTMO: `ftmo.traders` (or your specific server)

#### Interactive Brokers (IBKR)
1. Install TWS (Trader Workstation) or IB Gateway
2. Go to Edit → Settings → API → Settings
3. Enable API and note Host, Port, Client ID

### Step 3: Deploy with new secrets

1. Save the secrets file (Streamlit Cloud will auto-detect changes)
2. Streamlit will automatically redeploy your app
3. Check the "Deployed" status in the app logs

---

## 2. Managing Trading Modes from Dashboard

### Access the Control Center
1. Open your Bentley Budget Bot app
2. Go to "🔧 Admin Control Center" page
3. Click the "🎮 Broker Modes" tab

### Global Mode Control
- **Paper Mode**: Default - all trades are simulated, no real money
- **Live Mode**: Real money trading - only use if accounts are funded

Click "Apply Global Mode" to switch.

### Per-Broker Mode Overrides
Switch individual brokers to different modes:
- Alpaca → Paper (for testing)
- MT5 → Live (for real prop firm trading)

This lets you run ML experiments on paper while live trading on prop accounts.

### Bot Control
- **Start Bot**: Activates bot in the control system
- **Stop Bot**: Deactivates bot (pauses trading)

Note: This controls the bot registry but does not forcefully kill running processes.
Use PowerShell commands to fully stop running bots.

### Environment Variable Overrides
For quick mode switching without Streamlit:

```powershell
# Switch Alpaca to LIVE mode (overrides config file)
$env:ALPACA_MODE = "live"

# Switch MT5 to PAPER mode
$env:MT5_MODE = "paper"

# Check current setting
Write-Host "Alpaca Mode: $($env:ALPACA_MODE)"
```

---

## 3. Bot-to-Account Mapping

By default, each bot is assigned to a broker:

| Bot | Broker | Accounts | Mode |
|-----|--------|----------|------|
| Titan | Alpaca | Paper + Live | Configurable |
| Vega | IBKR | Paper  (for now) | Paper |
| Rigel | MT5 | FTMO Paper/Live | Configurable |
| Dogon | MT5 | Prop Firm | Configurable |
| Orion | MT5 | Forex Props | Configurable |
| Draco | Alpaca | Paper | Paper |
| Altair | Alpaca | Paper | Paper |
| Procryon | Alpaca | Crypto | Configurable |
| ... | ... | ... | ... |

## 4. ML Experiments Strategy

Run ML training on Paper while trading Live:

1. **Training Setup**:
   ```powershell
   # Terminal 1: Start Rigel & Dogon on PAPER (ML experiments)
   $env:MT5_MODE = "paper"
   python -m src.bots.rigel
   python -m src.bots.dogon
   ```

2. **Live Accounts** (other bots):
   ```powershell
   # Terminal 2: Titan & Orion on LIVE (real trading)
   $env:ALPACA_MODE = "live"
   python -m src.bots.titan
   python -m src.bots.orion
   ```

3. **Monitor from Dashboard**:
   - Watch each bot's P&L in "🎮 Broker Modes" tab
   - Switch modes as needed
   - Track A/B test results in MLflow

---

## 5. Credential Security Best Practices

### ✅ DO:
- Use separate Paper & Live API keys per broker
- Rotate API keys quarterly
- Use strong passwords for MT5 accounts
- Store secrets only in Streamlit Cloud (never in code)
- Review logs for unauthorized access attempts

### ❌ DON'T:
- Hardcode credentials in Python files
- Share .env files or config files in version control
- Use the same API key for multiple environments
- Leave admin dashboard accessible to non-admins
- Log full credentials in debug output

### Checking Credentials
The app validates on startup:

```python
# If you see this error:
"❌ Alpaca credentials not configured"

# Check your Streamlit Secrets:
# Settings → Secrets → Verify [alpaca] section exists with both:
# - ALPACA_PAPER_API_KEY = "pk_..."
# - ALPACA_PAPER_SECRET_KEY = "..."
```

---

## 6. Environment Variables Reference

### Mode Control Variables
```bash
# Set broker mode (overrides config file)
ALPACA_MODE = "paper" | "live"
MT5_MODE = "paper" | "live"
AXI_MODE = "paper" | "live"
IBKR_MODE = "paper" | "live"
```

### Credential Variables (Fallback)
```bash
# Alpaca (if not using [alpaca] section)
ALPACA_API_KEY = "pk_..."
ALPACA_SECRET_KEY = "..."
ALPACA_ENVIRONMENT = "paper" | "live"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

# MT5
MT5_USER = "account_number"
MT5_PASSWORD = "password"
MT5_SERVER = "server_name"
MT5_PORT = "443"

# MLflow
MLFLOW_TRACKING_URI = "http://localhost:5000"
MLFLOW_SERVER_URL = "http://localhost:5000"
```

---

## 7. Troubleshooting

### "HTTP 401: unauthorized" (Alpaca)
**Cause**: API key and secret don't match

**Fix**:
1. Verify in Streamlit Cloud Secrets:
   ```toml
   [alpaca]
   ALPACA_PAPER_API_KEY = "pk_..."
   ALPACA_PAPER_SECRET_KEY = "..."  # Matching pair
   ```
2. Don't mix paper key with live secret
3. Verify key format starts with `pk_` (Alpaca format)

### "AXI MT5 host not configured"
**Cause**: `AXI_MT5_SERVER` or `MT5_SERVER` env var is missing

**Fix**:
1. Add to Streamlit Secrets:
   ```toml
   [axi]
   AXI_MT5_SERVER = "Axi-US51-Live"
   ```
2. Or set environment variable:
   ```powershell
   $env:AXI_MT5_SERVER = "Axi-US51-Live"
   ```

### Can't see "🎮 Broker Modes" tab in Admin Control Center
**Cause**: `broker_mode_config.py` not loading properly

**Fix**:
1. Restart Streamlit app: `streamlit run streamlit_app.py`
2. Check for import errors in app logs
3. Verify `config/broker_mode_config.py` exists

### Mode changes not persisting after app restart
**Cause**: `config/broker_modes.json` file is not being written

**Fix**:
1. Check file permissions on `config/` directory
2. Verify disk space is available
3. Look for file write errors in app logs

---

## 8. Config File Location

The broker modes configuration persists here during local development:

```
BentleyBudgetBot/
  config/
    broker_modes.json  # 👈 Mode and bot status stored here
```

**Example broker_modes.json**:
```json
{
  "global_mode": "paper",
  "broker_modes": {
    "alpaca": "paper",
    "mt5": "live",
    "axi": "paper",
    "ibkr": "paper"
  },
  "active_bots": {
    "Titan": true,
    "Vega": false,
    "Rigel": true,
    ...
  },
  "bot_broker_mapping": {
    "Titan": "alpaca",
    "Vega": "ibkr",
    "Rigel": "mt5",
    ...
  }
}
```

---

## 9. Testing Your Setup

### Test  Alpaca Connection
1. Go to Admin Control Center → Broker Health tab
2. Click "Test Alpaca Connection"
3. Should show ✅ if configured correctly

### Test MT5 Connection
1. Go to Admin Control Center → Broker Health tab
2. Click "Test MT5 Connection"  
3. Should show ✅ if server is reachable

### Start a Bot
1. Go to Admin Control Center → Broker Modes tab
2. Find a bot in the "Inactive Bots" section
3. Click "▶️ Start"
4. Bot should now appear in "Active Bots" list

---

## 10. Getting Help

If you encounter issues:

1. **Check Streamlit logs** - App dashboard shows recent errors
2. **Review config file** - `config/broker_modes.json` shows current state
3. **Check environment variables** - Run:
   ```powershell
   Write-Host "ALPACA_MODE: $($env:ALPACA_MODE)"
   Write-Host "MT5_MODE: $($env:MT5_MODE)"
   ```
4. **Test connections** - Use Admin Control Center → Broker Health

---

**Last Updated:** March 2026
**Version:** 1.0
**Supported Brokers:** Alpaca, MT5 (AXI, FTMO), Interactive Brokers
