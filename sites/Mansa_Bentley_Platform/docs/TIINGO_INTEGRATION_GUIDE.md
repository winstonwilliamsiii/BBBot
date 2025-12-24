# Tiingo API Integration Guide

## Overview

This guide covers the **Tiingo API integration** for fetching equity fundamental and technical analysis data for Bentley Budget Bot visualizations.

## 🚀 Quick Start

### 1. Setup Your API Key

```bash
# Get a free API key from Tiingo
# Visit: https://www.tiingo.com/

# Add to your .env file
echo "TIINGO_API_KEY=your_api_key_here" >> .env
```

### 2. Test Your Connection

```bash
# Run the test script
python test_tiingo.py
```

Expected output:
```
✅ API Key found
✅ Tiingo client initialized
✅ AAPL: 30 records fetched
✅ Database connection successful
```

### 3. Fetch Data

```bash
# Fetch prices with technical indicators
python tiingo_integration.py --fetch prices --technical --save-csv

# Fetch specific tickers
python tiingo_integration.py --tickers IONQ QBTS SOUN RGTI --technical

# Save to database
python tiingo_integration.py --fetch all --save-db --technical
```

### 4. View in Streamlit

```bash
streamlit run "pages/01_📈_Investment_Analysis.py"
```

## 📊 Available Scripts

### 1. `tiingo_integration.py` - Main Data Fetcher

**Purpose**: Fetch equity prices, fundamentals, and calculate technical indicators

**Usage**:
```bash
# Fetch daily prices (default: 2 years)
python tiingo_integration.py --fetch prices --tickers AAPL MSFT GOOGL

# Fetch with technical indicators
python tiingo_integration.py --fetch prices --technical

# Fetch all data types
python tiingo_integration.py --fetch all --tickers IONQ QBTS

# Save to CSV
python tiingo_integration.py --save-csv --output-dir data

# Save to MySQL database
python tiingo_integration.py --save-db

# Customize lookback period
python tiingo_integration.py --days 365  # 1 year of data
```

**Options**:
- `--fetch`: Data type (prices, metadata, intraday, all)
- `--tickers`: List of ticker symbols
- `--days`: Number of days of historical data (default: 730)
- `--technical`: Calculate technical indicators
- `--save-db`: Save to MySQL database
- `--save-csv`: Save to CSV files
- `--output-dir`: Output directory for CSV (default: data/)

### 2. `test_tiingo.py` - Connection Test

**Purpose**: Verify Tiingo API setup and database connection

**Usage**:
```bash
python test_tiingo.py
```

**What it tests**:
- ✅ API key configuration
- ✅ API connectivity
- ✅ Sample data fetching (AAPL, MSFT, IONQ, QBTS)
- ✅ Database connection (optional)

### 3. `airflow/dags/tiingo_data_historical.py` - Airflow DAG

**Purpose**: Automated daily/weekly data fetching via Airflow

**Tickers**: AAPL, MSFT, GOOGL, AMZN, RGTI, QBTS, SOUN, IONQ

**Schedule**: Configurable (default: daily)

**Database Table**: `stock_prices_tiingo`

## 📈 Data Types Available

### 1. Daily Prices (EOD Data)
```python
# Columns: date, open, high, low, close, volume
# Adjusted: adj_open, adj_high, adj_low, adj_close, adj_volume
# Also: split_factor
```

**Free Tier**: ✅ Available
**Lookback**: 2+ years

### 2. Ticker Metadata
```python
# Company information
# Exchange code
# Start date
# Description
```

**Free Tier**: ✅ Available

### 3. Intraday Data (IEX)
```python
# Resample frequencies: 1min, 5min, 15min, 30min, 1hour
# Real-time quotes
```

**Free Tier**: ⚠️ Limited (requires premium)

### 4. Technical Indicators (Calculated)

Automatically calculated from price data:

**Trend Indicators**:
- Simple Moving Averages (SMA): 20, 50, 200-day
- Exponential Moving Averages (EMA): 12, 26-day
- MACD (Moving Average Convergence Divergence)
- MACD Signal Line & Histogram

**Momentum Indicators**:
- RSI (Relative Strength Index) - 14 period
- Average True Range (ATR) - 14 period

**Volatility Indicators**:
- Bollinger Bands (20-day, 2 std dev)
  - Upper Band
  - Middle Band (SMA 20)
  - Lower Band

**Volume Indicators**:
- Volume SMA - 20 period

## 🗄️ Database Schema

### Table: `stock_prices_tiingo`

```sql
CREATE TABLE stock_prices_tiingo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(18, 4),
    high DECIMAL(18, 4),
    low DECIMAL(18, 4),
    close DECIMAL(18, 4),
    volume BIGINT,
    adj_open DECIMAL(18, 4),
    adj_high DECIMAL(18, 4),
    adj_low DECIMAL(18, 4),
    adj_close DECIMAL(18, 4),
    adj_volume BIGINT,
    split_factor DECIMAL(10, 6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_ticker_date (ticker, date),
    INDEX idx_ticker (ticker),
    INDEX idx_date (date)
);
```

### Table: `stock_prices_tiingo_technical`

Same as above, plus technical indicator columns:
- `sma_20`, `sma_50`, `sma_200`
- `ema_12`, `ema_26`
- `macd`, `macd_signal`, `macd_hist`
- `rsi`
- `bb_upper`, `bb_middle`, `bb_lower`
- `volume_sma_20`
- `atr`

## 📊 Integration with Streamlit

### Investment Analysis Page

The data fetched by Tiingo scripts is automatically available in the Investment Analysis page:

**Location**: `pages/01_📈_Investment_Analysis.py`

**Features Using Tiingo Data**:

1. **Portfolio Overview Tab**
   - Real-time price display
   - Historical performance charts
   - Volume analysis

2. **Technical Analysis Tab**
   - Candlestick charts
   - Moving averages overlay
   - Volume bars
   - Technical indicators (if calculated)

3. **Fundamental Ratios Tab**
   - Company metadata
   - Valuation metrics

### Custom Visualization Example

```python
import pandas as pd
from tiingo_integration import TiingoAPIClient

# Initialize client
client = TiingoAPIClient(api_key)

# Fetch data with technical indicators
df = client.fetch_daily_prices('IONQ', start_date, end_date)
df = client.calculate_technical_indicators(df)

# Create Plotly chart
import plotly.graph_objects as go

fig = go.Figure()

# Candlestick
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name='Price'
))

# SMA 50
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['sma_50'],
    name='SMA 50',
    line=dict(color='blue')
))

# Bollinger Bands
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['bb_upper'],
    name='BB Upper',
    line=dict(color='gray', dash='dash')
))

st.plotly_chart(fig)
```

## 🔄 Automated Data Pipeline

### Option 1: Airflow DAG (Recommended for Production)

```bash
# Copy the DAG to your Airflow dags folder
cp airflow/dags/tiingo_data_historical.py ~/airflow/dags/

# Trigger manually
airflow dags trigger tiingo_historical_data

# Or wait for scheduled run (configured in DAG)
```

### Option 2: Cron Job

```bash
# Add to crontab
crontab -e

# Fetch daily at 6 PM (after market close)
0 18 * * 1-5 cd /path/to/BentleyBudgetBot && python tiingo_integration.py --fetch prices --save-db --technical

# Fetch metadata weekly on Sunday
0 10 * * 0 cd /path/to/BentleyBudgetBot && python tiingo_integration.py --fetch metadata --save-db
```

### Option 3: Manual Schedule

```bash
# Create a simple shell script
cat > fetch_tiingo_daily.sh << 'EOF'
#!/bin/bash
cd /path/to/BentleyBudgetBot
source .venv/bin/activate  # Or your virtual environment
python tiingo_integration.py --fetch prices --technical --save-db
EOF

chmod +x fetch_tiingo_daily.sh

# Run manually when needed
./fetch_tiingo_daily.sh
```

## 🎯 Recommended Tickers

### Quantum Computing Stocks
```python
QUANTUM_TICKERS = ['IONQ', 'QBTS', 'RGTI', 'ARQQ']
```

### AI/Technology Stocks
```python
AI_TICKERS = ['SOUN', 'BBAI', 'AI', 'PLTR']
```

### Large Cap Tech
```python
BIG_TECH = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA']
```

### Combined Portfolio
```python
DEFAULT_TICKERS = [
    # Quantum Computing
    'IONQ', 'QBTS', 'RGTI',
    # AI/ML
    'SOUN', 'PLTR',
    # Big Tech
    'AAPL', 'MSFT', 'GOOGL', 'AMZN'
]
```

## 🔧 Troubleshooting

### Issue: "TIINGO_API_KEY not found"

**Solution**:
```bash
# Verify .env file exists
ls -la .env

# Check contents (should have TIINGO_API_KEY)
grep TIINGO .env

# If missing, add it
echo "TIINGO_API_KEY=your_key_here" >> .env
```

### Issue: "403 Forbidden" or "Premium subscription required"

**Cause**: Some tickers or data types require paid Tiingo subscription

**Solution**:
- Free tier: Most major stocks (AAPL, MSFT, etc.)
- Premium: Small cap, real-time intraday, some quantum stocks
- Alternative: Use yfinance for free alternatives

### Issue: No data returned for ticker

**Possible causes**:
1. Invalid ticker symbol
2. Ticker not available on Tiingo
3. Date range too far in past
4. API rate limiting

**Solution**:
```bash
# Verify ticker exists
python -c "from tiingo_integration import TiingoAPIClient; c=TiingoAPIClient('your_key'); print(c.fetch_ticker_metadata('TICKER'))"

# Try shorter date range
python tiingo_integration.py --tickers TICKER --days 30

# Check API limits (free tier: 500 requests/hour, 20,000/month)
```

### Issue: Database connection failed

**Solution**:
```bash
# Test MySQL connection
mysql -u root -p -e "SELECT 1"

# Create database if missing
mysql -u root -p -e "CREATE DATABASE bbbot1"

# Update .env with correct credentials
# MYSQL_HOST=localhost
# MYSQL_PORT=3306
# MYSQL_USER=root
# MYSQL_PASSWORD=your_password
# MYSQL_DATABASE=bbbot1

# Test connection
python -c "from sqlalchemy import create_engine; engine = create_engine('mysql+pymysql://user:pass@localhost/bbbot1'); engine.connect()"
```

## 📊 Data Quality & Validation

### Check Fetched Data

```bash
# View CSV files
ls -lh data/

# Check latest prices
tail -20 data/IONQ_prices_*.csv

# Count records per ticker
wc -l data/*_prices_*.csv
```

### Validate Database Data

```sql
-- Check record counts
SELECT ticker, COUNT(*) as records, 
       MIN(date) as first_date, 
       MAX(date) as last_date
FROM stock_prices_tiingo
GROUP BY ticker;

-- Check latest prices
SELECT * FROM stock_prices_tiingo
WHERE date = (SELECT MAX(date) FROM stock_prices_tiingo)
ORDER BY ticker;

-- Check for gaps in data
SELECT ticker, date,
       DATEDIFF(date, LAG(date) OVER (PARTITION BY ticker ORDER BY date)) as gap_days
FROM stock_prices_tiingo
HAVING gap_days > 5  -- More than 5 days gap (accounting for weekends)
ORDER BY ticker, date;
```

## 🎨 Visualization Examples

### 1. Price Comparison Chart

```python
# In Streamlit
tickers = ['IONQ', 'QBTS', 'SOUN']
for ticker in tickers:
    df = client.fetch_daily_prices(ticker)
    st.line_chart(df['close'], use_container_width=True)
```

### 2. Technical Indicators Dashboard

```python
df = client.fetch_daily_prices('IONQ')
df = client.calculate_technical_indicators(df)

col1, col2, col3 = st.columns(3)
col1.metric("Latest Price", f"${df['close'].iloc[-1]:.2f}")
col2.metric("RSI", f"{df['rsi'].iloc[-1]:.1f}")
col3.metric("SMA 50", f"${df['sma_50'].iloc[-1]:.2f}")
```

### 3. Volume Analysis

```python
fig = go.Figure()
fig.add_trace(go.Bar(
    x=df.index,
    y=df['volume'],
    name='Volume'
))
st.plotly_chart(fig)
```

## 📚 API Documentation

- **Tiingo API Docs**: https://api.tiingo.com/documentation
- **Python Requests**: https://requests.readthedocs.io/
- **Pandas**: https://pandas.pydata.org/docs/
- **SQLAlchemy**: https://docs.sqlalchemy.org/

## 🔐 Security Best Practices

1. ✅ **Never commit .env file** - Already in .gitignore
2. ✅ **Use environment variables** - Not hardcoded keys
3. ✅ **Rotate API keys regularly** - Every 90 days
4. ✅ **Monitor API usage** - Check Tiingo dashboard
5. ✅ **Limit permissions** - Use read-only database users

## 📈 Performance Tips

1. **Batch requests** - Fetch multiple tickers in one run
2. **Cache results** - Use `@st.cache_data` in Streamlit
3. **Limit date ranges** - Don't fetch more data than needed
4. **Use database** - Faster than repeated API calls
5. **Schedule off-hours** - Run fetches after market close

## 🎉 Next Steps

1. ✅ Test your API connection: `python test_tiingo.py`
2. ✅ Fetch sample data: `python tiingo_integration.py --tickers AAPL`
3. ✅ View in Streamlit: See Investment Analysis page
4. ✅ Setup automation: Configure Airflow DAG or cron
5. ✅ Add custom tickers: Update DEFAULT_TICKERS in scripts
6. ✅ Build visualizations: Use fetched data in Streamlit pages

---

**Happy Trading! 📊💹**
