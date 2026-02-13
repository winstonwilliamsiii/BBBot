# MT5 Paper Trading - Quick Start Guide

## Prerequisites ✅

Before starting, ensure you have:

1. **Windows Operating System** (MetaTrader5 is Windows-only)
2. **MetaTrader 5 Desktop** installed on Windows
3. **Demo/Paper Trading Account** set up (File → Open Demo Account in MT5)
4. **MT5 Terminal logged in** (must be running before starting the server)
5. **Python 3.11+** with Windows-specific dependencies:
   ```powershell
   pip install -r requirements-mt5.txt
   ```

> ⚠️ **Linux/Mac Users:** MT5 Python connector only works on Windows. For Linux deployments, only the REST API endpoints will work (no actual trading execution).

---

## Step 1: Start MetaTrader 5 Terminal

1. Open **MetaTrader 5** application
2. Log into your **DEMO account** (paper trading)
3. **Keep MT5 running** in the background

> ⚠️ The REST API server requires MT5 terminal to be running and logged in.

---

## Step 2: Start the MT5 REST Server

Open PowerShell in the project directory and run:

```powershell
.\START_MT5_PAPER_TRADING.ps1
```

This script will:
- ✅ Check if MT5 is running
- ✅ Activate Python virtual environment
- ✅ Install MetaTrader5 package (if needed)
- ✅ Start REST API server on `http://localhost:8080`

---

## Step 3: Test the Connection

### Health Check
```bash
curl http://localhost:8080/health
```
**Expected Response:**
```json
{
  "status": "ok",
  "service": "mt5-bridge"
}
```

### Connect to MT5 (Auto-connect)
```bash
curl -X POST http://localhost:8080/connect
```
The server will automatically connect to the MT5 terminal that's already running.

### Get Account Info
```bash
curl http://localhost:8080/account
```
**Expected Response:**
```json
{
  "success": true,
  "data": {
    "login": 123456789,
    "balance": 10000.0,
    "equity": 10000.0,
    "margin": 0.0,
    "free_margin": 10000.0,
    "leverage": 100,
    "currency": "USD"
  }
}
```

---

## Step 4: Place Your First Paper Trade

### Example: Buy EURUSD
```bash
curl -X POST http://localhost:8080/trade \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "EURUSD",
    "action": "buy",
    "volume": 0.01,
    "stop_loss": 1.0800,
    "take_profit": 1.0900,
    "comment": "Paper trade test"
  }'
```

### Example: Get Current Price
```bash
curl http://localhost:8080/price/EURUSD
```

### Example: View Open Positions
```bash
curl http://localhost:8080/positions
```

### Example: Close Position
```bash
curl -X POST http://localhost:8080/close \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "EURUSD"
  }'
```

---

## API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Server health check |
| `POST` | `/connect` | Connect to MT5 (auto-detects running terminal) |
| `POST` | `/disconnect` | Disconnect from MT5 |
| `GET` | `/account` | Get account information |
| `GET` | `/positions` | Get all open positions |
| `GET` | `/position/<symbol>` | Get position for specific symbol |
| `GET` | `/symbol/<symbol>` | Get symbol information |
| `GET` | `/market-data?symbol=X&timeframe=H1&limit=100` | Get historical market data |
| `GET` | `/price/<symbol>` | Get current price |
| `POST` | `/trade` | Place new trade |
| `POST` | `/close` | Close position |
| `POST` | `/modify` | Modify order (SL/TP) |

---

## Common Trading Symbols

### Forex
- `EURUSD` - Euro vs US Dollar
- `GBPUSD` - British Pound vs US Dollar
- `USDJPY` - US Dollar vs Japanese Yen
- `USDCOP` - US Dollar vs Colombian Peso

### Commodities
- `XAUUSD` - Gold vs US Dollar
- `XAGUSD` - Silver vs US Dollar

### Futures (if supported by broker)
- `NQ` - Nasdaq 100 Futures
- `ES` - S&P 500 Futures

> 💡 **Tip:** Check your broker's available symbols in MT5 Market Watch

---

## Troubleshooting

### MT5 Terminal Not Detected
**Error:** `MT5 Terminal not detected!`

**Solution:**
1. Open MetaTrader 5 application
2. Ensure it's logged into your account
3. Look for `terminal64.exe` in Task Manager
4. Restart the script

### Connection Failed
**Error:** `"success": false, "error": "MT5 initialization failed"`

**Solution:**
1. Restart MT5 terminal
2. Log out and log back in
3. Check if demo account is active
4. Restart the REST server

### Invalid Symbol
**Error:** `"error": "symbol not found"`

**Solution:**
1. Open MT5 Market Watch (Ctrl+M)
2. Right-click → "Show All"
3. Find the correct symbol name
4. Use exact symbol name in API call

---

## Next Steps

### Integration Options
1. **Python Client:** Use `requests` library to call the API
2. **JavaScript/Node.js:** Use `axios` or `fetch`
3. **Postman:** Import endpoints for manual testing
4. **Trading Bot:** Connect your algorithm to the REST API

### Example Python Client
```python
import requests

BASE_URL = "http://localhost:8080"

# Connect to MT5
response = requests.post(f"{BASE_URL}/connect")
print(response.json())

# Get account info
account = requests.get(f"{BASE_URL}/account")
print(f"Balance: ${account.json()['data']['balance']}")

# Place trade
trade_data = {
    "symbol": "EURUSD",
    "action": "buy",
    "volume": 0.01,
    "stop_loss": 1.0800,
    "take_profit": 1.0900
}
result = requests.post(f"{BASE_URL}/trade", json=trade_data)
print(result.json())
```

---

## Important Notes ⚠️

1. **Demo Account Only:** Use demo/paper trading accounts for testing
2. **Windows Only:** MT5 Python connector only works on Windows
3. **Terminal Required:** MT5 terminal must be running before starting the server
4. **Port 8080:** Default port - change in `START_MT5_PAPER_TRADING.ps1` if needed
5. **Risk Management:** Always set stop loss and take profit levels

---

## Support

For issues or questions:
- Check [mt5_rest.py](mt5_rest.py) source code
- Review [pages/api/mt5_bridge.py](pages/api/mt5_bridge.py) for MT5 bridge details
- See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for deployment info

---

**Happy Paper Trading! 📈**
