# MT5 EA Architecture & Design

## System Design

```
┌─────────────────────────────────────────────────────────┐
│          MT5 Terminal (MetaTrader 5)                    │
│  ┌───────────────────────────────────────────────────┐  │
│  │  BentleyBot_GBP_JPY_EA.ex5 (Compiled)             │  │
│  │  ┌──────────────────────────────────────────────┐ │  │
│  │  │ OnInit()     - Initialize indicators         │ │  │
│  │  │ OnTick()     - Main trading logic             │ │  │
│  │  │ OnDeinit()   - Cleanup resources             │ │  │
│  │  └──────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────┘  │
│                        ↓                                 │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Shared Libraries                                 │  │
│  │  • BentleyBot.mqh     (Core utilities)            │  │
│  │  • CustomIndicators.mqh (Indicator calculations) │  │
│  │  • Trade.mqh          (MT5 standard library)      │  │
│  └───────────────────────────────────────────────────┘  │
│                        ↓                                 │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Market Data & Indicators                         │  │
│  │  • GBPJPY H1 prices (Bid/Ask)                     │  │
│  │  • EMA(20), EMA(50), RSI(14)                      │  │
│  │  • ATR(14) for volatility                         │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
           ↓                              ↓
    ┌─────────────┐              ┌──────────────┐
    │ Place Orders │              │ Manage Trades │
    │ (Buy/Sell)  │              │ (SL/TP)      │
    └─────────────┘              └──────────────┘
           ↓                              ↓
    ┌──────────────────────────────────────────┐
    │  MT5 Account (Demo/Live)                 │
    │  • Open Positions                        │
    │  • Closed Deals                          │
    │  • Account History                       │
    └──────────────────────────────────────────┘
```

## EA Structure

### GBP/JPY EA - EMA Crossover + RSI
**Purpose**: Capture mid-term trends during London/New York overlap

**Strategy Logic**:
```
Entry Conditions (Long):
  IF EMA(20) > EMA(50)
    AND RSI(14) < 70
    AND Hour is between 12-16 UTC
    THEN Buy

Entry Conditions (Short):
  IF EMA(20) < EMA(50)
    AND Resistance Rejection confirmed
    AND RSI(14) > 70
    THEN Sell

Exit Conditions:
  Take Profit = Entry + 100 pips
  Stop Loss = Entry - 50 pips
```

**Parameters**:
- EMA periods: 20, 50
- RSI period: 14, Overbought: 70, Oversold: 30
- Risk per trade: 2%
- Max simultaneous trades: 3

### XAU/USD EA - Volatility & Mean Reversion
**Purpose**: Trade gold using Bollinger Bands and ATR

**Strategy Logic**:
```
Entry Conditions (Long):
  IF Price <= BB_Lower Band
    AND Bounce confirmed from support
    THEN Buy with ATR-based stops

Entry Conditions (Short):
  IF Price >= BB_Upper Band
    AND Resistance rejection confirmed
    THEN Sell with ATR-based stops

Dynamic Stops:
  SL = Entry ± (ATR × 1.5)
  TP = Entry ± (ATR × 3.0)
```

**Parameters**:
- Bollinger Bands: Period 20, StdDev 2
- ATR: Period 14, Multiplier 1.5
- Risk per trade: 2%
- Max simultaneous trades: 2

## Code Organization

### OnInit() - Initialization
```
1. Validate input parameters
2. Create indicator handles (EMA, RSI, ATR, Bollinger Bands)
3. Initialize trade object with magic number
4. Check for errors and return status
```

### OnTick() - Main Trading Logic
```
1. Wait for sufficient data (>50 bars)
2. Get current bid/ask prices
3. Check time filter (trading hours)
4. Check position limits
5. Retrieve indicator values
6. Evaluate entry conditions
7. Execute trades if conditions met
8. Manage existing positions
```

### OnDeinit() - Cleanup
```
1. Release all indicator handles
2. Clean up resources
3. Log deinitialization message
```

## Risk Management

### Position Sizing
```
Risk Amount = Account Balance × Risk Percent (2%)
Pips at Risk = |Entry Price - Stop Loss|
Lot Size = Risk Amount / (Pips × Pip Value)

Constraints:
  Min Lot ≤ Calculated Lot ≤ Max Lot
```

### Trade Filtering
- **Time Filter**: Only trade during specific hours (London 08:00 - New York 16:00 GMT)
- **Position Limit**: Max 3 concurrent trades
- **Cooldown**: Prevent over-trading with cooldown periods
- **Risk-Reward Ratio**: Minimum 1.5:1 required

### Volatility Management
- **ATR-based stops**: Adjusts to market conditions
- **Bollinger Bands**: Identifies overbought/oversold levels
- **RSI Filters**: Prevents trading in extreme conditions

## Integration Points

### Python Bridge (Optional)
```python
# Sync MT5 trades with Alpaca
import json
import time

def read_mt5_trades():
    """Read trades exported by EA from CSV"""
    with open('mt5/trades_export.csv', 'r') as f:
        trades = json.load(f)
    return trades

def sync_to_alpaca(trades):
    """Sync MT5 signals to Alpaca via API"""
    for trade in trades:
        if trade['status'] == 'CLOSED':
            alpaca_api.submit_order(
                symbol=trade['symbol'],
                qty=trade['quantity'],
                side=trade['direction'],
                type='MARKET'
            )
```

### Discord Notifications
```mql5
// Export trade alerts to Discord via webhook
// Requires: External library or HTTP POST capability
// Implementation: Send JSON trade data to Discord endpoint
```

## Performance Metrics

### Backtesting Metrics
- Profit Factor > 1.5
- Win Rate > 55%
- Max Drawdown < 20%
- Sharpe Ratio > 1.0
- Recovery Factor > 2.0

### Live Trading Metrics
- Slippage monitoring
- Execution time < 500ms
- Missed trades tracking
- Margin requirement vs. balance

## Deployment Checklist

- [ ] All indicators compile without errors
- [ ] Shared libraries included and accessible
- [ ] Risk parameters validated
- [ ] Time filters set correctly
- [ ] Magic numbers unique per EA
- [ ] Broker leverage verified
- [ ] Minimum account balance requirement met
- [ ] Demo account tested for 1 week
- [ ] Logs reviewed for errors
- [ ] Ready for live deployment

## File Dependencies

```
BentleyBot_GBP_JPY_EA.mq5
├── Trade.mqh (MT5 standard)
├── BentleyBot.mqh
│   └── (Utility functions)
└── CustomIndicators.mqh
    └── (Indicator calculations)

BentleyBot_XAU_USD_EA.mq5
├── Trade.mqh (MT5 standard)
├── BentleyBot.mqh
│   └── (Utility functions)
└── CustomIndicators.mqh
    └── (Indicator calculations)
```

## Version Control

All files tracked in Git:
```
mt5/
├── experts/*.mq5          (Source code)
├── indicators/*.mqh       (Includes)
├── libraries/*.mqh        (Libraries)
├── config/*.conf          (Configuration)
└── docs/*.md              (Documentation)
```

Workflow:
```
1. Edit in VS Code
2. Compile in MetaEditor
3. Test in MT5 terminal
4. Commit to GitHub
5. Deploy via CI/CD
```
