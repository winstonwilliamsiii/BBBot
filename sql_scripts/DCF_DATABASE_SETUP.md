# DCF Analysis - Database Setup Guide

**Database**: Bentley_Budget  
**Connection**: 127.0.0.1:3306  
**User**: root@localhost  
**Last Updated**: February 16, 2026

---

## 📊 Quick Start

### 1. Create Database Tables

The DCF analysis requires two tables in your `Bentley_Budget` database:

```bash
# Run the setup script
mysql -h 127.0.0.1 -u root -p Bentley_Budget < sql_scripts/setup_dcf_database.sql
```

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# DCF Database Configuration
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=Bentley_Budget
```

### 3. Verify Setup

```sql
-- Connect to MySQL
mysql -h 127.0.0.1 -u root -p Bentley_Budget

-- Check tables exist
SHOW TABLES LIKE 'fundamentals_annual';
SHOW TABLES LIKE 'prices_latest';

-- View sample data
SELECT * FROM fundamentals_annual LIMIT 5;
SELECT * FROM prices_latest LIMIT 5;
```

---

## 🗄️ Database Schema

### Table: fundamentals_annual

Stores historical fundamental financial data.

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT | Primary key |
| ticker | VARCHAR(10) | Stock symbol |
| fiscal_year | INT | Year of data |
| revenue | DECIMAL(20,2) | Annual revenue (USD) |
| free_cash_flow | DECIMAL(20,2) | FCF (USD) |
| shares_outstanding | DECIMAL(20,2) | Shares (millions) |
| net_debt | DECIMAL(20,2) | Total debt - cash |
| cash | DECIMAL(20,2) | Cash & equivalents |

**Required**: Minimum 5 years of historical data per ticker.

### Table: prices_latest

Stores current market prices for comparison.

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT | Primary key |
| ticker | VARCHAR(10) | Stock symbol |
| price | DECIMAL(12,4) | Current price |
| as_of_date | DATE | Price date |
| volume | BIGINT | Trading volume |
| market_cap | DECIMAL(20,2) | Market cap |

---

## 📥 Populating Data

### Option 1: Manual Entry (Example)

```sql
-- Add Apple fundamentals (5 years)
INSERT INTO fundamentals_annual 
    (ticker, fiscal_year, revenue, free_cash_flow, shares_outstanding, net_debt, cash)
VALUES 
    ('AAPL', 2023, 383285000000, 99584000000, 15550.06, -60700000000, 166300000000),
    ('AAPL', 2022, 394328000000, 111443000000, 15908.12, -51700000000, 156200000000),
    ('AAPL', 2021, 365817000000, 92953000000, 16426.79, -85100000000, 130100000000),
    ('AAPL', 2020, 274515000000, 73365000000, 16976.76, -76300000000, 90900000000),
    ('AAPL', 2019, 260174000000, 58896000000, 17772.95, -100700000000, 102900000000);

-- Add current price
INSERT INTO prices_latest (ticker, price, as_of_date)
VALUES ('AAPL', 189.50, CURDATE());
```

### Option 2: Python Script (Automated)

Create `scripts/populate_fundamentals.py`:

```python
import yfinance as yf
import mysql.connector
from datetime import datetime

# Connect to database
conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='your_password',
    database='Bentley_Budget'
)
cursor = conn.cursor()

# Fetch data for a ticker
ticker = 'AAPL'
stock = yf.Ticker(ticker)

# Get historical fundamentals (simplified)
financials = stock.financials
cashflow = stock.cashflow
balance = stock.balance_sheet

# Insert into database (you'll need to parse and format the data)
# See full script in sql_scripts/populate_fundamentals.py
```

### Option 3: API Integration

Use Financial APIs:
- **Alpha Vantage**: https://www.alphavantage.co/
- **Financial Modeling Prep**: https://financialmodelingprep.com/
- **IEX Cloud**: https://iexcloud.io/

---

## 🧪 Testing DCF Analysis

### 1. Test with Sample Data

```bash
# Run DCF analysis for Apple
python -c "from frontend.components.dcf_analysis import run_equity_dcf; import json; print(json.dumps(run_equity_dcf('AAPL'), indent=2))"
```

### 2. Test via Dashboard

1. Start Streamlit: `streamlit run streamlit_app.py`
2. Navigate to "Fundamental Analysis" section
3. Enter ticker: `AAPL`
4. Click "Run DCF Analysis"
5. Review valuation results

### 3. Expected Output

```json
{
  "ticker": "AAPL",
  "current_price": 189.50,
  "intrinsic_value_per_share": 205.32,
  "valuation_label": "Undervalued",
  "upside_percent": 8.35,
  "confidence_score": 0.87,
  "growth_rate_used": 0.0824,
  "term_years": 10
}
```

---

## 📊 Data Sources

### Recommended Sources for Historical Data

1. **Yahoo Finance** (Free)
   - Use `yfinance` Python library
   - Limited to public companies
   - Reliable for most equities

2. **Alpha Vantage** (Free tier available)
   - API key required
   - Good fundamental data
   - 500 calls/day limit

3. **SEC EDGAR** (Free)
   - Official filings (10-K, 10-Q)
   - Most accurate data
   - Requires parsing

4. **Financial Modeling Prep** (Paid)
   - Clean API
   - Historical fundamentals
   - Real-time updates

---

## 🔍 Verification Queries

### Check Data Coverage

```sql
-- Tickers with sufficient data (5+ years)
SELECT 
    ticker,
    COUNT(*) as years,
    MIN(fiscal_year) as earliest,
    MAX(fiscal_year) as latest
FROM fundamentals_annual
GROUP BY ticker
HAVING COUNT(*) >= 5;
```

### Find Missing Prices

```sql
-- Fundamentals without prices
SELECT DISTINCT f.ticker
FROM fundamentals_annual f
LEFT JOIN prices_latest p ON f.ticker = p.ticker
WHERE p.ticker IS NULL;
```

### Data Quality Check

```sql
-- Check for null FCF values
SELECT ticker, fiscal_year, free_cash_flow
FROM fundamentals_annual
WHERE free_cash_flow IS NULL OR free_cash_flow = 0;
```

---

## ⚠️ Troubleshooting

### "No fundamentals found for ticker"

**Cause**: Ticker not in `fundamentals_annual` table  
**Fix**: Add historical data for the ticker (minimum 5 years)

### "No current price found for ticker"

**Cause**: Ticker not in `prices_latest` table  
**Fix**: 
```sql
INSERT INTO prices_latest (ticker, price, as_of_date)
VALUES ('YOUR_TICKER', 100.00, CURDATE());
```

### "MySQL connection failed"

**Cause**: Database not running or wrong credentials  
**Fix**:
```bash
# Check MySQL is running
mysql -h 127.0.0.1 -u root -p

# Verify credentials in .env file
DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=your_actual_password
DB_NAME=Bentley_Budget
```

---

## 📚 Next Steps

1. ✅ Run `setup_dcf_database.sql` to create tables
2. ✅ Populate with at least 3-5 stocks for testing
3. ✅ Set environment variables in `.env`
4. ✅ Test DCF analysis via dashboard
5. ⚠️ Set up automated data updates (optional)
6. ⚠️ Create pull request to merge DCF feature

---

## 🔗 Related Files

- [frontend/components/dcf_analysis.py](../frontend/components/dcf_analysis.py) - DCF calculation engine
- [frontend/components/dcf_widget.py](../frontend/components/dcf_widget.py) - Dashboard widget
- [sql_scripts/setup_dcf_database.sql](../sql_scripts/setup_dcf_database.sql) - Database schema
- [.env.example](../.env.example) - Configuration template
