# QUICK START - Bentley Budget Bot Pipeline

## 🚀 Quick Setup (5 Steps)

### Step 1: Run Automated Setup
```powershell
.\scripts\setup\complete_pipeline_setup.ps1
```
This verifies prerequisites and configures Airflow connections.

### Step 2: Configure Airbyte Connections

**Start Airbyte**:
```bash
cd airbyte
docker-compose up -d
```

**Access UI**: http://localhost:8000

**Create 3 connections**:
1. **Tiingo → prices_daily** (Daily 6 PM)
2. **AlphaVantage → fundamentals_raw** (Weekly)
3. **StockTwits → sentiment_msgs** (Every 15 min)

📖 Full instructions: [docs/AIRBYTE_SETUP.md](docs/AIRBYTE_SETUP.md)

### Step 3: Load Initial Data

**Trigger Airbyte syncs** (manual in UI):
- Click each connection
- Click "Sync now"
- Wait for completion

**Verify data loaded**:
```bash
docker exec bentley-mysql mysql -uroot -proot bbbot1 -e "
SELECT 'prices_daily' AS table_name, COUNT(*) FROM prices_daily
UNION ALL
SELECT 'fundamentals_raw', COUNT(*) FROM fundamentals_raw
UNION ALL
SELECT 'sentiment_msgs', COUNT(*) FROM sentiment_msgs;"
```

### Step 4: Run dbt Pipeline

```bash
cd dbt_project

# Run all models (staging → marts)
dbt run --profiles-dir .

# Test data quality
dbt test --profiles-dir .

# Verify marts table
cd ..
docker exec bentley-mysql mysql -uroot -proot bbbot1 -e "SELECT COUNT(*) FROM marts.features_roi;"
```

### Step 5: Enable Airflow DAGs

**Access Airflow**: http://localhost:8080 (admin/admin)

**Enable 2 DAGs**:
1. ✅ `dbt_transformation_pipeline` (Daily 8 AM)
2. ✅ `stock_pipeline_comprehensive` (Daily 9 AM)

**Trigger manual run**:
- Click DAG name → "Trigger DAG" button
- Monitor in Graph View

---

## ✅ Verification Checklist

After setup, verify everything is working:

- [ ] MySQL tables exist (4 raw tables)
- [ ] Airbyte connections configured (3 connections)
- [ ] Raw tables have data (prices_daily > 0 rows)
- [ ] dbt models run successfully (staging + marts)
- [ ] marts.features_roi table exists and has data
- [ ] Airflow connections work (mysql_bbbot1)
- [ ] Airflow DAGs enabled and running
- [ ] MLFlow experiments logged (check http://localhost:5000)

---

## 📊 Pipeline Flow

```
6:00 PM  → Airbyte: Tiingo sync (prices_daily)
7:00 PM  → Airflow: Calculate technicals (optional)
8:00 AM  → Airflow: dbt transformation pipeline
           ↳ Staging models (stg_prices, stg_fundamentals, stg_sentiment)
           ↳ Marts models (features_roi with ML features)
9:00 AM  → Airflow: Stock pipeline comprehensive
           ↳ Validate raw data
           ↳ Log features to MLFlow
           ↳ Train ROI prediction model

Every 15 min → Airbyte: StockTwits sentiment
Weekly       → Airbyte: AlphaVantage fundamentals
```

---

## 🔧 Key Commands

### Check Services
```bash
# Docker containers
docker ps

# MySQL
docker exec bentley-mysql mysql -uroot -proot -e "SELECT 1;"

# Airflow
curl http://localhost:8080/health

# MLFlow
curl http://localhost:5000/health

# Airbyte
curl http://localhost:8000/health
```

### dbt Commands
```bash
cd dbt_project

# Test connection
dbt debug --profiles-dir .

# Run models
dbt run --profiles-dir .

# Test data quality
dbt test --profiles-dir .

# Generate docs
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .
```

### MySQL Queries
```bash
# Check raw tables
docker exec bentley-mysql mysql -uroot -proot bbbot1 -e "SHOW TABLES;"

# Check marts tables
docker exec bentley-mysql mysql -uroot -proot bbbot1 -e "SHOW TABLES FROM marts;"

# View sample data
docker exec bentley-mysql mysql -uroot -proot bbbot1 -e "SELECT * FROM marts.features_roi LIMIT 5;"
```

### Airflow Commands
```bash
# List DAGs
docker exec airflow-webserver airflow dags list

# Test DAG
docker exec airflow-webserver airflow dags test dbt_transformation_pipeline 2025-12-03

# List connections
docker exec airflow-webserver airflow connections list
```

---

## 🆘 Troubleshooting

### Issue: Airbyte sync fails
**Check**: API keys, MySQL connection, table permissions
**Fix**: Review Airbyte logs in UI

### Issue: dbt models fail
**Check**: MySQL port (3307 from host), profiles.yml configuration
**Fix**: Run `dbt debug --profiles-dir .`

### Issue: Airflow DAG import errors
**Check**: bbbot1_pipeline module accessible
**Fix**: `docker exec airflow-webserver pip install -e /opt/airflow/bbbot1_pipeline`

### Issue: No MLFlow experiments
**Check**: MLFlow tracking URI configured
**Fix**: Set `MLFLOW_TRACKING_URI=mysql+pymysql://root:root@127.0.0.1:3307/mlflow_db`

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [docs/COMPLETE_SETUP_GUIDE.md](docs/COMPLETE_SETUP_GUIDE.md) | **Master guide** with detailed steps |
| [docs/AIRBYTE_SETUP.md](docs/AIRBYTE_SETUP.md) | Airbyte connection configuration |
| [docs/AIRFLOW_CONNECTIONS.md](docs/AIRFLOW_CONNECTIONS.md) | Airflow setup and testing |
| [docs/DBT_ARCHITECTURE.md](docs/DBT_ARCHITECTURE.md) | dbt models and architecture |
| [docs/AIRBYTE_RAW_TABLES.md](docs/AIRBYTE_RAW_TABLES.md) | Raw table schemas |
| [DATA_PIPELINE_REFERENCE.md](DATA_PIPELINE_REFERENCE.md) | Quick reference guide |

---

## 🎯 Success Criteria

Pipeline is working correctly when:

1. ✅ Raw tables populated daily (prices_daily, fundamentals_raw)
2. ✅ dbt models run successfully (marts.features_roi has data)
3. ✅ Airflow DAGs execute without errors
4. ✅ MLFlow experiments logged with metrics
5. ✅ Streamlit dashboard displays current data

---

## 🌟 What's Next?

After completing quick start:

1. **Monitor pipeline**: Check Airflow/Airbyte/MLFlow daily
2. **Add more tickers**: Update Airbyte connection configurations
3. **Tune models**: Adjust MLFlow training parameters
4. **Create alerts**: Set up notifications for failures
5. **Optimize dbt**: Add incremental models for performance
6. **Extend features**: Add more technical indicators or data sources

### 💼 Bonus: Automated Trading (Optional)

**Execute trades** based on ML signals across 3 brokers:
- **Webull** → Equities & ETFs
- **Interactive Brokers (IBKR)** → Forex, Futures, Commodities
- **Binance** → Cryptocurrency

Setup guide: [docs/BROKER_TRADING_SETUP.md](docs/BROKER_TRADING_SETUP.md)

Quick install:
```bash
pip install webull ibapi python-binance
```

---

**Need help?** Check [docs/COMPLETE_SETUP_GUIDE.md](docs/COMPLETE_SETUP_GUIDE.md) for detailed instructions.
