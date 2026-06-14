# BentleyBot Pipeline Package

Professional Python package structure for stock data ingestion and financial metrics calculation.

## 📦 Package Structure

```
bbbot1_pipeline/
├── __init__.py              # Package initialization
├── config.env               # Environment variables (API keys, DB config)
├── db.py                    # Database utilities
├── ingest_yfinance.py       # Yahoo Finance data ingestion
├── ingest_alpha_vantage.py  # Alpha Vantage fundamentals ingestion
└── derive_ratios.py         # Financial metrics calculation
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install yfinance pandas pymysql sqlalchemy python-dotenv requests
```

### 2. Configure Environment

Edit `config.env` with your credentials:

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=bbbot1

ALPHA_VANTAGE_API_KEY=your_key_here
TIINGO_API_KEY=your_key_here
```

### 3. Test Database Connection

```bash
python -m bbbot1_pipeline.db
```

## 📊 Usage Examples

### Load Ticker Configuration

```python
from bbbot1_pipeline import load_tickers_config

# Load centralized ticker config
config = load_tickers_config()
quantum_tickers = config['tickers']['quantum']  # ['IONQ', 'QBTS', 'SOUN', 'RGTI']
all_tickers = config['tickers']['all']  # All tracked tickers
```

### Ingest Stock Prices (yfinance)

```python
from bbbot1_pipeline import run_yfinance_ingestion, load_tickers_config

# Fetch 2 years of data for quantum stocks
config = load_tickers_config()
tickers = config['tickers']['quantum']
run_yfinance_ingestion(tickers, lookback_days=730)
```

### Ingest Fundamentals (Alpha Vantage)

```python
from bbbot1_pipeline.ingest_alpha_vantage import run_alpha_vantage_ingestion

tickers = ["RGTI", "QBTS", "IONQ", "SOUN"]
run_alpha_vantage_ingestion(tickers)
```

### Calculate Metrics

```python
from bbbot1_pipeline import calculate_moving_averages, generate_ticker_summary

# Get moving averages
ma_data = calculate_moving_averages("RGTI")
print(ma_data)

# Get complete summary
summary = generate_ticker_summary("RGTI")
print(summary)
```

### Use in Airflow DAG

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from bbbot1_pipeline import run_yfinance_ingestion

def fetch_quantum_stocks():
    tickers = ["RGTI", "QBTS", "IONQ", "SOUN"]
    run_yfinance_ingestion(tickers)

with DAG('quantum_stocks_ingestion', ...) as dag:
    ingest_task = PythonOperator(
        task_id='ingest_yfinance',
        python_callable=fetch_quantum_stocks
    )
```

## 🗄️ Database Tables

### stock_prices_yf
Stores Yahoo Finance price data.

| Column | Type | Description |
|--------|------|-------------|
| ticker | VARCHAR(10) | Stock symbol |
| date | DATE | Trading date |
| open | DECIMAL(18,4) | Opening price |
| high | DECIMAL(18,4) | High price |
| low | DECIMAL(18,4) | Low price |
| close | DECIMAL(18,4) | Closing price |
| adj_close | DECIMAL(18,4) | Adjusted close |
| volume | BIGINT | Trading volume |

**Primary Key**: `(ticker, date)`

### stock_fundamentals
Stores company fundamental data.

| Column | Type | Description |
|--------|------|-------------|
| ticker | VARCHAR(10) | Stock symbol |
| report_date | DATE | Report date |
| market_cap | BIGINT | Market capitalization |
| pe_ratio | DECIMAL(10,2) | Price-to-Earnings ratio |
| eps | DECIMAL(10,4) | Earnings per share |
| revenue | BIGINT | Total revenue |
| net_income | BIGINT | Net income |
| total_assets | BIGINT | Total assets |
| total_liabilities | BIGINT | Total liabilities |

**Primary Key**: `(ticker, report_date)`

**Indexes**: 
- `idx_ticker_report_date` on `(ticker, report_date)`
- `idx_report_date` on `(report_date)`
- `idx_ticker_fundamentals` on `(ticker)`

### Performance Optimization

Run `sql/create_indexes.sql` to create optimized indexes:

```bash
mysql -u root -p -h 127.0.0.1 -P 3307 < bbbot1_pipeline/sql/create_indexes.sql
```

**Indexes created**:
- `stock_prices_yf`: `(ticker, date)`, `(date)`, `(ticker)`
- `stock_fundamentals`: `(ticker, report_date)`, `(report_date)`, `(ticker)`

These indexes dramatically improve query performance for:
- Ticker + date range queries (WHERE ticker = 'IONQ' AND date >= ...)
- Cross-ticker aggregations (GROUP BY ticker WHERE date >= ...)
- Single ticker lookups

## 🔧 Module Reference

### db.py
Database connection and utilities.

**Functions:**
- `get_mysql_connection()` - Get raw PyMySQL connection
- `get_mysql_engine()` - Get SQLAlchemy engine
- `insert_stock_prices(df, table_name)` - Insert price data
- `query_latest_prices(ticker, days)` - Get recent prices
- `query_fundamentals(ticker)` - Get fundamental data
- `create_fundamentals_table()` - Create fundamentals table

### ingest_yfinance.py
Yahoo Finance data ingestion.

**Functions:**
- `fetch_yfinance_prices(ticker, start, end)` - Fetch single ticker
- `fetch_yfinance_batch(tickers, start, end)` - Fetch multiple tickers
- `run_yfinance_ingestion(tickers, lookback_days)` - Main ingestion function

### ingest_alpha_vantage.py
Alpha Vantage fundamental data ingestion.

**Functions:**
- `fetch_company_overview(ticker)` - Fetch fundamentals from API
- `store_fundamentals(ticker, data)` - Store in database
- `run_alpha_vantage_ingestion(tickers)` - Main ingestion function

**Rate Limits:**
- Free tier: 5 API calls per minute
- Script automatically adds 12-second delays between calls

### derive_ratios.py
Financial metrics calculation.

**Functions:**
- `calculate_moving_averages(ticker, periods)` - Calculate MAs
- `calculate_pe_ratio(ticker)` - Calculate P/E ratio
- `calculate_daily_returns(ticker, days)` - Calculate daily returns
- `calculate_volatility(ticker, days)` - Calculate volatility
- `generate_ticker_summary(ticker)` - Complete summary

## 🔐 Security Notes

1. **Never commit `config.env` with real credentials**
2. Add to `.gitignore`:
   ```
   bbbot1_pipeline/config.env
   bbbot1_pipeline/.env
   ```
3. Use environment variables in production
4. Rotate API keys regularly

## 📈 Integration with Existing Stack

This package integrates with your BentleyBot infrastructure:

- **MySQL** (port 3307) - Data storage
- **Airflow DAGs** - Scheduled ingestion
- **Airbyte** - Syncs to Snowflake
- **Snowflake** (MARKET_DATA) - Analytics warehouse

## 🐛 Troubleshooting

### Import Error
```bash
# Make sure you're in the project root
cd C:\Users\winst\BentleyBudgetBot

# Install package in development mode
pip install -e .
```

### Database Connection Failed
```bash
# Test MySQL is running
docker ps | findstr mysql

# Test connection
python -m bbbot1_pipeline.db
```

### API Rate Limit
Alpha Vantage free tier: 5 calls/minute, 500 calls/day
- Increase delay between calls
- Consider upgrading API plan

## 📝 License

Part of BentleyBot project - Internal use only

## 👤 Author

BentleyBot Team - December 2025
