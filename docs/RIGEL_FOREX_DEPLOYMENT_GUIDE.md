# Rigel Multi-Pair Forex Trading System
## Complete Deployment Guide

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Deployment Options](#deployment-options)
6. [ML Integration](#ml-integration)
7. [Risk Management](#risk-management)
8. [Monitoring & Logging](#monitoring--logging)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 System Overview

**Rigel** is a production-ready multi-pair forex trading system implementing mean reversion strategies with advanced risk management. It supports deployment on:

- ✅ **Alpaca Markets** (Python) - Paper/Live trading
- ✅ **MetaTrader 5** (MQL5 EA) - Any MT5 broker
- 🔜 **Future**: MT4 compatibility

### Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Pair Orchestration** | Trade 7 major forex pairs simultaneously |
| **Risk Discipline** | 1% risk per trade, max 3 positions |
| **Liquidity Management** | 25% cash reserve minimum |
| **ML Hooks** | Integrate ML predictions for enhanced signals |
| **Session-Based Trading** | Trade during active market hours (9am-4pm EST) |
| **Mean Reversion Strategy** | EMA crossover + RSI + Bollinger Bands |

### Trading Pairs

- EUR/USD - Euro / US Dollar
- GBP/USD - British Pound / US Dollar
- USD/JPY - US Dollar / Japanese Yen
- USD/CHF - US Dollar / Swiss Franc
- AUD/USD - Australian Dollar / US Dollar
- NZD/USD - New Zealand Dollar / US Dollar
- USD/CAD - US Dollar / Canadian Dollar

---

## 🏗️ Architecture

### Python Bot (Alpaca)

```
rigel_forex_bot.py
│
├── Configuration (ForexConfig)
│   ├── API credentials
│   ├── Trading pairs
│   ├── Risk parameters
│   └── ML settings
│
├── Technical Indicators
│   ├── EMA Fast/Slow
│   ├── RSI
│   ├── Bollinger Bands
│   └── ATR
│
├── ML Predictor (Pluggable)
│   ├── Model loading
│   ├── Feature preparation
│   └── Prediction engine
│
├── Risk Manager
│   ├── Position sizing
│   ├── Liquidity checks
│   └── Daily loss limits
│
├── Strategy Engine
│   ├── Signal generation
│   ├── Mean reversion logic
│   └── Confidence scoring
│
└── Trading Bot
    ├── API connection
    ├── Market data fetching
    ├── Order execution
    └── Main loop
```

### MT5 EA

```
RigelForexEA.mq5
│
├── Input Parameters
│   ├── Trading pairs toggles
│   ├── Strategy settings
│   └── Risk controls
│
├── Indicator Initialization
│   ├── EMA handles
│   ├── RSI handles
│   └── Bollinger Bands handles
│
├── OnTick() Handler
│   ├── Session check
│   ├── Risk check
│   └── Signal scanning
│
└── Trade Execution
    ├── Position sizing
    ├── SL/TP calculation
    └── Order placement
```

---

## 📦 Installation

### Option 1: Alpaca Python Bot

#### Prerequisites

- Python 3.8+
- Alpaca account (paper or live)
- $1,000+ account balance recommended

#### Steps

```bash
# 1. Clone repository
cd BentleyBudgetBot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install additional forex requirements
pip install alpaca-trade-api pandas numpy

# 4. Create logs directory
mkdir -p logs

# 5. Configure environment variables
cp .env.example .env
# Edit .env with your credentials (see Configuration section)
```

### Option 2: MT5 Expert Advisor

#### Prerequisites

- MetaTrader 5 platform
- Active forex broker account
- MT5 account with forex trading enabled

#### Steps

```bash
# 1. Copy EA file to MT5
# Windows:
copy mt5\RigelForexEA.mq5 "%APPDATA%\MetaQuotes\Terminal\<ID>\MQL5\Experts\"

# 2. Open MT5
# 3. Navigate to Navigator -> Expert Advisors
# 4. Find "RigelForexEA"
# 5. Drag onto any chart
# 6. Configure parameters (see Configuration section)
# 7. Enable AutoTrading
```

---

## ⚙️ Configuration

### Python Bot (.env file)

```bash
# Alpaca API Credentials
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_SECRET_KEY=your_alpaca_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # or https://api.alpaca.markets for live

# Trading Configuration
DRY_RUN=true                    # Set to false for live trading
ENABLE_TRADING=false            # Set to true to enable order execution

# ML Integration (Optional)
ENABLE_ML=false                 # Enable ML predictions
ML_MODEL_PATH=models/rigel_forex_model.pkl

# Advanced (Optional)
RISK_PER_TRADE=0.01            # 1% risk per trade
MAX_OPEN_POSITIONS=3           # Max simultaneous positions
LIQUIDITY_BUFFER=0.25          # 25% cash reserve
```

### MT5 EA Parameters

Configure these when attaching the EA to a chart:

#### Trading Pairs
- `Trade_EURUSD` - true/false
- `Trade_GBPUSD` - true/false
- `Trade_USDJPY` - true/false
- (etc. for all 7 pairs)

#### Trading Session
- `SessionStartHour` - 9 (EST)
- `SessionEndHour` - 16 (EST)

#### Strategy
- `LongStrategy` - true (enable long positions)
- `ShortStrategy` - true (enable short positions)

#### Indicators
- `EMA_Fast` - 20
- `EMA_Slow` - 50
- `RSI_Period` - 14
- `RSI_Oversold` - 45
- `RSI_Overbought` - 55
- `BB_Period` - 20
- `BB_Deviation` - 2.0

#### Risk Management
- `RiskPerTrade` - 1.0 (%)
- `MaxOpenPositions` - 3
- `LiquidityBuffer` - 25.0 (%)
- `MaxDailyLoss` - 5.0 (%)

#### Stop Loss / Take Profit
- `StopLoss_Long` - 50 pips
- `TakeProfit_Long` - 100 pips
- `StopLoss_Short` - 30 pips
- `TakeProfit_Short` - 60 pips

#### Safety
- `DryRun` - true (recommended for testing)
- `EnableTrading` - false (change to true when ready)
- `MagicNumber` - 123456 (unique identifier)

---

## 🚀 Deployment Options

### 1️⃣ Local Development (Recommended for Testing)

#### Python
```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Run bot
python scripts/rigel_forex_bot.py
```

#### MT5
1. Open MT5 MetaEditor
2. Compile `RigelForexEA.mq5`
3. Attach to chart
4. Enable DryRun mode
5. Monitor Experts tab for logs

### 2️⃣ Production Deployment (Python)

#### Cloud Options

**Option A: AWS EC2**
```bash
# 1. Launch EC2 instance (t2.micro for testing, t2.small for production)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@ec2-instance

# 3. Install Python & dependencies
sudo apt update
sudo apt install python3-pip
pip3 install -r requirements.txt

# 4. Create systemd service
sudo nano /etc/systemd/system/rigel-forex.service
```

Service file:
```ini
[Unit]
Description=Rigel Forex Trading Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/BentleyBudgetBot
Environment="PATH=/home/ubuntu/.local/bin"
ExecStart=/usr/bin/python3 /home/ubuntu/BentleyBudgetBot/scripts/rigel_forex_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 5. Enable and start service
sudo systemctl enable rigel-forex
sudo systemctl start rigel-forex

# 6. Check status
sudo systemctl status rigel-forex

# 7. View logs
journalctl -u rigel-forex -f
```

**Option B: Docker**
```bash
# 1. Create Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ ./scripts/
COPY logs/ ./logs/

CMD ["python", "scripts/rigel_forex_bot.py"]

# 2. Build image
docker build -t rigel-forex:latest .

# 3. Run container
docker run -d \
  --name rigel-forex \
  --restart unless-stopped \
  -e ALPACA_API_KEY=your_key \
  -e ALPACA_SECRET_KEY=your_secret \
  -e DRY_RUN=false \
  -e ENABLE_TRADING=true \
  -v $(pwd)/logs:/app/logs \
  rigel-forex:latest

# 4. View logs
docker logs -f rigel-forex
```

**Option C: Railway.app / Heroku**
```bash
# 1. Create Procfile
worker: python scripts/rigel_forex_bot.py

# 2. Push to Railway/Heroku
git push railway main  # or git push heroku main

# 3. Set environment variables in dashboard
```

### 3️⃣ Production Deployment (MT5)

#### VPS Hosting (Recommended)

1. **Get Forex VPS**
   - Recommended: ForexVPS.net, VPSForexTrader, or broker-provided VPS
   - Ensure low latency to broker servers

2. **Install MT5 on VPS**
   - Download MT5 from your broker
   - Install and login to account

3. **Upload EA**
   - Copy `RigelForexEA.mq5` to VPS
   - Compile in MetaEditor
   - Attach to chart

4. **Configure Security**
   - Enable only necessary pairs
   - Set appropriate risk limits
   - Enable stop loss always
   - Use DryRun mode for 1 week first

5. **Monitor**
   - Check VPS daily
   - Review trades in MT5 History
   - Monitor account balance

---

## 🤖 ML Integration

### Overview

The Rigel system includes hooks for machine learning predictions. You can plug in your own ML model to enhance trading signals.

### Implementation Path

#### Step 1: Train ML Model (Python)

```python
# train_model.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

# Load historical data
data = pd.read_csv('historical_forex_data.csv')

# Feature engineering
features = ['ema_fast', 'ema_slow', 'rsi', 'bb_upper', 'bb_lower', 'atr']
X = data[features]
y = data['signal']  # 1=buy, -1=sell, 0=hold

# Train model
model = RandomForestClassifier(n_estimators=100)
model.fit(X, y)

# Save model
joblib.dump(model, 'models/rigel_forex_model.pkl')
```

#### Step 2: Update MLPredictor Class

```python
# In rigel_forex_bot.py, update MLPredictor._load_model()
def _load_model(self):
    import joblib
    self.model = joblib.load(self.model_path)
    logger.info(f"ML model loaded from {self.model_path}")

# Update MLPredictor.predict()
def predict(self, symbol: str, indicators: Dict) -> MLPrediction:
    if not self.enabled or not self.model:
        return MLPrediction.NEUTRAL
    
    # Prepare features
    features = pd.DataFrame([{
        'ema_fast': indicators['ema_fast'],
        'ema_slow': indicators['ema_slow'],
        'rsi': indicators['rsi'],
        'bb_upper': indicators['bb_upper'],
        'bb_lower': indicators['bb_lower'],
    }])
    
    # Predict
    prediction = self.model.predict(features)[0]
    
    # Map to MLPrediction enum
    if prediction == 1:
        return MLPrediction.MEAN_REVERT
    else:
        return MLPrediction.NEUTRAL
```

#### Step 3: Enable ML in Configuration

```bash
ENABLE_ML=true
ML_MODEL_PATH=models/rigel_forex_model.pkl
```

### MT5 ML Integration

For MT5, you have two options:

**Option A: Python API Server**
```python
# ml_api.py
from flask import Flask, request, jsonify
import joblib

app = Flask(__name__)
model = joblib.load('models/rigel_forex_model.pkl')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    features = [[
        data['ema_fast'],
        data['ema_slow'],
        data['rsi'],
        data['bb_upper'],
        data['bb_lower']
    ]]
    prediction = model.predict(features)[0]
    confidence = model.predict_proba(features).max()
    
    return jsonify({
        'prediction': int(prediction),
        'confidence': float(confidence)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Then in MT5 EA:
```cpp
// Use WebRequest to call Python API
// See RigelForexEA.mq5 bottom for placeholder code
```

**Option B: ONNX Model in MT5**
- Export your model to ONNX format
- Load ONNX model in MT5 using built-in ONNX functions
- Run predictions directly in EA

---

## 🛡️ Risk Management

### Position Sizing Formula

```
Risk Amount = Account Equity × Risk Per Trade (1%)
Position Size = Risk Amount ÷ (Stop Loss Pips × Pip Value)
```

Example:
- Account: $10,000
- Risk per trade: 1% = $100
- Stop loss: 50 pips
- Pip value: $10/pip (standard lot)
- Position size: $100 ÷ (50 × $10) = 0.2 lots

### Liquidity Controls

The system maintains a **25% cash reserve**:

```
Available for Trading = Cash - (Portfolio Value × 25%)
```

This ensures:
- Prevent over-leveraging
- Allow for drawdowns
- Maintain margin requirements

### Daily Loss Limit

Trading stops if:
```
Daily Loss > 5% of starting balance
```

Automatically resets at midnight.

### Maximum Positions

Limited to **3 simultaneous positions** to:
- Diversify risk
- Prevent correlation exposure
- Manage cognitive load

---

## 📊 Monitoring & Logging

### Python Bot Logs

Logs are written to:
```
logs/rigel_forex_bot.log
```

Log levels:
- **INFO**: Trade execution, signals, session events
- **WARNING**: API errors, missing data
- **ERROR**: Critical failures, execution errors

Example log:
```
2026-02-18 14:23:15 - INFO - Signal generated: BUY EUR/USD @ $1.08450 (Confidence: 78.5%)
2026-02-18 14:23:16 - INFO - EXECUTING TRADE: BUY EUR/USD
2026-02-18 14:23:16 - INFO -   Position Size: 10000 units
2026-02-18 14:23:16 - INFO -   Stop Loss: $1.08000 (50 pips)
2026-02-18 14:23:16 - INFO -   Take Profit: $1.09450 (100 pips)
2026-02-18 14:23:17 - INFO - ✓ Order placed: 12345678
```

### MT5 EA Logs

Logs appear in:
- **Experts Tab**: Real-time events
- **Journal Tab**: System events

### Recommended Monitoring Stack

```yaml
# docker-compose.yml for monitoring
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana

# Then expose metrics from rigel_forex_bot.py
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "Missing Alpaca API credentials"

**Problem**: Environment variables not loaded

**Solution**:
```bash
# Check .env file exists
ls -la .env

# Load manually
export $(cat .env | xargs)

# Or use python-dotenv
pip install python-dotenv
```

#### 2. "Insufficient data for indicators"

**Problem**: Not enough historical data fetched

**Solution**:
- Increase `LOOKBACK_DAYS` in config
- Check symbol is available on Alpaca
- Verify market is open

#### 3. MT5 EA not placing orders

**Problem**: Multiple possible causes

**Solutions**:
- ✅ Check `EnableTrading` is set to `true`
- ✅ Verify `DryRun` is set to `false`
- ✅ Enable AutoTrading in MT5 (toolbar button)
- ✅ Check account has sufficient margin
- ✅ Verify broker allows EA trading
- ✅ Check symbol is available on account

#### 4. High CPU usage

**Problem**: Too frequent scanning

**Solution**:
- Increase `interval_seconds` in `bot.run()`
- Reduce number of trading pairs
- Use longer timeframes

#### 5. ML model not loading

**Problem**: File path or dependencies

**Solution**:
```bash
# Create models directory
mkdir -p models

# Install ML dependencies
pip install scikit-learn joblib

# Check model exists
ls -la models/rigel_forex_model.pkl

# Test load manually
python -c "import joblib; joblib.load('models/rigel_forex_model.pkl')"
```

---

## 📈 Performance Testing

### Backtest (Recommended)

Before live trading, backtest the strategy:

```python
# Use backtrader or similar
import backtrader as bt

# Create backtest
# TODO: Implement backtest harness
```

For MT5:
- Use Strategy Tester in MT5
- Test on historical data (min 1 year)
- Optimize parameters
- Verify drawdown acceptable

### Paper Trading

Run in paper mode for at least **1 week**:

```bash
# Python
DRY_RUN=false
ENABLE_TRADING=true
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# MT5
DryRun = false
EnableTrading = true
# Use demo account
```

Monitor:
- Win rate
- Average profit/loss
- Maximum drawdown
- Sharpe ratio

---

## 🔐 Security Best Practices

1. **Never commit API keys**
   ```bash
   # Add to .gitignore
   .env
   *.key
   ```

2. **Use environment variables**
   - Avoid hardcoding credentials
   - Use secret management (AWS Secrets Manager, etc.)

3. **Enable IP whitelisting**
   - Alpaca supports IP restrictions
   - Limit API access to your VPS IP

4. **Use read-only keys for monitoring**
   - Separate keys for trading vs monitoring

5. **Enable 2FA**
   - Always enable 2FA on broker accounts

---

## 📚 Additional Resources

- [Alpaca API Documentation](https://alpaca.markets/docs/)
- [MQL5 Reference](https://www.mql5.com/en/docs)
- [Mean Reversion Trading](https://www.investopedia.com/terms/m/meanreversion.asp)
- [Risk Management Guide](https://www.babypips.com/learn/forex/risk-management)

---

## 🆘 Support

For issues or questions:
1. Check Issues tab on GitHub
2. Review logs carefully
3. Test in DRY_RUN mode first
4. Contact: [your-email@example.com]

---

## 📝 License

This software is provided for educational purposes. Use at your own risk. Trading forex carries significant risk of loss. Past performance does not guarantee future results.

**MIT License** - See LICENSE file for details.

---

**Last Updated**: February 18, 2026
**Version**: 1.0.0
