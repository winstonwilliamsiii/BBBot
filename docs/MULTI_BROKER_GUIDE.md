# Multi-Broker Trading Integration Guide

## 🎯 Overview

Complete trading setup for **MT5 (FOREX/Futures)**, **Alpaca (Stocks/Crypto)**, and **IBKR (Multi-Asset)** - all integrated into Bentley Budget Bot.

## 📦 What's Included

### Brokers & Asset Coverage

| Broker | Asset Classes | Status | Use Case |
|--------|--------------|--------|----------|
| **MT5** | FOREX, Commodities Futures | ✅ Ready | Currency pairs, Gold, Oil futures |
| **Alpaca** | Stocks, ETFs, Crypto | ✅ Ready | US equities, Bitcoin, Ethereum |
| **IBKR** | Stocks, FOREX, Futures, Options | ✅ Ready | Global markets, comprehensive trading |
| **Webull** | Stocks (Demo only) | ⚠️ Limited | Currently demo/paper trading only |

### Files Created

#### Connectors
- **`frontend/utils/alpaca_connector.py`** - Alpaca Markets API client (500+ lines)
  - Account management
  - Stock & crypto trading
  - Real-time market data
  - Position & order management
  - Paper trading support

- **`frontend/utils/ibkr_connector.py`** - Interactive Brokers Gateway client (450+ lines)
  - IBKR Gateway/Client Portal API
  - Multi-asset trading (stocks, FOREX, futures, options)
  - Contract search & market data
  - Order placement & management
  - Portfolio tracking

- **`frontend/utils/mt5_connector.py`** - MetaTrader 5 REST API client
  - FOREX trading
  - Commodities futures
  - Position management

#### Dashboards
- **`frontend/components/multi_broker_dashboard.py`** - Unified multi-broker interface
  - Single dashboard for all brokers
  - Combined portfolio view
  - Cross-broker position tracking
  - Consolidated P/L reporting

- **`frontend/components/mt5_dashboard.py`** - MT5-specific interface
- Individual broker tabs for detailed management

#### Pages
- **`pages/7_🌐_Multi_Broker_Trading.py`** - Main navigation page
- **`pages/6_🔌_MT5_Trading.py`** - MT5-specific page

#### Configuration
- **`.env.brokers.updated`** - Complete environment template

## 🚀 Quick Start

### 1. Install IBKR Gateway (if using IBKR)

**Windows:**
1. Download from: https://www.interactivebrokers.com/en/trading/ibgateway-stable.php
2. Install to: `C:\Jts\ibgateway\`
3. Run `ibgateway.exe`
4. Configure API settings:
   - Enable ActiveX and Socket Clients
   - Socket port: 5000
   - Read-Only API: No

**Mac:**
1. Download from same link
2. Install to `/Applications/IB Gateway.app`
3. Run and configure similarly

### 2. Configure Environment Variables

Copy to your `.env` file:

```bash
# ALPACA (Stocks & Crypto)
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_SECRET_KEY=your_alpaca_secret_key
ALPACA_PAPER=true

# IBKR (Multi-Asset)
IBKR_GATEWAY_URL=https://localhost:5000
IBKR_ACCOUNT_ID=your_account_id

# MT5 (FOREX & Futures)
MT5_API_URL=http://localhost:8000
MT5_USER=your_mt5_account
MT5_PASSWORD=your_mt5_password
MT5_HOST=broker_server.com
MT5_PORT=443
```

### 3. Get API Keys

#### Alpaca
1. Sign up: https://alpaca.markets/
2. Dashboard: https://app.alpaca.markets/paper/dashboard/overview
3. Generate API keys (Paper or Live)
4. Copy to `.env`

#### IBKR
1. Open IBKR account: https://www.interactivebrokers.com/
2. Install Gateway (see step 1)
3. Run Gateway and login
4. Account ID will be detected automatically

#### MT5
1. Open account with MT5 broker
2. Set up MT5 REST API server (separate component)
3. Configure connection details

### 4. Launch Application

```bash
streamlit run streamlit_app.py
```

Navigate to **🌐 Multi-Broker Trading** in the sidebar.

## 📚 API Reference

### Alpaca Connector

```python
from frontend.utils.alpaca_connector import AlpacaConnector

# Initialize
alpaca = AlpacaConnector(
    api_key="YOUR_KEY",
    secret_key="YOUR_SECRET",
    paper=True  # Paper or live trading
)

# Get account info
account = alpaca.get_account()
print(f"Buying Power: ${account['buying_power']}")

# Get positions
positions = alpaca.get_positions()
for pos in positions:
    print(f"{pos.symbol}: ${pos.unrealized_pl:.2f}")

# Place order
order = alpaca.place_order(
    symbol="AAPL",
    qty=10,
    side="buy",
    order_type="market",
    time_in_force="day"
)

# Get market data
bars = alpaca.get_bars("AAPL", timeframe="1Day", limit=30)
quote = alpaca.get_latest_quote("AAPL")

# Close position
alpaca.close_position("AAPL")
```

### IBKR Connector

```python
from frontend.utils.ibkr_connector import IBKRConnector

# Initialize (Gateway must be running)
ibkr = IBKRConnector(base_url="https://localhost:5000")

# Check authentication
if ibkr.is_authenticated():
    print("Connected!")

# Get accounts
accounts = ibkr.get_accounts()
print(f"Accounts: {accounts}")

# Get positions
positions = ibkr.get_positions(accounts[0])
for pos in positions:
    print(f"{pos.symbol}: ${pos.unrealized_pnl:.2f}")

# Search for contract
contracts = ibkr.search_contract("EUR.USD")
conid = contracts[0]['conid']

# Get market data
market_data = ibkr.get_market_data([conid], fields=[31, 84, 85])

# Place order
order = ibkr.place_order(
    account_id=accounts[0],
    conid=conid,
    order_type="MKT",
    side="BUY",
    quantity=1000,
    tif="DAY"
)

# Get historical data
history = ibkr.get_historical_data(conid, period="1d", bar="5min")
```

### MT5 Connector

```python
from frontend.utils.mt5_connector import MT5Connector

# Initialize
mt5 = MT5Connector(base_url="http://localhost:8000")

# Connect
mt5.connect(
    user="123456",
    password="password",
    host="broker.com",
    port=443
)

# Get account info
account = mt5.get_account_info()

# Get positions
positions = mt5.get_positions()

# Get market data
data = mt5.get_market_data("EURUSD", "H1", 100)

# Place trade
result = mt5.place_trade(
    symbol="EURUSD",
    order_type="BUY",
    volume=0.1,
    sl=1.0800,
    tp=1.0900
)
```

## 🎨 Streamlit Dashboard Features

### Multi-Broker Dashboard

1. **Connection Status Overview**
   - Real-time connection status for all brokers
   - Quick connect buttons
   - Account summaries

2. **Broker-Specific Tabs**
   - MT5: FOREX & Futures trading
   - Alpaca: Stocks & Crypto
   - IBKR: Multi-asset trading
   - Each with full trading capabilities

3. **Combined Portfolio View**
   - Unified position tracking
   - Cross-broker P/L aggregation
   - Total portfolio value
   - Asset allocation breakdown

4. **Trading Features**
   - Place orders across brokers
   - Manage positions
   - View market data
   - Track performance

## 📊 Usage Examples

### Example 1: Check All Account Balances

```python
import os
from dotenv import load_dotenv
from frontend.utils.alpaca_connector import AlpacaConnector
from frontend.utils.ibkr_connector import IBKRConnector
from frontend.utils.mt5_connector import MT5Connector

load_dotenv()

# Connect to all brokers
alpaca = AlpacaConnector(
    os.getenv("ALPACA_API_KEY"),
    os.getenv("ALPACA_SECRET_KEY"),
    paper=True
)

ibkr = IBKRConnector()
mt5 = MT5Connector(os.getenv("MT5_API_URL"))
mt5.connect(
    os.getenv("MT5_USER"),
    os.getenv("MT5_PASSWORD"),
    os.getenv("MT5_HOST")
)

# Get balances
alpaca_account = alpaca.get_account()
ibkr_accounts = ibkr.get_accounts()
mt5_account = mt5.get_account_info()

print(f"Alpaca: ${float(alpaca_account['portfolio_value']):,.2f}")
print(f"IBKR: {len(ibkr_accounts)} accounts")
print(f"MT5: ${mt5_account.get('equity', 0):,.2f}")
```

### Example 2: Cross-Broker Arbitrage Monitor

```python
# Monitor price differences across brokers
def monitor_arbitrage(symbol):
    # Get price from Alpaca
    alpaca_quote = alpaca.get_latest_quote(symbol)
    alpaca_price = float(alpaca_quote['quote']['ap'])
    
    # Get price from IBKR
    contracts = ibkr.search_contract(symbol)
    ibkr_data = ibkr.get_market_data([contracts[0]['conid']])
    ibkr_price = ibkr_data[0].get('31', 0)  # Last price
    
    # Calculate difference
    diff = abs(alpaca_price - ibkr_price)
    diff_pct = (diff / alpaca_price) * 100
    
    print(f"{symbol}:")
    print(f"  Alpaca: ${alpaca_price:.2f}")
    print(f"  IBKR: ${ibkr_price:.2f}")
    print(f"  Difference: {diff_pct:.3f}%")

monitor_arbitrage("AAPL")
```

### Example 3: Portfolio Rebalancing

```python
def rebalance_portfolio(target_allocations):
    """
    Rebalance portfolio across brokers
    target_allocations: {"AAPL": 0.3, "EUR.USD": 0.4, "BTC": 0.3}
    """
    
    # Get total portfolio value
    total_value = 0
    total_value += float(alpaca.get_account()['portfolio_value'])
    total_value += mt5.get_account_info().get('equity', 0)
    
    # Calculate target positions
    for symbol, allocation in target_allocations.items():
        target_value = total_value * allocation
        
        if symbol in ["BTC", "ETH"]:
            # Crypto on Alpaca
            current_pos = alpaca.get_position(symbol + "USD")
            # Adjust position...
        
        elif "." in symbol:
            # FOREX on MT5
            # Adjust MT5 position...
            pass
        
        else:
            # Stocks on Alpaca or IBKR
            # Adjust position...
            pass
```

## 🔧 Advanced Configuration

### Broker Selection by Asset Class

Configure primary broker for each asset type in `.env`:

```bash
PRIMARY_STOCK_BROKER=alpaca
PRIMARY_FOREX_BROKER=mt5
PRIMARY_FUTURES_BROKER=mt5
PRIMARY_CRYPTO_BROKER=alpaca
```

### Custom Order Routing

```python
def place_order_smart(symbol, qty, side, asset_class="stock"):
    """Route order to appropriate broker"""
    
    if asset_class == "stock":
        broker = os.getenv("PRIMARY_STOCK_BROKER", "alpaca")
        if broker == "alpaca":
            return alpaca.place_order(symbol, qty=qty, side=side)
        elif broker == "ibkr":
            contracts = ibkr.search_contract(symbol)
            return ibkr.place_order(
                account_id=ibkr.get_accounts()[0],
                conid=contracts[0]['conid'],
                order_type="MKT",
                side=side.upper(),
                quantity=qty
            )
    
    elif asset_class == "forex":
        return mt5.place_trade(symbol, "BUY" if side=="buy" else "SELL", qty)
```

## 🛡️ Security Best Practices

1. **Use Paper Trading First** - Test with demo accounts
2. **Secure API Keys** - Never commit to git
3. **Enable 2FA** - On all broker accounts
4. **Monitor Activity** - Set up alerts for unusual activity
5. **Use Read-Only Keys** - When possible, for monitoring
6. **Separate Live/Paper** - Keep credentials separate

## 🐛 Troubleshooting

### Alpaca Connection Issues

```python
# Test connection
alpaca = AlpacaConnector(api_key, secret_key, paper=True)
account = alpaca.get_account()

if not account:
    print("Connection failed - check API keys")
```

### IBKR Gateway Not Connecting

1. Verify Gateway is running (check system tray)
2. Check port 5000 is not blocked
3. Ensure API is enabled in Gateway settings
4. Try reauthenticating: `ibkr.reauthenticate()`

### MT5 Server Unreachable

1. Verify MT5 REST API server is running
2. Check firewall settings
3. Test with health check: `mt5.health_check()`

## 📊 Performance Metrics

Track performance across all brokers:

```python
def get_combined_metrics():
    metrics = {
        'total_value': 0,
        'total_pnl': 0,
        'positions': 0
    }
    
    # Alpaca
    alpaca_acc = alpaca.get_account()
    metrics['total_value'] += float(alpaca_acc['portfolio_value'])
    metrics['total_pnl'] += float(alpaca_acc['equity']) - float(alpaca_acc['last_equity'])
    metrics['positions'] += len(alpaca.get_positions() or [])
    
    # MT5
    mt5_acc = mt5.get_account_info()
    metrics['total_value'] += mt5_acc.get('equity', 0)
    metrics['total_pnl'] += mt5_acc.get('equity', 0) - mt5_acc.get('balance', 0)
    metrics['positions'] += len(mt5.get_positions() or [])
    
    return metrics
```

## 🎯 Next Steps

1. ✅ Configure all broker credentials
2. ✅ Test connections with paper/demo accounts
3. ✅ Explore individual broker dashboards
4. ✅ Try the combined portfolio view
5. ✅ Set up automated trading strategies

---

**You're ready for multi-broker trading! 🚀📈**
