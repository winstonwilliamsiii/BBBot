# BentleyBot API Routes Documentation

Complete API reference for all unified broker endpoints.

## 📍 Available Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/trade` | POST | Execute trades across brokers |
| `/api/positions` | GET | Get current positions |
| `/api/balance` | GET | Get account balance |
| `/api/order-status` | GET | Check order status |

## 🔑 Authentication

All endpoints use environment-based broker credentials:
- **Alpaca**: `ALPACA_KEY_ID`, `ALPACA_SECRET_KEY`
- **IBKR**: `IBKR_GATEWAY_URL`, `IBKR_ACCOUNT_ID`
- **Schwab**: `SCHWAB_CLIENT_ID`, `SCHWAB_REFRESH_TOKEN`
- **MT5**: `MT5_API_URL`
- **Binance**: `BINANCE_API_KEY`, `BINANCE_API_SECRET`

## 📊 1. Trade Execution

**POST** `/api/trade`

Place orders across multiple brokers with automatic routing.

### Request
```json
{
  "class": "equities",
  "symbol": "AAPL",
  "qty": 10,
  "side": "buy",
  "params": {
    "type": "limit",
    "limit_price": 150.00,
    "time_in_force": "day"
  }
}
```

### Response
```json
{
  "broker": "alpaca",
  "orderId": "abc-123-def",
  "status": "accepted",
  "filledQty": null,
  "symbol": "AAPL",
  "side": "buy",
  "qty": 10,
  "timestamp": "2026-01-11T12:00:00.000Z",
  "raw": { ... }
}
```

### Supported Order Types
- `market` - Execute at current market price
- `limit` - Execute at specified price or better
- `stop` - Market order triggered at stop price
- `stop_limit` - Limit order triggered at stop price
- `trailing_stop` - Stop order that trails market price

[See full trade API docs](README.md#api-reference)

## 📦 2. Get Positions

**GET** `/api/positions`

Retrieve all open positions from broker account.

### Query Parameters
- `class` - Asset class (default: `equities`)
- `broker` - Optional broker override

### Examples

```bash
# Get equities positions (auto-selects broker)
curl http://localhost:3000/api/positions?class=equities

# Get positions from specific broker
curl http://localhost:3000/api/positions?class=equities&broker=alpaca

# Get forex positions
curl http://localhost:3000/api/positions?class=forex
```

### Response
```json
{
  "broker": "alpaca",
  "positions": [
    {
      "broker": "alpaca",
      "symbol": "AAPL",
      "qty": 10,
      "avgPrice": 150.00,
      "marketValue": 1520.50,
      "unrealizedPnL": 20.50,
      "raw": { ... }
    },
    {
      "broker": "alpaca",
      "symbol": "TSLA",
      "qty": 5,
      "avgPrice": 240.00,
      "marketValue": 1205.25,
      "unrealizedPnL": 5.25,
      "raw": { ... }
    }
  ]
}
```

### Response Fields
- `broker` - Broker name
- `symbol` - Ticker symbol
- `qty` - Current position size
- `avgPrice` - Average entry price
- `marketValue` - Current market value
- `unrealizedPnL` - Unrealized profit/loss
- `raw` - Raw broker response

## 💰 3. Get Balance

**GET** `/api/balance`

Retrieve account balance, buying power, and equity.

### Query Parameters
- `class` - Asset class (default: `equities`)
- `broker` - Optional broker override

### Examples

```bash
# Get account balance (auto-selects broker)
curl http://localhost:3000/api/balance?class=equities

# Get balance from specific broker
curl http://localhost:3000/api/balance?class=equities&broker=alpaca

# Get crypto account balance
curl http://localhost:3000/api/balance?class=crypto
```

### Response
```json
{
  "broker": "alpaca",
  "balance": {
    "broker": "alpaca",
    "cash": 10000.00,
    "buyingPower": 40000.00,
    "equity": 12000.00,
    "portfolioValue": 12000.00,
    "currency": "USD",
    "raw": { ... }
  }
}
```

### Response Fields
- `broker` - Broker name
- `cash` - Available cash
- `buyingPower` - Total buying power (includes margin)
- `equity` - Total account equity
- `portfolioValue` - Total portfolio value
- `currency` - Account currency
- `raw` - Raw broker response

## 📋 4. Get Order Status

**GET** `/api/order-status`

Check the status of a previously placed order.

### Query Parameters
- `orderId` - Order ID (required)
- `class` - Asset class (default: `equities`)
- `broker` - Optional broker override

### Examples

```bash
# Check order status (auto-selects broker)
curl "http://localhost:3000/api/order-status?orderId=abc-123&class=equities"

# Check order from specific broker
curl "http://localhost:3000/api/order-status?orderId=abc-123&broker=alpaca"
```

### Response
```json
{
  "broker": "alpaca",
  "status": {
    "broker": "alpaca",
    "orderId": "abc-123-def",
    "status": "filled",
    "symbol": "AAPL",
    "side": "buy",
    "qty": 10,
    "filledQty": 10,
    "avgFillPrice": 150.25,
    "submittedAt": "2026-01-11T10:00:00.000Z",
    "filledAt": "2026-01-11T10:00:05.123Z",
    "updatedAt": "2026-01-11T10:00:05.123Z",
    "raw": { ... }
  }
}
```

### Order Status Values
- `new` - Order accepted but not yet submitted
- `accepted` - Order submitted to exchange
- `pending_new` - Order being processed
- `partially_filled` - Part of order filled
- `filled` - Order completely filled
- `canceled` - Order canceled
- `rejected` - Order rejected by broker/exchange
- `expired` - Order expired
- `unknown` - Status cannot be determined

## 🔄 Complete Trading Workflow

### Example: Buy 10 shares of AAPL

```bash
# Step 1: Check account balance
curl http://localhost:3000/api/balance?class=equities
# Response: { "cash": 10000, "buyingPower": 40000, ... }

# Step 2: Place limit buy order
curl -X POST http://localhost:3000/api/trade \
  -H "Content-Type: application/json" \
  -d '{
    "class": "equities",
    "symbol": "AAPL",
    "qty": 10,
    "side": "buy",
    "params": {
      "type": "limit",
      "limit_price": 150.00,
      "time_in_force": "day"
    }
  }'
# Response: { "orderId": "abc-123", "status": "accepted", ... }

# Step 3: Check order status (wait for fill)
curl "http://localhost:3000/api/order-status?orderId=abc-123&class=equities"
# Response: { "status": "filled", "filledQty": 10, "avgFillPrice": 150.05, ... }

# Step 4: View updated positions
curl http://localhost:3000/api/positions?class=equities
# Response: { "positions": [{ "symbol": "AAPL", "qty": 10, ... }] }

# Step 5: Check updated balance
curl http://localhost:3000/api/balance?class=equities
# Response: { "cash": 8499.50, "equity": 11500.50, ... }
```

## 🌐 Broker Routing

All endpoints automatically route to the correct broker based on:
1. **Asset class** - Different brokers for equities, futures, forex, etc.
2. **Environment** - MVP uses paper trading, PRODUCTION uses live brokers
3. **Broker override** - Optional `broker` parameter

### Default Routing

**MVP Mode**:
```
Equities → Alpaca (paper)
Futures → NinjaTrader + TradeStation
Options → IBKR
Forex → MT5 + IBKR
Crypto → Binance
```

**PRODUCTION Mode**:
```
Equities → IBKR, Schwab
Futures → NinjaTrader + TradeStation
Options → IBKR
Forex → MT5 + IBKR
Crypto → Binance
```

Set via `APP_ENV` environment variable.

## 🛠️ Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Missing Alpaca credentials",
  "details": "Set ALPACA_KEY_ID and ALPACA_SECRET_KEY",
  "timestamp": "2026-01-11T12:00:00.000Z"
}
```

### HTTP Status Codes
- `200` - Success
- `400` - Bad request (invalid parameters)
- `405` - Method not allowed
- `500` - Server error (broker API failure)

## 🔧 Development

### Start Development Server
```bash
npm run dev
```

API available at: `http://localhost:3000/api/*`

### Test Endpoints
```bash
# Test all endpoints
node tests/test_trade_api.js

# Test positions
curl http://localhost:3000/api/positions?class=equities

# Test balance
curl http://localhost:3000/api/balance?class=equities
```

## 📝 TypeScript Types

### Common Types
```typescript
type AssetClass = 'equities' | 'futures' | 'options' | 'forex' | 'crypto'
type OrderSide = 'buy' | 'sell'
type OrderType = 'market' | 'limit' | 'stop' | 'stop_limit' | 'trailing_stop'
type TimeInForce = 'day' | 'gtc' | 'opg' | 'cls' | 'ioc' | 'fok'
```

### Request/Response Interfaces
```typescript
interface Asset {
  class: AssetClass
  symbol: string
  qty: number
  side: OrderSide
  params?: {
    type?: OrderType
    limit_price?: number
    stop_price?: number
    time_in_force?: TimeInForce
    // ...
  }
}

interface NormalizedPosition {
  broker: string
  symbol: string
  qty: number
  avgPrice?: number
  marketValue?: number
  unrealizedPnL?: number
  raw: any
}

interface NormalizedBalance {
  broker: string
  cash: number | null
  buyingPower: number | null
  equity: number | null
  portfolioValue?: number | null
  currency?: string
  raw: any
}

interface NormalizedOrderStatus {
  broker: string
  orderId: string
  status: string
  symbol?: string
  side?: string
  qty?: number
  filledQty: number | null
  avgFillPrice?: number | null
  submittedAt?: string
  filledAt?: string
  updatedAt?: string
  raw: any
}
```

## 📚 Related Documentation

- **[Trade API Full Docs](README.md)** - Complete trade endpoint documentation
- **[Broker Mapping](../BROKER_MAPPING.md)** - Official broker-to-asset assignments
- **[Quick Reference](../BROKER_QUICK_REFERENCE.md)** - Streamlit integration guide
- **[Implementation Summary](../TRADE_API_SUMMARY.md)** - Project overview

## 🆘 Troubleshooting

### Positions endpoint returns empty array
- Check broker credentials are set correctly
- Verify you have open positions in the account
- Try specifying broker explicitly: `?broker=alpaca`

### Balance endpoint returns null values
- Check broker connection status
- Verify account credentials
- Check broker is supported for asset class

### Order status returns "unknown"
- Order ID may be invalid or from different broker
- Specify correct broker: `?broker=alpaca`
- Check order was placed successfully

### "Unsupported broker" error
- Check asset class is valid
- Verify broker credentials are configured
- Review [BROKER_MAPPING.md](../BROKER_MAPPING.md) for supported combinations

---

**Last Updated**: January 11, 2026  
**Version**: 1.0.0
