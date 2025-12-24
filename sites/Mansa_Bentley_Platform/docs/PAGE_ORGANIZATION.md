# Page Organization & Navigation Guide

## 📋 New Page Order

The application has been reorganized with the following page structure:

### **Home Page** (streamlit_app.py)
**Path:** `/`  
**Icon:** 🤖  
**Title:** Bentley Bot Dashboard

**Features:**
- Bot Status Overview
- 🤖 **Bentley AI Assistant** (NEW)
  - Natural language Q&A about finances
  - DeepSeek AI integration
  - Context-aware responses
  - Macro/micro economic analysis
  - BLS and Census data insights
- Portfolio Data Upload
- Portfolio Performance Metrics
- 💰 Personal Budget Summary (for authenticated users)

---

### **01 - Personal Budget** 💰
**Path:** `pages/01_💰_Personal_Budget.py`  
**Access:** Authenticated users with VIEW_BUDGET permission

**Features:**
- Cash flow tracking (income/expenses/net flow)
- Budget vs actual comparisons
- Transaction history with search/filter
- Spending trends and insights
- Plaid bank account integration
- Category-wise spending breakdown

---

### **02 - Investment Analysis** 📈
**Path:** `pages/02_📈_Investment_Analysis.py`  
**Access:** Authenticated users (Client, Investor, Admin)

**Features:**
- Portfolio overview and performance
- Fundamental analysis (Alpha Vantage, Tiingo, yfinance)
- Broker connections display
  - WeBull
  - Interactive Brokers (IBKR)
  - Binance
  - NinjaTrader
  - MetaTrader 5 (Meta5)
- WeFolio funds tracking
- KYC/Investment agreement compliance

---

### **03 - Live Crypto Dashboard** 🔴
**Path:** `pages/03_🔴_Live_Crypto_Dashboard.py`  
**Status:** Existing page

**Features:**
- Real-time cryptocurrency prices
- Market cap and volume data
- Price charts and trends
- Portfolio crypto positions
- Exchange integrations (Binance, etc.)

---

### **04 - Broker Trading** 💼
**Path:** `pages/04_💼_Broker_Trading.py`  
**Status:** Existing page

**Features:**
- Multi-broker account management
- Position tracking across brokers
- Trade execution interface
- Order history and performance
- Broker-specific features

**Supported Brokers:**
- WeBull
- Interactive Brokers (IBKR)
- Binance
- NinjaTrader
- MetaTrader 5 (Meta5)

---

### **05 - Trading Bot** 🤖
**Path:** `pages/05_🤖_Trading_Bot.py`  
**Status:** Existing page

**Features:**
- Automated trading strategies
- Bot configuration and management
- Backtesting results
- Performance monitoring
- Risk management settings

---

## 🤖 Bentley AI Assistant

### Overview
The new chatbot interface on the home page provides AI-powered financial insights and Q&A capabilities.

### Features
- **Natural Language Q&A** - Ask questions in plain English
- **Context-Aware** - Understands your portfolio and budget data
- **Economic Data** - Integrates BLS and Census statistics
- **Market News** - Summarizes macro and micro economic news
- **Multi-Source** - Combines data from all pages

### Configuration
Add to `.env`:
```bash
# DeepSeek AI (Recommended)
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_API_ENDPOINT=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_MODEL=deepseek-chat

# Economic Data APIs
BLS_API_KEY=your_bls_key_here
CENSUS_API_KEY=your_census_key_here
```

### Example Questions
**Portfolio:**
- "How is my portfolio performing?"
- "What are my top holdings?"
- "Should I rebalance?"

**Budget:**
- "How much did I spend last month?"
- "Am I over budget?"
- "What are my largest expenses?"

**Market:**
- "What's happening in crypto?"
- "Latest economic indicators?"
- "Should I buy or sell?"

**Trading:**
- "What positions do I have open?"
- "How is my IBKR account performing?"
- "Trading strategy for today?"

---

## 🔄 Navigation Updates

### From Home Page
- **Personal Budget** → Click "View Full Budget Dashboard" button
- **Investment Analysis** → Use sidebar navigation
- **Live Crypto Dashboard** → Use sidebar navigation
- **Broker Trading** → Use sidebar navigation
- **Trading Bot** → Use sidebar navigation

### From Any Page
- **Home** → `st.switch_page("streamlit_app.py")`
- **Personal Budget** → `st.switch_page("pages/01_💰_Personal_Budget.py")`
- **Investment Analysis** → `st.switch_page("pages/02_📈_Investment_Analysis.py")`
- **Live Crypto Dashboard** → `st.switch_page("pages/03_🔴_Live_Crypto_Dashboard.py")`
- **Broker Trading** → `st.switch_page("pages/04_💼_Broker_Trading.py")`
- **Trading Bot** → `st.switch_page("pages/05_🤖_Trading_Bot.py")`

---

## 🔐 Authentication & Permissions

### Page Access Levels

| Page | Guest | Client | Investor | Admin |
|------|-------|--------|----------|-------|
| Home (Bot Status) | ✅ | ✅ | ✅ | ✅ |
| Personal Budget | ❌ | ✅ | ✅ | ✅ |
| Investment Analysis | ❌ | ✅ | ✅ | ✅ |
| Live Crypto Dashboard | ✅ | ✅ | ✅ | ✅ |
| Broker Trading | ❌ | ✅* | ✅* | ✅ |
| Trading Bot | ❌ | ❌ | ✅ | ✅ |

*Requires KYC + Investment Agreement

### Chatbot Access
- **Unauthenticated:** Basic Q&A with rule-based responses
- **Authenticated:** Full AI-powered insights with personal data context

---

## 📊 Data Flow

```
Home Page (Bot Status)
├── Portfolio Data Upload → yfinance data fetch
├── 🤖 Bentley AI Assistant → DeepSeek API
│   ├── Portfolio context from yfinance
│   ├── Budget context from MySQL
│   ├── Market data from APIs
│   └── Economic data (BLS, Census)
└── Budget Summary → MySQL database

Personal Budget Page (01)
└── Plaid API → MySQL → Budget Analysis Module

Investment Analysis Page (02)
├── Alpha Vantage → Fundamentals
├── Tiingo → Market Data
├── yfinance → Backup Data
└── Broker Connections → Demo/Live Data

Live Crypto Dashboard (03)
└── Binance API / CoinGecko API

Broker Trading (04)
├── WeBull API
├── IBKR API
├── Binance API
├── NinjaTrader API
└── Meta5 API

Trading Bot (05)
└── Strategy Engine → Broker APIs
```

---

## 🚀 Quick Start

### 1. Start the Application
```bash
streamlit run streamlit_app.py
```

### 2. Configure Chatbot (Optional)
```bash
# Add to .env
DEEPSEEK_API_KEY=your_key_here
```

### 3. Login
- Navigate to Personal Budget or Investment Analysis
- Use demo credentials:
  - Username: `client` / Password: `client123`
  - Username: `investor` / Password: `investor123`

### 4. Use the Chatbot
- Scroll down on home page
- Ask questions about your finances
- Get AI-powered insights

---

## 📝 Development Notes

### Adding New Pages
Pages are auto-discovered by Streamlit based on filename order:
- `01_*` appears first
- `02_*` appears second
- etc.

To add a new page:
1. Create file: `pages/0X_Icon_Name.py`
2. Add page content
3. Update navigation links in other pages

### Chatbot Integration
To add chatbot context from your page:
```python
from frontend.components.bentley_chatbot import get_chatbot_context_data

# Build context
context = get_chatbot_context_data()
context['your_data'] = "Your page-specific data"
```

### Updating Navigation
Search codebase for hardcoded page paths:
```bash
grep -r "pages/0" .
```

Update references after renaming pages.

---

## 🔧 Troubleshooting

### Chatbot Not Appearing
- Check `frontend/components/bentley_chatbot.py` exists
- Verify imports in `streamlit_app.py`
- Restart Streamlit server

### Wrong Page Order
- Check filename prefixes (`01_`, `02_`, etc.)
- Streamlit orders by filename, not title
- Restart server after renaming

### Navigation Errors
- Update `st.switch_page()` calls
- Check for hardcoded page paths
- Use correct filename including prefix

### API Errors
- Verify `.env` has required API keys
- Check API rate limits
- Test with fallback responses first

---

## 📚 Related Documentation

- **Plaid Integration:** `docs/PLAID_QUICK_START.md`
- **RBAC System:** `docs/QUICKSTART_INVESTMENT_RBAC.md`
- **Fundamentals:** `docs/IMPLEMENTATION_SUMMARY_FUNDAMENTALS.md`
- **Roadmap:** `docs/PLAID_INTEGRATION_ROADMAP.md`

---

**Last Updated:** December 9, 2025  
**Version:** 2.0.0
