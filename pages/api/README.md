# Unified Broker Trade API

Production-ready REST API for executing trades across multiple brokers with intelligent routing, fallback handling, and comprehensive observability.

## Overview

The `/api/trade` endpoint provides a unified interface for trading across:
- **Alpaca** (equities) - ✅ Fully implemented
- **Interactive Brokers** (equities, options, forex, futures) - 🚧 Stub ready
- **Charles Schwab** (equities, options) - 🚧 Stub ready
- **MetaTrader 5** (forex) - 🚧 Stub ready
- **Binance** (crypto) - 🚧 Stub ready

## Broker-to-Asset Mapping

| Asset Class    | MVP Brokers              | PRODUCTION Brokers       |
|----------------|--------------------------|---------------------------|
| Equities/ETFs  | Alpaca                   | IBKR, Schwab              |
| Futures        | NinjaTrader, TradeStation| NinjaTrader, TradeStation |
| Options        | IBKR                     | IBKR                      |
| Forex          | MT5, IBKR                | MT5, IBKR                 |
| Crypto         | Binance                  | Binance                   |

### MVP Mode (Default)
Uses paper trading and development brokers:
- **Equities/ETFs** → Alpaca (paper trading)
- **Futures** → NinjaTrader + TradeStation
- **Options** → IBKR
- **Forex** → MT5 + IBKR
- **Crypto** → Binance

### PRODUCTION Mode
Prioritizes institutional brokers:
- **Equities/ETFs** → IBKR, Schwab (live trading)
- **Futures** → NinjaTrader + TradeStation
- **Options** → IBKR
- **Forex** → MT5 + IBKR
- **Crypto** → Binance

Set via `APP_ENV` environment variable.

## Quick Start

### 1. Configure Environment

Copy `.env.brokers` to `.env` and fill in your credentials:

```bash
cp .env.brokers .env
```

Minimum required for MVP:
```env
APP_ENV=MVP
ALPACA_KEY_ID=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Start Development Server

```bash
npm run dev
```

### 4. Test the API

Simple market order:
```bash
curl -X POST http://localhost:3000/api/trade \
  -H "Content-Type: application/json" \
  -d '{
    "class": "equities",
    "symbol": "AAPL",
    "qty": 1,
    "side": "buy"
  }'
```

Limit order:
```bash
curl -X POST http://localhost:3000/api/trade \
  -H "Content-Type: application/json" \
  -d '{
    "class": "equities",
    "symbol": "TSLA",
    "qty": 5,
    "side": "buy",
    "params": {
      "type": "limit",
      "limit_price": 250.00,
      "time_in_force": "gtc",
      "extended_hours": false
    }
  }'
```

## API Reference

### Endpoint

```
POST /api/trade
```

### Request Schema

```typescript
{
  class: 'equities' | 'futures' | 'options' | 'forex' | 'crypto'  // Required
  symbol: string                                                   // Required
  qty: number                                                      // Required
  side: 'buy' | 'sell'                                            // Required
  params?: {
    // Order type parameters
    type?: 'market' | 'limit' | 'stop' | 'stop_limit' | 'trailing_stop'
    time_in_force?: 'day' | 'gtc' | 'opg' | 'cls' | 'ioc' | 'fok'
    
    // Price parameters
    limit_price?: number        // For limit and stop_limit orders
    stop_price?: number         // For stop and stop_limit orders
    trail_price?: number        // For trailing_stop orders
    trail_percent?: number      // For trailing_stop orders (alternative to trail_price)
    
    // Execution parameters
    extended_hours?: boolean    // Allow pre/post market execution
    client_order_id?: string    // Your custom order identifier
    
    // Broker-specific (optional)
    conid?: number             // IBKR contract ID
    strike?: number            // Options strike price
    expiry?: string            // Options expiry date
    option_type?: 'call' | 'put'
    [key: string]: any         // Additional broker-specific params
  }
}
```

### Response Schema

Success (200):
```typescript
{
  broker: string                // Broker that executed the order
  orderId: string | null        // Broker's order ID
  status: string                // Order status (e.g., 'accepted', 'filled', 'pending')
  filledQty: number | null      // Quantity filled (may be partial)
  symbol: string                // Symbol traded
  side: 'buy' | 'sell'         // Order side
  qty: number                   // Order quantity
  timestamp: string             // ISO 8601 timestamp
  raw: any                      // Raw broker response for debugging
}
```

Error (400, 405, 500):
```typescript
{
  error: string                 // Error message
  details?: string              // Additional error details
  timestamp: string             // ISO 8601 timestamp
}
```

## Order Types Explained

### Market Order
Executes immediately at current market price:
```json
{
  "params": {
    "type": "market",
    "time_in_force": "day"
  }
}
```

### Limit Order
Executes only at specified price or better:
```json
{
  "params": {
    "type": "limit",
    "limit_price": 150.00,
    "time_in_force": "gtc"
  }
}
```

### Stop Order
Market order triggered when price reaches stop price:
```json
{
  "params": {
    "type": "stop",
    "stop_price": 145.00,
    "time_in_force": "day"
  }
}
```

### Stop Limit Order
Limit order triggered when price reaches stop price:
```json
{
  "params": {
    "type": "stop_limit",
    "stop_price": 145.00,
    "limit_price": 144.00,
    "time_in_force": "gtc"
  }
}
```

### Trailing Stop Order
Stop order that trails the market price:
```json
{
  "params": {
    "type": "trailing_stop",
    "trail_percent": 1.0,  // Trail by 1%
    "time_in_force": "gtc"
  }
}
```

## Time In Force Options

- `day` - Order active until market close (default)
- `gtc` - Good til canceled (active until filled or manually canceled)
- `opg` - Execute at market open only
- `cls` - Execute at market close only
- `ioc` - Immediate or cancel (fill immediately, cancel remainder)
- `fok` - Fill or kill (fill entire order immediately or cancel)

## Extended Hours Trading

Enable pre-market (4:00-9:30 AM ET) and after-hours (4:00-8:00 PM ET) trading:

```json
{
  "params": {
    "extended_hours": true
  }
}
```

⚠️ **Note**: Extended hours trading has lower liquidity and wider spreads.

## Error Handling

The API returns appropriate HTTP status codes:

- `200` - Success
- `400` - Invalid request (bad payload, unsupported broker, etc.)
- `405` - Method not allowed (only POST accepted)
- `500` - Server error (broker API failure, network issues, etc.)

All errors include:
```typescript
{
  error: string      // Human-readable error message
  details?: string   // Stack trace (development only)
  timestamp: string  // When error occurred
}
```

## Logging & Observability

All operations are logged with structured JSON:

```json
{
  "level": "INFO",
  "message": "Trade completed",
  "requestId": "trade_1736627839_abc123",
  "broker": "alpaca",
  "symbol": "AAPL",
  "qty": 10,
  "side": "buy",
  "orderId": "abc-def-ghi",
  "timestamp": "2026-01-11T12:34:56.789Z"
}
```

View logs in development:
```bash
npm run dev 2>&1 | grep TradeAPI
```

## Testing

### Unit Tests
```bash
npm test
```

### Integration Tests
```bash
npm run test:integration
```

### Manual Testing Script
```bash
node tests/test_trade_api.js
```

## Adding New Brokers

To implement a new broker adapter:

1. **Create adapter function** in `trade.ts`:
```typescript
async function yourBrokerTrade(asset: Asset): Promise<NormalizedOrder> {
  // 1. Validate environment variables
  // 2. Map asset to broker-specific payload
  // 3. Call broker API
  // 4. Normalize response
  // 5. Return NormalizedOrder
}
```

2. **Add to selectBroker preferences**:
```typescript
const preferences: Record<AssetClass, Record<EnvMode, string[]>> = {
  equities: { 
    MVP: ['alpaca', 'yourbroker'], 
    PRODUCTION: ['ibkr', 'yourbroker'] 
  },
  // ...
}
```

3. **Add switch case** in main handler:
```typescript
switch (broker) {
  case 'yourbroker':
    result = await yourBrokerTrade(asset)
    break
  // ...
}
```

4. **Test thoroughly** with paper/sandbox accounts first

## Examples

### Buy 100 shares of SPY at market
```bash
curl -X POST http://localhost:3000/api/trade \
  -H "Content-Type: application/json" \
  -d '{
    "class": "equities",
    "symbol": "SPY",
    "qty": 100,
    "side": "buy"
  }'
```

### Sell 50 shares of AAPL with limit
```bash
curl -X POST http://localhost:3000/api/trade \
  -H "Content-Type: application/json" \
  -d '{
    "class": "equities",
    "symbol": "AAPL",
    "qty": 50,
    "side": "sell",
    "params": {
      "type": "limit",
      "limit_price": 175.00,
      "time_in_force": "day"
    }
  }'
```

### Stop loss order
```bash
curl -X POST http://localhost:3000/api/trade \
  -H "Content-Type: application/json" \
  -d '{
    "class": "equities",
    "symbol": "TSLA",
    "qty": 10,
    "side": "sell",
    "params": {
      "type": "stop",
      "stop_price": 240.00,
      "time_in_force": "gtc"
    }
  }'
```

### Trailing stop order (1.5% trail)
```bash
curl -X POST http://localhost:3000/api/trade \
  -H "Content-Type: application/json" \
  -d '{
    "class": "equities",
    "symbol": "NVDA",
    "qty": 25,
    "side": "sell",
    "params": {
      "type": "trailing_stop",
      "trail_percent": 1.5,
      "time_in_force": "gtc"
    }
  }'
```

## Production Deployment

### Vercel Deployment
```bash
vercel --prod
```

### Environment Variables
Set in Vercel dashboard or via CLI:
```bash
vercel env add APP_ENV production
vercel env add ALPACA_KEY_ID production
vercel env add ALPACA_SECRET_KEY production
vercel env add ALPACA_BASE_URL production
```

### Security Checklist
- [ ] All credentials stored in environment variables (never committed)
- [ ] HTTPS enforced for all API calls
- [ ] Rate limiting configured
- [ ] API authentication/authorization implemented
- [ ] Paper trading tested thoroughly before live deployment
- [ ] Monitoring and alerting configured
- [ ] Error notifications set up
- [ ] Backup broker credentials stored securely

## Support & References

- **Alpaca API Docs**: https://alpaca.markets/docs/api-references/trading-api/
- **IBKR Gateway**: See `c:\Users\winst\BentleyBudgetBot\bbbot1_pipeline\broker_api.py`
- **MT5 Integration**: See `c:\Users\winst\BentleyBudgetBot\mt5_rest_api_server.py`
- **Project Structure**: See `PROJECT_STRUCTURE.md`
- **Copilot Instructions**: See `.github/copilot-instructions.md`

## Troubleshooting

### "Missing Alpaca credentials" error
Ensure these are set in `.env`:
```env
ALPACA_KEY_ID=pk_xxx
ALPACA_SECRET_KEY=xxx
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

### "Unsupported broker" error
Check:
1. `APP_ENV` is set correctly
2. Asset class is valid
3. Broker adapter is implemented for that asset class

### Orders not executing
1. Check broker account status
2. Verify sufficient buying power
3. Check market hours (use `extended_hours: true` if needed)
4. Review broker logs in console

### IBKR connection issues
1. Ensure IBKR Gateway is running (`http://localhost:5000`)
2. Verify credentials in `.env`
3. Check Gateway authentication status
4. See IBKR troubleshooting in project docs

## License

MIT - See LICENSE file for details
