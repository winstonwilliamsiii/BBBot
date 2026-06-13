# dbt Quick Reference Guide

## Setup

```bash
# Install dbt
pip install dbt-core dbt-mysql dbt-snowflake

# Test connection
cd dbt_project
dbt debug --profiles-dir .
```

## Common Commands

```bash
# Run all models
dbt run

# Run specific layer
dbt run --select staging
dbt run --select marts

# Run specific model and dependencies
dbt run --select +features_roi

# Test data quality
dbt test
dbt test --select marts

# Generate documentation
dbt docs generate
dbt docs serve  # View at http://localhost:8080

# Clean build artifacts
dbt clean
```

## Model Layers

### Staging (Views)
- **stg_prices**: Daily OHLC from Tiingo
- **stg_fundamentals**: Financial statements
- **stg_sentiment**: Social sentiment data

### Marts (Tables)
- **fundamentals_derived**: Financial ratios (PE, PB, ROI, etc.)
- **sentiment_aggregates**: Daily sentiment metrics
- **features_roi**: ML features for ROI prediction ⭐

## Integration Points

### MLFlow Consumption
```python
from sqlalchemy import create_engine
import pandas as pd

engine = create_engine('mysql+pymysql://root:root@127.0.0.1:3307/bbbot1')
features = pd.read_sql('SELECT * FROM marts.features_roi', engine)

# Train model
X = features[['pe_ratio', 'pb_ratio', 'roa', 'avg_sentiment_score']]
y = features['target_roi']
```

### Airflow Scheduling
```python
# airflow/dags/dbt_transformation_pipeline.py
# Runs daily at 8 AM after Airbyte syncs
```

## Database Schemas

```
bbbot1 (database)
├── bbbot1 (schema) - Raw Airbyte data
│   ├── prices_daily
│   ├── fundamentals_raw
│   └── sentiment_raw
├── staging (schema) - dbt views
│   ├── stg_prices
│   ├── stg_fundamentals
│   └── stg_sentiment
└── marts (schema) - dbt tables
    ├── fundamentals_derived
    ├── sentiment_aggregates
    └── features_roi
```

## Troubleshooting

```bash
# Check connection
dbt debug --profiles-dir dbt_project

# Verbose logging
dbt run --debug

# View compiled SQL
cat dbt_project/target/compiled/bentley_budget_bot/models/marts/features_roi.sql

# Check for errors
cat dbt_project/target/run_results.json
```

## File Locations

- **Project config**: `dbt_project/dbt_project.yml`
- **Connection profiles**: `dbt_project/profiles.yml`
- **Models**: `dbt_project/models/`
- **Tests**: `dbt_project/models/*/schema.yml`
- **Documentation**: `dbt_project/README.md`
- **Generated artifacts**: `dbt_project/target/`

## Resources

- Full documentation: `docs/DBT_ARCHITECTURE.md`
- Package organization: `docs/PACKAGE_ORGANIZATION.md`
- Airflow DAG: `airflow/dags/dbt_transformation_pipeline.py`
- MLFlow integration: `airflow/dags/mlflow_regression_fundamental_analysis.py`
