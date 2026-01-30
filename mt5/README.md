# MT5 Bot Development - Quick Start

## ⚡ 5-Minute Setup

### 1. **Install Prerequisites**
```bash
# Download MT5 from MetaTrader website
# https://www.metatrader5.com/

# Install Python 3.9+
# https://www.python.org/

# Clone BentleyBot repo
git clone https://github.com/winstonwilliamsiii/BBBot
cd BBBot/mt5
```

### 2. **Open in VS Code**
```bash
code .
```

### 3. **Compile in MT5**
- Open MetaTerminal → Tools → MetaEditor
- File → Open → Select `experts/BentleyBot_GBP_JPY_EA.mq5`
- Press F5 to compile
- Check for errors in compiler output

### 4. **Test in Demo**
- Launch MT5 Terminal
- Select Demo Account
- Charts → Right-click → Expert Advisors → Select EA
- Drag EA to GBPJPY H1 chart
- Allow AutoTrading
- Monitor trade execution

## 📁 File Structure

```
mt5/
├── experts/                    # EAs (Compiled & Source)
│   ├── BentleyBot_GBP_JPY_EA.mq5
│   └── BentleyBot_XAU_USD_EA.mq5
├── libraries/                  # Shared code
│   └── BentleyBot.mqh
├── indicators/                 # Custom indicators
│   └── CustomIndicators.mqh
├── tests/                      # Backtest sets
│   └── BACKTEST_TEMPLATE.txt
├── config/                     # Configuration
│   ├── trading_config.json
│   └── trading_symbols.conf
├── docs/                       # Documentation
│   ├── SETUP.md
│   ├── ARCHITECTURE.md
│   └── API_INTEGRATION.md
└── README.md                   # This file
```

## 🔧 Configuration

### Trading Hours (UTC)
- **GBP/JPY**: 12:00 - 16:00 (London-New York overlap)
- **XAU/USD**: 08:00 - 20:00 (Extended hours)

### Risk Settings
- **Risk per Trade**: 2%
- **Max Concurrent Trades**: 3
- **Min Risk/Reward**: 1.5:1
- **Max Daily Loss**: 5%

### Indicators
- **GBP/JPY**: EMA(20), EMA(50), RSI(14)
- **XAU/USD**: ATR(14), Bollinger Bands(20), EMA(50)

## 📊 EA Details

### BentleyBot_GBP_JPY_EA
**Strategy**: EMA Crossover + RSI Confirmation
- **Entry**: EMA(20) > EMA(50) + RSI confirmation
- **Exit**: Take Profit +100 pips / Stop Loss -50 pips
- **Hours**: 12:00-16:00 UTC (London-NY overlap)

### BentleyBot_XAU_USD_EA
**Strategy**: Volatility-based Mean Reversion
- **Entry**: Price at Bollinger Bands + ATR volatility
- **Exit**: Dynamic stops based on ATR
- **Hours**: 08:00-20:00 UTC (Extended coverage)

## 🚀 Development Workflow

```
┌──────────────┐
│ Edit in Code │ ← VS Code with MQL5 syntax
└──────┬───────┘
       ▼
┌──────────────┐
│  Compile     │ ← MetaEditor (MT5)
└──────┬───────┘
       ▼
┌──────────────┐
│  Backtest    │ ← Strategy Tester
└──────┬───────┘
       ▼
┌──────────────┐
│  Demo Test   │ ← Live demo account
└──────┬───────┘
       ▼
┌──────────────┐
│  Push to Git │ ← GitHub
└──────┬───────┘
       ▼
┌──────────────┐
│  Production  │ ← Small live account
└──────────────┘
```

## 🧪 Testing & Validation

### Before Going Live
1. ✅ Compile without errors
2. ✅ Backtest 6+ months of data
3. ✅ Demo trade for 1-2 weeks
4. ✅ Review logs for issues
5. ✅ Verify SL/TP execution
6. ✅ Check volatility handling

### Performance Targets
- **Win Rate**: > 55%
- **Profit Factor**: > 1.5
- **Max Drawdown**: < 20%
- **Sharpe Ratio**: > 1.0

## 🔌 Integration

### Python Bridge (Optional)
Sync trades with Alpaca or other brokers:
```python
python scripts/mt5_alpaca_bridge.py
```

### Discord Notifications
Get trade alerts in Discord:
```python
python scripts/discord_notifier.py
```

## 📚 Documentation

- [Setup & Installation](docs/SETUP.md)
- [System Architecture](docs/ARCHITECTURE.md)
- [API Integration Guide](docs/API_INTEGRATION.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## 🐛 Common Issues

### EA Not Trading
- Check time filter (market hours)
- Verify position limit not reached
- Review indicator values in terminal

### Compilation Errors
- Ensure all `#include` files exist
- Check MQL5 syntax
- Review compiler output log

### Trades Not Syncing to Alpaca
- Verify Python bridge running
- Check file permissions
- Review API credentials

## 📞 Support

- Check logs in MT5 Terminal (View → Experts)
- Review documentation in `docs/` folder
- Test in demo account first

## 🔐 Risk Warning

⚠️ **This EA is for educational purposes only. Always test thoroughly in demo before using real money.**

- Start with small positions
- Monitor regularly
- Use stop losses
- Never risk more than 2% per trade

## 📝 License

See [LICENSE](../LICENSE) file

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Test thoroughly
4. Submit pull request
5. Follow code standards

---

**Ready to trade?** Start with [SETUP.md](docs/SETUP.md) for step-by-step instructions.
