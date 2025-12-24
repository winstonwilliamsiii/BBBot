# Database Naming Strategy: MySQL vs Snowflake

## Current Setup (Recommended Architecture)

```
┌─────────────────────────────────────────────────────────────────┐
│                         MySQL (Operational)                     │
├─────────────────────────────────────────────────────────────────┤
│  Database: bbbot1                                               │
│  ├─ stock_prices_yf (yfinance data - quantum stocks)            │
│  ├─ stock_prices (tiingo data - will be added)                  │
│  └─ [other operational tables]                                  │
│                                                                  │
│  Database: mansa_bot                                            │
│  └─ [Airflow metadata]                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Airbyte Sync
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Snowflake (Analytics Warehouse)              │
├─────────────────────────────────────────────────────────────────┤
│  Database: MARKET_DATA                                          │
│  ├─ Schema: YFINANCE                                            │
│  │  └─ stock_prices (from MySQL bbbot1.stock_prices_yf)         │
│  │                                                               │
│  ├─ Schema: TIINGO                                              │
│  │  └─ stock_prices (from MySQL bbbot1.stock_prices)            │
│  │                                                               │
│  ├─ Schema: STOCKTWITS                                          │
│  │  └─ sentiment_data                                           │
│  │                                                               │
│  ├─ Schema: BARCHART                                            │
│  │  └─ futures_data                                             │
│  │                                                               │
│  └─ Schema: ANALYTICS (your analysis layer)                     │
│     ├─ consolidated_prices (combined from all sources)          │
│     ├─ daily_returns                                            │
│     └─ portfolio_performance                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Why Keep Different Names?

### 1. **Different Purposes**
| System | Database | Purpose |
|--------|----------|---------|
| MySQL | `bbbot1` | Operational: Live data ingestion, DAG processing |
| Snowflake | `MARKET_DATA` | Analytics: Historical analysis, reporting, ML |

### 2. **Snowflake's Power: Multiple Sources → One Database**
```sql
-- In Snowflake MARKET_DATA database, you'll have:

-- From yfinance (MySQL bbbot1.stock_prices_yf)
SELECT * FROM MARKET_DATA.YFINANCE.STOCK_PRICES;

-- From Tiingo (MySQL bbbot1.stock_prices)
SELECT * FROM MARKET_DATA.TIINGO.STOCK_PRICES;

-- Combined view
SELECT * FROM MARKET_DATA.ANALYTICS.CONSOLIDATED_PRICES;
```

### 3. **Better Organization by SOURCE**
Instead of multiple databases, use **schemas** to separate sources:

```
MARKET_DATA (Database)
├── YFINANCE (Schema) ← Free real-time data
├── TIINGO (Schema) ← Premium historical data
├── STOCKTWITS (Schema) ← Sentiment data
├── POLYGON (Schema) ← If you add later
├── BARCHART (Schema) ← Futures/options
└── ANALYTICS (Schema) ← Your analysis/aggregations
```

## Implementation Plan

### Step 1: Update Your DAGs for Clarity
Let me update your Tiingo DAG to use a clear table name:
