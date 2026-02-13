# DEMO VERSION AVAILABLE

## ✅ Working Demo for Investor Presentation

A fully functional demo version is available that shows **all UI/UX features** without requiring database infrastructure.

### How to Run Demo

```bash
cd C:\Users\winst\BentleyBudgetBot
.\.venv\Scripts\streamlit.exe run demo_streamlit_app.py
```

Then open: **http://localhost:8501**

### What's Included in Demo

✅ **Stock Portfolio** - Display of 5 sample stocks with:
- Ticker, shares, price, total value
- Performance indicators
- Visual breakdown charts

✅ **Cryptocurrency Holdings** - Display of 5 cryptocurrencies with:
- Current prices
- Holdings and values
- 24h change indicators

✅ **Transaction History** - Sample transactions with:
- Date, description, amount, category
- Trending analysis
- Category breakdown charts

✅ **Analysis Tab** - Portfolio analytics showing:
- Performance metrics (YTD, monthly, Sharpe ratio)
- Risk assessment
- Dashboard widgets

✅ **Professional UI** - Featuring:
- Custom styling and colors
- Responsive layout
- Sidebar controls
- Metrics cards
- Tab navigation

### Differences from Full Version

| Feature | Demo | Full |
|---------|------|------|
| **Stock Data** | Sample data | Real from Yahoo Finance |
| **Crypto Data** | Sample data | Real from exchanges |
| **Portfolio Persistence** | In-memory only | MySQL database |
| **Bank Connections** | Not available | Plaid integration |
| **ML Predictions** | Not available | MLflow models |
| **User Accounts** | Not available | RBAC system |
| **Investment Analysis** | Static | Live MLflow experiments |

### Infrastructure Issues (For Reference)

The **full** version (streamlit_app.py) requires:

1. **MySQL Server** (Port 3307)
   - Current: Connection refused
   - Status: Docker container running but may have initialization issues

2. **Plaid Integration**
   - Status: Configured in .env
   - Issue: Not needed for demo

3. **MLflow** 
   - Status: Configured for port 3307
   - Issue: Requires MySQL connectivity

### For Full Version Setup

See: [INFRASTRUCTURE_SETUP.md](./INFRASTRUCTURE_SETUP.md)

### Notes for Investor

**Talking Points:**
- "This is the demo version showing the final UI/UX"
- "Full version adds real data integration"
- "Backend infrastructure is separate from frontend"
- "Demo runs locally without any setup"

**Demo Workflow:**
1. Show Stock Portfolio tab - explain how real data would feed in
2. Show Crypto Holdings - explain exchange integration
3. Show Transactions - explain how Plaid connects real bank data
4. Show Analysis - explain ML models that would power insights
5. Sidebar - show configuration options

**Questions They Might Ask:**
- "Can it connect to my real accounts?" → Full version has Plaid integration
- "Can it predict returns?" → Full version uses MLflow with historical data
- "Where does data live?" → MySQL backend with API access
- "How scalable is this?" → Cloud-ready with Streamlit Cloud deployment

---

**Status:** ✅ Demo is ready for presentation  
**Created:** January 17, 2026
