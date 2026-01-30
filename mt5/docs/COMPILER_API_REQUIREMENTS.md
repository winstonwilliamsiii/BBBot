# MT5 Compiler & API Requirements - Complete Guide

## Executive Summary

The MT5 ecosystem requires integration between three primary components:

1. **MQL5 Compiler** (MetaEditor) - Compiles EA source to binary
2. **MT5 Terminal** - Executes compiled EAs and manages trades
3. **External APIs** - Connect to Alpaca, Discord, etc.

---

## Part 1: MT5 Compiler Setup & Requirements

### Software Requirements

| Component | Version | Purpose |
|-----------|---------|---------|
| MetaTrader 5 | Latest | Trading platform & terminal |
| MetaEditor | Latest | MQL5 compiler (bundled with MT5) |
| .NET Framework | 4.5+ | Required for some MT5 features |
| Windows | 7/8/10/11 or Server 2019+ | Operating system |

### Installation

**Option A: Standard Installation**
```bash
# Download from MetaTrader website
# https://www.metatrader5.com/en/download

# Run installer
MetaTrader5Setup.exe

# Accepts default settings for trading
# MetaEditor included automatically
```

**Option B: Silent Installation (VPS/Automation)**
```bash
# Install without UI
MetaTrader5Setup.exe /auto

# Extract portable terminal
MetaTrader5Portable.zip

# Run terminal with automation
terminal.exe /config:config.ini
```

### MetaEditor Access

**Method 1: From MT5 Terminal**
```
1. Open MT5 Terminal
2. Tools → MetaEditor
3. Or: Press Alt+F9
```

**Method 2: Standalone Launch**
```bash
# Direct execution
"C:\Program Files\MetaTrader 5\metaeditor64.exe"

# With auto-open file
metaeditor64.exe "C:\path\to\BentleyBot_GBP_JPY_EA.mq5"
```

---

## Part 2: MQL5 Compilation Process

### File Structure & Compilation

**Required Files**:
```
mt5/
├── experts/
│   ├── BentleyBot_GBP_JPY_EA.mq5      (Main EA - includes other files)
│   └── BentleyBot_XAU_USD_EA.mq5      (Gold EA)
├── indicators/
│   └── CustomIndicators.mqh           (Indicator calculations)
├── libraries/
│   └── BentleyBot.mqh                 (Core utilities)
└── ...include paths must be relative...
```

### Include Path Resolution

**MQL5 Include Search Order**:
```
1. Relative path from current file
   #include "..\\libraries\\BentleyBot.mqh"
   
2. Terminal\MQL5\Include\ directory
   #include <StdLibrary.mqh>
   
3. Built-in includes
   #include <Trade\Trade.mqh>
```

### Compilation Commands

**GUI Compilation**:
```
1. Open MetaEditor
2. File → Open → Select .mq5 file
3. View → Compilation (or press F5)
4. Check Compiler output for errors
```

**Command Line Compilation**:
```bash
# Single file
metaeditor64.exe /compile:"C:\path\BentleyBot_GBP_JPY_EA.mq5" /log:"compile.log"

# Batch compilation
metaeditor64.exe /compile:"C:\path\experts\*.mq5" /log:"compile_all.log"

# With parameters
metaeditor64.exe /compile:"file.mq5" /log:"output.log" /dir:"workdir"
```

**Python Wrapper for Compilation**:
```python
import subprocess
import os

def compile_mql5(mq5_file, output_dir=None):
    """Compile MQL5 file using MetaEditor"""
    
    metaeditor = r"C:\Program Files\MetaTrader 5\metaeditor64.exe"
    
    cmd = [
        metaeditor,
        f'/compile:"{mq5_file}"'
    ]
    
    if output_dir:
        cmd.append(f'/log:"{os.path.join(output_dir, "compile.log")}"')
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Check for errors
    if result.returncode != 0:
        print(f"Compilation failed:\n{result.stderr}")
        return False
    
    print(f"Compiled successfully: {mq5_file}")
    return True

# Usage
compile_mql5(r"mt5\experts\BentleyBot_GBP_JPY_EA.mq5", r"mt5\compiled")
```

### Output Files

**After Compilation**:
```
Terminal\<TerminalID>\MQL5\Experts\
├── BentleyBot_GBP_JPY_EA.ex5     (Compiled binary - ready to trade)
├── BentleyBot_XAU_USD_EA.ex5     (Compiled binary)
└── *.log                          (Compilation logs)
```

### Common Compilation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Cannot find include file | Wrong path | Use relative paths: `..\\libraries\\` |
| Undeclared identifier | Missing include | Add `#include <Trade\Trade.mqh>` |
| Invalid handle | Bad indicator creation | Check indicator parameters |
| Syntax error | MQL5 syntax issue | Review MQL5 documentation |

---

## Part 3: MT5 Terminal & API Integration

### MT5 Built-in APIs

#### A. Trade API (OrderSend)
```mql5
#include <Trade\Trade.mqh>

CTrade trade;

// Buy order
trade.Buy(1.0,              // lot size
          "GBPJPY",         // symbol
          ask_price,        // entry price
          sl_price,         // stop loss
          tp_price,         // take profit
          "Comment");       // trade comment

// Sell order
trade.Sell(1.0, "GBPJPY", bid_price, sl_price, tp_price, "Comment");

// Modify position
trade.PositionModify(ticket, new_sl, new_tp);

// Close position
trade.PositionClose(ticket);
```

#### B. Account API
```mql5
// Get account information
double balance = AccountInfoDouble(ACCOUNT_BALANCE);
double equity = AccountInfoDouble(ACCOUNT_EQUITY);
double margin = AccountInfoDouble(ACCOUNT_MARGIN);
double free_margin = AccountInfoDouble(ACCOUNT_FREEMARGIN);

string company = AccountInfoString(ACCOUNT_COMPANY);
int leverage = (int)AccountInfoInteger(ACCOUNT_LEVERAGE);
```

#### C. Market Data API
```mql5
// Get symbol prices
double bid = SymbolInfoDouble(Symbol_Pair, SYMBOL_BID);
double ask = SymbolInfoDouble(Symbol_Pair, SYMBOL_ASK);

// Get symbol properties
double point = SymbolInfoDouble(Symbol_Pair, SYMBOL_POINT);
double tick_value = SymbolInfoDouble(Symbol_Pair, SYMBOL_TRADE_TICK_VALUE);
int digits = (int)SymbolInfoInteger(Symbol_Pair, SYMBOL_DIGITS);
```

#### D. Position API
```mql5
// Get open positions
int total_positions = PositionsTotal();

for(int i = PositionsTotal() - 1; i >= 0; i--)
  {
    if(PositionGetSymbol(i) == Symbol_Pair)
      {
        long pos_type = PositionGetInteger(POSITION_TYPE);
        double pos_volume = PositionGetDouble(POSITION_VOLUME);
        double pos_price = PositionGetDouble(POSITION_PRICE_OPEN);
        double pos_sl = PositionGetDouble(POSITION_SL);
        double pos_tp = PositionGetDouble(POSITION_TP);
      }
  }
```

### External API Integration

#### Option 1: File-Based Communication
```mql5
// EA writes trade signals to file
void ExportSignal(string symbol, double price, string type)
  {
    int handle = FileOpen("signals.csv", FILE_WRITE | FILE_CSV);
    FileWrite(handle, TimeCurrent(), symbol, price, type);
    FileClose(handle);
  }

// Python reads file
df = pd.read_csv('signals.csv')
for signal in df.itertuples():
    alpaca_api.submit_order(symbol=signal.symbol, ...)
```

#### Option 2: REST API (Advanced)
```mql5
// Requires DLL imports or external library
// Implementation via HTTP POST to Python Flask server

// Python Flask endpoint
@app.route('/trade_signal', methods=['POST'])
def receive_signal():
    data = request.json
    order = api.submit_order(
        symbol=data['symbol'],
        qty=data['qty'],
        side=data['type'],
        type='market'
    )
    return {'status': 'success', 'order_id': order.id}
```

#### Option 3: Database Sync
```mql5
// Write to local database
// Python monitors and syncs

import sqlite3

db = sqlite3.connect('mt5_trades.db')
cursor = db.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY,
        timestamp DATETIME,
        symbol TEXT,
        price REAL,
        type TEXT,
        status TEXT
    )
''')

# Poll for pending trades
cursor.execute('SELECT * FROM trades WHERE status = ?', ('pending',))
for trade in cursor.fetchall():
    api.submit_order(...)  # Sync to Alpaca
```

---

## Part 4: Connection & API Checklist

### Pre-Deployment Requirements

**MetaEditor/Compiler**:
- [ ] MT5 installed with MetaEditor
- [ ] MetaEditor launches without errors
- [ ] Can open and compile .mq5 files
- [ ] Include paths set correctly
- [ ] No missing dependencies

**MT5 Terminal Connection**:
- [ ] Broker account configured
- [ ] Demo/Live account selectable
- [ ] Market quotes flowing (bid/ask active)
- [ ] Symbols subscribed (GBPJPY, XAUUSD)
- [ ] AutoTrading enabled in settings

**External API Keys** (if needed):
- [ ] Alpaca API key & secret
- [ ] Discord webhook URL
- [ ] Other broker credentials
- [ ] All credentials in `.env` file

**Python Environment**:
- [ ] Python 3.9+ installed
- [ ] Required packages: `alpaca-trade-api`, `requests`, `pandas`
- [ ] Virtual environment activated
- [ ] Bridge scripts tested

### Testing Connection

**MT5 Terminal Test**:
```mql5
// Add this to EA OnInit()
void TestConnection()
  {
    Print("=== Connection Test ===");
    Print("Terminal: Connected");
    Print("Symbol: ", Symbol_Pair);
    Print("Bid: ", SymbolInfoDouble(Symbol_Pair, SYMBOL_BID));
    Print("Ask: ", SymbolInfoDouble(Symbol_Pair, SYMBOL_ASK));
    Print("Account Balance: ", AccountInfoDouble(ACCOUNT_BALANCE));
    Print("=== All Systems OK ===");
  }
```

**Python Bridge Test**:
```python
# Test Alpaca connection
from alpaca_trade_api import REST

api = REST(api_key, secret_key)
account = api.get_account()
print(f"Connected to Alpaca | Balance: ${account.buying_power}")

# Test Discord webhook
import requests
requests.post(webhook_url, json={"content": "✅ BentleyBot Online"})
print("Discord connected")
```

---

## Part 5: Complete Integration Architecture

```
┌─────────────────────────────────────────┐
│   Development (VS Code)                 │
│   .mq5 source files                     │
└──────────────┬──────────────────────────┘
               │ (Git push)
               ▼
┌─────────────────────────────────────────┐
│   MetaEditor (MT5 Compiler)             │
│   Compile .mq5 → .ex5                   │
└──────────────┬──────────────────────────┘
               │ (Copy to terminal)
               ▼
┌─────────────────────────────────────────┐
│   MT5 Terminal (Execution)              │
│   • Load .ex5 on chart                  │
│   • Execute OnTick()                    │
│   • Place orders                        │
└──────────────┬──────────────────────────┘
               │ (Write signals to file)
               ▼
┌─────────────────────────────────────────┐
│   Python Bridge Service                 │
│   • Monitor signals                     │
│   • Call external APIs                  │
│   • Process notifications               │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
┌─────────────┐    ┌──────────────┐
│   Alpaca    │    │    Discord   │
│   Trading   │    │ Notifications│
└─────────────┘    └──────────────┘
```

---

## Part 6: Deployment Summary

### Required Software Stack
1. **MetaTrader 5** - Trading platform
2. **MetaEditor** - MQL5 compiler (bundled)
3. **Python 3.9+** - Bridge/integration scripts
4. **.NET Framework 4.5+** - System dependency

### Integration Methods
1. **File-based** - CSV signals (simplest, recommended for start)
2. **REST API** - HTTP endpoints (requires advanced MQL5)
3. **Database** - SQLite/MySQL sync (flexible)

### Workflow
1. Edit EA in VS Code
2. Compile with MetaEditor (F5)
3. Test in MT5 Terminal (demo account)
4. Backtest with Strategy Tester
5. Deploy to production
6. Monitor with Python scripts

### Go-Live Requirements
- ✅ Compiled EAs without errors
- ✅ 6+ months backtesting passed
- ✅ 1+ week demo account testing
- ✅ Python bridge scripts running
- ✅ Discord notifications configured
- ✅ Monitoring procedures documented
- ✅ Risk parameters validated

---

## Part 7: Support Resources

**Official Documentation**:
- [MQL5 Language Reference](https://www.mql5.com/en/docs)
- [MT5 Platform Documentation](https://www.metatrader5.com/en/help)
- [Trade Library Reference](https://www.mql5.com/en/docs/trade)

**Quick References**:
- [Setup Guide](SETUP.md)
- [Architecture Guide](ARCHITECTURE.md)
- [API Integration Guide](API_INTEGRATION.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

---

**Status**: ✅ **Ready for Production**
**Last Updated**: 2026-01-29
**Maintainer**: BentleyBot Development Team
