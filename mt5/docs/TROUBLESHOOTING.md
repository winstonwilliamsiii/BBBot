# MT5 Troubleshooting Guide

## Compilation Issues

### ❌ "Cannot find include file"
**Problem**: Compiler can't locate `#include` files

**Solution**:
```
1. Verify file path in #include statement
2. Check that .mqh files exist in correct directory
3. Use relative paths: #include "..\\libraries\\BentleyBot.mqh"
4. Ensure no typos in filenames
```

**Example Fix**:
```mql5
// WRONG
#include <BentleyBot.mqh>

// RIGHT
#include "..\\libraries\\BentleyBot.mqh"
```

---

### ❌ "Undeclared identifier 'trade'"
**Problem**: Trade object not initialized

**Solution**:
```mql5
// Add at top of EA
#include <Trade\Trade.mqh>

// In OnInit()
CTrade trade;
if(!trade.SetExpertMagicNumber(123456))
  {
    Print("ERROR: Failed to initialize trade object");
    return(INIT_FAILED);
  }
```

---

### ❌ "Invalid handle"
**Problem**: Indicator handle not created properly

**Solution**:
```mql5
// Check handle creation
ema20_handle = iMA(Symbol(), TimeFrame, 20, 0, MODE_EMA, PRICE_CLOSE);

if(ema20_handle == INVALID_HANDLE)
  {
    Print("ERROR: Failed to create EMA indicator");
    return(INIT_FAILED);
  }
```

---

## Runtime Issues

### ❌ EA Not Trading
**Checklist**:
- [ ] AutoTrading enabled in terminal
- [ ] EA attached to correct chart
- [ ] Time filter matches current time (UTC)
- [ ] Market hours validated
- [ ] Position limit not exceeded
- [ ] Sufficient account balance
- [ ] No errors in terminal logs

**Debug Steps**:
```mql5
// Add logging to OnTick()
void OnTick()
  {
    Print("Current time: ", TimeToString(TimeCurrent()));
    Print("Hour: ", TimeHour(TimeCurrent()));
    Print("Bars: ", Bars(Symbol(), TimeFrame));
    
    if(!IsWithinTradingHours(Start_Hour, End_Hour))
      {
        Print("Outside trading hours");
        return;
      }
    
    Print("Within trading hours - proceeding...");
  }
```

---

### ❌ "Not enough money"
**Problem**: Insufficient funds for position size

**Solution**:
```mql5
// Check account balance
double account_balance = AccountInfoDouble(ACCOUNT_BALANCE);
double min_margin = SymbolInfoDouble(Symbol(), SYMBOL_MARGIN_INITIAL);

Print("Account Balance: ", account_balance);
Print("Required Margin: ", min_margin);

// Reduce risk percentage if needed
double reduced_risk = Risk_Percent / 2;  // Cut risk in half
```

---

### ❌ Trade Execution Slippage
**Problem**: Fills at different prices than expected

**Solution**:
```mql5
// Add slippage tolerance to orders
trade.Buy(lot_size, Symbol(), ask, sl, tp, 
          "Comment", 
          50);  // 50 pips slippage tolerance

// Or use pending orders
trade.BuyLimit(lot_size, limit_price, Symbol(), sl, tp);
```

---

## Data & Indicator Issues

### ❌ Indicator Returns 0 or NaN
**Problem**: Insufficient data or calculation error

**Solution**:
```mql5
// Wait for sufficient bars before using indicators
if(Bars(Symbol(), TimeFrame) < 100)
  {
    Print("Insufficient data - waiting for ", 
          100 - Bars(Symbol(), TimeFrame), 
          " more bars");
    return;
  }

// Verify indicator value is valid
double ema = GetIndicatorValue(ema_handle, 0);
if(ema == 0 || IsNaN(ema))
  {
    Print("Invalid indicator value");
    return;
  }
```

---

### ❌ MultiIndex DataFrame Error
**Problem**: Yahoo Finance returns different column structure

**Solution**: 
See [BentleyBot copilot-instructions.md](../../.github/copilot-instructions.md#debugging-areas)

---

## Connection Issues

### ❌ Cannot Connect to Broker
**Problem**: MT5 not connected to broker

**Solution**:
```
1. Check internet connection
2. Verify broker credentials
3. Disable firewall/VPN temporarily
4. Check broker status page
5. Restart MT5 terminal
6. Re-login to account
```

---

### ❌ No Quote Data Received
**Problem**: Market data not streaming

**Solution**:
```
1. Ensure symbol is subscribed (MarketWatch)
2. Check broker market hours
3. Verify symbol name (GBPJPY vs GBPJPY1)
4. Review bid/ask prices: Print(Bid, " / ", Ask);
5. Check network connectivity
```

---

## Performance Issues

### ❌ EA Causing Lag/Freezing
**Problem**: Excessive resource usage

**Solution**:
```mql5
// Optimize indicator calculations
// Use OnTick() instead of OnTimer() when possible
// Limit number of open trades
// Reduce indicator count
// Use efficient array operations

// Example: Cache indicator values
static double prev_ema20 = 0;
double ema20 = GetIndicatorValue(ema20_handle, 0);

if(ema20 == prev_ema20)
  return;  // No change, skip processing

prev_ema20 = ema20;
```

---

### ❌ High CPU Usage
**Problem**: Inefficient code consuming resources

**Solution**:
1. Review OnTick() for expensive operations
2. Use static variables to cache values
3. Limit array operations
4. Reduce logging frequency
5. Profile code with MT5 debugger

---

## Logging & Debugging

### Enable Debug Logging
```mql5
#define DEBUG 1

void DebugLog(string message)
  {
   #ifdef DEBUG
      Print("[DEBUG] ", TimeToString(TimeCurrent()), " - ", message);
   #endif
  }

// Usage
DebugLog("EMA20: " + DoubleToString(ema20));
DebugLog("RSI: " + DoubleToString(rsi));
```

### View Terminal Logs
```
In MT5:
1. View → Experts
2. Scroll through messages
3. Right-click → Save As (export logs)
```

---

## Testing Checklist

- [ ] Compiles without errors
- [ ] All indicators initialize successfully
- [ ] OnTick() processes without errors
- [ ] Trade execution tested in backtest
- [ ] Demo account test 48+ hours
- [ ] No errors in terminal logs
- [ ] Slippage within acceptable range
- [ ] Position sizing correct
- [ ] SL/TP hit as expected
- [ ] Ready for production

---

## Common Parameter Issues

### ❌ TimeFrame Not Recognized
**Problem**: ENUM_TIMEFRAMES invalid

**Solution**:
```mql5
// Use correct enum values
PERIOD_M1    // 1 minute
PERIOD_M5    // 5 minutes
PERIOD_M15   // 15 minutes
PERIOD_H1    // 1 hour
PERIOD_H4    // 4 hours
PERIOD_D1    // 1 day
PERIOD_W1    // 1 week
PERIOD_MN1   // 1 month

// Or use numeric equivalents
1, 5, 15, 60, 240, 1440, 10080, 43200
```

---

### ❌ Symbol Not Found
**Problem**: Invalid symbol name

**Solution**:
```mql5
// Check symbol exists
if(!SymbolSelect(Symbol_Pair, true))
  {
    Print("Symbol not found: ", Symbol_Pair);
    return(INIT_FAILED);
  }

// Verify exact name matches broker's format
// Examples: GBPJPY, XAUUSD, EURUSD
// Some brokers use: GBPJPY.m, GBPJPY#CFD
```

---

## Getting Help

### Check These Resources
1. **Terminal Logs**: View → Experts (scroll through messages)
2. **Expert Log Files**: `%APPDATA%\Roaming\MetaQuotes\Terminal\<ID>\logs\`
3. **MQL5 Documentation**: https://www.mql5.com/en/docs
4. **Strategy Tester Results**: Check optimization reports

### Debug Output Example
```mql5
Print("=== EA Initialization ===");
Print("Symbol: ", Symbol_Pair);
Print("Timeframe: ", Period());
Print("Time: ", TimeToString(TimeCurrent()));
Print("Bid/Ask: ", Bid, " / ", Ask);
Print("Bars: ", Bars(Symbol(), TimeFrame));
Print("===== Start Trading =====");
```

---

## Emergency Shutdown

**If EA is malfunctioning**:
```
1. Right-click chart → Expert Advisors (uncheck EA)
2. Close chart
3. Restart MT5 if needed
4. Review logs for errors
5. Fix code
6. Recompile
7. Test in demo first
```

---

## Contact Support

- **MQL5 Community**: https://www.mql5.com/en/forum
- **MetaTrader Support**: https://www.metatrader5.com/en/support
- **Strategy Issues**: Review backtesting reports

---

**Last Updated**: 2026-01-29
