# Prediction Analytics - Railway Deployment Guide
**Branch:** `feature/prediction-analytics`

## 🚀 Railway Service Architecture

### Microservices Deployed:
1. **bentley-ingestion-worker** - Polymarket/Kalshi data feeds (every 10 min)
2. **bentley-probability-engine** - Probability calculations (every 15 min)
3. **bentley-sentiment-analyzer** - NLP sentiment analysis (every 30 min)
4. **bentley-bot-consumer** - AI trade bot (continuous)

## 📦 Deployment Steps

### 1. **Push Branch to GitHub**
```bash
git push origin feature/prediction-analytics
```

### 2. **Railway Configuration**
Railway will auto-detect `railway/prediction-analytics-service.yml`

**Required Environment Variables in Railway Dashboard:**
```env
BENTLEY_DB_HOST=<railway-mysql-host>
BENTLEY_DB_USER=bentley_user
BENTLEY_DB_PASSWORD=<secret>
KALSHI_API_KEY=<kalshi-key>
KALSHI_PRIVATE_KEY=<kalshi-private-key>
ALPACA_API_KEY=<alpaca-key>
ALPACA_SECRET=<alpaca-secret>
```

### 3. **Database Migration**
```bash
# SSH into Railway or run locally against Railway DB
railway run python -c "
import pymysql
conn = pymysql.connect(host='<host>', user='<user>', password='<pass>', database='Bentley_Bot')
with open('migrations/20260126_prediction_analytics.sql') as f:
    conn.cursor().execute(f.read())
conn.commit()
"
```

### 4. **Service Health Checks**
Each service exposes `/health` endpoint:
- `https://bentley-ingestion-worker.up.railway.app/health`
- `https://bentley-probability-engine.up.railway.app/health`
- `https://bentley-sentiment-analyzer.up.railway.app/health`
- `https://bentley-bot-consumer.up.railway.app/health`

## 📊 Appwrite Investor Dashboard

### Deploy Appwrite Function:
```bash
cd appwrite/functions/prediction-dashboard
appwrite deploy function
```

**Function Configuration:**
- **Runtime:** Python 3.11
- **Entrypoint:** main.py
- **Path:** `/api/prediction-dashboard`
- **Timeout:** 15s
- **Environment Variables:**
  - BENTLEY_DB_HOST
  - BENTLEY_DB_PORT=3306
  - BENTLEY_DB_USER
  - BENTLEY_DB_PASSWORD

### API Endpoints:

#### **GET /api/prediction-dashboard**
Fetch dashboard overview with top predictions, bot performance, and active signals.

**Query Parameters:**
- `limit` (default: 10) - Number of top predictions
- `min_confidence` (default: 0.7) - Minimum confidence threshold
- `bot_id` (default: passive-income-bot-v1)
- `days` (default: 30) - Performance period
- `signals_limit` (default: 20) - Number of active signals

**Response:**
```json
{
  "timestamp": "2026-01-26T10:30:00Z",
  "top_predictions": [...],
  "bot_performance": {
    "bot_id": "passive-income-bot-v1",
    "total_trades": 45,
    "win_rate": 68.89,
    "total_profit_loss": 1250.75,
    "daily_performance": [...]
  },
  "active_signals": [...]
}
```

#### **GET /api/contract/{contract_id}**
Get detailed information about a specific contract.

**Response:**
```json
{
  "contract_id": "POLY_BTC_2026Q1",
  "contract_name": "Bitcoin above $100k by Q1 2026",
  "source": "Polymarket",
  "implied_probability": 72.50,
  "confidence_score": 0.88,
  "sentiment_score": 0.65,
  "bot_trades_count": 3,
  "total_bot_pnl": 45.30
}
```

## 🤖 Bot Consumer Configuration

### Paper Trading Mode (Default)
```env
PAPER_TRADING=true
BOT_ID=passive-income-bot-v1
CONFIDENCE_THRESHOLD=0.75
MIN_SENTIMENT_SCORE=0.3
MAX_POSITION_SIZE=100.00
```

### Live Trading Mode
```env
PAPER_TRADING=false
TRADE_ENABLED=true
# + Broker API keys
```

## 📈 Data Flow

```
Polymarket/Kalshi APIs
    ↓ (every 10 min)
Ingestion Worker → event_contracts + orderbook_data
    ↓ (every 15 min)
Probability Engine → prediction_probabilities
    ↓ (every 30 min)
Sentiment Analyzer → sentiment_signals + nlp_sentiment_data
    ↓ (continuous)
Bot Consumer → passive_income_logs
    ↓
Appwrite Dashboard → Investor Visualization
```

## 🔍 Monitoring

### Railway Logs:
```bash
railway logs -s bentley-ingestion-worker
railway logs -s bentley-probability-engine
railway logs -s bentley-sentiment-analyzer
railway logs -s bentley-bot-consumer
```

### Database Queries:
```sql
-- Check recent predictions
SELECT * FROM mansa_quant.prediction_probabilities 
ORDER BY created_at DESC LIMIT 10;

-- Check bot performance
SELECT * FROM mansa_quant.passive_income_logs
WHERE bot_id = 'passive-income-bot-v1'
ORDER BY execution_timestamp DESC LIMIT 20;

-- Daily bot metrics
SELECT * FROM mansa_quant.bot_performance_metrics
WHERE bot_id = 'passive-income-bot-v1'
ORDER BY date_utc DESC;
```

## 🎯 Testing Checklist

- [ ] Deploy Railway services
- [ ] Validate ingestion worker fetches Polymarket/Kalshi data
- [ ] Confirm probability engine calculates probabilities
- [ ] Verify sentiment analyzer stores NLP results
- [ ] Test bot consumer makes paper trades
- [ ] Deploy Appwrite dashboard function
- [ ] Validate dashboard API returns correct data
- [ ] Monitor logs for errors

## 🚢 Production Merge

Once validated in `feature/prediction-analytics`:
1. Create PR to `main`
2. Run full test suite
3. Review Railway preview deployment
4. Merge to main → Auto-deploy to production (bentley-core)
