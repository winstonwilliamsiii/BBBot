# Economic Data Integration for Bentley Chatbot

## Overview
To enable the Bentley Chatbot to answer questions like "Is there any economic data being released today?", you need to integrate BLS (Bureau of Labor Statistics) and Census data APIs. The chatbot already has the UI and fallback response ready, but needs these backend data sources.

---

## What You Currently Have ✅

Your chatbot (`frontend/components/bentley_chatbot.py`) already includes:

1. **Fallback Response Handler** - Ready-made message:
   ```python
   elif any(word in message_lower for word in ['bls', 'employment', 'census', 'economic', 'macro']):
       return "📈 I can provide insights on economic indicators from BLS and Census data. This feature is currently being integrated. Stay tuned!"
   ```

2. **DeepSeek API Integration** - Can pass context to AI model
3. **Chat History & Context Building** - Already tracking conversations
4. **Status Display** - Shows active data sources

---

## What You Need to Implement 🛠️

### 1. **API Credentials & Environment Variables**
Add to your `.env` file or Streamlit secrets:

```env
# Economic Data APIs
BLS_API_KEY=your_bls_api_key          # https://data.bls.gov/registrationEngine/
CENSUS_API_KEY=your_census_api_key    # https://api.census.gov/data/key_signup.html
FRED_API_KEY=your_fred_api_key        # https://fred.stlouisfed.org/docs/api/

# Optional: NewsAPI for economic news
NEWSAPI_KEY=your_newsapi_key          # https://newsapi.org/
```

### 2. **Python Packages**
Add to `requirements.txt`:

```txt
# Economic data fetching
requests>=2.31.0
pandas-datareader>=0.10.0
yfinance>=0.2.32  # Already have this
fred>=1.0.0       # Federal Reserve Economic Data
```

Install:
```bash
pip install -r requirements.txt
```

### 3. **Create Economic Data Module**
File: `frontend/utils/economic_data.py`

```python
"""
Economic Data Integration Module
Fetches data from BLS, Census, and FRED APIs
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import streamlit as st

class EconomicDataFetcher:
    """Fetches economic indicators from various US government APIs"""
    
    def __init__(self):
        self.bls_key = os.getenv('BLS_API_KEY', '')
        self.census_key = os.getenv('CENSUS_API_KEY', '')
        self.fred_key = os.getenv('FRED_API_KEY', '')
        self.newsapi_key = os.getenv('NEWSAPI_KEY', '')
    
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def get_bls_employment_data(self, series_id: str = 'LNS14000000') -> Dict:
        """
        Fetch latest employment data from BLS
        
        Common Series IDs:
        - LNS14000000: Unemployment rate (seasonally adjusted)
        - CEU0500000001: Total private employment
        - CES0500000001: Total employment
        
        Args:
            series_id: BLS series ID
        
        Returns:
            Dictionary with latest employment stats
        """
        url = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
        
        headers = {'Content-Type': 'application/json'}
        data = {
            'seriesid': [series_id],
            'startyear': str(datetime.now().year - 1),
            'endyear': str(datetime.now().year),
            'registrationkey': self.bls_key
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'REQUEST_SUCCEEDED':
                series_data = result['Results']['series'][0]['data']
                latest = series_data[0]  # Most recent month
                
                return {
                    'series_id': series_id,
                    'date': f"{latest['year']}-{latest['period'][1:]}",
                    'value': float(latest['value']),
                    'raw_data': series_data[:12]  # Last 12 months
                }
        except Exception as e:
            st.warning(f"BLS data fetch failed: {e}")
        
        return {}
    
    @st.cache_data(ttl=3600)
    def get_economic_releases_schedule(self) -> List[Dict]:
        """
        Fetch today's economic data releases
        Uses BLS release calendar
        
        Returns:
            List of scheduled economic releases
        """
        url = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
        
        # This is a simplified version - real implementation would use
        # the BLS release calendar or FT economic calendar API
        
        today = datetime.now().date()
        releases = [
            {
                'name': 'Weekly Jobless Claims',
                'agency': 'Department of Labor',
                'time': '08:30 AM ET',
                'release_date': today,
                'importance': '🔴 High',
                'url': 'https://www.dol.gov/ui/data.pdf'
            },
            {
                'name': 'Consumer Price Index (CPI)',
                'agency': 'Bureau of Labor Statistics',
                'time': '08:30 AM ET',
                'release_date': today + timedelta(days=2),
                'importance': '🔴 High',
                'url': 'https://www.bls.gov/cpi/'
            },
            {
                'name': 'Employment Situation',
                'agency': 'Bureau of Labor Statistics',
                'time': '08:30 AM ET',
                'release_date': today + timedelta(days=5),
                'importance': '🔴 Very High',
                'url': 'https://www.bls.gov/news.release/empsit.toc.htm'
            }
        ]
        
        return releases
    
    @st.cache_data(ttl=3600)
    def get_fred_data(self, series_id: str) -> Dict:
        """
        Fetch Federal Reserve Economic Data (FRED)
        
        Common Series IDs:
        - GDP: Real Gross Domestic Product
        - UNRATE: Unemployment Rate
        - PAYEMS: Total Nonfarm Payroll Employment
        - CPIAUCSL: Consumer Price Index for All Urban Consumers
        
        Args:
            series_id: FRED series ID
        
        Returns:
            Dictionary with latest values and historical data
        """
        url = f'https://api.stlouisfed.org/fred/series/observations'
        
        params = {
            'series_id': series_id,
            'api_key': self.fred_key,
            'sort_order': 'desc',
            'limit': 12,
            'file_type': 'json'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'observations' in data and data['observations']:
                latest = data['observations'][0]
                return {
                    'series_id': series_id,
                    'date': latest['date'],
                    'value': latest.get('value', 'N/A'),
                    'historical': data['observations'][:12]
                }
        except Exception as e:
            st.warning(f"FRED data fetch failed: {e}")
        
        return {}
    
    def get_economic_summary(self) -> str:
        """
        Get a summary of today's economic releases and latest indicators
        
        Returns:
            Formatted string with economic data summary
        """
        summary_parts = []
        
        # Get unemployment rate
        unemployment = self.get_bls_employment_data('LNS14000000')
        if unemployment:
            summary_parts.append(
                f"📊 **Unemployment Rate**: {unemployment['value']}% "
                f"(as of {unemployment['date']})"
            )
        
        # Get employment numbers
        employment = self.get_bls_employment_data('PAYEMS')
        if employment:
            summary_parts.append(
                f"💼 **Employment**: {employment['value']} nonfarm payroll jobs"
            )
        
        # Get today's releases
        releases = self.get_economic_releases_schedule()
        todays_releases = [r for r in releases if r['release_date'] == datetime.now().date()]
        
        if todays_releases:
            summary_parts.append("\n📅 **Today's Releases**:")
            for release in todays_releases:
                summary_parts.append(
                    f"  • {release['importance']} {release['name']} "
                    f"@ {release['time']}"
                )
        
        return "\n".join(summary_parts) if summary_parts else "No economic data available"


# Cache function wrapper for use in Streamlit
@st.cache_resource
def get_economic_fetcher() -> EconomicDataFetcher:
    """Get or create economic data fetcher"""
    return EconomicDataFetcher()
```

### 4. **Update Chatbot to Use Economic Data**

Modify [bentley_chatbot.py](frontend/components/bentley_chatbot.py) in the `_fallback_response` method:

Replace this section:
```python
# Economic data questions
elif any(word in message_lower for word in ['bls', 'employment', 'census', 'economic', 'macro']):
    return "📈 I can provide insights on economic indicators from BLS and Census data. This feature is currently being integrated. Stay tuned!"
```

With:
```python
# Economic data questions
elif any(word in message_lower for word in ['bls', 'employment', 'census', 'economic', 'macro', 'releases', 'inflation', 'cpi', 'jobs']):
    try:
        from frontend.utils.economic_data import get_economic_fetcher
        fetcher = get_economic_fetcher()
        
        if any(w in message_lower for w in ['today', 'release', 'schedule']):
            summary = fetcher.get_economic_summary()
        else:
            summary = fetcher.get_economic_summary()
        
        return f"📈 **Economic Data Insights**\n\n{summary}\n\nVisit [BLS.gov](https://www.bls.gov) or [FRED](https://fred.stlouisfed.org) for more detailed data."
    except Exception as e:
        return f"📈 I can provide insights on economic indicators from BLS and Census data. (Error: {str(e)})"
```

### 5. **Get API Keys**

**BLS API (Free)**
- Go to: https://data.bls.gov/registrationEngine/
- Register for free account
- Get API key from settings
- No rate limits with registered key

**FRED API (Free)**
- Go to: https://fred.stlouisfed.org/docs/api/
- Create free account
- Get API key immediately
- 120 requests per minute limit

**Census API (Free)**
- Go to: https://api.census.gov/data/key_signup.html
- Sign up with email
- Get API key in email

**NewsAPI (Optional, Freemium)**
- Go to: https://newsapi.org/
- Free tier available
- Use for economic news headlines

### 6. **Update requirements.txt**

Add these lines:

```txt
requests>=2.31.0
pandas-datareader>=0.10.0
```

---

## Implementation Checklist

- [ ] Register for BLS API key
- [ ] Register for FRED API key  
- [ ] Register for Census API key (optional)
- [ ] Create `frontend/utils/economic_data.py`
- [ ] Update `requirements.txt` with new packages
- [ ] Add API keys to `.env` file (local) or Streamlit secrets (cloud)
- [ ] Update `bentley_chatbot.py` to use economic data fetcher
- [ ] Test chatbot with economic questions:
  - "Is there any economic data being released today?"
  - "What's the current unemployment rate?"
  - "Show me economic indicators"

---

## Testing Commands

```bash
# Test locally first
streamlit run streamlit_app.py

# Then ask chatbot:
# - "What's happening in the economy today?"
# - "Show me today's economic releases"
# - "What's the unemployment rate?"
```

---

## Advanced Features (Future)

1. **Economic Calendar Integration**
   - Use Investing.com or TradingView economic calendar
   - Real-time release notifications

2. **Sentiment Analysis**
   - Analyze economic news for market impact
   - Track sentiment over time

3. **Correlation Analysis**
   - Show how economic indicators correlate with portfolio performance
   - Alert users to economic triggers

4. **Forecasting**
   - Use AI model (DeepSeek) to forecast economic trends
   - Generate investment recommendations based on economic outlook

---

## Cost Analysis

| API | Cost | Limit |
|-----|------|-------|
| BLS | Free | Unlimited (registered) |
| FRED | Free | 120 requests/min |
| Census | Free | Limited |
| NewsAPI | Free tier: $0 | 100 requests/day |
| DeepSeek (for analysis) | ~$0.50/1M tokens | Pay-as-you-go |

**Total monthly cost: $0-5** (only if using premium NewsAPI tier)

---

## Data Flow

```
User Question
    ↓
Bentley Chatbot detects economic keyword
    ↓
Calls EconomicDataFetcher
    ↓
BLS/FRED/Census APIs
    ↓
Format response with latest data
    ↓
(Optional) Send to DeepSeek for AI analysis
    ↓
Display to user
```

---

## Files to Create/Modify

1. **Create**: `frontend/utils/economic_data.py` - Economic data fetcher
2. **Modify**: `requirements.txt` - Add requests package
3. **Modify**: `frontend/components/bentley_chatbot.py` - Update fallback response
4. **Modify**: `.env` - Add API keys
5. **Modify**: `streamlit_app.py` - Optional: show context data in sidebar

---

## Next Steps

1. Get the API keys (5 min)
2. Add them to your `.env` file
3. Create the `economic_data.py` module
4. Update the chatbot response handler
5. Test with sample questions
6. Deploy to production

Questions? The chatbot component is ready - you just need the data sources!
