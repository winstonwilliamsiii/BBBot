# Multi-Broker Trading Integration Guide

## 🎯 Overview

Bentley Budget Bot supports multiple brokers for comprehensive trading across all asset classes:

### ✅ Currently Integrated
- **Alpaca** - Stocks & Crypto (Paper & Live Trading)
- **MT5** - FOREX & Futures via REST API Server
- **IBKR** - Multi-Asset via Gateway/Client Portal

### 🔜 Planned Integrations
- **QuantConnect** - IBKR algorithmic trading platform
- **Think or Swim** - TD Ameritrade (via Charles Schwab Dev API)
- **NinjaTrader** - Professional Futures & FOREX platform
- **Binance** - Cryptocurrency exchange (Production)

---

## 📋 Quick Start - Alpaca

### 1. Get Alpaca API Credentials

1. Sign up at [https://alpaca.markets/](https://alpaca.markets/)
2. Navigate to **Paper Trading** → **API Keys**
3. Generate new API keys
4. Copy API Key and Secret Key

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Alpaca Trading API (Stocks & Crypto)
ALPACA_API_KEY=PK... your actual key
ALPACA_SECRET_KEY=... your actual secret
ALPACA_PAPER=true  # Set to 'false' for live trading
```

### 3. Test Connection

Run the test script:

```bash
python test_alpaca_connection.py
```

Expected output:
```
============================================================
ALPACA CONNECTION TEST
============================================================
✅ Alpaca connector imported successfully
✅ ALPACA_API_KEY found: PK...
✅ ALPACA_SECRET_KEY found: ...
✅ Trading Mode: PAPER
✅ Authentication successful!

📊 Account Summary:
   Account ID: ...
   Status: ACTIVE
   Buying Power: $100,000.00
   Cash: $100,000.00
   Portfolio Value: $100,000.00

✅ READY TO TRADE!
```

### 4. Access in Streamlit

```bash
streamlit run streamlit_app.py
```

Navigate to any of these pages:
- **📈 Investment Analysis** - View broker connection status
- **💼 Broker Trading** - Test connection and view positions
- **🌐 Multi-Broker Trading Hub** - Full trading interface

---

## 🔌 MT5 Integration

### Prerequisites
1. MetaTrader 5 Terminal installed
2. MT5 account (demo or live)
3. MT5 REST API Server running

### Configuration

```bash
# MetaTrader 5 REST API Server
MT5_API_URL=http://localhost:8000
MT5_USER=your_mt5_account_number
MT5_PASSWORD=your_mt5_password
MT5_HOST=your_broker_server
MT5_PORT=443
```

### Start MT5 Server

```bash
# Terminal 1: Start MT5 REST API Server
python mt5_rest_api_server.py

# Terminal 2: Test connection
python test_mt5_connection.py

# Terminal 3: Run Streamlit
streamlit run streamlit_app.py
```

See [MT5_SERVER_SETUP.md](MT5_SERVER_SETUP.md) for detailed instructions.

---

## 🏦 IBKR Integration

### Prerequisites
1. IBKR Gateway or Trader Workstation (TWS)
2. IBKR account
3. Gateway running on port 5000

### Configuration

```bash
# Interactive Brokers (IBKR) Gateway
IBKR_GATEWAY_URL=https://localhost:5000
```

### Start IBKR Gateway

1. Download IBKR Gateway from [https://www.interactivebrokers.com/](https://www.interactivebrokers.com/)
2. Start Gateway and login
3. Configure API settings:
   - Enable API connections
   - Port: 5000
   - Allow localhost connections

### Access in App

Navigate to **🌐 Multi-Broker Trading Hub** and click "Connect IBKR"

---

## 🌐 Multi-Broker Trading Hub

### Features

- **Unified Dashboard** - View all broker accounts in one place
- **Combined Portfolio** - Aggregate positions across all brokers
- **Real-time Data** - Live market data from all connected brokers
- **Order Management** - Place orders on any connected broker

### Connection Status

The dashboard shows connection status for each broker:
- 🟢 **Connected** - Ready to trade
- 🔴 **Disconnected** - Click to connect

### Supported Asset Classes

| Broker | Stocks | Crypto | FOREX | Futures | Options |
|--------|--------|--------|-------|---------|---------|
| Alpaca | ✅ | ✅ | ❌ | ❌ | ❌ |
| MT5 | ❌ | ❌ | ✅ | ✅ | ❌ |
| IBKR | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 🔜 Future Integrations

### QuantConnect (IBKR Algorithmic)

**Purpose:** Algorithmic trading via QuantConnect platform using IBKR as broker

**Configuration:**
```bash
# QuantConnect
QUANTCONNECT_USER_ID=your_user_id
QUANTCONNECT_API_TOKEN=your_api_token
QUANTCONNECT_PROJECT_ID=your_project_id
```

**Features:**
- Backtesting with historical data
- Live algorithmic trading
- Strategy optimization
- Cloud-based execution

---

### Think or Swim (TD Ameritrade / Charles Schwab)

**Purpose:** Professional charting and trading platform

**Configuration:**
```bash
# TD Ameritrade / Think or Swim
TDA_API_KEY=your_api_key
TDA_REDIRECT_URI=https://localhost:8501
TDA_ACCOUNT_ID=your_account_id
```

**Features:**
- Advanced charting
- Options trading
- Level 2 market data
- Paper trading

---

### NinjaTrader (Futures & FOREX)

**Purpose:** Professional futures and FOREX trading platform

**Configuration:**
```bash
# NinjaTrader
NINJATRADER_USERNAME=your_username
NINJATRADER_PASSWORD=your_password
NINJATRADER_LICENSE_KEY=your_license_key
```

**Features:**
- Advanced order types
- Market replay
- Strategy development
- High-frequency trading

---

### Binance (Cryptocurrency)

**Purpose:** Cryptocurrency spot and derivatives trading

**Configuration:**
```bash
# Binance (Production)
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_TESTNET=false  # Set to true for testnet
```

**Features:**
- Spot trading
- Futures trading
- Margin trading
- Staking

---

## 🧪 Testing Workflow

### 1. Test Individual Connectors

```bash
# Test Alpaca
python test_alpaca_connection.py

# Test MT5
python test_mt5_connection.py

# Test IBKR (when available)
python test_ibkr_connection.py
```

### 2. Test in Streamlit

```bash
streamlit run streamlit_app.py
```

**Test Pages:**
1. **📈 Investment Analysis** - Check broker integration section
2. **💼 Broker Trading** - Test connection buttons
3. **🌐 Multi-Broker Trading Hub** - Full integration test

### 3. Verify Connection

Each page should show:
- ✅ Broker name with connection status
- Account balance/portfolio value
- Active positions (if any)
- Ability to place test orders (on paper accounts)

---

## 📊 Connection Status Dashboard

Access from any page to see:

```
🔗 Broker Connections
┌─────────────────────────────────────┐
│ Alpaca (Stocks/Crypto)              │
│ Status: 🟢 Connected                │
│ Portfolio: $100,000.00               │
│ [Disconnect]                         │
├─────────────────────────────────────┤
│ MT5 (FOREX/Futures)                 │
│ Status: 🟢 Connected                │
│ Balance: $50,000.00                  │
│ [Disconnect]                         │
├─────────────────────────────────────┤
│ IBKR (Multi-Asset)                  │
│ Status: 🔴 Disconnected             │
│ [Connect]                            │
├─────────────────────────────────────┤
│ Future Brokers                       │
│ QuantConnect, TD Ameritrade,        │
│ NinjaTrader, Binance                │
│ Status: 🔜 Coming Soon              │
└─────────────────────────────────────┘
```

---

## 🔒 Security Best Practices

### API Keys

- ✅ **Never commit** `.env` file to Git
- ✅ **Use paper trading** for testing
- ✅ **Rotate keys** regularly
- ✅ **Enable IP whitelisting** where supported
- ✅ **Use read-only keys** for monitoring

### Trading Safety

- ✅ **Start with paper trading**
- ✅ **Test with small amounts** on live
- ✅ **Set up stop losses**
- ✅ **Monitor positions** regularly
- ✅ **Keep logs** of all trades

---

## 📚 Additional Resources

- [Alpaca API Documentation](https://alpaca.markets/docs/)
- [MT5 Python Integration](https://www.mql5.com/en/docs/python_metatrader5)
- [IBKR API Guide](https://www.interactivebrokers.com/en/trading/ib-api.php)
- [QuantConnect Documentation](https://www.quantconnect.com/docs/)
- [TD Ameritrade API](https://developer.tdameritrade.com/)

---

## 🆘 Troubleshooting

### Alpaca Connection Failed

```bash
# Check credentials
echo $ALPACA_API_KEY
echo $ALPACA_SECRET_KEY

# Test API directly
curl -H "APCA-API-KEY-ID: $ALPACA_API_KEY" \
     -H "APCA-API-SECRET-KEY: $ALPACA_SECRET_KEY" \
     https://paper-api.alpaca.markets/v2/account
```

### MT5 Connection Timeout

- Ensure MT5 terminal is running
- Check REST API server is running on port 8000
- Verify firewall allows local connections

### IBKR Authentication Failed

- Ensure Gateway is running
- Check Gateway port (default: 5000)
- Verify API settings in Gateway configuration

---

## 📞 Support

For issues or questions:
1. Check this documentation
2. Review test scripts output
3. Check broker API status pages
4. Open an issue on GitHub

---

**🚀 Ready to trade across all asset classes with Bentley Budget Bot!**
