# Database Architecture - BentleyBot

**Date:** January 17, 2026  
**Status:** ✅ CLARIFIED

## Database Setup Overview

### Docker MySQL (Port 3307) - LOCAL DEVELOPMENT

**Container:** `Demo_Bots`  
**Host:** `127.0.0.1`  
**Port:** `3307`  
**User:** `root`  
**Password:** `root`

**Contains TWO databases on the SAME MySQL server:**

```
┌─────────────────────────────────────────────────┐
│   Docker MySQL Container (Port 3307)           │
├─────────────────────────────────────────────────┤
│                                                 │
│  📊 bbbot1 Database                            │
│  ├─ stock_prices_yf (yfinance prices)         │
│  ├─ fundamentals (financial statements)        │
│  ├─ stock_prices_tiingo (Tiingo data)         │
│  ├─ barchart_data (Barchart futures)          │
│  ├─ alphavantage_data (AV data)               │
│  └─ stocktwits_sentiment (social sentiment)    │
│                                                 │
│  🔬 mlflow_db Database                         │
│  ├─ experiments (MLflow experiments)           │
│  ├─ runs (experiment runs)                     │
│  ├─ metrics (logged metrics: PE, ROI, etc.)   │
│  ├─ params (run parameters)                    │
│  ├─ tags (run tags)                            │
│  └─ ... (34 MLflow tables total)              │
│                                                 │
│  🚁 mansa_bot Database                         │
│  └─ Airflow metadata tables (44 tables)        │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Railway MySQL (Port 54537) - PRODUCTION/STREAMLIT CLOUD

**Host:** `nozomi.proxy.rlwy.net`  
**Port:** `54537`  
**User:** `root`  
**Password:** `cBlIUSygvPJCgPbNKHePJekQlClRamri`

**Contains:**
- `railway` - Main app data
- `mydb` - Plaid/Budget transactions  
- `mlflow_db` - MLflow for Streamlit Cloud deployment (same structure as local)

---

## MLflow Connection Logic

### How MLflow Decides Which Database to Use

**File:** [bbbot1_pipeline/mlflow_config.py](bbbot1_pipeline/mlflow_config.py)

```python
def get_mlflow_config() -> dict:
    mlflow_host = os.getenv('MLFLOW_MYSQL_HOST')
    
    if mlflow_host and mlflow_host != '127.0.0.1':
        # ✈️ RAILWAY/CLOUD - For Streamlit Cloud deployment
        return {
            "host": mlflow_host,  # nozomi.proxy.rlwy.net
            "port": 54537,
            "database": "mlflow_db"
        }
    else:
        # 🐳 LOCAL DOCKER - For development on your machine
        return {
            "host": "127.0.0.1",
            "port": 3307,
            "database": "mlflow_db"
        }
```

**Connection String Examples:**

**Local Development:**
```
mysql+pymysql://root:root@127.0.0.1:3307/mlflow_db
```

**Streamlit Cloud (Railway):**
```
mysql+pymysql://root:PASSWORD@nozomi.proxy.rlwy.net:54537/mlflow_db
```

---

## Your Questions Answered

### Q1: "Will the MLFlow triggers come from Railway now?"

**Answer:** No, MLflow triggers come from **wherever your code is running:**

| Environment | MLflow Connects To | When |
|-------------|-------------------|------|
| **Local Python scripts** | Docker port 3307 | When MLFLOW_MYSQL_HOST not set or = 127.0.0.1 |
| **Local Airflow DAGs** | Docker port 3307 | Same - runs on your machine |
| **Streamlit Cloud** | Railway port 54537 | When MLFLOW_MYSQL_HOST = nozomi.proxy.rlwy.net |

### Q2: "Why can't MLflow reliably connect to port 3307?"

**Answer:** MLflow **CAN** connect to port 3307! ✅

**Test Results:**
```bash
✅ MLFlow connection successful!
   Found 2 experiment(s)
   Tracking URI: mysql+pymysql://root:root@127.0.0.1:3307/mlflow_db
```

**Common Issues That May Have Confused You:**
1. ❌ Docker container not running → Start with `docker-compose up -d`
2. ❌ Wrong password in .env → Must be `MLFLOW_MYSQL_PASSWORD=root`
3. ❌ mlflow_db database didn't exist → Now created with 34 tables

### Q3: "How do bbbot1 and mlflow_db both work on port 3307?"

**Answer:** They are **different databases on the SAME MySQL server.**

Think of it like this:
```
MySQL Server (Port 3307)
  ├─ Database: bbbot1      ← Stock data goes here
  ├─ Database: mlflow_db   ← MLflow experiments go here
  └─ Database: mansa_bot   ← Airflow metadata goes here
```

**They DON'T conflict because:**
- Different database names (bbbot1 vs mlflow_db)
- Same MySQL server, different schemas
- Like different folders on the same drive

---

## Data Flow: How Everything Works Together

### Step 1: Data Ingestion (Airflow)
```mermaid
Airbyte/Airflow DAGs
    ↓
MySQL Port 3307
    ├─> bbbot1.stock_prices_yf (raw prices)
    └─> bbbot1.fundamentals (financials)
```

### Step 2: Data Transformation (dbt)
```mermaid
dbt models in bbbot1_pipeline/sql/
    ↓
Read from: bbbot1.stock_prices_yf
Calculate: PE ratios, moving averages, ROI
    ↓
Write to: bbbot1.marts.features_roi
```

### Step 3: MLflow Logging (Python)
```mermaid
derive_ratios.py (Python script)
    ↓
1. Query: bbbot1.stock_prices_yf
2. Calculate: PE ratio, PB ratio, etc.
3. Log metrics: mlflow.log_metric("pe_ratio", 15.2)
    ↓
MySQL Port 3307
    └─> mlflow_db.metrics (experiment results)
```

### Step 4: Streamlit Display
```mermaid
Streamlit Investment Analysis page
    ↓
Query MLflow: "Get latest experiments"
    ↓
MySQL Port 3307 (local) OR Railway Port 54537 (cloud)
    └─> mlflow_db.runs (retrieve logged metrics)
    ↓
Display: Charts, tables, comparisons
```

---

## Configuration Files Summary

### .env (Local Development)
```bash
# Docker MySQL (Port 3307)
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_PASSWORD=root

# BBBot1 Database (Stock Data)
BBBOT1_MYSQL_HOST=127.0.0.1
BBBOT1_MYSQL_PORT=3307
BBBOT1_MYSQL_PASSWORD=root
BBBOT1_MYSQL_DATABASE=bbbot1

# MLflow Database (Experiments)
MLFLOW_MYSQL_HOST=127.0.0.1
MLFLOW_MYSQL_PORT=3307
MLFLOW_MYSQL_PASSWORD=root
MLFLOW_MYSQL_DATABASE=mlflow_db
```

### Streamlit Secrets (Cloud Deployment)
```toml
# Railway MySQL (Port 54537)
MLFLOW_MYSQL_HOST = "nozomi.proxy.rlwy.net"
MLFLOW_MYSQL_PORT = "54537"
MLFLOW_MYSQL_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"
MLFLOW_MYSQL_DATABASE = "mlflow_db"
```

---

## Workflow Recap (With Database Details)

### Complete Pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. DATA SOURCES                                             │
└─────────────────────────────────────────────────────────────┘
   Tiingo, Barchart, AlphaVantage, YFinance, StockTwits
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. AIRFLOW INGESTION                                        │
│    DAGs: ingest_yfinance.py, ingest_alpha_vantage.py       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. MYSQL STORAGE (Port 3307)                                │
│    Database: bbbot1                                         │
│    Tables: stock_prices_yf, fundamentals, etc.             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. DBT TRANSFORMATIONS                                      │
│    Models: stg_prices, stg_fundamentals, features_roi      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. PYTHON ANALYSIS (derive_ratios.py)                      │
│    Calculate: PE ratio, ROE, moving averages               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. MLFLOW LOGGING                                           │
│    log_fundamental_ratios()                                 │
│    Database: mlflow_db (Port 3307)                         │
│    Tables: experiments, runs, metrics, params              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. STREAMLIT DISPLAY                                        │
│    Investment Analysis page queries MLflow                  │
│    Shows: Latest experiments, metrics, comparisons         │
└─────────────────────────────────────────────────────────────┘
```

---

## Testing MLflow Connection

### Test Local Docker Connection (Port 3307)
```bash
cd C:\Users\winst\BentleyBudgetBot
python -c "from bbbot1_pipeline.mlflow_config import validate_connection; validate_connection()"
```

**Expected Output:**
```
✅ MLFlow connection successful!
   Found 2 experiment(s)
```

### Test Railway Connection (Port 54537)
```bash
$env:MLFLOW_MYSQL_HOST="nozomi.proxy.rlwy.net"
$env:MLFLOW_MYSQL_PORT="54537"
$env:MLFLOW_MYSQL_PASSWORD="cBlIUSygvPJCgPbNKHePJekQlClRamri"
python -c "from bbbot1_pipeline.mlflow_config import validate_connection; validate_connection()"
```

---

## Quick Reference: Which Database for What?

| Data Type | Database | Port | Location |
|-----------|----------|------|----------|
| Stock prices from yfinance | bbbot1 | 3307 | Docker |
| Financial fundamentals | bbbot1 | 3307 | Docker |
| Calculated ratios (dbt) | bbbot1 | 3307 | Docker |
| **MLflow experiments** | **mlflow_db** | **3307** | **Docker (local)** |
| **MLflow experiments** | **mlflow_db** | **54537** | **Railway (cloud)** |
| Airflow metadata | mansa_bot | 3307 | Docker |
| Plaid transactions | mydb | 54537 | Railway |

---

## Key Takeaways

1. ✅ **MLflow DOES work with port 3307** - Connection test successful
2. ✅ **bbbot1 and mlflow_db coexist** - Different databases, same MySQL server
3. ✅ **Local = Docker:3307, Cloud = Railway:54537** - Auto-detected by mlflow_config.py
4. ✅ **MLflow logs FROM your Python scripts** - Not triggered by Railway
5. ✅ **Same mlflow_db structure** - Whether local Docker or Railway cloud

---

**Updated:** January 17, 2026  
**Status:** ✅ All databases operational  
**MLflow Connection:** ✅ Working on port 3307
