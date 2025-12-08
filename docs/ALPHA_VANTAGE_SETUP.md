# Alpha Vantage API Setup Guide

## Overview
Alpha Vantage is used as a fallback source for comprehensive fundamental data when Tiingo API is rate-limited. It provides 30+ fundamental metrics including PE ratios, margins, growth rates, and more.

## Getting Your API Key

### 1. Sign Up for Free API Key
1. Visit: https://www.alphavantage.co/support/#api-key
2. Enter your email and first name
3. Click "GET FREE API KEY"
4. Check your email for the API key

**Free Tier Limits:**
- 5 API calls per minute
- 500 API calls per day
- No credit card required

### 2. Configure Your API Key

Add to your `.env` file:
```bash
# Alpha Vantage API Key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
```

Or set as environment variable:
```powershell
# PowerShell
$env:ALPHA_VANTAGE_API_KEY="your_alpha_vantage_key_here"

# Or add to your system environment variables
```

### 3. Verify Installation

Test your API key:
```bash
python -c "from frontend.utils.fundamentals_fetcher import fetch_alpha_vantage_fundamentals; import os; print(fetch_alpha_vantage_fundamentals('AAPL', os.getenv('ALPHA_VANTAGE_API_KEY')))"
```

Expected output:
```
{'ticker': 'AAPL', 'company_name': 'Apple Inc', 'market_cap': '3100000000000', ...}
```

## Multi-Source Strategy

### Fallback Priority
The system tries sources in this order:
1. **Alpha Vantage** (most comprehensive, 30+ metrics)
2. **Tiingo** (basic metadata only)
3. **yfinance** (backup, no API key needed)

### Why Alpha Vantage First?
- More comprehensive fundamentals than Tiingo
- Includes analyst targets, growth rates, sector info
- More reliable for fundamental analysis
- Tiingo free tier has limited fundamental endpoints

## Available Fundamentals from Alpha Vantage

### Valuation Metrics
- Market Cap
- PE Ratio (Trailing & Forward)
- PEG Ratio
- Price to Book
- Price to Sales
- EV to Revenue
- EV to EBITDA

### Profitability
- Profit Margin
- Operating Margin
- Return on Equity (ROE)
- Return on Assets (ROA)

### Growth Metrics
- Quarterly Revenue Growth (YoY)
- Quarterly Earnings Growth (YoY)
- Revenue Per Share

### Dividend Info
- Dividend Yield
- Dividend Per Share
- Ex-Dividend Date
- Dividend Date

### Technical Indicators
- 52 Week High/Low
- 50-Day Moving Average
- 200-Day Moving Average
- Beta

### Company Info
- Sector
- Industry
- Analyst Target Price
- EPS (Trailing)

## Rate Limiting

### Built-in Protection
The system automatically:
- Limits to 5 calls per minute (Alpha Vantage free tier)
- Caches results for 1 hour (Streamlit `@st.cache_data`)
- Falls back to Tiingo/yfinance if rate limited

### Manual Rate Limit Handling
If you see `"Too Many Requests"` error:
1. Wait 1 minute (minute-based rate limiting)
2. Or wait until next day (daily limit reset)
3. System will automatically try next source (Tiingo/yfinance)

### Checking Rate Limit Status
Add this code to debug:
```python
from frontend.utils.fundamentals_fetcher import alpha_vantage_limiter

# Check time since last call
import time
print(f"Time since last call: {time.time() - alpha_vantage_limiter.last_call_time:.2f}s")
```

## Integration with Investment Analysis Page

### Automatic Integration
The Investment Analysis page automatically uses multi-source fetching:
1. User selects ticker
2. Choose "Auto (Alpha Vantage → Tiingo → yfinance)" in radio button
3. System tries Alpha Vantage first
4. Success indicator shows which source was used

### Manual Source Selection
Users can also choose "yfinance only" to bypass API calls if:
- Not concerned about rate limits
- Don't need comprehensive fundamentals
- Prefer real-time Yahoo Finance data

## Troubleshooting

### API Key Not Working
```bash
# Check if key is set
echo $env:ALPHA_VANTAGE_API_KEY

# Test with curl
curl "https://www.alphavantage.co/query?function=OVERVIEW&symbol=AAPL&apikey=YOUR_KEY"
```

### Still Getting Rate Limits
- Check if you exceeded 500 calls/day limit
- Try tomorrow (daily limit resets at midnight EST)
- System will automatically use Tiingo/yfinance fallback

### Missing Fundamentals
Some tickers may not have complete data:
- Check if ticker is valid (US markets preferred)
- Try a different ticker (e.g., AAPL, MSFT, GOOGL)
- Alpha Vantage focuses on US equities

### Error: "Please consider optimizing..."
This is Alpha Vantage's rate limit message. Solution:
- Wait 1 minute for next call
- Or system automatically falls back to Tiingo/yfinance

## Best Practices

### Development
1. Use `.env` file for API keys (never commit!)
2. Add `.env` to `.gitignore`
3. Test with known good tickers (AAPL, MSFT)

### Production
1. Set environment variables in hosting platform
2. Use cached results to minimize API calls
3. Monitor rate limit usage in logs

### Data Freshness
- Fundamentals cached for 1 hour
- Daily data updates from Alpha Vantage
- Clear cache with: `st.cache_data.clear()`

## Cost Optimization

### Free Tier (Recommended for Small Projects)
- 5 calls/minute = enough for interactive use
- 500 calls/day = ~20 tickers × 25 queries
- Perfect for personal portfolios

### Premium Tiers (If Needed)
- 75 calls/minute: $49.99/month
- 600 calls/minute: $149.99/month
- Visit: https://www.alphavantage.co/premium/

### Reducing API Calls
1. **Cache aggressively** - 1 hour TTL is good for fundamentals
2. **Batch user sessions** - Fetch all tickers at once
3. **Use yfinance for real-time prices** - Save API calls for fundamentals only
4. **Pre-fetch during off-hours** - Store in database

## Example Code

### Fetch Single Ticker
```python
from frontend.utils.fundamentals_fetcher import cached_fetch_fundamentals

data = cached_fetch_fundamentals('AAPL')
print(f"Market Cap: {data.get('market_cap')}")
print(f"PE Ratio: {data.get('pe_ratio')}")
print(f"Data Source: {data.get('source')}")
```

### Fetch Multiple Tickers
```python
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']

for ticker in tickers:
    data = cached_fetch_fundamentals(ticker)
    if data:
        print(f"{ticker}: PE={data.get('pe_ratio')}, Source={data.get('source')}")
    else:
        print(f"{ticker}: No data available")
```

### Force Specific Source
```python
from frontend.utils.fundamentals_fetcher import fetch_fundamentals_multi_source

# Try only Alpha Vantage
data = fetch_fundamentals_multi_source('AAPL', sources=['alpha_vantage'])

# Try specific order
data = fetch_fundamentals_multi_source('AAPL', sources=['tiingo', 'alpha_vantage', 'yfinance'])
```

## Resources

### Official Documentation
- Alpha Vantage Docs: https://www.alphavantage.co/documentation/
- Company Overview Endpoint: https://www.alphavantage.co/documentation/#company-overview
- Free API Key: https://www.alphavantage.co/support/#api-key

### Support
- Alpha Vantage Support: support@alphavantage.co
- Community Forum: https://www.alphavantage.co/support/#support
- GitHub Issues: Report issues in your repo

### Related Guides
- [Tiingo Integration Guide](TIINGO_INTEGRATION_GUIDE.md) - Primary equity data source
- [RBAC Setup](INVESTMENT_ANALYSIS_RBAC.md) - Permission system
- [Quick Commands](TIINGO_QUICK_COMMANDS.md) - Common operations

## FAQ

**Q: Do I need both Alpha Vantage AND Tiingo keys?**
A: No, but recommended. System works with just one source.

**Q: Which is better for fundamentals?**
A: Alpha Vantage has 30+ metrics vs Tiingo's basic metadata.

**Q: Can I use only yfinance?**
A: Yes, select "yfinance only" in the data source radio button.

**Q: How do I clear the cache?**
A: Run `st.cache_data.clear()` in Streamlit or restart app.

**Q: What if both APIs are rate limited?**
A: System automatically falls back to yfinance (no API key).

**Q: How long does cache last?**
A: 1 hour. Fundamentals don't change frequently.

**Q: Can I change the cache duration?**
A: Yes, edit `ttl=3600` in `cached_fetch_fundamentals()` function.

**Q: Does this work with international stocks?**
A: Best for US stocks. Some international coverage varies by source.
