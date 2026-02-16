# Trading Parameters & Risk Management

**Last Updated**: February 15, 2026  
**Trading Mode**: Paper Trading (Alpaca)  
**Strategy**: Bracket Orders with Automatic Stop Loss & Take Profit

---

## 🎯 Default Risk Parameters

### Standard Bracket Order Settings
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Stop Loss** | -10% from entry | Limits downside risk |
| **Take Profit** | +20% from entry | 2:1 reward-to-risk ratio |
| **Risk/Reward** | 2:1 | Favorable odds for profitability |
| **Time in Force** | GTC (Good-Til-Cancelled) | Orders remain active until filled or cancelled |
| **Order Type** | Limit (for entry) | Control exact entry price |

### Position Sizing Guidelines
- **Maximum per trade**: 10% of portfolio value
- **Total exposure**: No more than 5 positions simultaneously
- **Minimum liquidity**: Only trade stocks with >500K daily volume

---

## 📊 Current Active Positions

### TURB (Pending)
```
Symbol:         TURB
Status:         PENDING BUY ORDER
Quantity:       2,000 shares
Entry Price:    $0.6881 (limit)
Stop Loss:      $0.6193 (-10%)
Take Profit:    $0.8257 (+20%)

Cost:           $1,376.20
Max Risk:       $137.60 (10% of cost)
Max Reward:     $275.20 (20% of cost)
R/R Ratio:      2:1
```

**Order Details**:
- Order ID: `2ca59420-4c0c-49b6-a6be-fd060c6eac34`
- Order Status: `new` (unfilled - waiting for price)
- Bracket Type: Full bracket (entry + stop + profit)
- Protection: Automatic upon fill

### SUPX (Existing Position)
```
Symbol:         SUPX  
Status:         OPEN POSITION
Quantity:       167 shares (estimated)
Current Price:  ~$19.66
Protection:     Separate stop/profit orders needed
```

**Recommended Protection**:
- Stop Loss: $17.69 (-10% from current)
- Take Profit: $23.59 (+20% from current)

---

## 🛡️ Risk Management Rules

### 1. Mandatory Stop Loss
✅ **RULE**: Every position MUST have a stop loss
- Bracket orders include automatic stop loss
- Never disable stop loss protection
- Stop loss set at order entry, not after

### 2. Position Limits
- **Single Position**: Max 15% of account value
- **Total Exposure**: Max 80% of account value
- **Cash Reserve**: Maintain minimum 20% cash

### 3. Daily Loss Limit
- **Max Daily Loss**: 5% of account value
- **Action**: Stop trading if limit hit
- **Reset**: Daily loss limit resets at market open

### 4. Trade Frequency
- **Max Trades/Day**: 10 (paper trading)
- **Max Trades/Week**: 25 (paper trading)
- **Cool Down**: 30 minutes between loss trades

---

## 📈 Entry Criteria

### Technical Requirements
- [ ] Price above 50-day moving average (uptrend)
- [ ] Volume above 20-day average (liquidity)
- [ ] RSI between 30-70 (not overbought/oversold)
- [ ] Support level identified for stop loss placement

### Fundamental Requirements
- [ ] Market cap > $50M (avoid penny stocks)
- [ ] Trading volume > 500K shares/day
- [ ] No pending bankruptcy/delisting
- [ ] Positive news sentiment (optional)

### Order Entry Best Practices
1. Use **limit orders** to control entry price
2. Set limit slightly below ask for buys
3. Set limit slightly above bid for sells
4. Use **GTC** orders for bracket protection

---

## 🚪 Exit Criteria

### Automatic Exits (Bracket Orders)
1. **Stop Loss Triggered** (-10%): Automatic sell at stop price
2. **Take Profit Hit** (+20%): Automatic sell at profit target
3. **Order Filled**: Protection activates immediately

### Manual Exit Conditions
Consider manual exit if:
- Fundamental thesis changes (earnings miss, bad news)
- Technical break (support violated without stop hit)
- Better opportunity identified (capital reallocation)
- Market-wide crash (risk-off scenario)

### Partial Exits
For large positions (>$5,000):
- Exit 50% at +10% gain (secure partial profit)
- Let remaining 50% run to +20% target
- Move stop to breakeven after +10% gain

---

## 🔧 Bracket Order Configuration

### Standard Bracket
```python
alpaca.place_bracket_order(
    symbol="TICKER",
    qty=quantity,
    side="buy",
    order_type="limit",
    limit_price=entry_price,
    take_profit_limit_price=entry_price * 1.20,  # +20%
    stop_loss_stop_price=entry_price * 0.90,     # -10%
    time_in_force="gtc"
)
```

### Aggressive Bracket (Higher Risk/Reward)
```python
# 2.5:1 R/R ratio
take_profit = entry_price * 1.25  # +25%
stop_loss = entry_price * 0.90    # -10%
```

### Conservative Bracket (Lower Risk/Reward)
```python
# 1.5:1 R/R ratio
take_profit = entry_price * 1.15  # +15%
stop_loss = entry_price * 0.90    # -10%
```

---

## 📊 Performance Metrics

### Target Performance
| Metric | Target | Notes |
|--------|--------|-------|
| **Win Rate** | > 50% | More wins than losses |
| **Avg Win/Loss** | > 2:1 | Wins larger than losses |
| **Monthly Return** | 5-10% | Realistic target |
| **Max Drawdown** | < 15% | Stop trading if exceeded |
| **Sharpe Ratio** | > 1.0 | Risk-adjusted returns |

### Review Schedule
- **Daily**: Review open positions and P&L
- **Weekly**: Calculate win rate and total P&L
- **Monthly**: Full performance review and strategy adjustment
- **Quarterly**: Backtesting and parameter optimization

---

## 🚨 Emergency Procedures

### Market Crash (>5% drop)
1. Close all open positions immediately
2. Cancel all pending orders
3. Move to 100% cash
4. Wait for market stabilization (3-5 days)

### Technical Failure
1. Check Alpaca API status: https://status.alpaca.markets/
2. Verify internet connection
3. Manually manage positions via Alpaca dashboard
4. Contact support if unable to close positions

### Stop Loss Failure
1. Place manual market order immediately
2. Document failure incident
3. Report to Alpaca support
4. Review all open positions for stop loss status

---

## 🔍 Pre-Trade Checklist

Before placing any trade:

- [ ] Account has sufficient buying power
- [ ] Stop loss and take profit levels calculated
- [ ] Position size within risk limits (max 15% of account)
- [ ] Entry price justified by technical/fundamental analysis
- [ ] Bracket order configured correctly
- [ ] Discord notifications enabled (optional)
- [ ] MySQL logging enabled (optional)
- [ ] Market hours confirmed (avoid after-hours unless intended)

---

## 📝 Trade Documentation Template

For each trade, document:

```
Date: YYYY-MM-DD
Symbol: TICKER
Entry Price: $X.XX
Quantity: XXX shares
Stop Loss: $X.XX (-10%)
Take Profit: $X.XX (+20%)

Entry Reason:
- Technical: [Chart pattern, indicator signals]
- Fundamental: [News, earnings, catalyst]

Strategy: [Bracket order, momentum, breakout]
Risk: $XXX (10% of cost)
Reward: $XXX (20% of cost)

Exit:
- Date: YYYY-MM-DD
- Exit Price: $X.XX
- P&L: $XXX (+/- X%)
- Exit Reason: [Stop loss, take profit, manual]

Lessons Learned:
[What worked, what didn't]
```

---

## 📚 Related Documentation

- [TURB_ACTION_GUIDE.md](../TURB_ACTION_GUIDE.md) - TURB-specific trading guide
- [BRACKET_ORDER_DEPLOYMENT.md](../BRACKET_ORDER_DEPLOYMENT.md) - Technical implementation
- [DISCORD_NOTIFICATIONS.md](DISCORD_NOTIFICATIONS.md) - Alert setup
- [TRADE_LOGGING_SETUP.md](TRADE_LOGGING_SETUP.md) - Database tracking

---

## 💡 Resources

- **Alpaca API Docs**: https://alpaca.markets/docs/
- **Risk Management**: https://www.investopedia.com/risk-management/
- **Position Sizing**: https://www.investopedia.com/position-sizing-calculator/
- **R/R Ratio**: https://www.investopedia.com/risk-reward-ratio/
