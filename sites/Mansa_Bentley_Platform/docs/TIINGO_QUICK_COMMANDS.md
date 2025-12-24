# Tiingo API - Quick Command Reference

## 🚀 Essential Commands

### Setup & Testing
```bash
# 1. Add API key to .env
echo "TIINGO_API_KEY=your_api_key_here" >> .env

# 2. Test connection
python test_tiingo.py

# 3. Activate virtual environment (if using)
.\.venv\Scripts\Activate.ps1  # PowerShell
source .venv/bin/activate      # Bash
```

### Fetch Data - Common Scenarios

```bash
# Scenario 1: Quick test with major stocks
python tiingo_integration.py --tickers AAPL MSFT --days 30

# Scenario 2: Quantum computing stocks with technical analysis
python tiingo_integration.py --tickers IONQ QBTS SOUN RGTI --technical --save-csv

# Scenario 3: Full portfolio - 2 years with indicators and database
python tiingo_integration.py --fetch all --technical --save-db --save-csv

# Scenario 4: Custom ticker list for today's trading
python tiingo_integration.py --tickers AAPL GOOGL AMZN NVDA TSLA --days 90 --technical

# Scenario 5: Update database with latest prices
python tiingo_integration.py --fetch prices --save-db
```

### View Results

```bash
# Check CSV files
ls data/

# View latest data
cat data/AAPL_prices_*.csv | tail -5

# Count records
wc -l data/*.csv

# Launch Streamlit dashboard
streamlit run "pages/01_📈_Investment_Analysis.py"
```

## 📊 Ticker Lists

```bash
# Quantum Computing
python tiingo_integration.py --tickers IONQ QBTS RGTI ARQQ --technical

# AI/ML Stocks
python tiingo_integration.py --tickers SOUN BBAI PLTR AI --technical

# Big Tech (FAANG+)
python tiingo_integration.py --tickers AAPL MSFT GOOGL AMZN META NVDA TSLA --technical

# All Combined (Default)
python tiingo_integration.py --technical --save-csv
```

## 🗄️ Database Operations

```bash
# Create database and tables
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS bbbot1"
mysql -u root -p bbbot1 < mysql_setup.sql/investment_analysis_schema.sql

# Fetch and save to database
python tiingo_integration.py --save-db

# Query data
mysql -u root -p bbbot1 -e "SELECT ticker, COUNT(*) FROM stock_prices_tiingo GROUP BY ticker"

# Check latest prices
mysql -u root -p bbbot1 -e "SELECT * FROM stock_prices_tiingo WHERE date = CURDATE() ORDER BY ticker"
```

## 🔄 Automation

```bash
# Windows Task Scheduler (PowerShell)
$action = New-ScheduledTaskAction -Execute "python" -Argument "tiingo_integration.py --save-db --technical" -WorkingDirectory "C:\path\to\BentleyBudgetBot"
$trigger = New-ScheduledTaskTrigger -Daily -At 6PM
Register-ScheduledTask -TaskName "TiingoDataFetch" -Action $action -Trigger $trigger

# Linux/Mac Cron (edit crontab)
crontab -e
# Add: 0 18 * * 1-5 cd /path/to/BentleyBudgetBot && python tiingo_integration.py --save-db

# Manual script
cat > fetch_daily.sh << 'EOF'
#!/bin/bash
cd /path/to/BentleyBudgetBot
source .venv/bin/activate
python tiingo_integration.py --fetch prices --technical --save-db --save-csv
EOF
chmod +x fetch_daily.sh
./fetch_daily.sh
```

## 📈 Common Workflows

### Workflow 1: Daily Market Close Update
```bash
# After market close (4 PM ET), fetch latest prices
python tiingo_integration.py --fetch prices --save-db
streamlit run "pages/01_📈_Investment_Analysis.py"
```

### Workflow 2: Weekend Analysis
```bash
# Saturday morning - full analysis with technical indicators
python tiingo_integration.py --fetch all --technical --save-csv --save-db

# Review CSVs
ls -lh data/

# View in Streamlit with full indicators
streamlit run "pages/01_📈_Investment_Analysis.py"
```

### Workflow 3: New Ticker Research
```bash
# Research a new ticker
python tiingo_integration.py --tickers NEWTICKER --days 365 --technical --save-csv

# View CSV
cat data/NEWTICKER_prices_*.csv

# Add to Streamlit for comparison
# Edit pages/01_📈_Investment_Analysis.py and add to available_tickers
```

### Workflow 4: Historical Backfill
```bash
# Fetch 5 years of data for analysis
python tiingo_integration.py --tickers AAPL --days 1825 --technical --save-db
```

## 🔍 Troubleshooting Commands

```bash
# Check environment variables
env | grep TIINGO

# Test API key directly
curl -H "Authorization: Token YOUR_KEY" "https://api.tiingo.com/tiingo/daily/aapl"

# Check database connection
python -c "from sqlalchemy import create_engine; engine = create_engine('mysql+pymysql://user:pass@localhost/bbbot1'); print(engine.connect())"

# Verify installed packages
pip list | grep -E "requests|pandas|sqlalchemy|pymysql|python-dotenv"

# Check file permissions
ls -la data/
ls -la .env

# View recent error logs
tail -50 data/*.log  # If logging to file
```

## 📊 Data Validation

```bash
# Python quick checks
python << 'EOF'
import pandas as pd
from pathlib import Path

# List all CSV files
for f in Path('data').glob('*_prices_*.csv'):
    df = pd.read_csv(f)
    print(f"{f.name}: {len(df)} records, {df['date'].min()} to {df['date'].max()}")
EOF

# SQL checks
mysql -u root -p bbbot1 << 'EOF'
SELECT 
    ticker,
    COUNT(*) as records,
    MIN(date) as first_date,
    MAX(date) as last_date,
    AVG(close) as avg_price
FROM stock_prices_tiingo
GROUP BY ticker
ORDER BY ticker;
EOF
```

## 🎯 Performance Optimization

```bash
# Fetch only what you need
python tiingo_integration.py --tickers AAPL --days 30  # Fast

# Use batching for many tickers
python tiingo_integration.py --tickers $(cat my_tickers.txt | tr '\n' ' ')

# Save to database for reuse
python tiingo_integration.py --save-db  # Fetch once, query many times

# Parallel fetching (advanced)
parallel -j 4 python tiingo_integration.py --tickers {} ::: AAPL MSFT GOOGL AMZN
```

## 🔐 Security Commands

```bash
# Check .env is not in git
git ls-files | grep .env  # Should return nothing

# Verify .gitignore
cat .gitignore | grep .env  # Should show .env

# Rotate API key (get new one from Tiingo, then update)
sed -i 's/TIINGO_API_KEY=old_key/TIINGO_API_KEY=new_key/' .env

# Check file permissions (Linux/Mac)
chmod 600 .env  # Owner read/write only
```

## 📦 Package Management

```bash
# Install required packages
pip install requests pandas sqlalchemy pymysql python-dotenv plotly

# Or from requirements
pip install -r requirements.txt

# Verify installation
python -c "import requests, pandas, sqlalchemy, pymysql, dotenv; print('All packages installed')"
```

## 🎨 Streamlit Integration

```bash
# Run Investment Analysis page
streamlit run "pages/01_📈_Investment_Analysis.py"

# Run specific page
streamlit run streamlit_app.py

# Run with specific port
streamlit run "pages/01_📈_Investment_Analysis.py" --server.port 8502

# Run in browser-less mode
streamlit run "pages/01_📈_Investment_Analysis.py" --server.headless true
```

## 💡 Quick Tips

```bash
# Tip 1: Always test with one ticker first
python tiingo_integration.py --tickers AAPL --days 7

# Tip 2: Use --save-csv to inspect data before database commit
python tiingo_integration.py --save-csv && ls -lh data/

# Tip 3: Check API limits (free tier: 500/hour, 20000/month)
# Visit: https://api.tiingo.com/account/usage

# Tip 4: Use nohup for long-running fetches
nohup python tiingo_integration.py --days 1825 --save-db > fetch.log 2>&1 &

# Tip 5: Create aliases for frequent commands
alias fetch-prices='python tiingo_integration.py --fetch prices --save-db'
alias fetch-tech='python tiingo_integration.py --technical --save-csv'
```

## 🆘 Emergency Recovery

```bash
# If data fetch fails mid-way, check what you have
ls -lh data/

# If database is corrupted, rebuild from CSV
mysql -u root -p bbbot1 -e "TRUNCATE TABLE stock_prices_tiingo"
for f in data/*_prices_*.csv; do
    # Import CSV logic here
    echo "Import $f"
done

# If API key stops working, get new one
# 1. Visit https://www.tiingo.com/
# 2. Generate new key
# 3. Update .env
# 4. Test: python test_tiingo.py
```

---

## 📞 Quick Help

```bash
# Get help on any command
python tiingo_integration.py --help
python test_tiingo.py --help

# View documentation
cat docs/TIINGO_INTEGRATION_GUIDE.md
```

**Remember**: Always test with a small dataset first! 🧪
