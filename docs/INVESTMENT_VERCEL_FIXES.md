# Investment Page & Vercel Issues - Solutions

## Issue Summary (December 25, 2025)

### ❌ **Current Problems:**
1. **Investment Page**: Only uses yfinance API, no MySQL/Plaid integration
2. **No API caching**: Every page refresh makes new API calls (slow + rate limits)
3. **Vercel 404 Error**: Streamlit cannot be deployed on Vercel (serverless only)

---

## ✅ **Solution 1: Add API Caching (URGENT)**

### Problem:
- `yf.download()` called on every page refresh
- No caching = slow loads + API rate limits

### Fix:
Add `@st.cache_data` decorator to data fetching functions in Investment Analysis page.

**Before:**
```python
df = yf.download(ticker, start=start_date, end=end_date, progress=False)
```

**After:**
```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_stock_data(ticker, start_date, end_date):
    """Cached stock data fetcher"""
    try:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        return df
    except Exception as e:
        st.error(f"Failed to fetch {ticker}: {e}")
        return None

# Usage:
df = fetch_stock_data(ticker, start_date, end_date)
```

### Files to Update:
- `pages/02_📈_Investment_Analysis.py` (lines 357, 642)

---

## ✅ **Solution 2: Integrate MySQL Portfolio Data**

### Problem:
Investment page doesn't show YOUR actual portfolio from MySQL/Plaid transactions.

### Fix:
Create a function to fetch portfolio holdings from Appwrite Functions or MySQL.

**New Function:**
```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_user_portfolio(user_id):
    """Fetch user's actual holdings from Appwrite"""
    from services.transactions import get_transactions
    
    transactions = get_transactions(user_id, limit=1000)
    
    if "error" in transactions:
        st.warning("Could not load portfolio. Using demo tickers.")
        return None
    
    # Calculate holdings from transactions
    holdings = {}
    for tx in transactions.get('transactions', []):
        symbol = tx.get('symbol')
        quantity = tx.get('quantity', 0)
        if symbol:
            holdings[symbol] = holdings.get(symbol, 0) + quantity
    
    return holdings
```

---

## ✅ **Solution 3: Fix Vercel Deployment**

### Problem:
**Vercel CANNOT host Streamlit apps.** Your `https://bentley-budget-bot.vercel.app/` shows 404 because:
- Vercel = Serverless functions + static sites only
- Streamlit = Long-running Python server (not serverless)

### Options:

#### **Option A: Keep Streamlit Local + Deploy API to Vercel**
- Run Streamlit on your laptop: `http://localhost:8501`
- Deploy Appwrite Functions for backend logic
- Use Vercel for status page only (current `api/index.py`)

#### **Option B: Deploy Streamlit to Render/Railway/Heroku**
- **Render.com**: Free tier, supports Streamlit
- **Railway.app**: Supports Streamlit, easy GitHub deploy
- **Heroku**: Classic option (paid)

#### **Option C: Convert to Next.js Frontend (Major Rewrite)**
- Build React/Next.js frontend
- Call Appwrite Functions for data
- Deploy to Vercel
- **Time**: 2-4 weeks of development

### Recommended: **Option B - Deploy to Render.com**

**Steps:**
1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: bentley-budget-bot
    env: python
    buildCommand: pip install -r requirements-streamlit.txt
    startCommand: streamlit run streamlit_app.py --server.port=$PORT
    envVars:
      - key: APPWRITE_PROJECT_ID
        value: 68869ef500017ca73772
      - key: APPWRITE_ENDPOINT
        value: https://cloud.appwrite.io/v1
```

2. Connect GitHub repo to Render
3. Deploy (auto-deploys on git push)
4. Get public URL: `https://bentley-budget-bot.onrender.com`

---

## 📋 **Immediate Action Items**

### High Priority (Today):
1. ✅ **Add caching to Investment page** - Prevents API rate limits
2. ✅ **Update Vercel expectations** - It's for API only, not Streamlit

### Medium Priority (This Week):
3. **Deploy Streamlit to Render.com** - Get public URL
4. **Integrate portfolio data from Appwrite** - Show real holdings

### Low Priority (Future):
5. Consider Next.js rewrite for full Vercel deployment

---

## 🔧 **Quick Commands**

### Test Investment Page Locally:
```powershell
cd C:\Users\winst\OneDrive\Documentos\GitHub\BBBot
.venv\Scripts\Activate.ps1
streamlit run streamlit_app.py
```

### Deploy to Render (after adding render.yaml):
1. Go to https://render.com
2. New → Web Service
3. Connect GitHub repo: BBBot
4. Render auto-detects Python
5. Deploy

---

## ✅ **Expected Outcomes**

- **Caching**: Investment page loads 5-10x faster
- **Portfolio Integration**: See YOUR actual holdings (not demo tickers)
- **Public URL**: https://bentley-budget-bot.onrender.com (via Render)
- **Vercel**: Keep as API/status endpoint only
