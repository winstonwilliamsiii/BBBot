# MLflow Railway Setup - Complete Configuration

**Date:** January 14, 2026  
**Status:** ✅ COMPLETE

## Summary

Successfully created `mlflow_db` database on Railway MySQL with all 34 MLflow tracking tables initialized. The Investment Analysis page ([frontend/pages/02_📈_Investment_Analysis.py](frontend/pages/02_📈_Investment_Analysis.py)) requires MLflow for the "🔬 MLflow Experiments" tab.

## What Was Created

### 1. Railway MySQL Database
- **Database:** `mlflow_db`
- **Host:** nozomi.proxy.rlwy.net
- **Port:** 54537
- **Tables:** 34 MLflow tracking tables created via migrations
- **Experiment:** `bentley_bot_analysis` (ID: 1)

### 2. MLflow Tables Created
✅ Core tables:
- `experiments` - Experiment metadata
- `runs` - MLflow run tracking
- `metrics` - Logged metrics (PE ratio, ROI, etc.)
- `params` - Run parameters (tickers, dates)
- `tags` - Run tags and metadata
- `registered_models` - Model registry
- `model_versions` - Model versioning

📝 Supporting tables (34 total):
- `alembic_version`, `assessments`, `datasets`, `entity_associations`, `evaluation_dataset_records`, `evaluation_dataset_tags`, `evaluation_datasets`, `experiment_tags`, `input_tags`, `inputs`, `jobs`, `latest_metrics`, `logged_model_metrics`, `logged_model_params`, `logged_model_tags`, `logged_models`, `model_version_tags`, `model_version_tags`, `registered_model_aliases`, `registered_model_tags`, `scorer_versions`, `scorers`, `spans`, `trace_info`, `trace_request_metadata`, `trace_tags`, `webhook_events`, `webhooks`

## Streamlit Cloud Configuration

### Required Secrets

Add these to **Streamlit Cloud → bbbot305 → Settings → Secrets**:

```toml
# ============================================================
# MLFLOW CONFIGURATION (Railway MySQL)
# ============================================================

[mlflow]
MLFLOW_MYSQL_HOST = "nozomi.proxy.rlwy.net"
MLFLOW_MYSQL_PORT = "54537"
MLFLOW_MYSQL_DATABASE = "mlflow_db"
MLFLOW_MYSQL_USER = "root"
MLFLOW_MYSQL_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"

[mlflow_tracking]
MLFLOW_TRACKING_URI = "mysql+pymysql://root:cBlIUSygvPJCgPbNKHePJekQlClRamri@nozomi.proxy.rlwy.net:54537/mlflow_db"
```

### Complete Secrets Template

Here's your full Streamlit secrets configuration with all databases:

```toml
# ============================================================
# RAILWAY MYSQL CONNECTION (Production Cloud Database)
# ============================================================

MYSQL_HOST = "nozomi.proxy.rlwy.net"
MYSQL_PORT = "54537"
MYSQL_USER = "root"
MYSQL_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"
MYSQL_DATABASE = "railway"

# ============================================================
# BUDGET DATABASE (Plaid Transactions)
# ============================================================

BUDGET_MYSQL_HOST = "nozomi.proxy.rlwy.net"
BUDGET_MYSQL_PORT = "54537"
BUDGET_MYSQL_USER = "root"
BUDGET_MYSQL_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"
BUDGET_MYSQL_DATABASE = "mydb"

# ============================================================
# BBBOT1 DATABASE (Stock Market Data)
# ============================================================

BBBOT1_MYSQL_HOST = "nozomi.proxy.rlwy.net"
BBBOT1_MYSQL_PORT = "54537"
BBBOT1_MYSQL_USER = "root"
BBBOT1_MYSQL_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"
BBBOT1_MYSQL_DATABASE = "bbbot1"

# ============================================================
# MLFLOW DATABASE (Experiment Tracking)
# ============================================================

MLFLOW_MYSQL_HOST = "nozomi.proxy.rlwy.net"
MLFLOW_MYSQL_PORT = "54537"
MLFLOW_MYSQL_USER = "root"
MLFLOW_MYSQL_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"
MLFLOW_MYSQL_DATABASE = "mlflow_db"

MLFLOW_TRACKING_URI = "mysql+pymysql://root:cBlIUSygvPJCgPbNKHePJekQlClRamri@nozomi.proxy.rlwy.net:54537/mlflow_db"

# ============================================================
# ALPACA TRADING API (Paper Trading)
# ============================================================

ALPACA_API_KEY = "PKAYRIJUWUPO5VVWVTIWDXPRJ3"
ALPACA_SECRET_KEY = "HDegV257ex4j1Wc7C3714mVBLoyircYYMTxTozZKWeaA"
ALPACA_PAPER = "true"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

# ============================================================
# APPWRITE BACKEND
# ============================================================

APPWRITE_ENDPOINT = "https://cloud.appwrite.io/v1"
APPWRITE_PROJECT_ID = "68869ef500017ca73772"
APPWRITE_DATABASE_ID = "694481eb003c0a14151d"
APPWRITE_API_KEY = "standard_96d4a373241caa900a3bf2a3912d2faf6a87d65c2759ba1bc94f38949765edbcc3990a1f8e7010880b1551b1f016f730d1fbfc63d50273184508ab0fe525b57de6e7224e2260e6023f4f7b9a8b50c22a870f2752654f87b627c6b190f6de28b4980776c34bfce0d0923e7609b8080fa717a2b5eec6e39df1cf10b9ec2e187f75"

# ============================================================
# PLAID API (Banking Data)
# ============================================================

PLAID_CLIENT_ID = "68b8718ec2f428002456a84c"
PLAID_SECRET = "1849c4090173dfbce2bda5453e7048"
PLAID_ENV = "sandbox"
PLAID_SECRET_PRODUCTION = "b859911ae600444f480c39c90c1930"
```

## Code Changes Made

### 1. Updated `bbbot1_pipeline/mlflow_config.py`
- **Change:** Modified to support both local (Docker port 3307) and Railway cloud environments
- **Auto-detection:** Checks `MLFLOW_MYSQL_HOST` environment variable:
  - If Railway host detected → Uses Railway config
  - If localhost/not set → Uses local Docker config
- **Database:** Changed from `bbbot1` to `mlflow_db` for cleaner separation

### 2. Created `setup_mlflow_railway.py`
- **Purpose:** One-time setup script to create mlflow_db on Railway
- **Functions:**
  - Creates `mlflow_db` database on Railway MySQL
  - Initializes MLflow tracking (runs Alembic migrations)
  - Creates 34 MLflow tables automatically
  - Creates default experiment: `bentley_bot_analysis`
  - Prints Streamlit secrets configuration

### 3. Updated `.env`
- **Change:** Added Railway MySQL password
- **Old:** `RAILWAY_MYSQL_PASSWORD=<from_streamlit_secrets>`
- **New:** `RAILWAY_MYSQL_PASSWORD=cBlIUSygvPJCgPbNKHePJekQlClRamri`

## Database Architecture Summary

### Local Development (Docker - Port 3307)
```
bentley-mysql container:
├── bbbot1 (6 tables) - Stock market data
├── mlflow_db (34 tables) - MLflow experiments  
└── mansa_bot (44 tables) - Airflow orchestration
```

### Production (Railway - Port 54537)
```
Railway MySQL:
├── railway - Main app data
├── mydb - Plaid/Budget transactions
├── bbbot1 - Stock market data (to be migrated)
└── mlflow_db - MLflow experiments ✅ JUST CREATED
```

## How Investment Analysis Uses MLflow

Location: [frontend/pages/02_📈_Investment_Analysis.py](frontend/pages/02_📈_Investment_Analysis.py)

### Tab 2: 🔬 MLflow Experiments (Lines 388-390)
```python
with tab2:
    display_mlflow_experiments(selected_tickers)
```

### What It Displays (Lines 595-650):
- **Recent Experiments** - Last N runs with slider
- **Run Metadata:**
  - Run name and timestamp
  - Status (FINISHED, FAILED, RUNNING)
  - Ticker symbols analyzed
  - Data source (yfinance, CSV, etc.)
- **Metrics Logged:**
  - `pe_ratio` - Price-to-Earnings ratio
  - `total_value` - Portfolio value
  - `rows_fetched` - Data volume
  - `response_time_seconds` - API performance
- **Ticker Analysis** - Detailed view per ticker with historical runs

### MLflow Logging (Line 492-504):
```python
if enable_logging and MLFLOW_AVAILABLE:
    try:
        tracker = get_tracker()
        tracker.log_data_ingestion(
            ticker=ticker,
            source='yfinance',
            rows=len(df),
            duration=fetch_time
        )
        st.success(f"✅ Logged data ingestion to MLFlow ({fetch_time:.2f}s)")
    except Exception as e:
        st.warning(f"⚠️ MLFlow logging failed: {e}")
```

## Testing Steps

### 1. Local Testing
```bash
# Test MLflow connection locally
cd C:\Users\winst\BentleyBudgetBot
python -c "from bbbot1_pipeline.mlflow_config import validate_connection; validate_connection()"
```

### 2. Railway Connection Test
```bash
# Test Railway MLflow_db connection
python -c "import os; os.environ['MLFLOW_MYSQL_HOST']='nozomi.proxy.rlwy.net'; os.environ['MLFLOW_MYSQL_PORT']='54537'; os.environ['MLFLOW_MYSQL_PASSWORD']='cBlIUSygvPJCgPbNKHePJekQlClRamri'; os.environ['MLFLOW_MYSQL_DATABASE']='mlflow_db'; from bbbot1_pipeline.mlflow_config import validate_connection; validate_connection()"
```

### 3. Streamlit Cloud Testing
After adding secrets to Streamlit Cloud:

1. Go to https://bbbot305.streamlit.app/
2. Navigate to "📈 Investment Analysis" page
3. Click "🔬 MLflow Experiments" tab
4. Should see: "bentley_bot_analysis" experiment
5. Enable "🔬 Enable MLFlow Logging" toggle in sidebar
6. Run analysis on a ticker (e.g., AAPL)
7. Check MLflow tab for new logged run

## Verification Queries

### Check Database Exists
```sql
-- Connect to Railway MySQL
SHOW DATABASES LIKE 'mlflow_db';
```

### Check Tables Created
```sql
USE mlflow_db;
SHOW TABLES;
-- Should show 34 tables
```

### Check Experiments
```sql
SELECT * FROM experiments;
-- Should show:
-- | experiment_id | name                     | artifact_location |
-- | 0             | Default                  | ...               |
-- | 1             | bentley_bot_analysis     | ...               |
```

### Check Runs (After Using App)
```sql
SELECT run_uuid, experiment_id, status, start_time 
FROM runs 
ORDER BY start_time DESC 
LIMIT 10;
```

## Next Steps

### Immediate
1. ✅ Add MLflow secrets to Streamlit Cloud (you said you did this)
2. ⏳ Test Investment Analysis page on Streamlit Cloud
3. ⏳ Verify MLflow Experiments tab shows data

### Short-term
1. Migrate `bbbot1` database to Railway (stock_prices_yf, fundamentals, etc.)
2. Test all Streamlit pages with Railway databases
3. Update remaining database connections to use Railway

### Long-term
1. Set up MLflow artifact storage (S3 or Appwrite Storage)
2. Configure MLflow model registry for ML models
3. Implement automated experiment tracking in pipelines

## Files Created/Modified

### Created
- ✅ `setup_mlflow_railway.py` - Railway MLflow setup script

### Modified
- ✅ `bbbot1_pipeline/mlflow_config.py` - Environment-aware configuration
- ✅ `.env` - Added Railway MySQL password

## Troubleshooting

### Issue: MLflow tables not created
**Solution:** Re-run setup script:
```bash
python setup_mlflow_railway.py
```

### Issue: "Can't connect to MySQL server"
**Check:**
1. Railway MySQL is running (check Railway dashboard)
2. Password is correct in secrets
3. Host/port are correct: `nozomi.proxy.rlwy.net:54537`

### Issue: "pymysql module not found"
**Solution:**
```bash
pip install pymysql
```

### Issue: Streamlit can't import mlflow_config
**Check:**
1. `bbbot1_pipeline` is in Python path
2. `requirements.txt` includes `mlflow`
3. Streamlit Cloud has rebuilt after secret changes

## Documentation References

- MLflow Documentation: https://mlflow.org/docs/latest/tracking.html
- MySQL Backend: https://mlflow.org/docs/latest/tracking.html#mysql
- Railway MySQL: https://docs.railway.app/databases/mysql

---

**Setup Completed:** January 14, 2026, 11:16 PM  
**Railway Database:** mlflow_db (34 tables)  
**Experiment Created:** bentley_bot_analysis (ID: 1)  
**Status:** ✅ Ready for Production
