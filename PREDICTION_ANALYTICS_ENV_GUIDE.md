# Environment Configuration for Prediction Analytics Branch

**Branch:** `feature/prediction-analytics`

## 🎯 Which .env File to Use?

### For Railway Deployment
**File:** `.env.railway-prediction`

This file maps all required secrets for the prediction analytics microservices:
- Bentley_Bot database credentials
- Polymarket/Kalshi API keys
- Optional: Twitter, Discord, OpenAI for sentiment analysis
- Alpaca broker credentials for trading

**Step 1: Copy Template**
```bash
cp .env.railway-prediction .env.railway-prediction.local  # for local testing
```

**Step 2: Fill in Secrets**
Edit `.env.railway-prediction.local` with:
- `KALSHI_API_KEY` - Get from https://kalshi.com/api
- `TWITTER_API_KEY` - Optional, for social sentiment
- `DISCORD_BOT_TOKEN` - Optional, for Discord discussions
- `OPENAI_API_KEY` - Optional, for advanced NLP
- `ALPACA_API_KEY` + `ALPACA_SECRET` - From https://alpaca.markets

**Step 3: Add to Railway Dashboard**
1. Go to Railway → Your Project → Variables
2. Add each variable from `.env.railway-prediction` as a new secret
3. Railway will inject them at runtime

---

### For Local Testing (Demo_Bots on port 3307)
**File:** `.env.development`

Demo mode uses simplified setup:
```env
DEMO_MYSQL_HOST=127.0.0.1
DEMO_MYSQL_PORT=3307
DEMO_MYSQL_USER=root
DEMO_MYSQL_PASSWORD=your_password
DEMO_MYSQL_DB=Demo_Bots
```

**Run:**
```bash
python prediction_analytics/demo_main.py
```

---

## 📋 Complete Variable Reference

| Variable | Railway Env | Local Env | Example | Required |
|----------|-----------|----------|---------|----------|
| `BENTLEY_DB_HOST` | ✅ | ❌ | `bentley-db.railway.internal` | Yes |
| `BENTLEY_DB_PORT` | ✅ | ❌ | `3306` | Yes |
| `BENTLEY_DB_USER` | ✅ | ❌ | `bentley_user` | Yes |
| `BENTLEY_DB_PASSWORD` | ✅ | ❌ | `***secret***` | Yes |
| `KALSHI_API_KEY` | ✅ | ✅ | `pk_live_...` | Yes |
| `TWITTER_API_KEY` | ✅ | ✅ | `Bearer ***` | No |
| `DISCORD_BOT_TOKEN` | ✅ | ✅ | `MTA0...` | No |
| `OPENAI_API_KEY` | ✅ | ✅ | `sk-...` | No |
| `ALPACA_API_KEY` | ✅ | ✅ | `PK...` | Yes (for trading) |
| `ALPACA_SECRET` | ✅ | ✅ | `***secret***` | Yes (for trading) |

---

## 🚀 Quick Setup for Railway

### Option A: Manual Setup (Recommended for security)
1. **Create `.env.railway-prediction.local`** (local copy, DO NOT commit)
2. **Fill in secrets manually** in Railway Dashboard UI
3. **Deploy**: `git push origin feature/prediction-analytics`
4. Railway auto-deploys with variables from dashboard

### Option B: Using .env File in Railway
1. Store `.env.railway-prediction` in Railway's "Config" tab
2. Railway reads and applies variables automatically

---

## ⚠️ Important Security Notes

- **Never commit secrets** to git
- `.env.railway-prediction` is a TEMPLATE with placeholder values
- Create `.env.railway-prediction.local` for actual secrets (add to `.gitignore`)
- Railway Dashboard is the secure source of truth for production secrets

---

## 📚 Reference Files

| File | Purpose |
|------|---------|
| `.env.railway-prediction` | Template for Railway env vars |
| `.env.development` | Local development (Demo_Bots) |
| `.env.production` | Streamlit Cloud production |
| `prediction_analytics/config.py` | Production config (reads Railway vars) |
| `prediction_analytics/config_dual.py` | Demo config (reads local vars) |

---

## ✅ Pre-Deployment Checklist

- [ ] Gather all API keys (Kalshi, Twitter, Discord, OpenAI, Alpaca)
- [ ] Create `.env.railway-prediction.local` with actual values
- [ ] Test locally with `python prediction_analytics/demo_main.py`
- [ ] Add variables to Railway Dashboard
- [ ] Deploy: `git push origin feature/prediction-analytics`
- [ ] Monitor Railway logs for startup errors
- [ ] Validate data in Bentley_Bot database
