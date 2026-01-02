# MetaTrader 5 REST API Integration

## 🎯 Overview

This integration allows you to connect Bentley Budget Bot to MetaTrader 5 (MT5) via REST API, enabling:

- ✅ MT5 account login and authentication
- ✅ Real-time account information (balance, equity, margin)
- ✅ Market data retrieval (OHLCV candlestick data)
- ✅ View and manage open positions
- ✅ Place trades (market and pending orders)
- ✅ Modify positions (stop loss, take profit)
- ✅ Close positions
- ✅ Webhook configuration for real-time events

## 📁 Files Created

### Core Module
- **`frontend/utils/mt5_connector.py`** - Main MT5 REST API connector class
  - `MT5Connector` - Main class for all MT5 operations
  - `MT5Account` - Account credentials dataclass
  - `MT5Position` - Position data structure
  - `quick_connect()` - Convenience function for quick connections

### Streamlit Components
- **`frontend/components/mt5_dashboard.py`** - Full Streamlit UI for MT5 trading
  - Connection management interface
  - Account summary dashboard
  - Position management (view, close, modify)
  - Market data charts with Plotly
  - Trade placement form
  - Webhook configuration

### Pages
- **`pages/6_🔌_MT5_Trading.py`** - Standalone MT5 trading page

### Examples & Config
- **`examples/mt5_usage_examples.py`** - Complete usage examples
- **`.env.mt5.example`** - Environment variable template
- **`docs/MT5_INTEGRATION.md`** - This documentation

## 🚀 Quick Start

### 1. Set Up MT5 REST API Server

You need an MT5 REST API server running. The connector uses these endpoints:

```
GET  /Connect          - Connect to MT5 account
GET  /Disconnect       - Disconnect
GET  /AccountInfo      - Get account information
GET  /Positions        - Get open positions
GET  /MarketData       - Get OHLCV data
GET  /SymbolInfo       - Get symbol details
POST /PlaceTrade       - Place trade order
POST /ClosePosition    - Close position
POST /ModifyPosition   - Modify SL/TP
POST /SetupWebhook     - Configure webhooks
GET  /Health           - Health check
```

### 2. Configure Environment Variables

Copy `.env.mt5.example` to your `.env` file:

```bash
# Add to .env
MT5_API_URL=http://localhost:8000
MT5_USER=your_account_number
MT5_PASSWORD=your_password
MT5_HOST=broker_server.com
MT5_PORT=443
```

### 3. Use in Streamlit

Option A: Access via navigation (multi-page app)
```bash
streamlit run streamlit_app.py
# Navigate to "🔌 MT5 Trading" page
```

Option B: Run standalone page
```bash
streamlit run pages/6_🔌_MT5_Trading.py
```

### 4. Python Script Usage

```python
from frontend.utils.mt5_connector import quick_connect

# Connect to MT5
mt5 = quick_connect(
    base_url="http://localhost:8000",
    user="123456",
    password="password",
    host="broker.com"
)

if mt5:
    # Get account info
    account = mt5.get_account_info()
    print(f"Balance: ${account['balance']}")
    
    # Get positions
    positions = mt5.get_positions()
    for pos in positions:
        print(f"{pos.symbol}: ${pos.profit}")
    
    # Place trade
    result = mt5.place_trade(
        symbol="EURUSD",
        order_type="BUY",
        volume=0.1,
        sl=1.0800,
        tp=1.0900
    )
    
    mt5.disconnect()
```

## 📚 API Reference

### MT5Connector Class

#### Connection Methods

```python
connector = MT5Connector(base_url="http://localhost:8000")

# Connect to MT5
connector.connect(user, password, host, port=443) -> bool

# Disconnect
connector.disconnect() -> bool

# Health check
connector.health_check() -> bool
```

#### Account Methods

```python
# Get account information
account_info = connector.get_account_info()
# Returns: {'balance': float, 'equity': float, 'margin': float, ...}

# Get symbol information
symbol_info = connector.get_symbol_info("EURUSD")
# Returns: {'bid': float, 'ask': float, 'spread': int, ...}
```

#### Market Data Methods

```python
# Get OHLCV candlestick data
market_data = connector.get_market_data(
    symbol="EURUSD",
    timeframe="H1",  # M1, M5, M15, M30, H1, H4, D1, W1, MN1
    count=100
)
# Returns: {'bars': [{'time': str, 'open': float, 'high': float, ...}]}
```

#### Position Methods

```python
# Get all open positions
positions = connector.get_positions()
# Returns: List[MT5Position]

# Close position
connector.close_position(ticket=12345) -> bool

# Modify position
connector.modify_position(
    ticket=12345,
    sl=1.0850,  # New stop loss
    tp=1.0950   # New take profit
) -> bool
```

#### Trading Methods

```python
# Place trade order
result = connector.place_trade(
    symbol="EURUSD",
    order_type="BUY",  # BUY, SELL, BUY_LIMIT, SELL_LIMIT, etc.
    volume=0.1,        # Lot size
    price=1.0850,      # For pending orders (optional)
    sl=1.0800,         # Stop loss (optional)
    tp=1.0900,         # Take profit (optional)
    comment="My trade"
)
# Returns: {'success': bool, 'ticket': int, ...}
```

#### Webhook Methods

```python
# Setup webhook for real-time events
connector.setup_webhook(
    webhook_url="https://your-server.com/webhook",
    events=['trade', 'position', 'account']
) -> bool
```

## 🎨 Streamlit Components

The MT5 dashboard provides a complete trading interface:

### Features

1. **Connection Management**
   - Connect/disconnect to MT5 account
   - Health check for API server
   - Connection status display

2. **Account Summary**
   - Balance, equity, margin metrics
   - Real-time profit/loss
   - Detailed account information

3. **Position Management**
   - View all open positions in table
   - Close positions with one click
   - Modify stop loss and take profit
   - Colored profit/loss indicators

4. **Market Data & Charts**
   - Fetch OHLCV data for any symbol
   - Interactive Plotly candlestick charts
   - Current bid/ask/spread display
   - Multiple timeframes (M1 to MN1)

5. **Trade Placement**
   - Place market and pending orders
   - Set stop loss and take profit
   - Custom order comments
   - Support for all order types

6. **Webhook Configuration**
   - Configure webhook URL
   - Select event types (trade, position, account, market)
   - Real-time event notifications

## 🔧 Customization

### Add Custom Endpoints

Extend `MT5Connector` class in `frontend/utils/mt5_connector.py`:

```python
def get_order_history(self, days: int = 7) -> Optional[List]:
    """Get order history for last N days"""
    endpoint = f"{self.base_url}/OrderHistory"
    params = {'days': days}
    response = self.session.get(endpoint, params=params, timeout=5)
    return response.json()
```

### Customize UI Components

Edit `frontend/components/mt5_dashboard.py`:

```python
def render_custom_section():
    """Add custom trading section"""
    st.subheader("My Custom Feature")
    # Your custom UI code
```

## 🛡️ Security Best Practices

1. **Never commit credentials** - Use `.env` file (already in `.gitignore`)
2. **Use HTTPS** - For production MT5 API server
3. **Implement rate limiting** - On your MT5 REST API server
4. **Validate inputs** - Before sending to MT5
5. **Use webhooks** - For real-time updates instead of polling
6. **Monitor logs** - Check for suspicious activity

## 🐛 Troubleshooting

### Connection Issues

```python
# Test health check first
connector = MT5Connector("http://localhost:8000")
if not connector.health_check():
    print("MT5 API server is not responding")
```

### Common Errors

| Error | Solution |
|-------|----------|
| Connection refused | Check if MT5 API server is running |
| Authentication failed | Verify MT5_USER, MT5_PASSWORD, MT5_HOST |
| Timeout errors | Check network connectivity, increase timeout |
| Invalid symbol | Verify symbol name with broker |

### Debug Logging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Example Workflows

### Trading Bot Example

```python
from frontend.utils.mt5_connector import quick_connect
import time

mt5 = quick_connect(
    base_url="http://localhost:8000",
    user=os.getenv("MT5_USER"),
    password=os.getenv("MT5_PASSWORD"),
    host=os.getenv("MT5_HOST")
)

if mt5:
    # Monitor positions
    while True:
        positions = mt5.get_positions()
        
        for pos in positions:
            # Close if profit > $100
            if pos.profit > 100:
                print(f"Taking profit on {pos.symbol}")
                mt5.close_position(pos.ticket)
        
        time.sleep(60)  # Check every minute
```

### Market Analysis Example

```python
import pandas as pd

mt5 = quick_connect(...)

# Get multi-symbol data
symbols = ["EURUSD", "GBPUSD", "USDJPY"]
data = {}

for symbol in symbols:
    market_data = mt5.get_market_data(symbol, "H1", 100)
    if market_data:
        df = pd.DataFrame(market_data['bars'])
        data[symbol] = df
        
# Analyze correlations
for symbol, df in data.items():
    print(f"{symbol} - Last close: {df.iloc[-1]['close']}")
```

## 🔗 Integration with Bentley Bot Features

### Combine with Budget Dashboard

Track trading profits in your budget:

```python
# In budget_dashboard.py
from frontend.utils.mt5_connector import MT5Connector

# Get trading P&L
mt5 = MT5Connector(...)
if mt5.connected:
    account = mt5.get_account_info()
    trading_profit = account['equity'] - account['balance']
    
    # Add to budget income
    st.metric("Trading Profit (Today)", f"${trading_profit:.2f}")
```

### Portfolio Integration

Add MT5 positions to portfolio view:

```python
# In streamlit_app.py
positions = mt5.get_positions()
for pos in positions:
    portfolio_data.append({
        'Symbol': pos.symbol,
        'Value': pos.volume * pos.current_price,
        'Profit': pos.profit
    })
```

## 📞 Support & Resources

- **MT5 API Documentation**: Check your MT5 REST API server docs
- **Bentley Bot Docs**: See main README.md
- **Issues**: Open GitHub issue for bugs
- **Examples**: Run `python examples/mt5_usage_examples.py`

## 🎯 Next Steps

1. ✅ Set up MT5 REST API server
2. ✅ Configure environment variables
3. ✅ Test connection with examples
4. ✅ Access MT5 Trading page in Streamlit
5. ✅ Start trading! (Use demo account first)

---

**Happy Trading! 🚀📈**
