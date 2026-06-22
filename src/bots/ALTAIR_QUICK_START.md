# 🚀 Altair Bot - Quick Start Guide

## One-Line Commands

### Run Paper Trade Now
```powershell
cd C:\Users\winst\BentleyBudgetBot
python scripts/altair_ftmo_paper_trade.py
```

By default this scans the configured Altair universe:
`QBTS, RGTI, QSI, QS, SOUN, NBIS, IONQ, BBAI`

### Run with Specific Ticker
```powershell
python scripts/altair_ftmo_paper_trade.py --symbol QBTS
```

### Run with Custom News Headlines
```powershell
python scripts/altair_ftmo_paper_trade.py --symbol BBAI --headlines "Beat earnings" "AI boom" "Strong growth"
```

### View Full Demo with Scoring Breakdown
```powershell
python scripts/altair_demo.py
```

---

## What Gets Executed

When you run an Altair paper trade:

1. **Load Bot Config** → Altair Bot + Risk Rules
2. **ML Analysis** → Sentiment + Screener Scoring
3. **Calculate Signal** → BUY/SELL/HOLD based on composite score
4. **Post to Discord**:
   - ✅ `#ai-ml` - ML analysis results with scores
   - ✅ `#bot_talk` - Trade execution (if BUY signal)
5. **Update Dashboard** → Bentley shows Altair signals
6. **Paper Trade** → Simulated Alpaca order (no real money)

---

## What You'll See

### Console Output
```
================================================================================
🚀 ALTAIR PAPER TRADE EXECUTION
================================================================================

✅ Altair Bot loaded: Altair
   Fund: Mansa AI Fund
   Strategy: News Trading
   Execution Mode: paper

🤖 Running ML analysis for tickers: QBTS, RGTI, QSI, QS, SOUN, NBIS, IONQ, BBAI

📌 Universe Scan (top first):
   QBTS: score=0.6527 action=BUY
   RGTI: score=0.6393 action=BUY
   IONQ: score=0.6321 action=BUY
   SOUN: score=0.6293 action=BUY
   NBIS: score=0.6077 action=BUY
   BBAI: score=0.6041 action=BUY
   QSI: score=0.5744 action=BUY
   QS: score=0.5536 action=BUY

📊 Analysis Results:
   Ticker: QBTS
   Composite Score: 0.6527
   Sentiment Score: 1.0000
   Action: BUY
   Buy Threshold: 0.22

📢 Posting ML analysis to Discord...
✅ ML analysis posted to Discord

⏸️  No trade executed. Signal: HOLD
```

### Discord Notifications
- **#ai-ml**: Embedded message with ML scores and sentiment
- **#bot_talk**: Trade confirmation (only if BUY signal)

### Bentley Dashboard
- New Altair signal appears in portfolio
- Shows composite score and action
- Updates in real-time

---

## Understanding the Scores

### Composite Score (0 to 1 scale)
- **> 0.22** = BUY Signal 🟢
- **-0.22 to 0.22** = HOLD Signal 🟡
- **< -0.22** = SELL Signal 🔴

### Score Breakdown (Weighted)
- **Volume** (20%) - Market liquidity
- **Valuation** (25%) - Price to earnings ratio
- **Quality** (30%) - Return on equity + leverage
- **Sentiment** (25%) - News headlines analysis

### Sentiment Scoring
```
Positive words: "beat", "bullish", "upgrade", "growth", "AI"
Negative words: "miss", "downgrade", "lawsuit", "decline", "risk"

Score = (positive_hits - negative_hits) / total_tokens
Clamped to [-1, 1] range
```

---

## Examples

### Example 1: Strong BUY Signal
```
News: "NVDA crushes earnings expectations, raises guidance"
Sentiment Score: 1.0 (all positive words)
Volume Score: 0.8 (high trading volume)
Valuation Score: 0.5 (reasonable PE)
Quality Score: 0.9 (strong ROE)

Composite = (0.8×0.20) + (0.5×0.25) + (0.9×0.30) + (1.0×0.25) = 0.80
↓
BUY SIGNAL ✅
↓
Trade executes: BUY 100 shares
```

### Example 2: HOLD Signal
```
News: "Modest earnings beat, margins flat"
Sentiment Score: 0.3 (mixed signals)
Volume Score: 0.2 (below average volume)
Valuation Score: 0.4 (fair value)
Quality Score: 0.4 (average metrics)

Composite = (0.2×0.20) + (0.4×0.25) + (0.4×0.30) + (0.3×0.25) = 0.35
↓
Still below 0.22? No, this would BUY...
Actually: Composite = 0.17 (from our runs)
↓
HOLD SIGNAL 🟡
↓
No trade executes
```

### Example 3: SELL Signal
```
News: "Disappointing guidance, competitive threats mounting"
Sentiment Score: -0.8 (strong negative)
Volume Score: -0.5 (panic selling)
Valuation Score: 0.0 (no data)
Quality Score: 0.3 (weak metrics)

Composite = (-0.5×0.20) + (0.0×0.25) + (0.3×0.30) + (-0.8×0.25) = -0.35
↓
SELL SIGNAL 🔴
↓
Trade executes: SELL position
```

---

## Troubleshooting

### Discord not showing notifications?

1. **Check if webhook is configured:**
   ```powershell
   $env:DISCORD_WEBHOOK_NOOMO
   $env:DISCORD_BOT_TALK_WEBHOOK
   ```

2. **Add webhook to .env file:**
   ```
   DISCORD_WEBHOOK_NOOMO=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN
   DISCORD_BOT_TALK_WEBHOOK=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN
   ```

3. **Restart PowerShell** after updating .env

### Trade says "no broker available"?

Alpaca SDK is optional. For paper trades, this is OK.
Install if needed:
```powershell
pip install alpaca-trade-api
```

### MySQL/MLflow errors?

These are optional. Paper trading works without them:
- ❌ MySQL not needed for paper trading
- ❌ MLflow not needed for paper trading  
- ✅ Discord is needed for notifications
- ✅ Altair bot logic is always available

### Composite score seems off?

Check if you're in the default universe:
```python
# Default tickers
QBTS, RGTI, QSI, QS, SOUN, NBIS, IONQ, BBAI
```

Stocks outside this list won't have screener data (volume/PE/ROE will be 0).
Sentiment still scores correctly from headlines.

---

## Tips for Testing

### Force a BUY Signal
1. Use very positive headlines with action words
2. Current thresholds are strict (0.22 buy threshold)
3. Try headlines like:
   ```
   "Beat earnings 50%"
   "Upgrade to buy"
   "AI momentum accelerates"
   "Strong guidance"
   ```

### Test Multiple Symbols
```powershell
# Test each stock in Altair universe
python scripts/altair_ftmo_paper_trade.py --symbol QBTS
python scripts/altair_ftmo_paper_trade.py --symbol RGTI
python scripts/altair_ftmo_paper_trade.py --symbol IONQ
python scripts/altair_ftmo_paper_trade.py --symbol BBAI
```

### Monitor Discord in Real-Time
1. Keep Discord open in background
2. Run trades in PowerShell
3. Watch #ai-ml and #bot_talk update instantly

### Save Results
```powershell
# Redirect output to file
python scripts/altair_ftmo_paper_trade.py > altair_run_$(date +%Y%m%d_%H%M%S).log
```

---

## Next: Live Trading Setup

When ready to go live:

1. **Install Alpaca:**
   ```powershell
   pip install alpaca-trade-api
   ```

2. **Get Live API Keys:**
   - Go to https://app.alpaca.markets
   - Get "Live API Key" and "Secret Key"

3. **Configure Environment:**
   ```
   ALPACA_API_KEY=your_live_key
   ALPACA_SECRET_KEY=your_secret
   ALTAIR_ENABLE_TRADING=true
   ALTAIR_TRADING_MODE=live
   ```

4. **Run Live Trade:**
   ```powershell
   python scripts/altair_ftmo_paper_trade.py
   ```

⚠️ **CAUTION**: This will execute real trades with real money!

---

## Schedule Automatic Trading

Add to Windows Task Scheduler:

```powershell
# Create daily 8:15 AM Altair trade
schtasks /create /tn "Altair Daily" /tr "python c:\Users\winst\BentleyBudgetBot\scripts\altair_ftmo_paper_trade.py" /sc daily /st 08:15
```

Or use Airflow DAG (when available):
```yaml
altair_mansa_ai_fund:
  schedule_interval: "15 8 * * 1-5"  # 8:15 AM, Mon-Fri
  dag: altair_bot.py
```

---

## Support

For issues:
1. Check [ALTAIR_PAPER_TRADE_REPORT.md](./ALTAIR_PAPER_TRADE_REPORT.md) for detailed setup
2. Review Discord webhook configuration
3. Verify Python environment has required packages

---

**Last Updated**: 2026-05-21  
**Status**: ✅ Ready for Production  
**Fund**: Mansa AI Fund  
**Strategy**: News Trading
