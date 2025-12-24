# Multi-Source Fundamentals - Quick Reference

## 🚀 Quick Start

### 1. Get API Keys (2 minutes)
```bash
# Alpha Vantage (Primary - Most comprehensive)
# Visit: https://www.alphavantage.co/support/#api-key
# Free: 5 calls/min, 500/day

# Tiingo (Fallback - Basic metadata)
# Visit: https://www.tiingo.com/
# Free: 500 calls/hour, 20,000/month
```

### 2. Configure Environment
```bash
# Add to .env file
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
TIINGO_API_KEY=your_tiingo_key
```

### 3. Test Installation
```bash
# Quick test
python test_fundamentals.py

# Single ticker test
python -c "from frontend.utils.fundamentals_fetcher import cached_fetch_fundamentals; print(cached_fetch_fundamentals('AAPL'))"
```

## 📊 Data Source Priority

```
User Request → Try Alpha Vantage (30+ metrics)
              ↓ (if rate limited/fails)
              Try Tiingo (basic metadata)
              ↓ (if fails)
              Try yfinance (backup, no key)
              ↓ (if fails)
              Return None
```

## 🎯 Key Features

### Rate Limiting
- **Alpha Vantage**: 5 calls/min (automatic wait)
- **Tiingo**: 5 calls/min (configurable)
- **yfinance**: No limits (but less reliable)

### Caching
- **Duration**: 1 hour per ticker
- **Clear**: `st.cache_data.clear()` in Streamlit
- **Purpose**: Minimize API calls, improve speed

### Error Handling
- HTTP 429 → Automatic fallback to next source
- API key missing → Skip to next source
- Invalid ticker → Return None gracefully

## 📱 Usage in Investment Analysis Page

### User Interface
1. Select ticker from dropdown
2. Choose data source:
   - **Auto (Alpha Vantage → Tiingo → yfinance)** ← Recommended
   - **yfinance only** ← No API keys needed
3. View fundamentals with source indicator

### Display
```
✅ Data from: alpha_vantage
---------------------------
Market Cap: $3.10T
PE Ratio: 28.50
PEG Ratio: 2.31
...
```

## 🔧 Code Examples

### Fetch Fundamentals
```python
from frontend.utils.fundamentals_fetcher import cached_fetch_fundamentals

# Auto-fetch with caching (1 hour)
data = cached_fetch_fundamentals('AAPL')

# Access fields
market_cap = data.get('market_cap')
pe_ratio = data.get('pe_ratio')
source = data.get('source')  # 'alpha_vantage', 'tiingo', or 'yfinance'
```

### Custom Source Order
```python
from frontend.utils.fundamentals_fetcher import fetch_fundamentals_multi_source

# Try specific sources only
data = fetch_fundamentals_multi_source(
    'MSFT',
    sources=['tiingo', 'yfinance']  # Skip Alpha Vantage
)
```

### Format Values
```python
from frontend.utils.fundamentals_fetcher import format_fundamental_value

# Automatic formatting
formatted = format_fundamental_value('market_cap', 3100000000000)
# Returns: "$3.10T"

formatted = format_fundamental_value('dividend_yield', 0.0052)
# Returns: "0.52%"
```

## 📈 Available Fundamentals

### Alpha Vantage (30+ fields)
✅ Market Cap, PE, PEG, P/B, P/S  
✅ Profit/Operating Margins  
✅ ROE, ROA, Revenue Per Share  
✅ Dividend Yield, EPS  
✅ Quarterly Growth (Revenue & Earnings)  
✅ Analyst Target Price  
✅ Sector, Industry  
✅ 52W High/Low, Moving Averages  
✅ Beta  

### Tiingo (Limited)
⚠️ Company Name  
⚠️ Ticker Symbol  
⚠️ Description  
⚠️ Start/End Dates  

### yfinance (Moderate)
✓ Market Cap, PE ratios  
✓ Basic margins  
✓ Dividend info  
✓ Balance sheet items  

## 🐛 Troubleshooting

### "Too Many Requests" Error
```bash
# Check rate limit status
python -c "from frontend.utils.fundamentals_fetcher import alpha_vantage_limiter; import time; print(f'Last call: {time.time() - alpha_vantage_limiter.last_call_time:.0f}s ago')"

# Solution:
# 1. Wait 1 minute (rate limit resets)
# 2. System automatically tries next source
# 3. Or use "yfinance only" mode
```

### API Key Not Working
```powershell
# Check if set
echo $env:ALPHA_VANTAGE_API_KEY

# Test manually
curl "https://www.alphavantage.co/query?function=OVERVIEW&symbol=AAPL&apikey=$env:ALPHA_VANTAGE_API_KEY"

# Re-set if needed
$env:ALPHA_VANTAGE_API_KEY="your_key_here"
```

### Missing Fundamentals
```python
# Check what data is returned
data = cached_fetch_fundamentals('TICKER')
print(f"Source: {data.get('source')}")
print(f"Available fields: {list(data.keys())}")

# Try different ticker
# Some tickers have limited data
```

### Cache Issues
```python
# Clear Streamlit cache
import streamlit as st
st.cache_data.clear()

# Or restart app
# Ctrl+C, then: streamlit run streamlit_app.py
```

## 📊 Rate Limit Management

### Daily Limits
- **Alpha Vantage**: 500 calls/day (resets midnight EST)
- **Tiingo**: 20,000 calls/month (free tier)

### Monitoring Usage
```python
# Add to code for debugging
from frontend.utils.fundamentals_fetcher import alpha_vantage_limiter, tiingo_limiter

print(f"Alpha Vantage calls: Track in logs")
print(f"Tiingo calls: Track in logs")
```

### Optimization Tips
1. **Use cache** - 1 hour TTL reduces calls by 60x
2. **Batch requests** - Fetch all portfolio tickers at once
3. **Off-hours fetching** - Pre-fetch during low usage
4. **Database storage** - Store results for longer periods

## 🎨 Display Formatting

### Automatic Formatting
```python
format_fundamental_value('market_cap', 3100000000000)   # "$3.10T"
format_fundamental_value('market_cap', 150000000000)    # "$150.00B"
format_fundamental_value('pe_ratio', 28.5)              # "28.50"
format_fundamental_value('dividend_yield', 0.0052)      # "0.52%"
format_fundamental_value('profit_margin', 0.2531)       # "25.31%"
```

### Custom Formatting
```python
value = data.get('market_cap')
if value and value != 'N/A':
    if isinstance(value, str):
        value = float(value)
    formatted = f"${value/1e9:.2f}B"  # Custom billions
```

## 🔒 Security Best Practices

### API Key Storage
```bash
# ✅ Good: Environment variables
export ALPHA_VANTAGE_API_KEY=key

# ✅ Good: .env file (in .gitignore)
echo "ALPHA_VANTAGE_API_KEY=key" >> .env

# ❌ Bad: Hardcoded in code
api_key = "abc123def456"  # NEVER DO THIS
```

### Vercel/Production Deployment
```bash
# Add to Vercel environment variables
# Dashboard → Settings → Environment Variables
ALPHA_VANTAGE_API_KEY=your_key
TIINGO_API_KEY=your_key
```

## 📚 Related Documentation

- [Full Alpha Vantage Setup Guide](ALPHA_VANTAGE_SETUP.md)
- [Tiingo Integration Guide](TIINGO_INTEGRATION_GUIDE.md)
- [RBAC Setup](INVESTMENT_ANALYSIS_RBAC.md)
- [Quick Commands](TIINGO_QUICK_COMMANDS.md)

## ⚡ Performance Tips

### Speed Optimization
1. **Enable caching** - Already done with `@st.cache_data`
2. **Parallel fetching** - Use `concurrent.futures` for multiple tickers
3. **Database backend** - Store frequently accessed data in MySQL
4. **CDN for static data** - Sector/industry info rarely changes

### Cost Optimization
1. **Free tiers sufficient** - For portfolios < 50 tickers
2. **Smart caching** - 1 hour = 24x fewer calls
3. **Selective fetching** - Only fetch visible tickers
4. **Fallback strategy** - yfinance is free unlimited

## 🎯 Common Workflows

### Portfolio Analysis (20 tickers)
```python
tickers = ['AAPL', 'MSFT', 'GOOGL', ...]  # 20 tickers

for ticker in tickers:
    data = cached_fetch_fundamentals(ticker)
    # Process data...
    time.sleep(0.1)  # Small delay between

# With caching: ~20 API calls first time
# Subsequent: 0 API calls (served from cache)
```

### Real-time Updates
```python
# Clear cache for fresh data
st.cache_data.clear()

# Or set shorter TTL
@st.cache_data(ttl=600)  # 10 minutes
def fetch_with_short_cache(ticker):
    return cached_fetch_fundamentals(ticker)
```

### Batch Processing
```python
from concurrent.futures import ThreadPoolExecutor

def fetch_ticker(ticker):
    return cached_fetch_fundamentals(ticker)

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(fetch_ticker, tickers))
```

## 📞 Support

### API Provider Support
- **Alpha Vantage**: support@alphavantage.co
- **Tiingo**: support@tiingo.com

### Project Issues
- GitHub Issues: [Your Repo]/issues
- Documentation: See `docs/` folder

### Quick Help
```bash
# Test script
python test_fundamentals.py

# View logs
tail -f logs/streamlit.log

# Check environment
python -c "import os; print('Alpha Vantage:', 'SET' if os.getenv('ALPHA_VANTAGE_API_KEY') else 'MISSING')"
```
