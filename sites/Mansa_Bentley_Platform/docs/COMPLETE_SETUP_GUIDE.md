# Complete Pipeline Setup Guide

## Overview

This guide walks you through setting up the complete Bentley Budget Bot data pipeline from scratch.

## Pipeline Architecture

```
External APIs (Tiingo, AlphaVantage, StockTwits)
                    ↓
            Airbyte Ingestion
                    ↓
    Raw Tables (MySQL: bbbot1 database)
    • prices_daily
    • fundamentals_raw
    • sentiment_msgs
    • technicals_raw
                    ↓
        dbt Transformations
                    ↓
          Staging Models (views)
          • stg_prices
          • stg_fundamentals
          • stg_sentiment
                    ↓
           Marts Models (tables)
           • fundamentals_derived
           • sentiment_aggregates
           • features_roi (ML features)
                    ↓
            Airflow Orchestration
                    ↓
         MLFlow Model Training
                    ↓
        Streamlit Dashboard
```

## Quick Start

### Option 1: Automated Setup (Recommended)

```powershell
# Run complete setup script
.\scripts\setup\complete_pipeline_setup.ps1
```

This will:
- ✅ Verify Docker and MySQL are running
- ✅ Create raw data tables
- ✅ Configure Airflow connections
- ✅ Install dbt dependencies
- ✅ Test dbt connection
- ✅ Verify DAG and module files

### Option 2: Manual Setup

Follow the steps below for detailed configuration.

---

## Step-by-Step Setup

### Prerequisites

1. **Docker Desktop** running
2. **MySQL container** (bentley-mysql) running on port 3307
3. **Python 3.8+** with virtual environment
4. **API Keys**:
   - Tiingo API key
   - AlphaVantage API key
   - StockTwits (no key needed)

### Step 1: Create Raw Data Tables

```powershell
# Execute SQL script to create tables
Get-Content mysql_config/create_airbyte_raw_tables.sql | docker exec -i bentley-mysql mysql -uroot -proot bbbot1

# Verify tables created
docker exec bentley-mysql mysql -uroot -proot bbbot1 -e "SHOW TABLES;"
```

**Expected output**:
- prices_daily
- fundamentals_raw
- sentiment_msgs
- technicals_raw

📖 **Detailed guide**: [docs/AIRBYTE_RAW_TABLES.md](docs/AIRBYTE_RAW_TABLES.md)

---

### Step 2: Configure Airflow Connections

**2.1 - Start Airflow** (if not running):
```bash
cd docker
docker-compose -f docker-compose-airflow.yml up -d
```

**2.2 - Configure MySQL connection**:
```bash
docker exec airflow-webserver airflow connections add \
  mysql_bbbot1 \
  --conn-type mysql \
  --conn-host bentley-mysql \
  --conn-schema bbbot1 \
  --conn-login root \
  --conn-password root \
  --conn-port 3306
```

**2.3 - Test connection**:
```bash
docker exec airflow-webserver python -c "
from airflow.providers.mysql.hooks.mysql import MySqlHook
hook = MySqlHook(mysql_conn_id='mysql_bbbot1')
print(hook.get_first('SELECT DATABASE()'))
"
```

📖 **Detailed guide**: [docs/AIRFLOW_CONNECTIONS.md](docs/AIRFLOW_CONNECTIONS.md)

---

### Step 3: Install dbt

```bash
# Install dbt with MySQL and Snowflake adapters
pip install dbt-core dbt-mysql dbt-snowflake

# Verify installation
dbt --version
```

**Expected output**:
```
Core:
  - installed: 1.7.0
  - latest:    1.7.0

Plugins:
  - mysql:     1.7.0 - Up to date!
  - snowflake: 1.7.0 - Up to date!
```

---

### Step 4: Configure dbt

**4.1 - Test dbt connection**:
```bash
cd dbt_project
dbt debug --profiles-dir .
```

**Expected output**: `All checks passed!`

**4.2 - If connection fails**, check `dbt_project/profiles.yml`:
```yaml
dev:
  target: dev
  outputs:
    dev:
      type: mysql
      host: 127.0.0.1
      port: 3307  # Important: Use 3307 from host
      user: root
      password: root
      database: bbbot1
      schema: bbbot1
```

---

### Step 5: Configure Airbyte Connections

**5.1 - Start Airbyte** (if not running):
```bash
cd airbyte
docker-compose up -d
```

**5.2 - Access Airbyte UI**: http://localhost:8000

**5.3 - Create MySQL destination**:
- Name: `BentleyBot MySQL`
- Host: `bentley-mysql` (or `127.0.0.1`)
- Port: `3306` (Docker) or `3307` (host)
- Database: `bbbot1`
- User: `root`
- Password: `root`

**5.4 - Create connections**:

| Source | Destination Table | Sync Mode | Schedule |
|--------|------------------|-----------|----------|
| Tiingo API | prices_daily | Incremental | Daily 6 PM |
| AlphaVantage | fundamentals_raw | Incremental | Weekly |
| StockTwits | sentiment_msgs | Incremental | Every 15 min |

📖 **Detailed guide**: [docs/AIRBYTE_SETUP.md](docs/AIRBYTE_SETUP.md)

---

### Step 6: Run Initial Data Load

**6.1 - Trigger Airbyte syncs**:
- In Airbyte UI, manually trigger sync for each connection
- Wait for syncs to complete

**6.2 - Verify data loaded**:
```sql
docker exec bentley-mysql mysql -uroot -proot bbbot1 -e "
SELECT 'prices_daily' AS table_name, COUNT(*) FROM prices_daily
UNION ALL
SELECT 'fundamentals_raw', COUNT(*) FROM fundamentals_raw
UNION ALL
SELECT 'sentiment_msgs', COUNT(*) FROM sentiment_msgs;
"
```

---

### Step 7: Run dbt Pipeline

**7.1 - Run dbt models**:
```bash
cd dbt_project

# Run staging models first
dbt run --select staging --profiles-dir .

# Run marts models
dbt run --select marts --profiles-dir .

# Or run all models
dbt run --profiles-dir .
```

**7.2 - Test data quality**:
```bash
dbt test --profiles-dir .
```

**7.3 - Verify marts tables created**:
```sql
docker exec bentley-mysql mysql -uroot -proot bbbot1 -e "
SELECT * FROM marts.features_roi LIMIT 5;
"
```

📖 **Detailed guide**: [docs/DBT_ARCHITECTURE.md](docs/DBT_ARCHITECTURE.md)

---

### Step 8: Enable Airflow DAGs

**8.1 - Access Airflow UI**: http://localhost:8080

**8.2 - Enable DAGs**:
1. `dbt_transformation_pipeline` - Runs daily at 8 AM
2. `stock_pipeline_comprehensive` - Runs daily at 9 AM

**8.3 - Trigger manual DAG run**:
- Click on DAG name
- Click "Trigger DAG" button
- Monitor execution in Graph View

---

### Step 9: Verify Complete Pipeline

**9.1 - Check Airflow DAG execution**:
```
✅ dbt_transformation_pipeline
   ✅ check_raw_data_availability
   ✅ dbt_run_staging
   ✅ dbt_run_marts
   ✅ validate_dbt_models
```

**9.2 - Check MLFlow experiments**:
```bash
# Access MLFlow UI
http://localhost:5000

# Should see experiments:
- stock_pipeline_features
- roi_prediction_models
```

**9.3 - Verify Streamlit dashboard** (if running):
```bash
streamlit run streamlit_app.py
```

---

## File Structure

```
BentleyBudgetBot/
├── airflow/
│   ├── dags/
│   │   ├── dbt_transformation_pipeline.py      # dbt orchestration
│   │   └── stock_pipeline_comprehensive.py      # ML pipeline
│   └── ...
│
├── bbbot1_pipeline/
│   ├── ingest_alpha_vantage_updated.py         # AlphaVantage ingestion
│   ├── ingest_yfinance_updated.py              # yfinance ingestion
│   ├── mlflow_config.py                         # MLFlow configuration
│   ├── db.py                                    # Database utilities
│   └── ...
│
├── dbt_project/
│   ├── dbt_project.yml                          # dbt project config
│   ├── profiles.yml                             # Database connections
│   ├── models/
│   │   ├── staging/
│   │   │   ├── sources.yml                      # Raw table mappings
│   │   │   ├── stg_prices.sql                   # Price staging
│   │   │   ├── stg_fundamentals.sql             # Fundamentals staging
│   │   │   └── stg_sentiment.sql                # Sentiment staging
│   │   └── marts/
│   │       ├── fundamentals_derived.sql         # Financial ratios
│   │       ├── sentiment_aggregates.sql         # Sentiment metrics
│   │       └── features_roi.sql                 # ML features
│   └── ...
│
├── docs/
│   ├── AIRFLOW_CONNECTIONS.md                   # Airflow setup guide
│   ├── AIRBYTE_SETUP.md                         # Airbyte configuration
│   ├── AIRBYTE_RAW_TABLES.md                    # Table schemas
│   └── DBT_ARCHITECTURE.md                      # dbt architecture
│
├── mysql_config/
│   └── create_airbyte_raw_tables.sql            # MySQL table schemas
│
├── scripts/
│   └── setup/
│       ├── complete_pipeline_setup.ps1          # Automated setup
│       └── setup_airbyte_tables.ps1             # Table creation
│
└── DATA_PIPELINE_REFERENCE.md                   # Quick reference
```

---

## Configuration Files

### Key Configuration Files

1. **dbt_project/profiles.yml** - Database connections
2. **bbbot1_pipeline/mlflow_config.py** - MLFlow tracking URI
3. **airflow/dags/*.py** - DAG definitions
4. **.env** - API keys and secrets (create this)

### Environment Variables

Create `.env` file in project root:

```bash
# API Keys
ALPHA_VANTAGE_API_KEY=your_alphavantage_key
TIINGO_API_KEY=your_tiingo_key

# MySQL Configuration
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=bbbot1

# MLFlow Configuration
MLFLOW_TRACKING_URI=mysql+pymysql://root:root@127.0.0.1:3307/mlflow_db

# Airflow Configuration
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
```

---

## Troubleshooting

### Issue: Raw tables not created

**Solution**:
```powershell
# Re-run table creation script
.\scripts\setup\setup_airbyte_tables.ps1
```

### Issue: dbt connection fails

**Solution**:
```bash
# Check MySQL is accessible
docker exec bentley-mysql mysql -uroot -proot -e "SELECT 1;"

# Verify port mapping
docker ps | grep bentley-mysql

# Update profiles.yml with correct port (3307 from host)
```

### Issue: Airflow DAG import errors

**Solution**:
```bash
# Verify Python path
docker exec airflow-webserver python -c "import sys; print(sys.path)"

# Install bbbot1_pipeline in Airflow container
docker exec airflow-webserver pip install -e /opt/airflow/bbbot1_pipeline
```

### Issue: Airbyte sync fails

**Solution**:
1. Check API keys are valid
2. Verify MySQL credentials
3. Review Airbyte logs in UI
4. Test API endpoints manually

---

## Monitoring & Maintenance

### Daily Checklist

- [ ] Check Airbyte sync status (http://localhost:8000)
- [ ] Verify Airflow DAG runs (http://localhost:8080)
- [ ] Review MLFlow experiments (http://localhost:5000)
- [ ] Monitor MySQL table growth
- [ ] Check for data quality issues

### Weekly Tasks

- [ ] Review dbt test results
- [ ] Analyze MLFlow model performance
- [ ] Update API keys if needed
- [ ] Clean up old MLFlow runs
- [ ] Backup MySQL database

---

## Resources

### Documentation
- **Quick Reference**: [DATA_PIPELINE_REFERENCE.md](DATA_PIPELINE_REFERENCE.md)
- **Airflow Setup**: [docs/AIRFLOW_CONNECTIONS.md](docs/AIRFLOW_CONNECTIONS.md)
- **Airbyte Setup**: [docs/AIRBYTE_SETUP.md](docs/AIRBYTE_SETUP.md)
- **dbt Architecture**: [docs/DBT_ARCHITECTURE.md](docs/DBT_ARCHITECTURE.md)
- **Raw Tables**: [docs/AIRBYTE_RAW_TABLES.md](docs/AIRBYTE_RAW_TABLES.md)

### External Links
- **Airflow Docs**: https://airflow.apache.org/docs/
- **dbt Docs**: https://docs.getdbt.com/
- **Airbyte Docs**: https://docs.airbyte.com/
- **MLFlow Docs**: https://mlflow.org/docs/latest/

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review relevant documentation
3. Check Airflow/Airbyte logs
4. Verify all services are running

---

## Next Steps After Setup

1. ✅ **Complete this setup guide**
2. ⏭️ **Populate raw tables with historical data** (run Airbyte syncs)
3. ⏭️ **Train initial MLFlow models** (trigger stock_pipeline_comprehensive DAG)
4. ⏭️ **Configure Streamlit dashboard** to display results
5. ⏭️ **Set up monitoring and alerts**
6. ⏭️ **Schedule regular backups**

---

**Status**: Ready for production deployment after completing all steps above.
