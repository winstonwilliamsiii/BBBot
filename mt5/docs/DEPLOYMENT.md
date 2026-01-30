# MT5 Bot Deployment Guide

## Pre-Deployment Checklist

### Code Quality
- [ ] No compilation errors
- [ ] All indicators implemented
- [ ] Risk parameters validated
- [ ] Position sizing tested
- [ ] SL/TP logic verified
- [ ] Time filters configured

### Testing
- [ ] Backtest 6+ months of data
- [ ] Forward test 2+ weeks
- [ ] Demo account test 1+ week
- [ ] No errors in terminal logs
- [ ] Slippage within acceptable range
- [ ] All trades placed correctly

### Documentation
- [ ] README.md complete
- [ ] Configuration documented
- [ ] Deployment instructions clear
- [ ] Troubleshooting guide reviewed

---

## Deployment Steps

### Step 1: Prepare Production Environment

```bash
# 1. Create separate MT5 terminal for production (optional)
#    Recommended: Use VPS for 24/7 trading

# 2. Test broker connection
#    Verify account type (Demo/Live)
#    Check leverage and margin requirements

# 3. Disable EA during setup
#    Tools → Options → Expert Advisors
#    Uncheck "Allow automated trading"
```

### Step 2: Deploy EAs

```bash
# Windows User Directory
C:\Users\<UserName>\AppData\Roaming\MetaQuotes\Terminal\<TerminalID>\MQL5\

# Copy compiled files
Copy-Item "mt5\experts\*.ex5" `
         "C:\Users\$env:USERNAME\AppData\Roaming\MetaQuotes\Terminal\*\MQL5\Experts"

# Copy library files
Copy-Item "mt5\libraries\*.mqh" `
         "C:\Users\$env:USERNAME\AppData\Roaming\MetaQuotes\Terminal\*\MQL5\Include"

# Verify installation
Get-ChildItem "C:\Users\$env:USERNAME\AppData\Roaming\MetaQuotes\Terminal\*\MQL5\Experts\*.ex5"
```

### Step 3: Configure EAs

```
In MT5 Terminal:

1. Tools → Options → Expert Advisors
   ✓ Enable automated trading
   ✓ Enable signals (optional)
   
2. Tools → Options → Charts
   ✓ Verify GBPJPY and XAUUSD subscribed
   ✓ Set quote refresh to 100ms
   
3. View → MarketWatch
   ✓ Add symbols: GBPJPY, XAUUSD
```

### Step 4: Attach EAs to Charts

```
1. Open GBPJPY H1 chart
   - File → New Chart → GBPJPY, H1
   
2. Attach GBP/JPY EA
   - Insert → Expert Advisors → Select BentleyBot_GBP_JPY_EA
   - Review input parameters
   - Click "OK"
   
3. Verify EA is running
   - Check chart has "Expert Advisor Running" indicator
   - No errors in terminal logs
   
4. Repeat for XAUUSD H1 chart with Gold EA
```

### Step 5: Monitor Initial Trades

```
First 24 hours:
- Monitor every 2-4 hours
- Check trade execution
- Verify SL/TP placement
- Review logs for errors
- Monitor account balance

First week:
- Daily monitoring recommended
- Review trades history
- Compare with backtest expectations
- Adjust parameters if needed

After week 1:
- Reduce monitoring to daily check-ins
- Weekly performance review
- Monthly optimization review
```

---

## Live Trading Best Practices

### Risk Management
```
Daily Limits:
- Max Loss per Day: 5% of account
- Max Positions: 3-5 concurrent
- Max Trade Size: 2% of account per trade

Weekly Review:
- Win rate vs. expectations
- Profit/loss tracking
- Drawdown monitoring
```

### Monitoring

**Daily Tasks**:
- [ ] Check if EAs are running
- [ ] Review trades executed
- [ ] Check account balance
- [ ] Review terminal logs for errors

**Weekly Tasks**:
- [ ] Performance analysis
- [ ] Trade summary report
- [ ] Parameter adjustment if needed
- [ ] Update documentation

**Monthly Tasks**:
- [ ] Full strategy review
- [ ] Backtest latest data
- [ ] Optimization analysis
- [ ] Risk parameter review

### Emergency Procedures

**If EA Malfunctions**:
```
1. Disable EA immediately
   - Right-click chart → Expert Advisors (uncheck)
   
2. Close any problematic trades manually if needed
   
3. Review logs
   - View → Experts → Check messages
   
4. Fix code
   - Make necessary changes
   - Recompile
   
5. Test in demo first
   - Run on demo account for 24-48 hours
   
6. Redeploy if confirmed fixed
   - Attach to live chart
   - Monitor carefully
```

**If Market Condition Unusual**:
```
1. Reduce position sizes
   - Change Risk_Percent to 1% temporarily
   
2. Add additional filters
   - Tighten time windows
   - Increase volatility thresholds
   
3. Consider stopping trades temporarily
```

---

## Automation & VPS Setup

### Running on VPS (Recommended for 24/7 Trading)

**1. Rent VPS**
- Recommended: AWS, Azure, or dedicated VPS
- Minimum: 2GB RAM, 1 vCPU
- Windows Server 2019/2022

**2. Install MT5 on VPS**
```bash
# Download MT5 installer
# Run silent installation
MetaTrader5Setup.exe /auto

# Configure for headless operation
# Enable portable terminal mode
```

**3. Copy EA Files**
```bash
# Via RDP or SCP
# Copy all compiled .ex5 files
# Copy library .mqh files
```

**4. Enable Remote Desktop (Monitoring)**
```bash
# Connect via RDP to monitor
# Use local terminal for administration
```

### GitHub Actions Deployment (CI/CD)

**.github/workflows/mt5-deploy.yml**
```yaml
name: Deploy MT5 EAs

on:
  push:
    branches: [main]
    paths:
      - 'mt5/experts/**'
      - 'mt5/libraries/**'

jobs:
  deploy:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup MT5
        run: |
          # Install MT5 if not present
          
      - name: Compile EAs
        run: |
          $metaeditor = "C:\Program Files\MetaTrader 5\metaeditor64.exe"
          
          # Compile GBP/JPY EA
          & $metaeditor /compile:"mt5\experts\BentleyBot_GBP_JPY_EA.mq5"
          
          # Compile XAU/USD EA
          & $metaeditor /compile:"mt5\experts\BentleyBot_XAU_USD_EA.mq5"
      
      - name: Run Tests
        run: |
          # Run backtest
          python scripts/backtest_runner.py
      
      - name: Deploy to VPS
        run: |
          # SCP files to VPS
          scp -r mt5/experts/*.ex5 user@vps:/remote/path/
      
      - name: Notify Discord
        if: always()
        run: |
          python scripts/notify_deployment.py
```

---

## Performance Monitoring

### Key Metrics to Track

```
Daily:
- Number of trades
- Win/loss ratio
- Daily P&L
- Max drawdown in session

Weekly:
- Total P&L
- Win rate %
- Profit factor
- Sharpe ratio
- Recovery factor

Monthly:
- Cumulative returns
- Max monthly drawdown
- Consistency of returns
- Strategy performance vs. market
```

### Logging Setup

```mql5
// Add to EA initialization
void SetupLogging()
  {
    Print("===== TRADING SESSION START =====");
    Print("Time: ", TimeToString(TimeCurrent()));
    Print("Balance: ", AccountInfoDouble(ACCOUNT_BALANCE));
    Print("Equity: ", AccountInfoDouble(ACCOUNT_EQUITY));
    Print("Broker: ", AccountInfoString(ACCOUNT_COMPANY));
    Print("===== CONFIG =====");
    Print("Risk per Trade: ", Risk_Percent, "%");
    Print("Max Trades: ", Max_Trades);
    Print("Time Filter: ", Start_Hour, "-", End_Hour, " UTC");
  }
```

### Export Trade History

```python
# Python script to export trades
import csv
from datetime import datetime

def export_mt5_history(account_number, output_file='trades_history.csv'):
    """Export closed trades from MT5"""
    # Connect to MT5 terminal
    # Extract trade history
    # Save to CSV with:
    # - Entry time, symbol, type, volume, entry price
    # - Exit time, exit price, profit/loss, commission
    # - Duration, percentage return
    pass
```

---

## Troubleshooting Deployment

### EA Not Showing in Terminal

**Problem**: EA doesn't appear in insert menu

**Solution**:
```
1. Verify .ex5 file in correct directory
2. Restart MT5 terminal
3. Check compilation output for errors
4. Verify MQL5 version compatibility
```

### Trades Not Executing

**Problem**: EA attached but no trades placed

**Solution**:
```
1. Check AutoTrading is enabled
2. Verify time filter matches current time
3. Check position limit not exceeded
4. Review indicator values
5. Check broker connection
```

### High Slippage

**Problem**: Orders executing far from expected price

**Solution**:
```
1. Reduce order size (market impact)
2. Use limit orders instead of market
3. Trade during high-liquidity hours
4. Increase slippage tolerance in EA
```

---

## Rollback Procedure

**If Critical Issue Detected**:

```
1. Disable All EAs
   - Right-click chart → Expert Advisors (uncheck all)
   
2. Close Open Positions (if needed)
   - Manually close if automated close fails
   
3. Revert Code
   - git revert <commit>
   
4. Recompile
   - Rebuild EAs in MetaEditor
   
5. Test in Demo
   - Run 24+ hours in demo
   
6. Redeploy
   - After confirming fix
```

---

## Go-Live Checklist

Final verification before production trading:

- [ ] All EAs compiled without errors
- [ ] Backtest results acceptable
- [ ] Demo account test completed (1+ week)
- [ ] No critical issues in logs
- [ ] Monitoring procedures documented
- [ ] Emergency procedures understood
- [ ] Account properly capitalized
- [ ] Risk parameters reviewed
- [ ] VPS/infrastructure ready
- [ ] Deployment team notified
- [ ] Trading hours confirmed
- [ ] Broker support contact available

**Sign-off**: ___________________________ Date: __________

---

## Support & Maintenance

**Post-Deployment Support**:
- Daily monitoring for first 2 weeks
- Weekly performance reviews for first month
- Monthly optimization starting month 2
- Document all adjustments

**Scheduled Maintenance**:
- Weekly: Log review, backup EA files
- Monthly: Strategy performance analysis
- Quarterly: Full backtest with latest data
- Annual: Complete strategy review

---

**Last Updated**: 2026-01-29
**Deployment Status**: Ready for Production
