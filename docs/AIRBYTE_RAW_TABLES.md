# Airbyte Raw Tables Documentation

## Overview

This document describes the raw data tables created for Airbyte to ingest data from external APIs. These tables serve as the foundation for the dbt data transformation pipeline.

## Architecture

```
External APIs → Airbyte → Raw Tables → dbt Staging → dbt Marts → MLFlow
```

### Data Flow
1. **Airbyte** loads raw data from external APIs (Tiingo, AlphaVantage, StockTwits)
2. **Raw tables** store unprocessed data with minimal validation
3. **dbt staging models** clean and standardize the raw data
4. **dbt marts models** perform feature engineering and business logic
5. **MLFlow** consumes the `features_roi` table for ML model training

## Database Configuration

### MySQL (Primary)
- **Host**: 127.0.0.1:3307 (container: bentley-mysql)
- **Database**: bbbot1
- **User**: root
- **Schema**: Direct table access (no separate schema)

### Snowflake (Optional Production)
- **Database**: MARKET_DATA
- **Schema**: PUBLIC
- **Staging Schema**: STAGING (for dbt views)
- **Marts Schema**: MARTS (for dbt tables)

## Tables

### 1. prices_daily

**Purpose**: Daily OHLC (Open, High, Low, Close) price data from Tiingo API

**Schema**:
| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| id | INT | Primary key (auto-increment) | No |
| ticker | VARCHAR(10) | Stock ticker symbol | No |
| date | DATE | Trading date | No |
| open | DECIMAL(18,4) | Opening price | Yes |
| high | DECIMAL(18,4) | Highest price | Yes |
| low | DECIMAL(18,4) | Lowest price | Yes |
| close | DECIMAL(18,4) | Closing price | No |
| volume | BIGINT | Trading volume | Yes |
| adj_open | DECIMAL(18,4) | Adjusted opening price | Yes |
| adj_high | DECIMAL(18,4) | Adjusted high price | Yes |
| adj_low | DECIMAL(18,4) | Adjusted low price | Yes |
| adj_close | DECIMAL(18,4) | Adjusted closing price | Yes |
| adj_volume | BIGINT | Adjusted volume | Yes |
| split_factor | DECIMAL(10,6) | Stock split factor (default: 1.0) | Yes |
| dividend_amount | DECIMAL(10,4) | Dividend paid on this date | Yes |
| source | VARCHAR(50) | Data source (tiingo, yfinance, polygon) | Yes |
| created_at | TIMESTAMP | Record creation timestamp | No |
| updated_at | TIMESTAMP | Last update timestamp | No |

**Indexes**:
- Primary Key: `id`
- Unique: `(ticker, date)`
- Index: `ticker`, `date`, `(ticker, date)`, `created_at`

**Data Sources**: Tiingo API, Yahoo Finance, Polygon.io

**Sample Query**:
```sql
SELECT ticker, date, close, volume
FROM prices_daily
WHERE ticker = 'IONQ'
  AND date >= '2024-01-01'
ORDER BY date DESC
LIMIT 10;
```

---

### 2. fundamentals_raw

**Purpose**: Financial statement data (income statement, balance sheet, cash flow) from AlphaVantage and yfinance

**Schema**:
| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| id | INT | Primary key (auto-increment) | No |
| ticker | VARCHAR(10) | Stock ticker symbol | No |
| report_date | DATE | Financial report date | No |
| fiscal_period | VARCHAR(10) | Fiscal period (Q1, Q2, Q3, Q4, FY) | Yes |
| revenue | DECIMAL(18,2) | Total revenue | Yes |
| gross_profit | DECIMAL(18,2) | Gross profit | Yes |
| operating_income | DECIMAL(18,2) | Operating income | Yes |
| net_income | DECIMAL(18,2) | Net income | No |
| ebit | DECIMAL(18,2) | Earnings before interest and taxes | No |
| ebitda | DECIMAL(18,2) | EBITDA | No |
| eps | DECIMAL(10,4) | Earnings per share | Yes |
| total_assets | DECIMAL(18,2) | Total assets | No |
| total_equity | DECIMAL(18,2) | Shareholder equity | No |
| total_liabilities | DECIMAL(18,2) | Total liabilities | No |
| current_assets | DECIMAL(18,2) | Current assets | Yes |
| current_liabilities | DECIMAL(18,2) | Current liabilities | Yes |
| cash_and_equivalents | DECIMAL(18,2) | Cash and cash equivalents | No |
| inventory | DECIMAL(18,2) | Inventory | Yes |
| accounts_receivable | DECIMAL(18,2) | Accounts receivable | Yes |
| accounts_payable | DECIMAL(18,2) | Accounts payable | Yes |
| operating_cash_flow | DECIMAL(18,2) | Operating cash flow | Yes |
| investing_cash_flow | DECIMAL(18,2) | Investing cash flow | Yes |
| financing_cash_flow | DECIMAL(18,2) | Financing cash flow | Yes |
| free_cash_flow | DECIMAL(18,2) | Free cash flow | Yes |
| shares_outstanding | BIGINT | Number of shares outstanding | No |
| market_cap | DECIMAL(18,2) | Market capitalization | Yes |
| source | VARCHAR(50) | Data source | Yes |
| created_at | TIMESTAMP | Record creation timestamp | No |
| updated_at | TIMESTAMP | Last update timestamp | No |

**Indexes**:
- Primary Key: `id`
- Unique: `(ticker, report_date)`
- Index: `ticker`, `report_date`, `(ticker, report_date)`, `created_at`

**Data Sources**: AlphaVantage API, Yahoo Finance, Financial Modeling Prep

**Sample Query**:
```sql
SELECT ticker, report_date, net_income, ebitda, total_assets
FROM fundamentals_raw
WHERE ticker = 'MSFT'
  AND report_date >= '2023-01-01'
ORDER BY report_date DESC;
```

---

### 3. sentiment_msgs

**Purpose**: Social sentiment messages and metrics from StockTwits, Twitter/X, and Reddit

**Schema**:
| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| id | INT | Primary key (auto-increment) | No |
| ticker | VARCHAR(10) | Stock ticker symbol | No |
| timestamp | DATETIME | Message timestamp | No |
| message_id | VARCHAR(100) | External message ID (unique) | Yes |
| message_text | TEXT | Message content | Yes |
| sentiment_score | DECIMAL(5,4) | Sentiment score (-1 to 1) | Yes |
| sentiment_label | VARCHAR(20) | Sentiment (bullish, bearish, neutral) | Yes |
| likes_count | INT | Number of likes | Yes |
| retweets_count | INT | Number of retweets/shares | Yes |
| replies_count | INT | Number of replies | Yes |
| user_id | VARCHAR(100) | User ID from source | Yes |
| username | VARCHAR(100) | Username | Yes |
| user_followers | INT | User's follower count | Yes |
| user_verified | BOOLEAN | Is user verified? | Yes |
| source | VARCHAR(50) | Data source (stocktwits, twitter, reddit) | Yes |
| language | VARCHAR(10) | Message language code | Yes |
| has_link | BOOLEAN | Does message contain a link? | Yes |
| has_media | BOOLEAN | Does message contain media? | Yes |
| message_count | INT | Count for aggregation (default: 1) | Yes |
| bullish_count | INT | Bullish message count | Yes |
| bearish_count | INT | Bearish message count | Yes |
| created_at | TIMESTAMP | Record creation timestamp | No |
| updated_at | TIMESTAMP | Last update timestamp | No |

**Indexes**:
- Primary Key: `id`
- Unique: `message_id`
- Index: `ticker`, `timestamp`, `(ticker, timestamp)`, `sentiment_label`, `source`, `created_at`

**Data Sources**: StockTwits API, Twitter/X API, Reddit API

**Sample Query**:
```sql
SELECT ticker, timestamp, sentiment_label, sentiment_score, message_text
FROM sentiment_msgs
WHERE ticker = 'QBTS'
  AND timestamp >= NOW() - INTERVAL 7 DAY
  AND sentiment_label = 'bullish'
ORDER BY timestamp DESC
LIMIT 20;
```

---

### 4. technicals_raw

**Purpose**: Technical indicators and derived metrics calculated from price data

**Schema**:
| Column | Type | Description | Nullable |
|--------|------|-------------|----------|
| id | INT | Primary key (auto-increment) | No |
| ticker | VARCHAR(10) | Stock ticker symbol | No |
| date | DATE | Calculation date | No |
| sma_20 | DECIMAL(18,4) | 20-day Simple Moving Average | Yes |
| sma_50 | DECIMAL(18,4) | 50-day Simple Moving Average | Yes |
| sma_200 | DECIMAL(18,4) | 200-day Simple Moving Average | Yes |
| ema_12 | DECIMAL(18,4) | 12-day Exponential Moving Average | Yes |
| ema_26 | DECIMAL(18,4) | 26-day Exponential Moving Average | Yes |
| rsi_14 | DECIMAL(5,2) | 14-day Relative Strength Index | Yes |
| macd | DECIMAL(18,4) | MACD line | Yes |
| macd_signal | DECIMAL(18,4) | MACD signal line | Yes |
| macd_histogram | DECIMAL(18,4) | MACD histogram | Yes |
| bollinger_upper | DECIMAL(18,4) | Bollinger Band upper | Yes |
| bollinger_middle | DECIMAL(18,4) | Bollinger Band middle | Yes |
| bollinger_lower | DECIMAL(18,4) | Bollinger Band lower | Yes |
| atr_14 | DECIMAL(18,4) | 14-day Average True Range | Yes |
| volume_sma_20 | BIGINT | 20-day Volume Moving Average | Yes |
| obv | BIGINT | On-Balance Volume | Yes |
| adx_14 | DECIMAL(5,2) | 14-day Average Directional Index | Yes |
| stochastic_k | DECIMAL(5,2) | Stochastic %K | Yes |
| stochastic_d | DECIMAL(5,2) | Stochastic %D | Yes |
| price_change_1d | DECIMAL(10,4) | 1-day price change % | Yes |
| price_change_5d | DECIMAL(10,4) | 5-day price change % | Yes |
| price_change_20d | DECIMAL(10,4) | 20-day price change % | Yes |
| pivot_point | DECIMAL(18,4) | Pivot point | Yes |
| resistance_1 | DECIMAL(18,4) | Resistance level 1 | Yes |
| resistance_2 | DECIMAL(18,4) | Resistance level 2 | Yes |
| support_1 | DECIMAL(18,4) | Support level 1 | Yes |
| support_2 | DECIMAL(18,4) | Support level 2 | Yes |
| source | VARCHAR(50) | Data source (calculated, talib, tradingview) | Yes |
| created_at | TIMESTAMP | Record creation timestamp | No |
| updated_at | TIMESTAMP | Last update timestamp | No |

**Indexes**:
- Primary Key: `id`
- Unique: `(ticker, date)`
- Index: `ticker`, `date`, `(ticker, date)`, `created_at`

**Data Sources**: Calculated internally using TA-Lib, pandas-ta, or similar libraries

**Sample Query**:
```sql
SELECT ticker, date, rsi_14, macd, macd_signal, bollinger_upper, bollinger_lower
FROM technicals_raw
WHERE ticker = 'SOUN'
  AND date >= '2024-11-01'
ORDER BY date DESC;
```

---

## Data Pipeline Integration

### Airbyte Configuration

Each table should have a corresponding Airbyte connection:

1. **Tiingo → prices_daily**
   - Connector: HTTP API / Custom Python
   - Schedule: Daily at 6 PM (after market close)
   - Sync mode: Incremental (append)

2. **AlphaVantage → fundamentals_raw**
   - Connector: HTTP API / Custom Python
   - Schedule: Weekly (Sunday)
   - Sync mode: Incremental (append)

3. **StockTwits → sentiment_msgs**
   - Connector: HTTP API / Custom Python
   - Schedule: Every 15 minutes (during market hours)
   - Sync mode: Incremental (append)

4. **Price Calculation → technicals_raw**
   - Connector: Custom Python script
   - Schedule: Daily at 7 PM (after prices_daily sync)
   - Sync mode: Full refresh (recalculate)

### dbt Staging Models

The dbt staging models reference these raw tables using the `source()` function:

```sql
-- dbt_project/models/staging/stg_prices.sql
SELECT * FROM {{ source('raw', 'prices_daily') }}

-- dbt_project/models/staging/stg_fundamentals.sql
SELECT * FROM {{ source('raw', 'fundamentals_raw') }}

-- dbt_project/models/staging/stg_sentiment.sql
SELECT * FROM {{ source('raw', 'sentiment_msgs') }}
```

Update `dbt_project/models/staging/sources.yml` to map these tables.

### Airflow Orchestration

The `dbt_transformation_pipeline` DAG should run after Airbyte syncs complete:

```
Airbyte Sync (6 PM) → Wait 30 min → dbt Pipeline (8 AM next day)
```

---

## Setup Instructions

### MySQL Setup

1. **Execute SQL script**:
   ```bash
   # Using Docker (recommended)
   Get-Content mysql_config/create_airbyte_raw_tables.sql | docker exec -i bentley-mysql mysql -uroot -proot bbbot1
   
   # Or using mysql CLI directly
   mysql -h 127.0.0.1 -P 3307 -u root -proot bbbot1 < mysql_config/create_airbyte_raw_tables.sql
   ```

2. **Verify tables created**:
   ```bash
   docker exec bentley-mysql mysql -uroot -proot bbbot1 -e "SHOW TABLES;"
   ```

3. **Check table structures**:
   ```bash
   docker exec bentley-mysql mysql -uroot -proot bbbot1 -e "DESCRIBE prices_daily;"
   ```

### Snowflake Setup (Optional)

1. **Install Snowflake CLI**:
   ```bash
   # Windows
   choco install snowsql
   
   # Or download from: https://docs.snowflake.com/en/user-guide/snowsql-install-config.html
   ```

2. **Execute SQL script**:
   ```bash
   snowsql -a YOUR_ACCOUNT -u YOUR_USER -d MARKET_DATA -f airbyte/config/snowflake_airbyte_raw_tables.sql
   ```

3. **Verify tables**:
   ```sql
   USE DATABASE MARKET_DATA;
   USE SCHEMA PUBLIC;
   SHOW TABLES;
   ```

### dbt Sources Configuration

1. **Update sources.yml** (created by setup script):
   ```bash
   .\scripts\setup\setup_airbyte_tables.ps1
   ```

2. **Test dbt connection**:
   ```bash
   cd dbt_project
   dbt debug --profiles-dir .
   ```

3. **Run source freshness check**:
   ```bash
   dbt source freshness --profiles-dir .
   ```

---

## Maintenance

### Data Quality Checks

Run these queries periodically to ensure data quality:

```sql
-- Check for missing dates in price data
SELECT ticker, 
       MIN(date) AS first_date, 
       MAX(date) AS last_date,
       COUNT(*) AS total_records
FROM prices_daily
GROUP BY ticker;

-- Check for NULL values in critical fundamentals fields
SELECT ticker, report_date
FROM fundamentals_raw
WHERE net_income IS NULL 
   OR ebit IS NULL 
   OR total_assets IS NULL;

-- Check sentiment data freshness
SELECT ticker, 
       MAX(timestamp) AS last_message,
       COUNT(*) AS message_count
FROM sentiment_msgs
WHERE timestamp >= NOW() - INTERVAL 1 DAY
GROUP BY ticker;

-- Verify technical indicators are calculated
SELECT ticker,
       MAX(date) AS last_calculation,
       COUNT(*) AS indicator_count
FROM technicals_raw
WHERE date >= CURDATE() - INTERVAL 7 DAY
GROUP BY ticker;
```

### Troubleshooting

**Issue**: Tables created but empty

**Solution**: Configure Airbyte connections and trigger initial sync

**Issue**: dbt staging models fail

**Solution**: Check `dbt_project/models/staging/sources.yml` has correct table names

**Issue**: Duplicate records

**Solution**: Unique constraints prevent duplicates. Check Airbyte sync mode (should be incremental, not full refresh)

**Issue**: Old data not refreshing

**Solution**: Check Airbyte schedule and last sync time in Airbyte UI

---

## Next Steps

1. ✅ **Create raw tables** (completed)
2. ⏭️ **Configure Airbyte connections** to populate tables
3. ⏭️ **Update dbt staging models** to use `source('raw', 'table_name')`
4. ⏭️ **Run dbt pipeline** to validate data transformation
5. ⏭️ **Enable Airflow DAG** for daily orchestration
6. ⏭️ **Monitor data quality** with dbt tests and freshness checks

---

## References

- **dbt Documentation**: [dbt_project/README.md](../dbt_project/README.md)
- **Architecture Guide**: [docs/DBT_ARCHITECTURE.md](DBT_ARCHITECTURE.md)
- **Airbyte Docs**: https://docs.airbyte.com/
- **MySQL Docs**: https://dev.mysql.com/doc/
- **Snowflake Docs**: https://docs.snowflake.com/
