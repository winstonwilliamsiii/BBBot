# Prediction Analytics - Dual Implementation

## 🎯 Two Implementations Available

### 1. **Production** (Railway-ready, Bentley_Bot port 3306)
- **Entry:** `main.py`
- **DB:** SQLAlchemy with connection pooling
- **Target:** Bentley_Bot database, mansa_quant schema
- **Features:** Async operations, robust error handling, Railway orchestration

**Files:**
```
prediction_analytics/
├── main.py                    # Production orchestrator
├── config.py                  # Production config (Bentley_Bot)
├── services/
│   ├── db.py                  # SQLAlchemy engine
│   ├── polymarket_client.py   # Async Polymarket client
│   ├── kalshi_client.py       # Async Kalshi with WebSocket
│   ├── probability_engine.py  # Multi-method probability engine
│   └── sentiment_engine.py    # Production sentiment engine
```

**Run:**
```bash
python prediction_analytics/main.py
```

---

### 2. **Demo/Testing** (Simplified, Demo_Bots port 3307)
- **Entry:** `demo_main.py`
- **DB:** mysql.connector (simpler, no pooling)
- **Target:** Demo_Bots database (localhost testing)
- **Features:** Synchronous, lightweight, TextBlob sentiment

**Files:**
```
prediction_analytics/
├── demo_main.py               # Demo orchestrator
├── config_dual.py             # Dual config (Demo_Bots + Bentley_Bot)
├── services/
│   ├── demo_db.py             # mysql.connector layer
│   ├── demo_polymarket.py     # Sync Polymarket client (requests)
│   ├── demo_kalshi.py         # Sync Kalshi client (requests)
│   ├── demo_probability.py    # Simple midpoint probability
│   └── demo_sentiment.py      # TextBlob sentiment
```

**Run:**
```bash
# Set environment variables for Demo_Bots
export DEMO_MYSQL_HOST=127.0.0.1
export DEMO_MYSQL_PORT=3307
export DEMO_MYSQL_USER=root
export DEMO_MYSQL_PASSWORD=your_password
export DEMO_MYSQL_DB=Demo_Bots

python prediction_analytics/demo_main.py
```

---

## 🔧 Configuration

### Demo Environment (.env.demo)
```env
DEMO_MYSQL_HOST=127.0.0.1
DEMO_MYSQL_PORT=3307
DEMO_MYSQL_USER=root
DEMO_MYSQL_PASSWORD=password
DEMO_MYSQL_DB=Demo_Bots
KALSHI_API_KEY=your_key_id
KALSHI_PRIVATE_KEY=your_private_key
```

### Production Environment (Railway)
```env
MYSQL_HOST=<railway-host>
MYSQL_PORT=3306
MYSQL_USER=bentley_user
MYSQL_PASSWORD=<secret>
MYSQL_DB=Bentley_Bot
KALSHI_API_KEY=<key-id>
KALSHI_PRIVATE_KEY=<private-key>
```

---

## 📊 Database Schema

Both implementations use the same schema:
- `prediction_probabilities` - Implied probability calculations
- `sentiment_signals` - Sentiment scores and strengths

**Demo_Bots:** Testing/development on localhost:3307
**Bentley_Bot:** Production on Railway port 3306

---

## 🚀 Deployment Strategy

1. **Local Testing:** Use `demo_main.py` → Demo_Bots (port 3307)
2. **Production:** Use `main.py` → Bentley_Bot (port 3306) on Railway
3. **Railway:** Deploy production version with Dockerfile

---

## 📦 Dependencies

All dependencies in `requirements.txt`:
- **Production:** aiohttp, websockets, SQLAlchemy, PyMySQL, numpy, pandas
- **Demo:** mysql-connector-python, requests, textblob, python-dotenv

Install all:
```bash
pip install -r prediction_analytics/requirements.txt
```

---

## 🔍 Testing Workflow

```bash
# 1. Test locally with Demo_Bots
python prediction_analytics/demo_main.py

# 2. Validate data in Demo_Bots
mysql -h 127.0.0.1 -P 3307 -u root -p Demo_Bots
> SELECT * FROM prediction_probabilities LIMIT 10;

# 3. Deploy to Railway (production)
git push origin feature/prediction-analytics
# Railway auto-deploys main.py → Bentley_Bot
```

---

## 💡 When to Use Which

| Use Case | Implementation |
|----------|---------------|
| Local development/testing | `demo_main.py` |
| Railway production deployment | `main.py` |
| Quick prototype | `demo_main.py` |
| High-scale async operations | `main.py` |
