# Data Transformation Architecture with dbt

## Overview

BentleyBot uses **dbt (data build tool)** to transform raw data from Airbyte into clean, analytics-ready datasets for MLFlow model training and Streamlit dashboards.

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA PIPELINE FLOW                          │
└─────────────────────────────────────────────────────────────────┘

1. DATA INGESTION (Airbyte)
   ├─ Tiingo API → prices_daily
   ├─ AlphaVantage/yfinance → fundamentals_raw
   └─ StockTwits → sentiment_raw

2. DATA TRANSFORMATION (dbt)
   ├─ Staging Layer (Views)
   │  ├─ stg_prices: Clean price data
   │  ├─ stg_fundamentals: Standardize financials
   │  └─ stg_sentiment: Aggregate sentiment
   │
   └─ Marts Layer (Tables)
      ├─ fundamentals_derived: Calculate ratios
      ├─ sentiment_aggregates: Daily sentiment metrics
      └─ features_roi: ML features for ROI prediction

3. MODEL TRAINING (MLFlow)
   └─ Consume features_roi table
      ├─ Train regression models
      ├─ Log experiments & metrics
      └─ Store model artifacts

4. VISUALIZATION (Streamlit)
   └─ Query marts tables
      ├─ Investment Analysis dashboard
      └─ Live Crypto dashboard
```

## dbt Project Structure

```
dbt_project/
├── dbt_project.yml              # Project configuration
├── profiles.yml                 # Database connections
├── README.md                    # dbt documentation
│
├── models/
│   ├── staging/                 # Data cleaning layer
│   │   ├── stg_prices.sql
│   │   ├── stg_fundamentals.sql
│   │   ├── stg_sentiment.sql
│   │   └── schema.yml           # Tests & documentation
│   │
│   └── marts/                   # Business logic layer
│       ├── fundamentals_derived.sql
│       ├── sentiment_aggregates.sql
│       ├── features_roi.sql
│       └── schema.yml           # Tests & documentation
│
└── target/                      # Generated artifacts
    ├── manifest.json
    ├── run_results.json
    └── catalog.json
```

## Key Models

### Staging Models (Views)

#### 1. `stg_prices`
- **Purpose**: Clean and standardize daily price data
- **Source**: `prices_daily` (Tiingo via Airbyte)
- **Transformations**:
  - Cast data types
  - Filter null values
  - Standardize column names
- **Output**: View with OHLC data

#### 2. `stg_fundamentals`
- **Purpose**: Standardize fundamental financial data
- **Source**: `fundamentals_raw` (AlphaVantage/yfinance via Airbyte)
- **Transformations**:
  - Cast decimal types
  - Remove incomplete records
  - Ensure data quality
- **Output**: View with balance sheet & income statement data

#### 3. `stg_sentiment`
- **Purpose**: Aggregate sentiment from social media
- **Source**: `sentiment_raw` (StockTwits via Airbyte)
- **Transformations**:
  - Parse timestamps
  - Calculate sentiment scores
  - Normalize message counts
- **Output**: View with sentiment metrics

### Marts Models (Tables)

#### 1. `fundamentals_derived`
- **Purpose**: Calculate financial ratios for analysis
- **Depends on**: `stg_fundamentals`, `stg_prices`
- **Key Ratios**:
  - PE Ratio (Price-to-Earnings)
  - PB Ratio (Price-to-Book)
  - EV/EBIT, EV/EBITDA
  - ROA (Return on Assets)
  - ROI (Return on Investment) ← **Target variable**
  - Debt-to-Equity
  - Cash Ratio
- **Logic**: Joins fundamentals with closest price data
- **Output**: Table with calculated ratios

#### 2. `sentiment_aggregates`
- **Purpose**: Daily sentiment metrics by ticker
- **Depends on**: `stg_sentiment`
- **Key Metrics**:
  - Average sentiment score
  - Bullish/bearish ratios
  - 7-day moving averages
  - Sentiment momentum
  - Message volume
- **Output**: Table with daily sentiment aggregates

#### 3. `features_roi` ⭐
- **Purpose**: Feature engineering for MLFlow ROI prediction
- **Depends on**: `fundamentals_derived`, `sentiment_aggregates`, `stg_prices`
- **Features**:
  - **Fundamental**: PE, PB, ROA, ROI, debt ratios
  - **Technical**: Price momentum, volatility, volume
  - **Sentiment**: Scores, bullish ratio, moving averages
  - **Interactions**: PE × sentiment, ROA × sentiment
  - **Categorical**: Quantum vs traditional stocks
  - **Quality Flags**: Missing data indicators
- **Output**: Table consumed by MLFlow regression models

## Orchestration

### Airflow DAG: `dbt_transformation_pipeline`

```python
# Schedule: Daily at 8 AM (after Airbyte syncs)
# Tasks:
1. check_raw_data_availability   # Verify Airbyte loaded data
2. dbt_debug                      # Test dbt connection
3. dbt_deps                       # Install packages
4. dbt_run_staging                # Run staging models
5. dbt_test_staging               # Test staging quality
6. dbt_run_marts                  # Run marts models
7. dbt_test_marts                 # Test marts quality
8. validate_dbt_models            # Final validation
9. dbt_docs_generate              # Generate docs
```

### Integration with MLFlow DAG

```python
# airflow/dags/mlflow_regression_fundamental_analysis.py
# Updated to read from dbt marts

dbt_transformation >> mlflow_training
```

## Database Configuration

### MySQL (Local Development)
```yaml
host: 127.0.0.1
port: 3307
database: bbbot1
schemas:
  - staging  # dbt staging models
  - marts    # dbt marts models
  - bbbot1   # raw Airbyte data
```

### Snowflake (Production - Optional)
```yaml
database: MARKET_DATA
schemas:
  - PUBLIC
  - STAGING
  - MARTS
```

## Usage

### Install dbt

```bash
pip install dbt-core dbt-mysql dbt-snowflake
```

### Run dbt Commands

```bash
cd dbt_project

# Test connection
dbt debug --profiles-dir .

# Install dependencies
dbt deps

# Run all models
dbt run

# Run specific layer
dbt run --select staging
dbt run --select marts

# Run specific model
dbt run --select features_roi

# Test data quality
dbt test

# Generate documentation
dbt docs generate
dbt docs serve  # View at http://localhost:8080
```

### MLFlow Integration

```python
# Read features_roi in MLFlow DAG
from sqlalchemy import create_engine
import pandas as pd

engine = create_engine('mysql+pymysql://root:root@127.0.0.1:3307/bbbot1')
features_df = pd.read_sql('SELECT * FROM marts.features_roi', engine)

# Train model
from sklearn.linear_model import LinearRegression
X = features_df[['pe_ratio', 'pb_ratio', 'roa', 'avg_sentiment_score']]
y = features_df['target_roi']

model = LinearRegression()
model.fit(X, y)

# Log to MLFlow
from bbbot1_pipeline.mlflow_tracker import get_tracker
tracker = get_tracker()
tracker.log_model(model, 'roi_regression_model')
```

## Data Quality & Testing

dbt includes comprehensive tests:

```yaml
# schema.yml
tests:
  - not_null          # Ensure critical fields exist
  - unique            # Check uniqueness constraints
  - relationships     # Verify foreign keys
  - accepted_values   # Validate enums
  - dbt_utils tests   # Custom business logic
```

## Materialization Strategy

| Layer | Materialization | Reason |
|-------|----------------|--------|
| **Staging** | View | Fast, no storage, always fresh |
| **Marts** | Table | Optimized queries, stable for ML |

## Best Practices

1. **Run dbt after Airbyte syncs** (Airflow orchestration)
2. **Always test after running** (`dbt test`)
3. **Document your models** (schema.yml files)
4. **Use incremental models** for large datasets (future enhancement)
5. **Version control dbt models** (Git)

## Troubleshooting

### Connection Issues
```bash
# Test dbt connection
dbt debug --profiles-dir dbt_project

# Check MySQL port
docker ps | grep mysql
```

### Missing Tables
```bash
# Check raw data exists
mysql -h 127.0.0.1 -P 3307 -u root -p bbbot1 -e "SHOW TABLES;"
```

### Model Failures
```bash
# Run with verbose logging
dbt run --debug --select model_name

# Check target/run_results.json for errors
```

## Performance Optimization

- **Staging views**: No performance impact (computed on query)
- **Marts tables**: Pre-computed, fast for MLFlow
- **Indexes**: Add indexes on join keys (ticker, date)
- **Incremental models**: Process only new data (future enhancement)

## Future Enhancements

1. **Incremental models** for `features_roi` (process only new data)
2. **Snapshots** for slowly changing dimensions
3. **Seeds** for static reference data (ticker metadata)
4. **Macros** for reusable SQL logic
5. **dbt Cloud** for scheduling and monitoring

## Resources

- [dbt Documentation](https://docs.getdbt.com/)
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices)
- [dbt MySQL Adapter](https://github.com/dbeatty10/dbt-mysql)
- [dbt Snowflake Adapter](https://docs.getdbt.com/reference/warehouse-setups/snowflake-setup)
