# 🏛️ Mansa Capital - Project Structure
**Location:** `C:\Users\winst\BentleyBudgetBot`  
**GitHub:** `/mansa-capital/`  
**Updated:** January 11, 2026

---

## 📁 Directory Organization

```
C:\Users\winst\BentleyBudgetBot (mansa-capital)
│
├── /frontend/                    # Lovable/Vercel React/Next.js UI
│   ├── /components/              # Reusable UI components
│   ├── /pages/                   # App routes (/exchange, /dashboard)
│   ├── /public/                  # Static assets (logos, TerraMar branding)
│   └── /styles/                  # CSS/SCSS styling modules
│
├── /backend/                     # API Layer (Vercel serverless/FastAPI)
│   ├── /api/                     # API endpoints (budget, transactions, orders, KYC)
│   ├── /services/                # Brokerage connectors (tZERO, Plaid, Binance)
│   ├── /models/                  # Database schemas (MySQL, Supabase)
│   └── /utils/                   # Helpers (auth, logging, error handling)
│
├── /sdk/                         # Bentley Budget Bot + TerraMar Token SDK
│   ├── /budget/                  # Budget APIs, forecasting, transaction sync
│   ├── /tokenization/            # Token issuance, fractional ownership, compliance
│   └── /docs/                    # Developer guides, quick-starts
│
├── /railway/                     # Railway.app deployment configs
│   ├── Dockerfile                # Container build configuration
│   ├── railway.json              # Railway project/service definitions
│   └── /migrations/              # SQL migrations (MySQL/Postgres)
│
├── /postman/                     # API Testing Collections
│   ├── MansaCapital.postman_collection.json
│   └── Environment.json          # Dev/staging/prod variables
│
├── /integrations/                # External Brokerages & Services
│   ├── /tzero/                   # tZERO ATS API wrappers, order routing
│   ├── /plaid/                   # Bank transaction ingestion (3 providers)
│   ├── /binance/                 # Crypto trading endpoints
│   └── /stripe/                  # Payment/KYC flows
│
├── /scripts/                     # Automation Scripts
│   ├── deploy.sh                 # CI/CD deployment script
│   ├── seed-db.js                # Seed database with test data
│   └── test.sh                   # Run unit/integration tests
│
├── /tests/                       # Jest/Pytest Test Suites
│   ├── api.test.js
│   ├── sdk.test.js
│   └── integrations.test.js
│
├── /appwrite-functions/          # Appwrite Cloud Functions (11 deployed)
├── /bentleybot/                  # Legacy budget bot modules
├── /pages/                       # Streamlit multi-page app pages
├── .env                          # Environment variables (local only)
├── streamlit_app.py              # Main Streamlit application
├── package.json                  # Node.js dependencies
├── requirements.txt              # Python dependencies
└── README.md                     # Project overview
```

---

## 🔧 Key Components

### Frontend Stack
- **Framework:** React/Next.js (Lovable.dev)
- **Hosting:** Vercel
- **Styling:** CSS Modules + Tailwind CSS
- **State:** React Context / Redux

### Backend Stack
- **API:** Vercel Serverless Functions
- **Database:** MySQL (Railway) + Appwrite
- **Auth:** Appwrite Authentication
- **Functions:** 11 deployed Appwrite Cloud Functions

### Integrations Active
✅ **Banking APIs:**
- Plaid (sandbox - initializing)
- Capital One DevExchange (sandbox - ready)
- Bank of America CashPro (pending approval)

✅ **Broker APIs:**
- Alpaca Markets (paper trading)
- MetaTrader 5 (FOREX/commodities)
- Interactive Brokers (configured)
- Webull (demo mode)

✅ **Data Providers:**
- Tiingo (market data)
- Alpha Vantage (fundamentals)
- yfinance (historical prices)

---

## 🚀 Deployment Targets

| Service | Platform | Status | URL |
|---------|----------|--------|-----|
| Frontend | Vercel | ✅ Live | `https://vercel.app/mansa-capital` |
| Streamlit App | Streamlit Cloud | ✅ Live | `https://bbbot305.streamlit.app` |
| Backend API | Vercel Functions | ✅ Live | `/api/*` endpoints |
| Appwrite Functions | Appwrite Cloud | ✅ Deployed | 11 functions active |
| Database | Railway MySQL | ✅ Running | `nozomi.proxy.rlwy.net:54537` |
| Docker Services | Local | ⚠️ Mixed | 14 containers (2 unhealthy) |

---

## 📋 Quick Commands

### Development
```bash
# Start Streamlit app
streamlit run streamlit_app.py

# Start Vercel dev server
cd vercel-frontend && npm run dev

# Deploy Appwrite functions
appwrite push functions
```

### Testing
```bash
# Run Python tests
pytest tests/

# Run integration tests
python test_multi_broker.py

# Check environment
python check_env.py
```

### Database
```bash
# Connect to Railway MySQL
mysql -h nozomi.proxy.rlwy.net -P 54537 -u root -p

# Run migrations
python migrations/run_migrations.py
```

---

## 🎯 Next Steps
1. ⏳ Wait for Plaid Link initialization to complete
2. 📋 Await BofA CashPro approval
3. 🔧 Fix MLflow memory issues (increase Docker resources)
4. 🧪 Test Capital One DevExchange integration
5. 📦 Deploy TerraMar tokenization SDK

---

**Last Updated:** January 11, 2026  
**Maintained By:** Mansa Capital Development Team
