# BentleyBot Data Architecture - Final Structure

## Database Naming Convention (Updated Dec 2, 2025)

### MySQL (Operational Database) - Port 3307
**Database: `bbbot1`** - Live trading data storage

#### Tables by Data Source:
```sql
-- yfinance data (free, real-time)
stock_prices_yf
  - ticker, date, open, high, low, close, volume, adj_close
  - Data: RGTI, QBTS, IONQ, SOUN (quantum stocks)
  - DAG: yfinance_data_pull.py
  
-- Tiingo data (premium, when subscribed)
stock_prices_tiingo
  - ticker, date, open, high, low, close, volume
  - adj_open, adj_high, adj_low, adj_close, adj_volume, split_factor
  - Data: AAPL, MSFT, GOOGL, AMZN, etc.
  - DAG: tiingo_data_historical.py
  
-- Future tables (planned):
stock_prices_polygon      -- Polygon.io data
sentiment_stocktwits      -- Social sentiment
futures_barchart          -- Futures/options data
```

### Snowflake (Analytics Warehouse) - Cloud
**Database: `MARKET_DATA`** - Historical analysis & ML

#### Schema Organization:
```sql
-- Schema per data source
MARKET_DATA.YFINANCE.stock_prices       -- From MySQL bbbot1.stock_prices_yf
MARKET_DATA.TIINGO.stock_prices         -- From MySQL bbbot1.stock_prices_tiingo
MARKET_DATA.STOCKTWITS.sentiment        -- Future: sentiment data
MARKET_DATA.POLYGON.stock_prices        -- Future: polygon data

-- Analytics layer (your custom analysis)
MARKET_DATA.ANALYTICS.consolidated_prices   -- Combined from all sources
MARKET_DATA.ANALYTICS.daily_returns         -- Calculated returns
MARKET_DATA.ANALYTICS.portfolio_performance -- Your trading results
```

## Why This Structure?

### 1. Clear Source Identification
```sql
-- In MySQL, know the source immediately:
SELECT * FROM bbbot1.stock_prices_yf;       -- yfinance
SELECT * FROM bbbot1.stock_prices_tiingo;   -- Tiingo

-- In Snowflake, organized by schema:
SELECT * FROM MARKET_DATA.YFINANCE.stock_prices;
SELECT * FROM MARKET_DATA.TIINGO.stock_prices;
```

### 2. Easy to Combine Data
```sql
-- Create unified view in Snowflake:
CREATE VIEW MARKET_DATA.ANALYTICS.all_stock_prices AS
SELECT 'yfinance' as source, * FROM MARKET_DATA.YFINANCE.stock_prices
UNION ALL
SELECT 'tiingo' as source, * FROM MARKET_DATA.TIINGO.stock_prices;
```

### 3. Cost Optimization
- **MySQL**: Free, use for daily ingestion and live data
- **Snowflake**: Pay per use, sync data weekly/monthly for analysis

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    External Data Sources                    │
├─────────────────────────────────────────────────────────────┤
│  yfinance API  │  Tiingo API  │  StockTwits  │  Polygon.io │
└────────┬────────┴──────┬───────┴──────┬───────┴──────┬──────┘
         │               │              │              │
         ▼               ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Airflow DAGs (Ingestion)                 │
├─────────────────────────────────────────────────────────────┤
│  yfinance_data_pull.py  │  tiingo_data_historical.py  │ ... │
└────────┬────────────────┴───────────┬─────────────────┴─────┘
         │                            │
         ▼                            ▼
┌─────────────────────────────────────────────────────────────┐
│              MySQL Database: bbbot1 (Port 3307)             │
├─────────────────────────────────────────────────────────────┤
│  stock_prices_yf  │  stock_prices_tiingo  │  [future tables]│
└────────┬────────────────┴───────────┬─────────────────┴─────┘
         │                            │
         │         Airbyte Sync       │
         ▼                            ▼
┌─────────────────────────────────────────────────────────────┐
│         Snowflake Database: MARKET_DATA (Cloud)             │
├─────────────────────────────────────────────────────────────┤
│  YFINANCE Schema  │  TIINGO Schema  │  ANALYTICS Schema     │
└────────┬────────────────┴───────────┬─────────────────┴─────┘
         │                            │
         │   Analysis & Visualization │
         ▼                            ▼
┌─────────────────────────────────────────────────────────────┐
│            Your Tools (Tableau, Python, etc.)               │
└─────────────────────────────────────────────────────────────┘
```

## Querying Examples

### MySQL (Operational Queries)
```sql
-- Latest quantum stock prices (yfinance)
SELECT ticker, date, close 
FROM bbbot1.stock_prices_yf 
WHERE date = CURDATE()
ORDER BY ticker;

-- Check data availability by source
SELECT 
    'yfinance' as source,
    COUNT(*) as record_count,
    MIN(date) as earliest,
    MAX(date) as latest
FROM bbbot1.stock_prices_yf
UNION ALL
SELECT 
    'tiingo' as source,
    COUNT(*) as record_count,
    MIN(date) as earliest,
    MAX(date) as latest
FROM bbbot1.stock_prices_tiingo;
```

### Snowflake (Analytics Queries)
```sql
-- Compare prices across sources
SELECT 
    yf.ticker,
    yf.date,
    yf.close as yfinance_close,
    ti.close as tiingo_close,
    ABS(yf.close - ti.close) as price_diff
FROM MARKET_DATA.YFINANCE.stock_prices yf
JOIN MARKET_DATA.TIINGO.stock_prices ti
    ON yf.ticker = ti.ticker 
    AND yf.date = ti.date
WHERE yf.ticker IN ('AAPL', 'MSFT')
ORDER BY yf.date DESC;

-- Calculate portfolio performance
SELECT 
    ticker,
    AVG(close) as avg_price,
    MAX(close) as high,
    MIN(close) as low,
    STDDEV(close) as volatility
FROM MARKET_DATA.ANALYTICS.consolidated_prices
WHERE date >= DATEADD(month, -3, CURRENT_DATE())
GROUP BY ticker;
```

## Connection Credentials Reference

### MySQL Workbench
- Host: `127.0.0.1`
- Port: `3307`
- Username: `root`
- Password: `root`
- Database: `bbbot1`

### Snowflake (After Setup)
- Host: `your_account.region.snowflakecomputing.com`
- Username: `AIRBYTE_USER`
- Password: (set during setup)
- Database: `MARKET_DATA`
- Warehouse: `AIRBYTE_WH`

## Next Steps

1. ✅ **MySQL Setup** - Complete (yfinance data working)
2. ✅ **Table Naming** - Updated (stock_prices_yf, stock_prices_tiingo)
3. ⏳ **Snowflake Setup** - Optional (sign up when ready)
4. ⏳ **Airbyte Sync** - Configure when Snowflake is ready
5. ⏳ **Tiingo Premium** - Subscribe when budget allows

## Key Takeaway

**DON'T rename databases to match!** Keep:
- MySQL `bbbot1` for operational data (multiple source-specific tables)
- Snowflake `MARKET_DATA` for analytics (multiple source-specific schemas)

This gives you the best of both worlds:
- Fast ingestion in MySQL
- Powerful analytics in Snowflake
- Clear data lineage from source to analysis
