# BentleyBot Broker Quick Reference

## 🎯 Broker-to-Asset Mapping

```
┌─────────────────┬──────────────────────┬─────────────────────────┐
│ Asset Class     │ MVP Brokers          │ PRODUCTION Brokers      │
├─────────────────┼──────────────────────┼─────────────────────────┤
│ Equities/ETFs   │ Alpaca               │ IBKR, Schwab            │
│ Futures         │ NinjaTrader+TradeStation│ NinjaTrader+TradeStation│
│ Options         │ IBKR                 │ IBKR                    │
│ Forex           │ MT5 + IBKR           │ MT5 + IBKR              │
│ Crypto          │ Binance              │ Binance                 │
└─────────────────┴──────────────────────┴─────────────────────────┘
```

## 🔧 Environment Setup

### For MVP (Development/Paper Trading)
```bash
# .env or .streamlit/secrets.toml
APP_ENV=MVP
ALPACA_KEY_ID=your_paper_key
ALPACA_SECRET_KEY=your_paper_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

### For PRODUCTION (Live Trading)
```bash
# .env or .streamlit/secrets.toml
APP_ENV=PRODUCTION
IBKR_GATEWAY_URL=http://localhost:5000
IBKR_ACCOUNT_ID=your_account
SCHWAB_API_URL=https://api.schwabapi.com
SCHWAB_CLIENT_ID=your_client_id
```

## 📊 Streamlit Usage

### Access from Streamlit App
```python
import streamlit as st
import os

# Get current environment
env = os.getenv('APP_ENV', 'MVP')
st.write(f"Trading Environment: {env}")

# Show broker for each asset class
brokers = {
    'MVP': {
        'Equities/ETFs': 'Alpaca',
        'Futures': 'NinjaTrader + TradeStation',
        'Options': 'IBKR',
        'Forex': 'MT5 + IBKR',
        'Crypto': 'Binance'
    },
    'PRODUCTION': {
        'Equities/ETFs': 'IBKR, Schwab',
        'Futures': 'NinjaTrader + TradeStation',
        'Options': 'IBKR',
        'Forex': 'MT5 + IBKR',
        'Crypto': 'Binance'
    }
}

st.table(brokers[env])
```

### Call Trade API from Streamlit
```python
import streamlit as st
import requests

def place_trade(symbol, qty, side, asset_class='equities'):
    """Place trade via unified API"""
    response = requests.post(
        'http://localhost:3000/api/trade',
        json={
            'class': asset_class,
            'symbol': symbol,
            'qty': qty,
            'side': side
        }
    )
    return response.json()

# In your Streamlit app
col1, col2, col3 = st.columns(3)
with col1:
    symbol = st.text_input('Symbol', 'AAPL')
with col2:
    qty = st.number_input('Quantity', min_value=1, value=10)
with col3:
    side = st.selectbox('Side', ['buy', 'sell'])

if st.button('Execute Trade'):
    result = place_trade(symbol, qty, side)
    if result.get('status') == 'success':
        st.success(f"✅ Order placed: {result['orderId']}")
    else:
        st.error(f"❌ Trade failed: {result.get('error')}")
```

## 🎨 Streamlit Dashboard Widget

```python
import streamlit as st

def show_broker_status():
    """Display broker connection status"""
    st.subheader("🔌 Broker Connections")
    
    brokers = {
        'Alpaca': check_alpaca_health(),
        'IBKR': check_ibkr_health(),
        'MT5': check_mt5_health(),
        'Binance': check_binance_health()
    }
    
    for broker, status in brokers.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(broker)
        with col2:
            if status:
                st.success("🟢 Online")
            else:
                st.error("🔴 Offline")

# Add to your streamlit_app.py
show_broker_status()
```

## 📝 Configuration Files

### .streamlit/secrets.toml
```toml
[broker]
APP_ENV = "MVP"

[alpaca]
ALPACA_KEY_ID = "your_key"
ALPACA_SECRET_KEY = "your_secret"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

[ibkr]
IBKR_GATEWAY_URL = "http://localhost:5000"
IBKR_ACCOUNT_ID = "your_account"

[mt5]
MT5_API_URL = "http://localhost:8000"

[binance]
BINANCE_API_KEY = "your_key"
BINANCE_API_SECRET = "your_secret"
```

### Access in Streamlit
```python
import streamlit as st

# Access secrets
alpaca_key = st.secrets["alpaca"]["ALPACA_KEY_ID"]
env = st.secrets["broker"]["APP_ENV"]
```

## 🚀 Quick Commands

```bash
# Start Streamlit app
streamlit run streamlit_app.py

# Start Next.js API server
npm run dev

# Test trade API
node tests/test_trade_api.js

# Check broker connections
python test_multi_broker.py
```

## 📚 Documentation Links

- **Full API Docs**: [pages/api/README.md](pages/api/README.md)
- **Broker Mapping**: [BROKER_MAPPING.md](BROKER_MAPPING.md)
- **Implementation Guide**: [TRADE_API_SUMMARY.md](TRADE_API_SUMMARY.md)
- **Environment Config**: [.env.brokers](.env.brokers)

## ⚠️ Important Notes

1. **MVP Mode** uses paper trading accounts (safe for testing)
2. **PRODUCTION Mode** uses live accounts (real money)
3. Always test in MVP before switching to PRODUCTION
4. Keep credentials in `.env` or `.streamlit/secrets.toml` (never commit)
5. Each broker requires different setup (see BROKER_MAPPING.md)

## 🆘 Troubleshooting

### Alpaca Not Connecting
```bash
# Check credentials
python test_alpaca_connection.py
```

### IBKR Gateway Issues
```bash
# Verify Gateway is running
curl http://localhost:5000/v1/api/tickle
```

### MT5 REST Server Down
```bash
# Start MT5 REST API server
python mt5_rest_api_server.py
```

---

**Last Updated**: January 11, 2026  
**Version**: 1.0.0
