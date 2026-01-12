# BentleyBot Broker-to-Asset Mapping

## Official Broker Configuration

This document defines the authoritative broker-to-asset class mapping for the BentleyBot trading platform.

## Broker Assignment by Asset Class

| Asset Class    | Brokers Used                      | Environment Support |
|----------------|-----------------------------------|---------------------|
| **Equities/ETFs** | Alpaca (MVP), IBKR (Production), Schwab (Production) | MVP + PRODUCTION |
| **Futures**    | NinjaTrader + TradeStation        | MVP + PRODUCTION |
| **Options**    | IBKR                              | MVP + PRODUCTION |
| **Forex**      | MT5 + IBKR                        | MVP + PRODUCTION |
| **Crypto**     | Binance                           | MVP + PRODUCTION |

## Detailed Routing Logic

### Equities/ETFs
- **MVP Environment**: Alpaca (paper trading)
- **PRODUCTION Environment**: IBKR (primary), Schwab (secondary)
- **Fallback**: If primary broker fails, try secondary
- **Use Cases**: Stocks, exchange-traded funds

### Futures
- **Both Environments**: NinjaTrader (primary), TradeStation (secondary)
- **No MVP/PROD distinction**: Same brokers for both modes
- **Use Cases**: Commodities, indices, currency futures

### Options
- **Both Environments**: IBKR only
- **No fallback**: IBKR is the sole option provider
- **Use Cases**: Equity options, index options

### Forex
- **Both Environments**: MT5 (primary), IBKR (secondary)
- **Fallback**: If MT5 unavailable, use IBKR
- **Use Cases**: Currency pairs (EUR/USD, GBP/JPY, etc.)

### Crypto
- **Both Environments**: Binance only
- **No fallback**: Binance is the sole crypto provider
- **Use Cases**: Bitcoin, Ethereum, altcoins

## Environment Variables Required

### Alpaca (Equities - MVP)
```env
ALPACA_KEY_ID=your_key_id
ALPACA_SECRET_KEY=your_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # MVP
# ALPACA_BASE_URL=https://api.alpaca.markets  # Not used in MVP
```

### Interactive Brokers (Equities/Options/Forex - PRODUCTION)
```env
IBKR_HOST=127.0.0.1
IBKR_PORT=7497  # 7497=paper, 7496=live
IBKR_CLIENT_ID=1
IBKR_GATEWAY_URL=http://localhost:5000
IBKR_ACCOUNT_ID=your_account_id
```

### Charles Schwab (Equities - PRODUCTION)
```env
SCHWAB_API_URL=https://api.schwabapi.com
SCHWAB_CLIENT_ID=your_client_id
SCHWAB_CLIENT_SECRET=your_client_secret
SCHWAB_REFRESH_TOKEN=your_refresh_token
SCHWAB_ACCOUNT_ID=your_account_id
```

### NinjaTrader (Futures)
```env
NINJATRADER_API_URL=http://localhost:9000
NINJATRADER_ACCOUNT_ID=your_account_id
```

### TradeStation (Futures)
```env
TRADESTATION_API_URL=https://api.tradestation.com
TRADESTATION_CLIENT_ID=your_client_id
TRADESTATION_CLIENT_SECRET=your_client_secret
TRADESTATION_REFRESH_TOKEN=your_refresh_token
```

### MetaTrader 5 (Forex)
```env
MT5_API_URL=http://localhost:8000
```

### Binance (Crypto)
```env
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_API_URL=https://api.binance.com  # Live
# BINANCE_API_URL=https://testnet.binance.vision  # Testnet
BINANCE_TESTNET=false  # Set to true for testnet
```

## Implementation Notes

### Why These Brokers?

1. **Alpaca (Equities - MVP)**
   - Free paper trading
   - Easy API integration
   - Perfect for MVP/development
   - Commission-free live trading

2. **IBKR (Equities/Options/Forex - PRODUCTION)**
   - Industry standard for institutional trading
   - Comprehensive asset class coverage
   - Competitive pricing
   - Gateway API for automation

3. **Schwab (Equities - PRODUCTION)**
   - Commission-free trading
   - Reliable infrastructure
   - Secondary fallback for equities

4. **NinjaTrader + TradeStation (Futures)**
   - Specialized futures platforms
   - Advanced order types
   - Low latency execution

5. **MT5 (Forex)**
   - Most popular forex platform
   - Local REST API integration
   - Real-time data

6. **Binance (Crypto)**
   - Largest crypto exchange
   - Comprehensive API
   - High liquidity

### Fallback Strategy

The system implements intelligent fallback:

1. **Primary broker** - Try first
2. **Secondary broker** - If primary fails
3. **Error** - If all brokers unavailable

Example for Equities in PRODUCTION:
```
Request → Try IBKR → Success ✓
Request → Try IBKR → Fail → Try Schwab → Success ✓
Request → Try IBKR → Fail → Try Schwab → Fail → Error ✗
```

### Adding New Brokers

To add a broker:

1. Add credentials to `.env.brokers`
2. Update broker mapping in `pages/api/trade.ts`
3. Implement adapter function
4. Update this documentation
5. Test thoroughly in paper/sandbox mode

## API Usage Examples

### Equities (MVP - uses Alpaca)
```bash
curl -X POST http://localhost:3000/api/trade \
  -H "Content-Type: application/json" \
  -d '{
    "class": "equities",
    "symbol": "AAPL",
    "qty": 10,
    "side": "buy"
  }'
```

### Futures (uses NinjaTrader/TradeStation)
```bash
curl -X POST http://localhost:3000/api/trade \
  -H "Content-Type: application/json" \
  -d '{
    "class": "futures",
    "symbol": "ES",
    "qty": 1,
    "side": "buy"
  }'
```

### Options (uses IBKR)
```bash
curl -X POST http://localhost:3000/api/trade \
  -H "Content-Type: application/json" \
  -d '{
    "class": "options",
    "symbol": "AAPL",
    "qty": 1,
    "side": "buy",
    "params": {
      "strike": 150,
      "expiry": "2026-01-16",
      "option_type": "call"
    }
  }'
```

### Forex (uses MT5/IBKR)
```bash
curl -X POST http://localhost:3000/api/trade \
  -H "Content-Type: application/json" \
  -d '{
    "class": "forex",
    "symbol": "EURUSD",
    "qty": 10000,
    "side": "buy"
  }'
```

### Crypto (uses Binance)
```bash
curl -X POST http://localhost:3000/api/trade \
  -H "Content-Type: application/json" \
  -d '{
    "class": "crypto",
    "symbol": "BTCUSDT",
    "qty": 0.01,
    "side": "buy"
  }'
```

## Version History

- **v1.0.0** (2026-01-11) - Initial broker mapping established
  - Equities: Alpaca (MVP), IBKR + Schwab (PRODUCTION)
  - Futures: NinjaTrader + TradeStation
  - Options: IBKR
  - Forex: MT5 + IBKR
  - Crypto: Binance

## Related Documentation

- [Trade API README](pages/api/README.md)
- [Trade API Implementation](TRADE_API_SUMMARY.md)
- [Environment Configuration](.env.brokers)
- [Copilot Instructions](.github/copilot-instructions.md)

---

**Last Updated**: January 11, 2026  
**Maintained By**: BentleyBot Development Team
