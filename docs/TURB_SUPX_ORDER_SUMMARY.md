# Order Placement Summary - TURB & SUPX

**Date**: February 13, 2026  
**Account**: Alpaca Paper Trading  
**Status**: ✅ PARTIALLY COMPLETE

---

## ✅ ORDER 1: TURB - COMPLETE SUCCESS

**Bracket Order Placed**: `2ca59420-4c0c-49b6-a6be-fd060c6eac34`

### Order Details:
- **Symbol**: TURB
- **Quantity**: 2,000 shares
- **Entry Price**: $0.6881 (LIMIT order)
- **Order Type**: Bracket (automatic stop loss & take profit)
- **Status**: ✅ Accepted (waiting to fill at limit price)

### Risk Management:
- **Stop Loss**: $0.6193 (-10% from entry)
- **Take Profit**: $0.8257 (+20% from entry)
- **Cost**: $1,376.20
- **Risk**: $137.60
- **Reward**: $275.20
- **R/R Ratio**: 2.00:1 ✅

### What Happens Next:
1. Order fills when TURB price reaches $0.6881
2. Stop loss automatically becomes active at $0.6193
3. Take profit automatically becomes active at $0.8257
4. Whichever hits first will execute, canceling the other

---

## ⚠️ ORDER 2: SUPX - PARTIAL (Stop Loss Only)

**Stop Loss Order**: `2577251c-2393-406b-8efc-b1b26e713b8a`

### Current Position:
- **Symbol**: SUPX
- **Quantity**: 1 share
- **Avg Entry**: $15.64
- **Current Price**: $16.38
- **Unrealized P/L**: +$0.74 (+4.73%)

### Protection Added:
- ✅ **Stop Loss**: $14.74 (-10% from current price)
- ❌ **Take Profit**: NOT PLACED (see issue below)

### Issue Encountered:
Alpaca API returned **403 Forbidden** when attempting to place take profit order.

**Root Cause**: The stop loss order already "reserves" the 1 share for selling. Alpaca doesn't allow multiple overlapping sell orders on the same shares (you can't have both a stop order and a limit order trying to sell the same share).

### Solution Options:

**Option 1: Manual Monitoring** (Current State)
- Keep the stop loss at $14.74
- Manually sell at profit target ($19.66) if reached
- Risk: You might miss the profit target

**Option 2: Cancel & Replace with Bracket**
```bash
# Cancel the stop loss
python -c "from frontend.components.alpaca_connector import AlpacaConnector; import os; alpaca = AlpacaConnector(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_SECRET_KEY'), True); alpaca.cancel_order('2577251c-2393-406b-8efc-b1b26e713b8a'); print('Stop loss cancelled')"

# Then close and re-enter with bracket order
# (This resets your entry price and realizes current profit)
```

**Option 3: Accept Stop Loss Only** (Recommended)
- Keep current protection
- You have downside protection at -10%
- Monitor and manually take profit at +20%
- This is common for existing positions

---

## 📊 Current Account Status

### Open Positions:
1. **SUPX**: 1 share @ $16.38 (Avg entry: $15.64)
   - Stop Loss: ✅ $14.74
   - Take Profit: ❌ Manual only

### Open Orders:
1. **TURB**: BUY 2,000 @ $0.6881 (bracket order ✅)
   - Stop Loss leg: $0.6193
   - Take Profit leg: $0.8257
   
2. **TURB**: BUY 2,000 @ $0.6881 (duplicate bracket order ✅)
   - Stop Loss leg: $0.6193
   - Take Profit leg: $0.8257

3. **SPY**: BUY 1 @ market (bracket order ✅)

4. **SUPX**: SELL 1 @ $14.74 stop (stop loss only ⚠️)

### Buying Power: $196,551.86

---

## ⚠️ IMPORTANT NOTES

### Duplicate TURB Orders
You have **TWO** identical TURB bracket orders for 2,000 shares each!

- If both fill, you'll buy **4,000 shares** instead of 2,000
- Total cost would be $2,752.40
- Recommendation: **Cancel one order** to avoid double position

To cancel a duplicate TURB order:
```bash
# Check which order IDs
python -c "from frontend.components.alpaca_connector import AlpacaConnector; import os; alpaca = AlpacaConnector(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_SECRET_KEY'), True); orders = alpaca.get_orders(); turb = [o for o in orders if o.get('symbol')=='TURB']; print('\\n'.join([f\"{o.get('id')}: {o.get('qty')} @ {o.get('limit_price')}\" for o in turb]))"

# Cancel one (use actual order ID from above)
python -c "from frontend.components.alpaca_connector import AlpacaConnector; import os; alpaca = AlpacaConnector(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_SECRET_KEY'), True); alpaca.cancel_order('ORDER_ID_HERE'); print('Order cancelled')"
```

### SUPX Take Profit
For existing positions, Alpaca's API limitation prevents placing both stop loss AND take profit as separate orders. Your options:

1. **Keep as-is**: Stop loss protects downside, manual monitoring for upside
2. **Cancel stop loss**: Add take profit instead (protects upside, not downside)
3. **No action**: Just hold and monitor

**Recommendation**: Keep the stop loss. It protects your capital, which is more important than capturing every profit.

---

## ✅ Next Steps

1. **Cancel duplicate TURB order** (recommended)
2. **Monitor TURB**: Order fills when price reaches $0.6881
3. **Monitor SUPX**: You have stop loss protection at $14.74
4. **Set price alert**: Get notified when SUPX reaches $19.66 to manually take profit

---

## 🎯 Summary

| Order | Status | Entry | Stop Loss | Take Profit | R/R |
|-------|--------|-------|-----------|-------------|-----|
| TURB | ✅ Pending | $0.6881 | $0.6193 | $0.8257 | 2:1 |
| SUPX | ⚠️ Partial | $15.64 | $14.74 | Manual | — |

**Risk Management Score**: 8/10
- TURB fully protected ✅
- SUPX downside protected ⚠️
- Action required: Cancel duplicate TURB order
