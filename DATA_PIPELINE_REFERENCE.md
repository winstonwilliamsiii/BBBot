# Data Pipeline Quick Reference

## Table Mapping

### Raw Tables (Airbyte → MySQL)
| Raw Table | Purpose | dbt Source Reference |
|-----------|---------|---------------------|
| `prices_daily` | OHLC price data from Tiingo | `{{ source('raw', 'prices_daily') }}` |
| `fundamentals_raw` | Financial statements from AlphaVantage | `{{ source('raw', 'fundamentals_raw') }}` |
| `sentiment_msgs` | Social sentiment from StockTwits | `{{ source('raw', 'sentiment_msgs') }}` |
| `technicals_raw` | Technical indicators | `{{ source('raw', 'technicals_raw') }}` |

### Staging Models (dbt Views)
| Staging Model | Source Table | Purpose |
|--------------|--------------|---------|
| `stg_prices` | `prices_daily` | Cleaned price data with standardized columns |
| `stg_fundamentals` | `fundamentals_raw` | Validated financial data |
| `stg_sentiment` | `sentiment_msgs` | Aggregated sentiment metrics |

### Marts Models (dbt Tables)
| Marts Model | Dependencies | Purpose |
|-------------|--------------|---------|
| `fundamentals_derived` | `stg_fundamentals`, `stg_prices` | Financial ratios (PE, PB, ROA, etc.) |
| `sentiment_aggregates` | `stg_sentiment` | Daily sentiment metrics by ticker |
| `features_roi` | All marts + `stg_prices` | ML features for ROI prediction |

## Complete Data Flow

```
┌─────────────────┐
│  External APIs  │
│  (Tiingo, AV,   │
│   StockTwits)   │
└────────┬────────┘
         │ Airbyte Sync
         ▼
┌─────────────────┐
│   Raw Tables    │
│ • prices_daily  │
│ • fundamentals_ │
│   raw           │
│ • sentiment_    │
│   msgs          │
│ • technicals_   │
│   raw           │
└────────┬────────┘
         │ dbt staging
         ▼
┌─────────────────┐
│ Staging Views   │
│ • stg_prices    │
│ • stg_fundamen- │
│   tals          │
│ • stg_sentiment │
└────────┬────────┘
         │ dbt marts
         ▼
┌─────────────────┐
│  Marts Tables   │
│ • fundamentals_ │
│   derived       │
│ • sentiment_    │
│   aggregates    │
│ • features_roi  │
└────────┬────────┘
         │ MLFlow Training
         ▼
┌─────────────────┐
│ MLFlow Models   │
│ (ROI Prediction)│
└────────┬────────┘
         │ Inference
         ▼
┌─────────────────┐
│    Streamlit    │
│    Dashboard    │
└─────────────────┘
```

## Key Files

### MySQL Setup
- **Schema**: `mysql_config/create_airbyte_raw_tables.sql`
- **Setup Script**: `scripts/setup/setup_airbyte_tables.ps1`
- **Documentation**: `docs/AIRBYTE_RAW_TABLES.md`

### Snowflake Setup (Optional)
- **Schema**: `airbyte/config/snowflake_airbyte_raw_tables.sql`

### dbt Configuration
- **Project Config**: `dbt_project/dbt_project.yml`
- **Sources**: `dbt_project/models/staging/sources.yml`
- **Profiles**: `dbt_project/profiles.yml`

### Airflow Orchestration
- **DAG**: `airflow/dags/dbt_transformation_pipeline.py`
- **Schedule**: Daily at 8 AM (after Airbyte syncs)

## Quick Commands

### MySQL Verification
```powershell
# Check tables exist
docker exec bentley-mysql mysql -uroot -proot bbbot1 -e "SHOW TABLES;"

# Check table structure
docker exec bentley-mysql mysql -uroot -proot bbbot1 -e "DESCRIBE prices_daily;"

# Check row counts
docker exec bentley-mysql mysql -uroot -proot bbbot1 -e "
SELECT 
  'prices_daily' AS table_name, COUNT(*) AS row_count FROM prices_daily
  UNION ALL
  SELECT 'fundamentals_raw', COUNT(*) FROM fundamentals_raw
  UNION ALL
  SELECT 'sentiment_msgs', COUNT(*) FROM sentiment_msgs
  UNION ALL
  SELECT 'technicals_raw', COUNT(*) FROM technicals_raw;"
```

### dbt Operations
```bash
# Change to dbt directory
cd dbt_project

# Test database connection
dbt debug --profiles-dir .

# Check source freshness
dbt source freshness --profiles-dir .

# Run staging models
dbt run --select staging --profiles-dir .

# Run marts models
dbt run --select marts --profiles-dir .

# Run all models
dbt run --profiles-dir .

# Test data quality
dbt test --profiles-dir .

# Generate documentation
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .
```

### Airbyte Configuration
1. Create connections in Airbyte UI (http://localhost:8000)
2. Configure sources:
   - Tiingo API → `prices_daily`
   - AlphaVantage → `fundamentals_raw`
   - StockTwits → `sentiment_msgs`
   - Custom Python → `technicals_raw`
3. Set sync schedules:
   - Prices: Daily 6 PM
   - Fundamentals: Weekly
   - Sentiment: Every 15 min
   - Technicals: Daily 7 PM

## Troubleshooting

### Issue: Tables not created
```powershell
# Re-run setup script
.\scripts\setup\setup_airbyte_tables.ps1

# Or manually execute SQL
Get-Content mysql_config/create_airbyte_raw_tables.sql | docker exec -i bentley-mysql mysql -uroot -proot bbbot1
```

### Issue: dbt can't find tables
```bash
# Verify source configuration
cat dbt_project/models/staging/sources.yml

# Check database connection
cd dbt_project && dbt debug --profiles-dir .
```

### Issue: Staging models fail
```bash
# Check if raw tables have data
docker exec bentley-mysql mysql -uroot -proot bbbot1 -e "SELECT COUNT(*) FROM prices_daily;"

# Run only staging models
cd dbt_project && dbt run --select staging --profiles-dir .
```

### Issue: Marts models fail
```bash
# Ensure staging models run first
cd dbt_project && dbt run --select staging --profiles-dir .

# Then run marts
dbt run --select marts --profiles-dir .
```

## Data Quality Checks

### Automated Tests (via dbt)
```bash
# Run all tests
cd dbt_project && dbt test --profiles-dir .

# Test specific model
dbt test --select stg_prices --profiles-dir .
```

### Manual Verification
```sql
-- Check for recent price data
SELECT ticker, MAX(date) AS latest_date, COUNT(*) AS records
FROM prices_daily
GROUP BY ticker;

-- Verify fundamentals quality
SELECT ticker, report_date, net_income, ebitda
FROM fundamentals_raw
WHERE net_income IS NULL OR ebitda IS NULL;

-- Check sentiment coverage
SELECT ticker, DATE(timestamp) AS date, COUNT(*) AS messages
FROM sentiment_msgs
WHERE timestamp >= NOW() - INTERVAL 7 DAY
GROUP BY ticker, DATE(timestamp)
ORDER BY ticker, date;
```

## Integration Points

### MLFlow Consumption
```python
# In MLFlow DAG: airflow/dags/mlflow_regression_fundamental_analysis.py
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('mysql+pymysql://root:root@127.0.0.1:3307/bbbot1')

# Load ML features
features_df = pd.read_sql("""
    SELECT *
    FROM marts.features_roi
    WHERE ticker IN ('IONQ', 'QBTS', 'SOUN', 'RGTI')
      AND target_roi IS NOT NULL
    ORDER BY price_date DESC
""", engine)
```

### Streamlit Dashboard
```python
# In streamlit_app.py
import streamlit as st
from sqlalchemy import create_engine

engine = create_engine('mysql+pymysql://root:root@127.0.0.1:3307/bbbot1')

# Display sentiment aggregates
sentiment_df = pd.read_sql("""
    SELECT ticker, sentiment_date, avg_sentiment_score, bullish_ratio
    FROM marts.sentiment_aggregates
    WHERE sentiment_date >= CURDATE() - INTERVAL 30 DAY
    ORDER BY sentiment_date DESC
""", engine)

st.plotly_chart(create_sentiment_chart(sentiment_df))
```

## Status Check

✅ **Completed**:
- Raw tables created in MySQL
- dbt sources configured
- Staging models updated
- Documentation created

⏭️ **Next Steps**:
1. Configure Airbyte connections
2. Run initial dbt pipeline
3. Integrate with MLFlow DAG
4. Update Streamlit to use marts tables

## Resources

- **Full Documentation**: [docs/AIRBYTE_RAW_TABLES.md](../docs/AIRBYTE_RAW_TABLES.md)
- **dbt Architecture**: [docs/DBT_ARCHITECTURE.md](../docs/DBT_ARCHITECTURE.md)
- **dbt Quick Reference**: [dbt_project/QUICK_REFERENCE.md](../dbt_project/QUICK_REFERENCE.md)
