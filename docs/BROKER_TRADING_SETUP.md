# Broker Trading Integration Setup

## 📋 Overview

BentleyBot now supports automated trading across **3 broker platforms**:
- **Webull** → Equities & ETFs
- **Interactive Brokers (IBKR)** → Forex, Futures, Commodities
- **Binance** → Cryptocurrency

## 🚀 Quick Start

### 1. Install Broker APIs

```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install all broker APIs
pip install webull ibapi python-binance
```

### 2. Configure API Credentials

Copy the example file and add your credentials:
```bash
cp .env.brokers.example .env.brokers
```

Edit `.env.brokers` with your credentials:
```bash
# Webull
WEBULL_USERNAME=your_email@example.com
WEBULL_PASSWORD=your_password
WEBULL_DEVICE_ID=your_device_id

# Interactive Brokers
IBKR_HOST=127.0.0.1
IBKR_PORT=7497  # 7497 for paper, 7496 for live
IBKR_CLIENT_ID=1

# Binance
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_secret
BINANCE_TESTNET=true  # Set to false for live trading
```

Load environment variables:
```bash
# PowerShell
Get-Content .env.brokers | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}
```

### 3. Test Broker Connections

```bash
python bbbot1_pipeline/broker_api.py
```

Expected output:
```
🧪 Testing Broker API Integrations
======================================================================

1️⃣  Testing Webull (Equities/ETFs)...
✅ Webull connected successfully
Result: {'broker': 'webull', 'symbol': 'AAPL', 'side': 'BUY', ...}

2️⃣  Testing IBKR (Forex/Futures/Commodities)...
✅ IBKR connected successfully to 127.0.0.1:7497
Result: {'broker': 'ibkr', 'symbol': 'ES', 'side': 'BUY', ...}

3️⃣  Testing Binance (Crypto)...
✅ Binance TESTNET connected successfully
Result: {'broker': 'binance', 'symbol': 'BTCUSDT', 'side': 'BUY', ...}
```

### 4. Launch Trading Dashboard

```bash
streamlit run streamlit_app.py
```

Navigate to: **💼 Broker Trading** page

---

## 📚 Broker-Specific Setup

### Webull Setup

1. **Install Package**
   ```bash
   pip install webull
   ```

2. **Get Device ID**
   - Login to Webull mobile app
   - Go to Settings → Security
   - Find your Device ID

3. **Test Connection**
   ```python
   from bbbot1_pipeline.broker_api import WebullClient
   
   client = WebullClient()
   client.connect()
   positions = client.get_positions()
   print(positions)
   ```

### Interactive Brokers Setup

1. **Download TWS or IB Gateway**
   - Download from: https://www.interactivebrokers.com/en/trading/tws.php
   - Install TWS (Trader Workstation) or IB Gateway

2. **Enable API**
   - Open TWS/Gateway
   - Go to: Configure → Settings → API → Settings
   - Enable: "Enable ActiveX and Socket Clients"
   - Set Socket Port: **7497** (paper) or **7496** (live)
   - Add Trusted IP: 127.0.0.1

3. **Install API Package**
   ```bash
   pip install ibapi
   ```

4. **Test Connection**
   ```python
   from bbbot1_pipeline.broker_api import IBKRClient
   
   client = IBKRClient()
   client.connect()
   # Place test order
   result = client.place_order('ES', 'BUY', 1, sec_type='FUT', exchange='CME')
   print(result)
   ```

### Binance Setup

1. **Create API Key**
   - Login to Binance.com
   - Account → API Management
   - Create API Key
   - Enable: "Enable Spot & Margin Trading"
   - Save API Key and Secret

2. **Use Testnet (Recommended)**
   - Testnet: https://testnet.binance.vision/
   - Create testnet account
   - Get testnet API keys (free test BTC/ETH/USDT)

3. **Install Package**
   ```bash
   pip install python-binance
   ```

4. **Test Connection**
   ```python
   from bbbot1_pipeline.broker_api import BinanceClient
   
   client = BinanceClient()
   client.connect()
   balances = client.get_positions()
   print(balances)
   ```

---

## 💼 Usage Examples

### Execute Single Trade

```python
from bbbot1_pipeline.broker_api import execute_trade

# Buy 100 shares of AAPL on Webull
result = execute_trade('webull', 'AAPL', 'BUY', 100)

# Buy 1 ES futures contract on IBKR
result = execute_trade('ibkr', 'ES', 'BUY', 1, sec_type='FUT', exchange='CME')

# Buy 0.01 BTC on Binance
result = execute_trade('binance', 'BTCUSDT', 'BUY', 0.01)
```

### Get All Positions

```python
from bbbot1_pipeline.broker_api import get_all_positions

positions = get_all_positions()

print(f"Webull positions: {len(positions['webull'])}")
print(f"IBKR positions: {len(positions['ibkr'])}")
print(f"Binance balances: {len(positions['binance'])}")
```

### Automated Trading with Airflow

The `bentleybot_trading_dag.py` DAG automatically:
1. Fetches market data
2. Calculates indicators (RSI, MACD)
3. Generates BUY/SELL signals
4. Executes trades via broker APIs
5. Logs to MLFlow

Enable the DAG:
```bash
# Access Airflow UI
http://localhost:8080

# Enable: bentleybot_dag
# Schedule: Hourly
```

---

## 🎯 Trading Signal Routing

The system automatically routes trades to the appropriate broker:

| Asset Class | Broker | Example Symbols |
|------------|--------|----------------|
| **Equities** | Webull | AAPL, MSFT, GOOGL, TSLA |
| **ETFs** | Webull | SPY, QQQ, IWM, DIA |
| **Forex** | IBKR | EUR.USD, GBP.USD, USD.JPY |
| **Futures** | IBKR | ES (S&P), NQ (Nasdaq), GC (Gold) |
| **Commodities** | IBKR | CL (Oil), NG (Natural Gas), ZC (Corn) |
| **Crypto** | Binance | BTCUSDT, ETHUSDT, BNBUSDT |

### Routing Logic

```python
if symbol.endswith("USDT"):
    broker = "binance"  # Crypto
elif "." in symbol or len(symbol) <= 3:
    broker = "ibkr"  # Forex or Futures
else:
    broker = "webull"  # Equities/ETFs
```

---

## 🔒 Security Best Practices

1. **Use Paper Trading First**
   - Webull: Enable paper trading account
   - IBKR: Use TWS Paper Trading (port 7497)
   - Binance: Set `BINANCE_TESTNET=true`

2. **Protect API Keys**
   - Never commit `.env.brokers` to git
   - Use `.gitignore` to exclude sensitive files
   - Rotate API keys regularly

3. **Set Trading Limits**
   - Configure max position sizes
   - Set daily loss limits
   - Use stop-loss orders

4. **Monitor Execution**
   - Check MLFlow logs for trade results
   - Review broker dashboards daily
   - Set up alerts for failed trades

---

## 📊 Monitoring & Logging

All trades are logged to MLFlow with:
- Broker used
- Symbol, side, quantity
- Order ID and status
- Timestamp
- Error messages (if any)

View trades in MLFlow:
```bash
# Access MLFlow UI
http://localhost:5000

# Experiment: bentleybot_trading_signals
```

---

## 🐛 Troubleshooting

### Webull Connection Failed
- **Error**: "Login failed"
- **Solution**: Check username/password, verify device ID

### IBKR Connection Timeout
- **Error**: "Connection refused"
- **Solution**: 
  1. Ensure TWS/Gateway is running
  2. Check API is enabled (Configure → Settings → API)
  3. Verify port 7497 is correct
  4. Add 127.0.0.1 to Trusted IPs

### Binance API Error
- **Error**: "Invalid API key"
- **Solution**: 
  1. Verify API key and secret
  2. Check API permissions (enable spot trading)
  3. For testnet, use testnet keys from testnet.binance.vision

### Import Error
- **Error**: "ModuleNotFoundError: No module named 'webull'"
- **Solution**: Install missing package
  ```bash
  pip install webull ibapi python-binance
  ```

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `bbbot1_pipeline/broker_api.py` | Unified broker API integration |
| `pages/03_💼_Broker_Trading.py` | Streamlit trading dashboard |
| `.env.brokers.example` | Example credentials file |
| `docs/BROKER_TRADING_SETUP.md` | This documentation |
| `airflow/dags/bentleybot_trading_dag.py` | Automated trading DAG (updated) |

---

## 🎓 Next Steps

1. ✅ **Install broker APIs** → `pip install webull ibapi python-binance`
2. ✅ **Configure credentials** → Edit `.env.brokers`
3. ✅ **Test connections** → Run `broker_api.py`
4. ✅ **Launch dashboard** → Open Streamlit trading page
5. ⏭️ **Enable paper trading** → Test with fake money first
6. ⏭️ **Enable Airflow DAG** → Automated trading hourly
7. ⏭️ **Monitor MLFlow** → Track all trades

---

**⚠️ Important**: Always start with **paper trading** or **testnet** before using real money!

For issues or questions, check logs in:
- Airflow: `logs/bentleybot_dag/`
- MLFlow: `mlruns/bentleybot_trading_signals/`
