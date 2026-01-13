# Quick Start: Using the Broker Adapters

## 🚀 Setup Guide

### 1. Environment Variables Setup

Copy this template to your `.env.brokers` file and fill in your credentials:

```bash
# ============================================
# SCHWAB (OAuth2)
# ============================================
SCHWAB_CLIENT_ID=your_client_id
SCHWAB_CLIENT_SECRET=your_client_secret
SCHWAB_REFRESH_TOKEN=your_refresh_token
SCHWAB_ACCOUNT_ID=your_account_id
SCHWAB_API_URL=https://api.schwabapi.com

# ============================================
# BINANCE (HMAC SHA256)
# ============================================
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_API_URL=https://api.binance.com

# ============================================
# TRADESTATION (OAuth2)
# ============================================
TRADESTATION_CLIENT_ID=your_client_id
TRADESTATION_CLIENT_SECRET=your_client_secret
TRADESTATION_REFRESH_TOKEN=your_refresh_token
TRADESTATION_ACCOUNT_ID=your_account_id
TRADESTATION_API_URL=https://api.tradestation.com

# ============================================
# ENVIRONMENT MODE
# ============================================
APP_ENV=MVP  # or PRODUCTION
```

---

## 📡 API Usage Examples

### Get Positions

#### Schwab (Equities)
```bash
# Default (auto-selects broker based on asset class)
curl "http://localhost:3000/api/positions?class=equities"

# Explicit broker selection
curl "http://localhost:3000/api/positions?broker=schwab"
```

**Response:**
```json
{
  "broker": "schwab",
  "positions": [
    {
      "broker": "schwab",
      "symbol": "AAPL",
      "qty": 100,
      "avgPrice": 150.50,
      "marketValue": 15500.00,
      "unrealizedPnL": 500.00,
      "raw": { /* Schwab API response */ }
    }
  ]
}
```

#### Binance (Crypto)
```bash
curl "http://localhost:3000/api/positions?class=crypto"
```

**Response:**
```json
{
  "broker": "binance",
  "positions": [
    {
      "broker": "binance",
      "symbol": "BTC",
      "qty": 0.5,
      "raw": { "free": "0.25", "locked": "0.25" }
    }
  ]
}
```

#### TradeStation (Futures)
```bash
curl "http://localhost:3000/api/positions?class=futures&broker=tradestation"
```

---

### Get Balance

#### Schwab
```bash
curl "http://localhost:3000/api/balance?broker=schwab"
```

**Response:**
```json
{
  "broker": "schwab",
  "balance": {
    "broker": "schwab",
    "cash": 10000.00,
    "equity": 25500.00,
    "buyingPower": 50000.00,
    "raw": { /* Schwab balance data */ }
  }
}
```

#### Binance
```bash
curl "http://localhost:3000/api/balance?class=crypto"
```

#### TradeStation
```bash
curl "http://localhost:3000/api/balance?broker=tradestation"
```

---

### Get Order Status

#### Schwab
```bash
curl "http://localhost:3000/api/order-status?orderId=abc-123&broker=schwab"
```

**Response:**
```json
{
  "broker": "schwab",
  "status": {
    "broker": "schwab",
    "orderId": "abc-123",
    "status": "FILLED",
    "symbol": "AAPL",
    "side": "BUY",
    "qty": 100,
    "filledQty": 100,
    "avgFillPrice": 150.50,
    "submittedAt": "2024-01-15T10:30:00Z",
    "filledAt": "2024-01-15T10:30:15Z"
  }
}
```

#### Binance
```bash
curl "http://localhost:3000/api/order-status?orderId=12345678&broker=binance"
```

#### TradeStation
```bash
curl "http://localhost:3000/api/order-status?orderId=TS-987654&broker=tradestation"
```

---

## 🔐 OAuth2 Setup (Schwab & TradeStation)

### Initial Authorization Flow

Both Schwab and TradeStation require OAuth2 authorization. Here's how to get your refresh token:

#### 1. Register Your Application
- **Schwab**: [Schwab Developer Portal](https://developer.schwab.com/)
- **TradeStation**: [TradeStation Developer Portal](https://developer.tradestation.com/)

#### 2. Get Authorization Code
```bash
# Schwab
https://api.schwabapi.com/v1/oauth/authorize?
  client_id=YOUR_CLIENT_ID&
  redirect_uri=YOUR_REDIRECT_URI&
  response_type=code

# TradeStation
https://signin.tradestation.com/authorize?
  client_id=YOUR_CLIENT_ID&
  redirect_uri=YOUR_REDIRECT_URI&
  response_type=code
```

#### 3. Exchange Code for Tokens
```bash
# Schwab
curl -X POST https://api.schwabapi.com/v1/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=YOUR_AUTH_CODE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=YOUR_REDIRECT_URI"

# TradeStation
curl -X POST https://signin.tradestation.com/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=YOUR_AUTH_CODE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=YOUR_REDIRECT_URI"
```

#### 4. Save Refresh Token
Take the `refresh_token` from the response and add it to your `.env.brokers` file.

**Note:** The broker adapters automatically handle token refresh using the refresh token!

---

## 🔑 Binance API Setup

### 1. Create API Key
1. Log in to [Binance](https://www.binance.com/)
2. Go to **API Management**
3. Create a new API key
4. Enable **Spot & Margin Trading** (if needed)
5. Whitelist your server IP (optional but recommended)

### 2. Save Credentials
Copy the API Key and Secret Key to your `.env.brokers` file.

### 3. Test Connection
```bash
curl "http://localhost:3000/api/balance?broker=binance"
```

**Security Note:** Binance uses HMAC SHA256 signing for all authenticated requests. The adapter handles this automatically!

---

## 🧪 Testing Your Setup

### Health Check Script

Create `test_broker_connections.sh`:

```bash
#!/bin/bash

echo "Testing Schwab..."
curl -s "http://localhost:3000/api/positions?broker=schwab" | jq

echo -e "\nTesting Binance..."
curl -s "http://localhost:3000/api/balance?broker=binance" | jq

echo -e "\nTesting TradeStation..."
curl -s "http://localhost:3000/api/positions?broker=tradestation" | jq
```

### Node.js Test Script

Create `test_brokers.js`:

```javascript
const brokers = ['schwab', 'binance', 'tradestation']

async function testBroker(broker) {
  const response = await fetch(`http://localhost:3000/api/positions?broker=${broker}`)
  const data = await response.json()
  
  if (data.error) {
    console.error(`❌ ${broker}: ${data.error}`)
  } else {
    console.log(`✅ ${broker}: ${data.positions.length} positions`)
  }
}

Promise.all(brokers.map(testBroker))
```

Run it:
```bash
node test_brokers.js
```

---

## 🐛 Troubleshooting

### Schwab Errors

**401 Unauthorized**
- Check if `SCHWAB_REFRESH_TOKEN` is valid
- Token may have expired - reauthorize your app
- Verify `SCHWAB_CLIENT_ID` and `SCHWAB_CLIENT_SECRET`

**404 Not Found**
- Verify `SCHWAB_ACCOUNT_ID` is correct
- Check if account has active positions

### Binance Errors

**-1022 Invalid Signature**
- Check `BINANCE_API_SECRET` is correct
- Ensure system time is synchronized (Binance requires ±1s accuracy)

**-2015 Invalid API Key**
- Verify `BINANCE_API_KEY` is active
- Check IP whitelist settings

### TradeStation Errors

**401 Unauthorized**
- Check if `TRADESTATION_REFRESH_TOKEN` is valid
- Reauthorize if token expired

**403 Forbidden**
- Verify account has appropriate permissions
- Check if API access is enabled for your account

---

## 📊 Environment-Based Routing

The API automatically selects brokers based on `APP_ENV`:

```bash
# Development/Paper Trading
export APP_ENV=MVP

# Production/Live Trading
export APP_ENV=PRODUCTION
```

**Asset Class Mapping:**

| Asset Class | MVP Broker | Production Broker |
|-------------|-----------|-------------------|
| Equities | Alpaca | IBKR, Schwab |
| Futures | TradeStation | TradeStation |
| Options | IBKR | IBKR |
| Forex | MT5, IBKR | MT5, IBKR |
| Crypto | Binance | Binance |

---

## 📝 Integration with Streamlit App

### Example: Get Portfolio Value

```python
import requests

def get_total_portfolio_value():
    """Get combined portfolio value from all brokers"""
    total = 0
    
    # Get Schwab equity positions
    r = requests.get('http://localhost:3000/api/balance?broker=schwab')
    if r.ok:
        total += r.json()['balance']['equity']
    
    # Get Binance crypto balance
    r = requests.get('http://localhost:3000/api/balance?broker=binance')
    if r.ok:
        total += r.json()['balance']['equity']
    
    # Get TradeStation futures balance
    r = requests.get('http://localhost:3000/api/balance?broker=tradestation')
    if r.ok:
        total += r.json()['balance']['equity']
    
    return total

# Use in Streamlit
import streamlit as st

st.metric("Total Portfolio Value", f"${get_total_portfolio_value():,.2f}")
```

---

## 🎯 Next Steps

1. ✅ Set up environment variables
2. ✅ Complete OAuth2 authorization for Schwab/TradeStation
3. ✅ Create Binance API keys
4. ✅ Test all broker connections
5. ⏳ Integrate with your Streamlit dashboard
6. ⏳ Set up error monitoring and alerts
7. ⏳ Configure production environment

---

## 📚 Additional Resources

- [Broker Mapping Documentation](BROKER_MAPPING.md)
- [Full API Routes Reference](pages/api/API_ROUTES.md)
- [Implementation Details](BROKER_ADAPTERS_IMPLEMENTATION.md)
- [Trade API Summary](TRADE_API_SUMMARY.md)

---

*Need help? Check the troubleshooting section or review the implementation docs!*
