# MT5 Bot Development Workflow

## Directory Structure

```
mt5/
├── experts/                      # Compiled EAs (.ex5) + source (.mq5)
│   ├── BentleyBot_GBP_JPY_EA.mq5
│   ├── BentleyBot_XAU_USD_EA.mq5
│   └── compiled/                 # Compiled binaries
├── indicators/                   # Custom indicators (.mq5)
│   ├── CustomIndicators.mqh
│   └── compiled/
├── libraries/                    # Shared libraries (.mqh)
│   ├── BentleyBot.mqh
│   └── TradeManager.mqh
├── scripts/                      # Utility scripts
│   ├── backtest_runner.mq5
│   └── data_exporter.mq5
├── tests/                        # Test files (strategy backtests)
│   ├── GBP_JPY_backtest.set
│   └── XAU_USD_backtest.set
├── config/                       # Configuration files
│   ├── trading_symbols.conf
│   └── risk_parameters.json
├── docs/                         # Documentation
│   ├── SETUP.md
│   ├── ARCHITECTURE.md
│   ├── API_INTEGRATION.md
│   └── TROUBLESHOOTING.md
└── README.md
```

## Development Workflow

### 1. **Local Development (VS Code)**
- Edit `.mq5` files in VS Code with MQL5 syntax highlighting
- Use folder structure for organization
- Maintain version control with Git

### 2. **Compile in MetaEditor (MT5)**
- Open MetaEditor (Tools → MetaEditor in MT5)
- Load `.mq5` files from `mt5/experts/` directory
- Compile to generate `.ex5` binaries
- Check for compilation errors

### 3. **Deploy to MT5 Terminal**
- Copy compiled `.ex5` to `%APPDATA%\Roaming\MetaQuotes\Terminal\<TerminalID>\MQL5\Experts\`
- Or use MetaEditor's "Compile" button which auto-deploys
- Restart MT5 if needed

### 4. **Backtest Strategy**
- Open MT5 Strategy Tester (View → Strategy Tester)
- Select compiled EA and timeframe
- Load test data or use broker's historical data
- Set optimization parameters
- Review results and optimization history

### 5. **Live Testing (Demo Account)**
- Attach EA to chart during London/New York overlap (12:00-16:00 UTC)
- Monitor trades in real-time
- Review logs for debugging

### 6. **Iterate & Push to GitHub**
- Make code changes in VS Code
- Commit with descriptive messages
- Push to remote repository
- Recompile in MT5
- Re-test

## API & Compiler Integration

### MT5 Compiler Requirements
- **MetaEditor Version**: Latest (included with MT5 Terminator)
- **MQL5 Language**: Supported up to latest standard
- **Compilation Output**: `.ex5` binary files

### Connecting to MT5 Compiler

#### Option 1: **Manual Compilation (Recommended for Development)**
```
1. Open MetaTerminal → Tools → MetaEditor
2. File → Open → Select .mq5 file
3. Compile (F5) 
4. .ex5 automatically placed in Terminal\MQL5\Experts\
```

#### Option 2: **Command Line Compilation (CI/CD)**
```bash
# MetaEditor CLI path
"C:\Program Files\MetaTrader 5\metaeditor64.exe" /compile:"path/to/file.mq5" /log:"output.log"
```

#### Option 3: **Python Integration (For CI/CD Pipeline)**
```python
import subprocess
import os

def compile_mq5(mq5_path, output_dir):
    metaeditor_path = r"C:\Program Files\MetaTrader 5\metaeditor64.exe"
    
    cmd = [
        metaeditor_path,
        f'/compile:"{mq5_path}"',
        f'/log:"{output_dir}\\compile.log"'
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0

# Usage
compile_mq5(r"mt5\experts\BentleyBot_GBP_JPY_EA.mq5", r"mt5\compiled")
```

### API Connections for MT5

#### A. **OrderSend API (Built-in)**
```mql5
trade.Buy(lot_size, Symbol_Pair, entry_price, sl, tp, comment);
trade.Sell(lot_size, Symbol_Pair, entry_price, sl, tp, comment);
```

#### B. **WebSocket Integration (REST API to External Services)**
```mql5
// Connect to external services (Alpaca, Discord, etc.)
// Use Python bridge or REST endpoints

// Example: Send trade signals via HTTP POST
// This requires custom library implementation
```

#### C. **File I/O for Sync with Python Bots**
```mql5
// Export trades to CSV for Alpaca sync
int file_handle = FileOpen("trades_export.csv", FILE_WRITE);
FileWrite(file_handle, "Symbol,Time,Type,Volume,Price,SL,TP");
FileClose(file_handle);
```

### Git-based CI/CD Workflow for MT5

**.github/workflows/mt5-compile.yml**
```yaml
name: MT5 Compilation & Testing

on: [push, pull_request]

jobs:
  compile:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup MT5
        run: |
          # Download and install MT5 (or use pre-installed)
          # This assumes MT5 is already installed on runner
          
      - name: Compile MQL5 Files
        run: |
          $metaeditor = "C:\Program Files\MetaTrader 5\metaeditor64.exe"
          & $metaeditor /compile:"${{ github.workspace }}\mt5\experts\BentleyBot_GBP_JPY_EA.mq5"
          & $metaeditor /compile:"${{ github.workspace }}\mt5\experts\BentleyBot_XAU_USD_EA.mq5"
      
      - name: Run Backtest
        run: |
          # Run strategy tester in batch mode
          # Requires MT5 terminal automation
          
      - name: Upload Artifacts
        uses: actions/upload-artifact@v2
        with:
          name: compiled-eas
          path: mt5/compiled/
          
      - name: Notify Discord
        if: failure()
        run: |
          # Send notification on compilation failure
```

## MT5 Terminal Configuration

### Broker Connection
1. Launch MT5 terminal
2. Select broker (or use demo account for testing)
3. Enable "AutoTrading" in Terminal settings
4. Set account type: Demo/Live

### Data Sources
- **Historical Data**: Broker provides via terminal connection
- **Live Quotes**: Real-time from broker feed
- **Symbols Configuration**: Tools → Options → Charts → Symbols

### Account & Risk Settings
```
Account Balance:     $10,000 (Demo)
Maximum Positions:   3
Maximum Orders:      10
Default Slippage:    10 pips
Leverage:            1:50 (or broker default)
```

## Testing & Validation Checklist

- [ ] EA compiles without errors
- [ ] SL/TP logic validated in backtest
- [ ] Volatility handling confirmed
- [ ] Demo account trades placed successfully
- [ ] Logs show correct entry/exit signals
- [ ] Risk-reward ratios match settings
- [ ] No memory leaks or crashes
- [ ] Performance acceptable (no lag)
- [ ] Ready for live trading

## Troubleshooting

### Compilation Errors
- Check MQL5 syntax
- Verify all includes are present (`#include` paths)
- Review compiler output log

### Connection Issues
- Verify broker connection in MT5 terminal
- Check account credentials
- Review network/firewall settings

### Strategy Not Trading
- Check time filter (trading hours)
- Verify market hours and holidays
- Review indicator values
- Check position limits

## References
- [MQL5 Documentation](https://www.mql5.com/en/docs)
- [MetaTrader 5 Trading Platform](https://www.metatrader5.com/)
- [Strategy Testing & Optimization Guide](https://www.mql5.com/en/articles/195)
