# MT5 REST API Server Setup Guide

## ✅ Prerequisites Installed

- ✅ MetaTrader5 Python package
- ✅ Flask (REST API framework)
- ✅ Flask-CORS (Cross-origin support)
## 🚀 Quick Start

### Step 1: Update Your .env File

Your `.env` file now has MT5 configuration. Update these values:

```bash
MT5_USER=your_actual_account_number
MT5_PASSWORD=your_actual_password
MT5_HOST=your_broker_server.com
```

**Example broker servers:**
- MetaQuotes: `MetaQuotes-Demo`
- Admiral Markets: `AdmiralMarkets-Demo`
- IC Markets: `ICMarketsSC-Demo`
- XM: `XMGlobal-Demo`

### Step 2: Install & Run MetaTrader 5 Terminal

1. **Download MT5 Terminal:**
   - https://www.metatrader5.com/en/download
   - Or get from your broker's website

2. **Install and Login:**
   - Open MT5 terminal
   - Login with your account credentials
   - Make sure terminal stays open (minimized is fine)

3. **Enable Algo Trading:**
   - In MT5: Tools → Options → Expert Advisors
   - Check "Allow automated trading"
   - Check "Allow DLL imports"

### Step 3: Start the MT5 REST API Server

```bash
# In a separate terminal (keep MT5 terminal running)
python mt5_rest_api_server.py
```

You should see:
```
============================================================
MT5 REST API Server
============================================================
Starting server on http://localhost:8000

Make sure MetaTrader 5 terminal is running!

Available endpoints:
  GET  /Health           - Health check
  GET  /Connect          - Connect to MT5 account
  ...
============================================================
```

### Step 4: Test the Connection

In another terminal:

```bash
python test_mt5_connection.py
```

Expected output:
```
============================================================
TEST 1: Import MT5 Connector
============================================================
✅ MT5 connector imported successfully

============================================================
TEST 2: Health Check
============================================================
Testing connection to: http://localhost:8000
✅ MT5 API server is healthy and reachable

============================================================
TEST 3: MT5 Connection
============================================================
Connecting to MT5 account: 123456
Broker server: broker.com:443
✅ MT5 connection successful!
   Balance: $10,000.00
   Equity: $10,000.00
```

## 📊 Full Workflow

### Terminal 1: MT5 REST API Server
```bash
cd C:\Users\winst\BentleyBudgetBot
python mt5_rest_api_server.py
```

Keep this running!

### Terminal 2: Test Connection
```bash
python test_mt5_connection.py
```

### Terminal 3: Run Streamlit
```bash
streamlit run streamlit_app.py
```

Navigate to: **🔌 MT5 Trading** or **🌐 Multi-Broker Trading**

## 🧪 Manual Testing

Test the API directly:

```bash
# Health check
curl http://localhost:8000/Health

# Connect (replace with your credentials)
curl "http://localhost:8000/Connect?user=123456&password=yourpass&host=broker.com&port=443"

# Get account info
curl http://localhost:8000/AccountInfo

# Get positions
curl http://localhost:8000/Positions
```

## 🐛 Troubleshooting

### "MT5 initialization failed"
- ✅ Make sure MT5 terminal is running
- ✅ Check MT5 is not frozen/crashed
- ✅ Try restarting MT5 terminal

### "Login failed"
- ✅ Verify account number, password, server name
- ✅ Check account is active (not expired demo)
- ✅ Try logging in manually in MT5 terminal first

### "Connection refused" on port 8000
- ✅ Make sure mt5_rest_api_server.py is running
- ✅ Check no other app is using port 8000
- ✅ Check firewall settings

### Python package errors

```bash
# Reinstall packages
pip install --upgrade MetaTrader5 flask flask-cors
```

## 📝 Getting MT5 Demo Account

If you don't have an MT5 account:

1. **Open MT5 Terminal**
2. **File → Open an Account**
3. **Choose a broker** (e.g., MetaQuotes Software Corp for demo)
4. **Select "Open a demo account"**
5. **Fill in details** and click "Next"
6. **Save your credentials:**
   - Login: 123456 (your account number)
   - Password: (your password)
   - Server: MetaQuotes-Demo

Update your `.env` file with these values!

## 🎯 Next Steps After Connection Works

1. ✅ Test in Streamlit dashboard
2. ✅ Place test trades (on demo account!)
3. ✅ Set up Alpaca for stocks
4. ✅ Add IBKR Gateway for multi-asset

## 📚 API Reference

See full documentation:
- `docs/MT5_INTEGRATION.md` - Complete MT5 guide
- `docs/MULTI_BROKER_GUIDE.md` - Multi-broker setup

## 🔒 Security Notes

- ✅ Never commit your `.env` file (it's in .gitignore)
- ✅ Start with demo accounts for testing
- ✅ API server runs locally (not exposed to internet)
- ✅ Always verify trades before executing

---

**You're ready to trade FOREX and Futures! 🚀📈**
