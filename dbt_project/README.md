# dbt Project README

## Overview

This dbt project transforms raw financial data loaded by Airbyte into clean, analytics-ready datasets for MLFlow model training and Streamlit dashboards.

## Data Flow

```
Airbyte (Raw Data Ingestion)
    ↓
dbt Staging (Data Cleaning & Standardization)
    ↓
dbt Marts (Feature Engineering & Business Logic)
    ↓
MLFlow (ML Model Training & Tracking)
    ↓
Streamlit (Dashboard Visualization)
```

## Project Structure

```
dbt_project/
├── dbt_project.yml          # Project configuration
├── profiles.yml             # Database connection profiles
├── models/
│   ├── staging/             # Data cleaning & standardization
│   │   ├── stg_prices.sql
│   │   ├── stg_fundamentals.sql
│   │   ├── stg_sentiment.sql
│   │   └── schema.yml
│   └── marts/               # Business logic & feature engineering
│       ├── fundamentals_derived.sql
│       ├── sentiment_aggregates.sql
│       ├── features_roi.sql
│       └── schema.yml
└── README.md
```

## Models

### Staging Models (Views)

1. **stg_prices** - Daily OHLC price data
   - Source: `prices_daily` (Tiingo API via Airbyte)
   - Cleans and standardizes price data
   - Filters out null values

2. **stg_fundamentals** - Financial statement data
   - Source: `fundamentals_raw` (AlphaVantage/yfinance via Airbyte)
   - Standardizes fundamental metrics
   - Ensures data quality

3. **stg_sentiment** - Social sentiment data
   - Source: `sentiment_raw` (StockTwits via Airbyte)
   - Aggregates sentiment metrics
   - Normalizes sentiment scores

### Marts Models (Tables)

1. **fundamentals_derived** - Calculated financial ratios
   - PE Ratio, PB Ratio, EV/EBIT, EV/EBITDA
   - ROA, ROI, EPS, Debt-to-Equity
   - Joins fundamentals with latest prices
   - **Used by**: MLFlow regression models, Streamlit dashboards

2. **sentiment_aggregates** - Daily sentiment metrics
   - Daily average sentiment scores
   - Bullish/bearish ratios
   - 7-day moving averages
   - Sentiment momentum
   - **Used by**: Feature engineering, sentiment analysis

3. **features_roi** - ML feature engineering table
   - Combines fundamentals + technicals + sentiment
   - Target variable: ROI
   - Feature interactions and transformations
   - Data quality flags
   - **Used by**: MLFlow ROI prediction models

## Usage

### Run All Models

```bash
cd dbt_project
dbt run
```

### Run Specific Models

```bash
# Run only staging models
dbt run --select staging

# Run only marts models
dbt run --select marts

# Run specific model
dbt run --select features_roi

# Run model and its dependencies
dbt run --select +features_roi
```

### Test Models

```bash
# Test all models
dbt test

# Test specific model
dbt test --select features_roi
```

### Generate Documentation

```bash
dbt docs generate
dbt docs serve
```

## Database Connections

### MySQL (Local Development)
- Host: 127.0.0.1
- Port: 3307
- Database: bbbot1
- Schema: bbbot1

### Snowflake (Production - Optional)
- Database: MARKET_DATA
- Schema: PUBLIC
- Configure environment variables:
  - `SNOWFLAKE_ACCOUNT`
  - `SNOWFLAKE_USER`
  - `SNOWFLAKE_PASSWORD`
  - `SNOWFLAKE_ROLE`
  - `SNOWFLAKE_WAREHOUSE`

## MLFlow Integration

The `features_roi` mart is specifically designed for MLFlow:

```python
# Python code to consume features_roi
from sqlalchemy import create_engine
import pandas as pd

engine = create_engine('mysql+pymysql://root:root@127.0.0.1:3307/bbbot1')
features_df = pd.read_sql('SELECT * FROM marts.features_roi', engine)

# Use with MLFlow
from bbbot1_pipeline.mlflow_tracker import get_tracker
tracker = get_tracker()
tracker.log_fundamental_ratios(ticker, date, features_df.to_dict())
```

## Airflow Integration

Schedule dbt runs with Airflow:

```python
from airflow.operators.bash import BashOperator

dbt_run = BashOperator(
    task_id='dbt_run',
    bash_command='cd /path/to/dbt_project && dbt run',
    dag=dag
)
```

## Variables

Configure in `dbt_project.yml`:

```yaml
vars:
  quantum_tickers: ['IONQ', 'QBTS', 'SOUN', 'RGTI']
  major_tickers: ['AMZN', 'MSFT', 'GOOGL']
  start_date: '2023-01-01'
```

## Testing

All models include data quality tests:
- Not null checks
- Uniqueness constraints
- Referential integrity
- Data type validation

## Materialization Strategy

- **Staging**: Materialized as **views** (fast, no storage overhead)
- **Marts**: Materialized as **tables** (optimized for queries, MLFlow consumption)

## Next Steps

1. **Run initial dbt setup**:
   ```bash
   pip install dbt-mysql dbt-snowflake
   cd dbt_project
   dbt debug
   dbt run
   ```

2. **Schedule with Airflow**: Create DAG to run `dbt run` after Airbyte syncs

3. **Integrate with MLFlow**: Update MLFlow DAG to read from `features_roi`

4. **Add more models**: Expand marts with additional feature tables as needed
