# 🚀 Rigel Forex Bot - Quick Start Guide

## ⚡ Get Started in 5 Minutes

### Prerequisites
- ✅ Python 3.8+
- ✅ Alpaca account (get free paper account at [alpaca.markets](https://alpaca.markets))
- ✅ 10 minutes of your time

---

## 📦 Step 1: Install Dependencies

```bash
# Navigate to project directory
cd BentleyBudgetBot

# Install required packages
pip install alpaca-trade-api pandas numpy python-dotenv

# Create logs directory
mkdir -p logs
```

---

## 🔑 Step 2: Configure API Keys

Create a `.env` file in the project root:

```bash
# Create .env file
touch .env

# Edit with your favorite editor
nano .env
```

Add your Alpaca credentials:

```bash
# Alpaca API Configuration
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Safety Settings (IMPORTANT!)
DRY_RUN=true
ENABLE_TRADING=false

# Optional: ML Integration
ENABLE_ML=false
```

**⚠️ IMPORTANT**: Start with `DRY_RUN=true` and `ENABLE_TRADING=false` for safety!

---

## 🎮 Step 3: Run the Bot

### Test Run (Dry Run Mode)

```bash
# Run bot in dry run mode (no real orders)
python scripts/rigel_forex_bot.py
```

You should see output like:

```
========================================
RIGEL FOREX BOT CONFIGURATION
========================================
Trading Pairs: 7 pairs
Session Hours: 9:00 - 16:00 EST
Risk Per Trade: 1.0%
Max Positions: 3
Liquidity Buffer: 25.0%
ML Enabled: False
Dry Run: True
Trading Enabled: False
========================================
```

### Enable Paper Trading

Once you're comfortable with the signals, enable paper trading:

```bash
# Edit .env file
nano .env

# Change these lines:
DRY_RUN=false
ENABLE_TRADING=true
```

Then run again:

```bash
python scripts/rigel_forex_bot.py
```

---

## 📊 Step 4: Monitor the Bot

### View Logs

```bash
# Real-time log monitoring
tail -f logs/rigel_forex_bot.log

# Or on Windows
Get-Content logs/rigel_forex_bot.log -Wait
```

### Check Alpaca Dashboard

1. Go to [app.alpaca.markets](https://app.alpaca.markets)
2. Login to your account
3. Navigate to Dashboard → Positions
4. See your bot's trades in real-time

---

## 🎯 Understanding the Output

### Signal Example

```
2026-02-18 14:23:15 - INFO - Signal generated: BUY EUR/USD @ $1.08450 (Confidence: 78.5%)
```

This means:
- **Action**: Buy EUR/USD
- **Price**: $1.08450
- **Confidence**: 78.5% (based on technical indicators)

### Trade Execution

```
========================================
EXECUTING TRADE: BUY EUR/USD @ $1.08450 (Confidence: 78.5%)
  Position Size: 10000 units
  Entry: $1.08450
  Stop Loss: $1.08000 (50 pips)
  Take Profit: $1.09450 (100 pips)
  Risk/Reward: 1:2.00
========================================
✓ Order placed: 12345678
```

**What this means**:
- **Position Size**: 10,000 units (0.1 standard lot)
- **Stop Loss**: Automatic exit at $1.08000 if price goes down
- **Take Profit**: Automatic exit at $1.09450 if price goes up
- **Risk/Reward**: For every $1 risked, potential to gain $2

---

## 🛡️ Safety Features

The bot includes multiple safety controls:

### 1. **Liquidity Buffer** (25%)
- Always keeps 25% of portfolio in cash
- Prevents over-leveraging

### 2. **Position Limits** (Max 3)
- Never opens more than 3 positions simultaneously
- Manages risk exposure

### 3. **Risk Per Trade** (1%)
- Only risks 1% of account per trade
- Example: $10,000 account = $100 max risk per trade

### 4. **Daily Loss Limit** (5%)
- Stops trading if daily loss exceeds 5%
- Prevents catastrophic losses

### 5. **Session-Based Trading**
- Only trades during active market hours (9am-4pm EST)
- Avoids low-liquidity periods

---

## 🔧 Customization

### Change Trading Pairs

Edit `scripts/rigel_forex_bot.py`:

```python
# Line ~88
FOREX_PAIRS = [
    "EUR/USD",  # Euro / US Dollar
    "GBP/USD",  # Keep
    # "USD/JPY",  # Comment out to disable
    # Add more pairs as needed
]
```

### Adjust Risk Settings

In `.env` or directly in code:

```python
RISK_PER_TRADE = 0.01  # 1% (change to 0.02 for 2%)
MAX_OPEN_POSITIONS = 3  # (change to 5 for more positions)
LIQUIDITY_BUFFER = 0.25  # 25% (change to 0.30 for 30%)
```

### Modify Strategy Parameters

```python
# EMA periods
EMA_FAST = 20  # Try 10, 15, 20
EMA_SLOW = 50  # Try 30, 50, 100

# RSI thresholds
RSI_OVERSOLD = 45  # Lower = more aggressive (try 30, 40, 45)
RSI_OVERBOUGHT = 55  # Higher = more aggressive (try 55, 60, 70)

# Stop loss / Take profit (in pips)
STOP_LOSS_PIPS = {"long": 50, "short": 30}
TAKE_PROFIT_PIPS = {"long": 100, "short": 60}
```

---

## 📈 Performance Tracking

### Check Account Status

```python
# Add to your bot or run separately
from alpaca_trade_api import REST

api = REST(api_key, secret_key, base_url)
account = api.get_account()

print(f"Portfolio Value: ${float(account.portfolio_value):,.2f}")
print(f"Cash: ${float(account.cash):,.2f}")
print(f"P&L: ${float(account.equity) - float(account.last_equity):,.2f}")
```

### Export Trade History

```python
# Get closed positions
orders = api.list_orders(status='closed', limit=100)

for order in orders:
    print(f"{order.symbol}: {order.side} {order.qty} @ ${order.filled_avg_price}")
```

---

## 🐛 Common Issues & Solutions

### Issue 1: "Missing Alpaca API credentials"

**Solution**: 
```bash
# Check .env file exists
ls -la .env

# Verify credentials are set
cat .env | grep ALPACA
```

### Issue 2: "Outside trading session"

**Solution**: 
- Bot only trades 9am-4pm EST
- Wait for market hours or adjust `SESSION_START_HOUR`/`SESSION_END_HOUR`

### Issue 3: Bot not placing orders

**Check**:
1. ✅ `ENABLE_TRADING=true` in .env?
2. ✅ `DRY_RUN=false` in .env?
3. ✅ During trading session (9am-4pm EST)?
4. ✅ Account has sufficient balance?
5. ✅ Liquidity ratio above 20%?

### Issue 4: High CPU usage

**Solution**:
```python
# In main() function, increase interval
bot.run(interval_seconds=600)  # Check every 10 minutes instead of 5
```

---

## 🎓 Next Steps

### 1. **Paper Trade for 1 Week**
- Monitor bot performance
- Understand signal patterns
- Verify risk management works

### 2. **Backtest Strategy**
- Use historical data
- Optimize parameters
- Calculate expected returns

### 3. **Add ML Integration**
- Train prediction model
- Implement in MLPredictor class
- Boost signal confidence

### 4. **Scale to Live Trading**
- Move from paper to live account
- Start with small capital ($1,000)
- Gradually increase as confidence grows

---

## 📚 Resources

- **Full Documentation**: [docs/RIGEL_FOREX_DEPLOYMENT_GUIDE.md](RIGEL_FOREX_DEPLOYMENT_GUIDE.md)
- **Unit Tests**: [tests/test_rigel_forex_bot.py](../tests/test_rigel_forex_bot.py)
- **MT5 EA Version**: [mt5/RigelForexEA.mq5](../mt5/RigelForexEA.mq5)
- **Alpaca Docs**: https://alpaca.markets/docs/
- **Support**: Open an issue on GitHub

---

## ⚠️ Disclaimer

This software is provided for **educational purposes only**. 

- ❌ Not financial advice
- ❌ No guarantee of profits
- ✅ Use at your own risk
- ✅ Only trade with capital you can afford to lose

**Forex trading carries significant risk of loss.**

---

## 📝 Quick Reference

### Start Bot
```bash
python scripts/rigel_forex_bot.py
```

### View Logs
```bash
tail -f logs/rigel_forex_bot.log
```

### Run Tests
```bash
pytest tests/test_rigel_forex_bot.py -v
```

### Stop Bot
```bash
Ctrl+C
```

---

**Version**: 1.0.0  
**Last Updated**: February 18, 2026  
**Maintained by**: Bentley Budget Bot Team

---

🚀 **Ready to trade? Good luck and trade safely!** 🎯
