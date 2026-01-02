# Webull Trading API Integration

Complete integration of Webull OpenAPI SDK with BentleyBot for live trading capabilities.

## 📦 Installation

The Webull SDK is already included in your requirements. If you need to reinstall:

```bash
pip install webull-openapi-python-sdk>=1.0.3
```

## 🔑 Setup

### 1. Get API Credentials

1. Visit [Webull Open API Portal](https://www.webull.com/open-api)
2. Sign up for API access
3. Create an application to get:
   - **App Key** (API Key)
   - **App Secret** (API Secret)

### 2. Configure Environment Variables

Add to your `.env` file:

```env
# Webull Trading API
WEBULL_APP_KEY=your_app_key_here
WEBULL_APP_SECRET=your_app_secret_here
```

**Important:** Use TEST credentials during development!

### 3. Test Connection

Run the test script to verify setup:

```bash
python test_webull_connection.py
```

Expected output:
```
✅ Credentials found
✅ Client initialized successfully
✅ Found 1 account(s)
✅ ALL TESTS PASSED!
```

## 🚀 Usage

### Option 1: Streamlit Dashboard (Recommended)

Launch the interactive trading dashboard:

```bash
streamlit run pages/webull_trading.py
```

Features:
- 📊 Portfolio summary with real-time balances
- 📈 Current positions with P&L
- 🚀 Place market/limit orders
- 📋 View and manage open orders
- 👀 Preview orders before placing

### Option 2: Python API

```python
from services.webull_client import create_webull_client

# Initialize client (use_production=False for test environment)
client = create_webull_client(use_production=False)

# Get portfolio summary
summary = client.get_portfolio_summary()
print(f"Total Value: ${summary['total_value']:,.2f}")

# Get positions
positions = client.get_account_positions()
for pos in positions:
    print(client.format_position_for_display(pos))

# Place a market order
result = client.place_equity_order(
    symbol="AAPL",
    quantity=10,
    side="BUY",
    order_type="MARKET"
)
print(f"Order placed: {result['client_order_id']}")

# Place a limit order
result = client.place_equity_order(
    symbol="TSLA",
    quantity=5,
    side="BUY",
    order_type="LIMIT",
    limit_price=250.00,
    time_in_force="GTC"
)

# Preview order before placing
preview = client.preview_equity_order(
    symbol="NVDA",
    quantity=10,
    side="BUY",
    order_type="LIMIT",
    limit_price=800.00
)
print(f"Estimated cost: ${preview['estimated_cost']}")

# Get open orders
orders = client.get_open_orders()
for order in orders:
    print(f"{order['symbol']}: {order['side']} {order['quantity']}")

# Cancel an order
client.cancel_order(client_order_id="abc123...")

# Get account balance
balance = client.get_account_balance()
print(f"Buying Power: ${balance['buying_power']:,.2f}")
```

## 📚 API Reference

### WebullClient Methods

#### Account Management
- `get_accounts()` - Get list of all accounts
- `get_default_account_id()` - Get primary account ID
- `get_account_balance(account_id=None)` - Get cash/margin balances
- `get_account_positions(account_id=None)` - Get current holdings
- `get_portfolio_summary(account_id=None)` - Comprehensive portfolio data

#### Equity Trading
- `place_equity_order(symbol, quantity, side, order_type, limit_price, ...)` - Place stock order
- `preview_equity_order(symbol, quantity, side, ...)` - Preview order cost
- `cancel_order(client_order_id)` - Cancel pending order
- `get_open_orders()` - List all open orders
- `get_order_detail(client_order_id)` - Get order status

#### Options Trading
- `place_option_order(symbol, strike_price, option_expire_date, option_type, ...)` - Place option trade

#### Utilities
- `format_position_for_display(position)` - Format position for human reading

## 🔐 Security Best Practices

1. **Never commit API keys** - Always use environment variables
2. **Use test environment first** - Set `use_production=False` during development
3. **Validate orders** - Always preview orders before placing
4. **Set limits** - Implement position size limits
5. **Monitor closely** - Log all trading activity

## 🌍 Environments

### Test Environment (Development)
```python
client = create_webull_client(use_production=False)
```
- Endpoint: `us-openapi-alb.uat.webullbroker.com`
- Uses test credentials
- No real money involved
- Perfect for development

### Production Environment (Live Trading)
```python
client = create_webull_client(use_production=True)
```
- Endpoint: `api.webull.com`
- Uses production credentials
- **Real money at risk**
- Only use when fully tested

## 📊 Order Types

### Market Order
Executes immediately at best available price:
```python
client.place_equity_order(
    symbol="AAPL",
    quantity=10,
    side="BUY",
    order_type="MARKET"
)
```

### Limit Order
Executes only at specified price or better:
```python
client.place_equity_order(
    symbol="AAPL",
    quantity=10,
    side="BUY",
    order_type="LIMIT",
    limit_price=175.50
)
```

### Time in Force
- `DAY` - Expires at market close (default)
- `GTC` - Good 'til Canceled (persists across days)

## 🐛 Troubleshooting

### "Webull API credentials not found"
**Solution:** Add `WEBULL_APP_KEY` and `WEBULL_APP_SECRET` to `.env` file

### "Failed to fetch accounts"
**Possible causes:**
1. Invalid API credentials
2. API access not enabled on account
3. Using production keys in test mode (or vice versa)
4. Network/firewall issues

**Solution:** Run `python test_webull_connection.py` for detailed diagnostics

### Order placement fails
**Common issues:**
1. Insufficient buying power
2. Invalid symbol
3. Market closed (check trading hours)
4. Missing limit_price for LIMIT orders

## 📁 File Structure

```
BentleyBudgetBot/
├── services/
│   └── webull_client.py          # Main API client wrapper
├── pages/
│   └── webull_trading.py         # Streamlit dashboard
├── webull-sdk/
│   └── webull-openapi-demo-py-us/
│       ├── README.md             # Official SDK docs
│       ├── requirements.txt      # SDK dependencies
│       └── trade_client_example.py  # Official examples
├── test_webull_connection.py     # Connection test script
└── requirements.txt              # Project dependencies
```

## 🔄 Integration with BentleyBot

The Webull client integrates seamlessly with your existing infrastructure:

- Uses same `.env` pattern as other services
- Follows BentleyBot color scheme and styling
- Compatible with existing MySQL database structure
- Can be extended to log trades to database
- Works alongside Yahoo Finance data feeds

## 🚧 Future Enhancements

Potential additions:
- [ ] Store trade history in MySQL
- [ ] Real-time portfolio tracking with yfinance
- [ ] Automated trading strategies
- [ ] Risk management rules
- [ ] Trade notifications (email/SMS)
- [ ] Options strategies (spreads, iron condors)
- [ ] Paper trading mode
- [ ] Backtesting integration

## 📖 Resources

- [Webull OpenAPI Documentation](https://www.webull.com/open-api)
- [SDK GitHub Repository](https://github.com/webull-inc/webull-openapi-python-sdk)
- Test example: `webull-sdk/webull-openapi-demo-py-us/trade_client_example.py`

## ⚠️ Disclaimer

**This software is for educational purposes only. Trading involves risk. Past performance does not guarantee future results. Always understand the risks before trading real money.**

---

**Questions?** Check the test script output or review the official SDK examples in `webull-sdk/`.
