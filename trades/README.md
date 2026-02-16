# Trades Documentation

**Last Updated**: February 15, 2026  
**Purpose**: Centralized documentation for all trade management, monitoring, and reporting

---

## 📁 Folder Contents

This folder contains comprehensive documentation for:
- Trade execution records and logs
- Discord notification integration
- MySQL database tracking
- Trading strategies and parameters
- Order management procedures

---

## 📊 Current Trading Activity

### Active Trades
- **TURB**: Pending buy order (2,000 shares @ $0.6881)
- **SUPX**: Existing position with protection orders

### Documentation Files
1. [TRADE_LOGGING_SETUP.md](TRADE_LOGGING_SETUP.md) - MySQL database integration
2. [DISCORD_NOTIFICATIONS.md](DISCORD_NOTIFICATIONS.md) - Discord webhook setup and usage
3. [TRADING_PARAMETERS.md](TRADING_PARAMETERS.md) - Risk management and order parameters
4. [ORDER_EXECUTION_LOG.md](ORDER_EXECUTION_LOG.md) - Manual log template for trades

---

## 🔧 System Integration Status

### ✅ Implemented Features
- Alpaca API integration ([alpaca_connector.py](../frontend/components/alpaca_connector.py))
- Bracket order automation (stop loss + take profit)
- Paper trading support
- Real-time position monitoring

### ⚠️ Pending Integration
- Discord notifications (code exists but not integrated into production scripts)
- MySQL trade logging (table exists but not actively used)
- Automated trade recording

---

## 🚀 Quick Start

### Check Trade Status
```bash
# Check TURB position and orders
python check_turb_status_direct.py

# Check all positions
python display_portfolio.py
```

### Place Protected Orders
```bash
# TURB and SUPX order placement (with bracket protection)
python place_turb_supx_orders.py
```

### Cancel Orders
```bash
# Cancel specific TURB order
python cancel_duplicate_turb.py

# Cancel SPY orders
python cancel_spy_order.py
```

---

## 📚 Related Documentation

- [TURB_ACTION_GUIDE.md](../TURB_ACTION_GUIDE.md) - TURB trade management guide
- [TURB_SUPX_ORDER_SUMMARY.md](../TURB_SUPX_ORDER_SUMMARY.md) - Order placement summary
- [BRACKET_ORDER_DEPLOYMENT.md](../BRACKET_ORDER_DEPLOYMENT.md) - Bracket order system details

---

## 🔗 External Resources

- **Alpaca Documentation**: https://alpaca.markets/docs/
- **Trading Dashboard**: https://app.alpaca.markets/ (Paper Trading)
- **Discord Integration**: See [DISCORD_NOTIFICATIONS.md](DISCORD_NOTIFICATIONS.md)

---

## 📝 Notes

All trades use automatic bracket orders with:
- **Stop Loss**: 10% below entry
- **Take Profit**: 20% above entry
- **Risk/Reward Ratio**: 2:1
- **Time in Force**: GTC (Good-Til-Cancelled)

For questions or issues, refer to the specific documentation files in this folder.
