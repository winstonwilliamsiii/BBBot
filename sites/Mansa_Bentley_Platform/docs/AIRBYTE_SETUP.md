# Airbyte Connection Setup Guide

## Overview

This guide provides step-by-step instructions for configuring Airbyte connections to populate the raw data tables (prices_daily, fundamentals_raw, sentiment_msgs, technicals_raw) from external APIs.

## Prerequisites

- Airbyte running (default: http://localhost:8000)
- MySQL database with raw tables created
- API keys for external services (Tiingo, AlphaVantage, StockTwits)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         External APIs                            │
│  • Tiingo (prices)  • AlphaVantage (fundamentals)               │
│  • StockTwits (sentiment)  • Custom (technicals)                │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼ Airbyte Syncs
┌─────────────────────────────────────────────────────────────────┐
│                    MySQL Raw Tables (bbbot1)                     │
│  • prices_daily  • fundamentals_raw                              │
│  • sentiment_msgs  • technicals_raw                              │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼ dbt Transformations (staging → marts)
┌─────────────────────────────────────────────────────────────────┐
│                      dbt Marts Tables                            │
│  • fundamentals_derived  • sentiment_aggregates                  │
│  • features_roi (ML features)                                    │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼ MLFlow Training
┌─────────────────────────────────────────────────────────────────┐
│                     MLFlow Models & Streamlit                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Connection 1: Tiingo → prices_daily

### Purpose
Ingest daily OHLC price data from Tiingo API

### Source Configuration

1. **Navigate to Airbyte**: http://localhost:8000
2. **Create Source**:
   - Name: `Tiingo Stock Prices`
   - Source Type: `Custom` or `HTTP API`
   
3. **API Configuration**:
   ```yaml
   API Endpoint: https://api.tiingo.com/tiingo/daily/{ticker}/prices
   Method: GET
   Headers:
     Authorization: Token YOUR_TIINGO_API_KEY
   Query Parameters:
     startDate: 2024-01-01
     endDate: {{ current_date }}
     format: json
   ```

4. **Tickers to Fetch**:
   ```
   IONQ, QBTS, SOUN, RGTI, AMZN, MSFT, GOOGL, AAPL, TSLA
   ```

### Destination Configuration

1. **Destination**: MySQL
2. **Connection Details**:
   - Host: `bentley-mysql` (Docker) or `127.0.0.1` (host)
   - Port: `3306` (Docker) or `3307` (host)
   - Database: `bbbot1`
   - Username: `root`
   - Password: `root`
   - Table: `prices_daily`

3. **Sync Mode**: Incremental (Append)
4. **Primary Key**: `(ticker, date)`
5. **Cursor Field**: `date`

### Field Mapping

| Tiingo API Field | MySQL Column | Type | Notes |
|------------------|--------------|------|-------|
| ticker | ticker | VARCHAR(10) | Stock symbol |
| date | date | DATE | Trading date |
| open | open | DECIMAL(18,4) | Opening price |
| high | high | DECIMAL(18,4) | High price |
| low | low | DECIMAL(18,4) | Low price |
| close | close | DECIMAL(18,4) | Closing price |
| volume | volume | BIGINT | Trading volume |
| adjOpen | adj_open | DECIMAL(18,4) | Adjusted open |
| adjHigh | adj_high | DECIMAL(18,4) | Adjusted high |
| adjLow | adj_low | DECIMAL(18,4) | Adjusted low |
| adjClose | adj_close | DECIMAL(18,4) | Adjusted close |
| adjVolume | adj_volume | BIGINT | Adjusted volume |

### Schedule

- **Frequency**: Daily
- **Time**: 6:00 PM EST (after market close)
- **Timezone**: America/New_York

### Custom Python Connector (Alternative)

If using custom Python connector instead of HTTP API:

```python
# airbyte/sources/tiingo/tiingo_source.py

import requests
from datetime import datetime, timedelta

class TiingoSource:
    def __init__(self, api_key, tickers):
        self.api_key = api_key
        self.tickers = tickers
        self.base_url = "https://api.tiingo.com/tiingo/daily"
    
    def fetch_prices(self, ticker, start_date, end_date):
        url = f"{self.base_url}/{ticker}/prices"
        headers = {"Authorization": f"Token {self.api_key}"}
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "format": "json"
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Transform to match prices_daily schema
        for record in data:
            yield {
                "ticker": ticker,
                "date": record["date"][:10],  # Extract date only
                "open": record["open"],
                "high": record["high"],
                "low": record["low"],
                "close": record["close"],
                "volume": record["volume"],
                "adj_open": record.get("adjOpen"),
                "adj_high": record.get("adjHigh"),
                "adj_low": record.get("adjLow"),
                "adj_close": record.get("adjClose"),
                "adj_volume": record.get("adjVolume"),
                "source": "tiingo"
            }
    
    def read_records(self):
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        for ticker in self.tickers:
            yield from self.fetch_prices(ticker, start_date, end_date)
```

---

## Connection 2: AlphaVantage → fundamentals_raw

### Purpose
Ingest financial statement data (income statement, balance sheet, cash flow)

### Source Configuration

1. **Source Name**: `AlphaVantage Fundamentals`
2. **Source Type**: `HTTP API` or `Custom Python`

3. **API Configuration**:
   ```yaml
   # Company Overview
   API Endpoint: https://www.alphavantage.co/query
   Method: GET
   Query Parameters:
     function: OVERVIEW
     symbol: {ticker}
     apikey: YOUR_ALPHAVANTAGE_KEY
   
   # Income Statement
   API Endpoint: https://www.alphavantage.co/query
   Method: GET
   Query Parameters:
     function: INCOME_STATEMENT
     symbol: {ticker}
     apikey: YOUR_ALPHAVANTAGE_KEY
   ```

### Destination Configuration

- **Table**: `fundamentals_raw`
- **Sync Mode**: Incremental (Append + Update)
- **Primary Key**: `(ticker, report_date)`
- **Cursor Field**: `report_date`

### Field Mapping

| AlphaVantage Field | MySQL Column | Notes |
|--------------------|--------------|-------|
| Symbol | ticker | Stock symbol |
| fiscalDateEnding | report_date | Report date |
| fiscalPeriod | fiscal_period | Q1, Q2, Q3, Q4, FY |
| totalRevenue | revenue | Total revenue |
| grossProfit | gross_profit | Gross profit |
| operatingIncome | operating_income | Operating income |
| netIncome | net_income | **Required** |
| ebit | ebit | **Required** |
| ebitda | ebitda | **Required** |
| eps | eps | Earnings per share |
| totalAssets | total_assets | **Required** |
| totalShareholderEquity | total_equity | **Required** |
| totalLiabilities | total_liabilities | **Required** |
| cashAndCashEquivalents | cash_and_equivalents | **Required** |
| commonStockSharesOutstanding | shares_outstanding | **Required** |
| marketCap | market_cap | Market capitalization |

### Schedule

- **Frequency**: Weekly
- **Day**: Sunday
- **Time**: 2:00 AM
- **Reason**: Fundamental data updates infrequently

### Rate Limiting

AlphaVantage free tier: **5 API calls per minute, 500 per day**

```python
# Rate limiting configuration
RATE_LIMIT_CALLS = 5
RATE_LIMIT_PERIOD = 60  # seconds
DAILY_LIMIT = 500

# In connector code
import time

for ticker in tickers:
    # Fetch data
    fetch_fundamental_data(ticker)
    
    # Wait 12 seconds between calls (5 calls/minute)
    time.sleep(12)
```

---

## Connection 3: StockTwits → sentiment_msgs

### Purpose
Ingest social sentiment messages from StockTwits

### Source Configuration

1. **Source Name**: `StockTwits Sentiment`
2. **Source Type**: `Custom Python` (no official connector)

3. **API Configuration**:
   ```yaml
   API Endpoint: https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json
   Method: GET
   Authentication: None (public endpoint)
   ```

### Custom Python Connector

```python
# airbyte/sources/stocktwits/stocktwits_source.py

import requests
from datetime import datetime

class StockTwitsSource:
    def __init__(self, tickers):
        self.tickers = tickers
        self.base_url = "https://api.stocktwits.com/api/2/streams/symbol"
    
    def fetch_sentiment(self, ticker):
        url = f"{self.base_url}/{ticker}.json"
        
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        for message in data.get("messages", []):
            # Parse sentiment
            sentiment = message.get("entities", {}).get("sentiment", {})
            
            yield {
                "ticker": ticker,
                "timestamp": message["created_at"],
                "message_id": str(message["id"]),
                "message_text": message.get("body", ""),
                "sentiment_score": self._calculate_score(sentiment),
                "sentiment_label": sentiment.get("basic") if sentiment else "neutral",
                "likes_count": message.get("likes", {}).get("total", 0),
                "source": "stocktwits",
                "user_id": str(message["user"]["id"]),
                "username": message["user"]["username"],
                "user_followers": message["user"].get("followers", 0),
                "bullish_count": 1 if sentiment.get("basic") == "bullish" else 0,
                "bearish_count": 1 if sentiment.get("basic") == "bearish" else 0,
                "message_count": 1
            }
    
    def _calculate_score(self, sentiment):
        """Convert sentiment label to score"""
        if not sentiment:
            return 0.0
        
        label = sentiment.get("basic", "neutral")
        
        if label == "bullish":
            return 1.0
        elif label == "bearish":
            return -1.0
        else:
            return 0.0
    
    def read_records(self):
        for ticker in self.tickers:
            yield from self.fetch_sentiment(ticker)
```

### Destination Configuration

- **Table**: `sentiment_msgs`
- **Sync Mode**: Incremental (Append)
- **Primary Key**: `message_id`
- **Cursor Field**: `timestamp`

### Schedule

- **Frequency**: Every 15 minutes (during market hours)
- **Active Hours**: 9:30 AM - 4:00 PM EST
- **Days**: Monday - Friday

---

## Connection 4: Custom Python → technicals_raw

### Purpose
Calculate technical indicators from price data

### Implementation

This should be a **custom Airflow DAG** that:
1. Reads from `prices_daily`
2. Calculates technical indicators
3. Writes to `technicals_raw`

### Technical Indicators to Calculate

```python
# airflow/dags/calculate_technicals.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import ta  # Technical Analysis library

def calculate_technicals(ticker):
    """Calculate technical indicators for a ticker"""
    
    # Fetch price data
    query = f"""
    SELECT date, open, high, low, close, volume
    FROM prices_daily
    WHERE ticker = '{ticker}'
    ORDER BY date DESC
    LIMIT 200
    """
    
    df = pd.read_sql(query, engine)
    df = df.sort_values('date')
    
    # Calculate indicators
    df['sma_20'] = df['close'].rolling(20).mean()
    df['sma_50'] = df['close'].rolling(50).mean()
    df['sma_200'] = df['close'].rolling(200).mean()
    
    df['ema_12'] = df['close'].ewm(span=12).mean()
    df['ema_26'] = df['close'].ewm(span=26).mean()
    
    df['rsi_14'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_histogram'] = macd.macd_diff()
    
    bollinger = ta.volatility.BollingerBands(df['close'])
    df['bollinger_upper'] = bollinger.bollinger_hband()
    df['bollinger_middle'] = bollinger.bollinger_mavg()
    df['bollinger_lower'] = bollinger.bollinger_lband()
    
    df['atr_14'] = ta.volatility.AverageTrueRange(
        df['high'], df['low'], df['close'], window=14
    ).average_true_range()
    
    # Price changes
    df['price_change_1d'] = df['close'].pct_change(1) * 100
    df['price_change_5d'] = df['close'].pct_change(5) * 100
    df['price_change_20d'] = df['close'].pct_change(20) * 100
    
    # Insert into technicals_raw
    for _, row in df.iterrows():
        insert_technical_record(ticker, row)
```

### Schedule

- **Frequency**: Daily
- **Time**: 7:00 PM (after prices_daily sync completes)

---

## Sync Schedule Summary

| Connection | Source | Destination | Frequency | Time | Priority |
|------------|--------|-------------|-----------|------|----------|
| Tiingo | API | prices_daily | Daily | 6:00 PM | High |
| AlphaVantage | API | fundamentals_raw | Weekly | Sunday 2 AM | Medium |
| StockTwits | API | sentiment_msgs | 15 min | Market hours | High |
| Technicals | Python | technicals_raw | Daily | 7:00 PM | Medium |

---

## Orchestration Flow

```
6:00 PM  → Airbyte: Tiingo sync (prices_daily)
7:00 PM  → Airflow: Calculate technicals (technicals_raw)
8:00 AM  → Airflow: dbt transformation pipeline
9:00 AM  → Airflow: Stock pipeline comprehensive (MLFlow training)

Every 15 min (market hours) → Airbyte: StockTwits sync (sentiment_msgs)
Weekly (Sunday 2 AM) → Airbyte: AlphaVantage sync (fundamentals_raw)
```

---

## Setup Instructions

### Step 1: Start Airbyte

```bash
cd airbyte
docker-compose up -d
```

Access Airbyte UI: http://localhost:8000

### Step 2: Configure MySQL Destination

1. In Airbyte UI, go to **Destinations**
2. Click **+ New destination**
3. Select **MySQL**
4. Configure:
   - Name: `BentleyBot MySQL`
   - Host: `bentley-mysql` (Docker) or `127.0.0.1`
   - Port: `3306` (Docker) or `3307`
   - Database: `bbbot1`
   - Username: `root`
   - Password: `root`
5. Click **Set up destination**

### Step 3: Create Connections

For each source (Tiingo, AlphaVantage, StockTwits):

1. Go to **Connections**
2. Click **+ New connection**
3. Select **Source** (create new if needed)
4. Select **Destination**: BentleyBot MySQL
5. Configure **Stream** → **Table** mapping
6. Set **Sync mode**: Incremental
7. Set **Schedule**
8. Enable **Normalization** (optional)
9. Click **Set up connection**

### Step 4: Test Connections

```bash
# Trigger manual sync for each connection
# In Airbyte UI: Connections → Select connection → Sync now

# Verify data ingested
docker exec bentley-mysql mysql -uroot -proot bbbot1 -e "
SELECT 'prices_daily' AS table_name, COUNT(*) AS count FROM prices_daily
UNION ALL
SELECT 'fundamentals_raw', COUNT(*) FROM fundamentals_raw
UNION ALL
SELECT 'sentiment_msgs', COUNT(*) FROM sentiment_msgs
UNION ALL
SELECT 'technicals_raw', COUNT(*) FROM technicals_raw;
"
```

---

## Monitoring

### Check Sync Status

**Airbyte UI**:
- Navigate to **Connections**
- View sync history and logs
- Monitor success/failure rates

**MySQL Queries**:
```sql
-- Check latest data ingestion
SELECT 
    'prices_daily' AS table_name,
    MAX(created_at) AS last_update,
    COUNT(*) AS total_records
FROM prices_daily
UNION ALL
SELECT 
    'fundamentals_raw',
    MAX(created_at),
    COUNT(*)
FROM fundamentals_raw
UNION ALL
SELECT 
    'sentiment_msgs',
    MAX(created_at),
    COUNT(*)
FROM sentiment_msgs;
```

### Alerts

Configure Airbyte webhook notifications for:
- Sync failures
- Data quality issues
- API rate limit errors

---

## Troubleshooting

### Issue: No data synced

**Check**:
1. API keys are valid
2. Network connectivity from Airbyte to APIs
3. MySQL credentials correct
4. Raw tables exist

### Issue: Duplicate records

**Solution**:
- Ensure primary key constraints on destination tables
- Use **Incremental** sync mode, not **Full Refresh**

### Issue: API rate limits

**Solution**:
- Adjust sync frequency
- Implement batching in custom connectors
- Use incremental cursor to fetch only new data

---

## Next Steps

After configuring Airbyte:

1. ✅ **Create Airbyte connections** (this document)
2. ⏭️ **Run dbt pipeline**: `cd dbt_project && dbt run`
3. ⏭️ **Verify data quality**: `dbt test`
4. ⏭️ **Enable Airflow DAGs**:
   - `dbt_transformation_pipeline`
   - `stock_pipeline_comprehensive`
5. ⏭️ **Monitor pipeline in Airflow UI**: http://localhost:8080

---

## Resources

- **Airbyte Docs**: https://docs.airbyte.com/
- **Tiingo API**: https://api.tiingo.com/documentation
- **AlphaVantage API**: https://www.alphavantage.co/documentation/
- **StockTwits API**: https://api.stocktwits.com/developers/docs
- **MySQL Destination**: https://docs.airbyte.com/integrations/destinations/mysql
