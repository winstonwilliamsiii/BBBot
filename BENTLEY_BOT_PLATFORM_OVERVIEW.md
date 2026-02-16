# 🚀 Bentley Bot Platform Overview

**Multi-Tenant Trading Automation Platform**  
Mansa Capital Partners, LLC & Moor Capital Trust

---

## 🎯 What Is Bentley Bot?

A **two-layer platform** that combines:
1. **Client-Facing Portfolio Management** (what investors see)
2. **Internal Control Center** (how you manage 13 AI bots, 5+ brokers, and 4+ prop firms)

Think of it as: **"The Bloomberg Terminal meets AI-powered hedge fund operations"**

---

## 🏗️ Two-Layer Architecture

### Layer 1: Client Experience (Production Ready) ✅
- Portfolio dashboard with real-time valuations
- Budget management with Plaid bank sync
- Multi-broker trading interface
- Crypto dashboard with Binance integration
- Investment analysis and stock screener
- ML bot performance metrics

**Who uses this:** Investors, portfolio managers, clients

---

### Layer 2: Bentley Bot Control Center (In Development) 🔨
- Multi-broker orchestration (Alpaca, Schwab, IBKR, Binance, Coinbase)
- Prop firm execution via MT5/NinjaTrader (FTMO, Axi, Zenit)
- 13 AI/ML trading bots with MLflow tracking
- Risk engine (drawdown limits, FINRA compliance, prop rules)
- VPS/GCP deployment automation
- Execution logs and error monitoring
- Secrets management and key rotation
- Account scaling for funded prop accounts

**Who uses this:** You (Winston), Mansa team, system admins

---

## 📊 Platform Capabilities

### What You Can Do TODAY (Production)
- ✅ View portfolio across multiple accounts
- ✅ Track budget and expenses
- ✅ Analyze stocks with technical indicators
- ✅ Trade crypto on Binance
- ✅ Monitor ML bot performance
- ✅ Place orders via Alpaca
- ✅ Track positions and P&L

### What Control Center Will Add (4-6 weeks)
- 🔨 Deploy and manage 13 AI bots
- 🔨 Route orders intelligently across brokers
- 🔨 Execute on FTMO/Axi via MT5
- 🔨 Enforce risk limits automatically
- 🔨 Monitor all bots in real-time
- 🔨 Track execution quality per broker
- 🔨 Auto-halt trading on rule violations
- 🔨 Deploy bots to VPS with one click

---

## 🔧 Technology Stack

### Frontend
- **Streamlit** - Main dashboard (localhost:8501)
- **Next.js** - Alternative React UI (Vercel)

### Backend
- **Flask** - Control Center REST API
- **Python 3.12** - Core logic
- **MySQL** - Multi-tenant database (Railway)
- **Appwrite** - Auth and cloud functions

### Trading Infrastructure
- **MT5** - Prop firm execution (FTMO, Axi)
- **Alpaca API** - Equities trading
- **Binance SDK** - Crypto trading
- **yfinance** - Market data

### Data & ML
- **Airflow** - Workflow orchestration (localhost:8080)
- **MLflow** - ML experiment tracking (localhost:5000)
- **Airbyte** - Data ingestion (localhost:8000)
- **Redis** - Caching (localhost:6379)

### Deployment
- **Docker** - Local containerization
- **Vercel** - Frontend hosting
- **Streamlit Cloud** - [bbbot305.streamlit.app](https://bbbot305.streamlit.app)
- **FOREXVPS** - Windows VPS for MT5 (planned)
- **GCP** - Cloud deployment (planned)

---

## 🚀 Quick Start

### Option 1: Run Full Stack Locally
```bash
# 1. Start all Docker services
docker-compose up -d

# 2. Start Flask API (in one terminal)
python backend/api/app.py

# 3. Start Streamlit app (in another terminal)
streamlit run streamlit_app.py

# 4. Open service dashboard
start open_dashboard.ps1
```

**Access:**
- Streamlit: http://localhost:8501
- Flask API: http://localhost:5000
- Airflow: http://localhost:8080
- MLflow: http://localhost:5000 (different endpoint)
- Airbyte: http://localhost:8000

### Option 2: Use Cloud Deployment
- Production app: [bbbot305.streamlit.app](https://bbbot305.streamlit.app)
- API: Deployed on Vercel

---

## 📈 Supported Brokers & Platforms

| Broker | Asset Class | Status | API Type |
|--------|------------|--------|----------|
| **Alpaca** | Equities | ✅ Live | REST + WebSocket |
| **Binance** | Crypto | ✅ Live | REST |
| **MT5 (FTMO)** | Forex/CFDs | ✅ Ready | Python API |
| **MT5 (Axi)** | Forex/CFDs | ✅ Ready | Python API |
| **Schwab** | Equities | 🟡 OAuth Pending | REST |
| **IBKR** | Multi-asset | 🔨 In Progress | TWS API |
| **Coinbase** | Crypto | 🔨 Planned | Pro API |

---

## 🤖 Trading Bots

### Currently Active
1. **GoldRSI Strategy** (Alpaca/MT5)
   - RSI-based gold trading
   - Works across brokers via abstraction layer

2. **USD/COP Short Strategy** (MT5)
   - Forex pair trading
   - MT5 specific

### In Development (13 Total)
- Portfolio optimization bots
- Sentiment analysis bots
- Technical indicator bots
- Multi-timeframe strategies
- Crypto arbitrage bots

**Management:** MLflow dashboard tracks all experiments

---

## 🏢 Prop Firm Support

### FTMO (MT5)
- ✅ MT5 Expert Advisors deployed
- ✅ Python bridge to Alpaca signals
- 🔨 Rule engine (daily loss, max drawdown)

### Axi Select (MT5)
- ✅ MT5 integration ready
- 🔨 Account scaling automation

### Zenit (NinjaTrader)
- 🔨 Rithmic API connector planned
- 🔨 Futures contract support

---

## 🛡️ Risk Management

### Current (Basic)
- Manual position sizing
- Stop-loss in strategies
- Basic equity checks

### Control Center Will Add
- Pre-trade risk validation
- Portfolio-level limits
- Margin requirement checks
- Drawdown monitoring
- FINRA compliance (PDT rules)
- Prop firm rule enforcement
- Automatic trading halts

---

## 📂 Project Structure

### Organized Control Center Structure

```
/bentley-bot/              # 🆕 Organized control center code
├── bots/                  # 13 AI/ML trading bots
│   ├── bot1.py           # GoldRSI Strategy
│   ├── bot2.py           # USD/COP Short
│   ├── bot3.py           # Portfolio Optimizer
│   ├── bot4.py           # Sentiment Analyzer
│   ├── bot5.py           # Technical Indicator Bot
│   ├── bot6.py           # Multi-timeframe Strategy
│   ├── bot7.py           # Crypto Arbitrage
│   ├── bot8.py           # Mean Reversion
│   ├── bot9.py           # Momentum Strategy
│   ├── bot10.py          # Options Strategy
│   ├── bot11.py          # Pairs Trading
│   ├── bot12.py          # News Trading
│   └── bot13.py          # ML Ensemble
├── brokers/               # Broker API clients
│   ├── alpaca.py
│   ├── schwab.py
│   ├── ibkr.py
│   ├── binance.py
│   └── coinbase.py
├── prop_firms/            # Prop firm connectors
│   ├── ftmo_mt5.py
│   ├── axi_mt5.py
│   └── zenit_ninja.py
├── mlflow/                # ML pipelines
│   ├── train.py
│   ├── backtest.py
│   └── register.py
├── streamlit_app/         # UI modules
│   ├── admin.py
│   ├── investor.py
│   └── dashboards.py
└── utils/                 # Shared utilities
    ├── risk.py
    ├── config.py
    └── secrets.py
```

### Full Project Structure

```
BentleyBudgetBot/
├── bentley-bot/           # 🆕 NEW organized code
├── frontend/              # Client UI (Streamlit)
├── backend/               # FastAPI APIs
│   └── api/admin/         # Control Center (to build)
├── trading/               # Strategy engine
│   ├── strategies/        # Bot strategies
│   └── bots/              # Bot deployments
├── mt5/                   # Prop firm execution
│   ├── experts/           # MT5 Expert Advisors
│   └── scripts/           # Python-MT5 bridge
├── workflows/             # Data pipelines
│   ├── airflow/           # Orchestration
│   ├── mlflow/            # ML tracking
│   └── airbyte/           # Data ingestion
├── admin_ui/              # Control Center UI (to build)
├── docs/                  # Documentation
└── streamlit_app.py       # Main app entry
```

---

## 🎨 Use Cases

### For Investors (Client Layer)
- "Show me my portfolio performance"
- "What's my budget vs actual spending?"
- "Execute a trade on Binance"
- "How are the trading bots performing?"

### For Admins (Control Center)
- "Deploy GoldRSI bot to production"
- "Check health of all broker connections"
- "Halt all trading immediately"
- "View execution logs for past hour"
- "What's the current drawdown across all accounts?"
- "Deploy new bot version to FOREXVPS"

---

## 🔐 Security Features

- Multi-tenant database isolation
- Encrypted API credentials (AES-256)
- OAuth 2.0 for broker authentication
- Role-based access control (RBAC)
- Audit logging for all trades
- TLS encryption for all connections

---

## 📊 Key Metrics Dashboard

### Portfolio
- Total equity: $XXX,XXX
- Unrealized P&L: +$X,XXX
- Day's change: +X.XX%
- Asset allocation: Stocks XX% | Crypto XX% | Cash XX%

### Trading Bots
- Active bots: 3/13
- Total trades today: XX
- Win rate: XX%
- Sharpe ratio: X.XX

### Risk
- Current drawdown: -X.X%
- Max drawdown limit: -10%
- Leverage ratio: X.Xx
- Margin utilization: XX%

---

## 🚦 Getting Status

### Check All Services
```powershell
.\open_dashboard.ps1
```

### Fix Any Issues
```powershell
.\fix_services.ps1
```

### View Logs
```powershell
docker logs bentley-mlflow --tail 50
docker logs bentley-airflow-webserver --tail 50
```

---

## 📖 Documentation

- **Architecture:** [BENTLEY_BOT_CONTROL_CENTER_ARCHITECTURE.md](docs/BENTLEY_BOT_CONTROL_CENTER_ARCHITECTURE.md)
- **Quick Start:** [CONTROL_CENTER_QUICK_START.md](docs/CONTROL_CENTER_QUICK_START.md)
- **Broker Setup:** [BROKER_API_COMPLETE.md](docs/BROKER_API_COMPLETE.md)
- **Strategy Guide:** [BROKER_ABSTRACTION_EXPLAINED.md](docs/BROKER_ABSTRACTION_EXPLAINED.md)
- **MT5 Setup:** [mt5/README.md](mt5/README.md)

---

## 🛣️ Roadmap

### Phase 1 (Weeks 1-6): Control Center Foundation
- [ ] FastAPI admin API
- [ ] Broker health monitoring
- [ ] Bot deployment manager
- [ ] Execution logs dashboard

### Phase 2 (Weeks 7-10): ML Orchestration
- [ ] 13 bots deployed to production
- [ ] MLflow integration
- [ ] A/B testing framework
- [ ] Automated backtesting

### Phase 3 (Weeks 11-15): Prop Firm Integration
- [ ] FTMO rule engine
- [ ] Axi account automation
- [ ] NinjaTrader connector
- [ ] Payout tracking

### Phase 4 (Weeks 16-19): Risk & Compliance
- [ ] Pre-trade validation
- [ ] Real-time monitoring
- [ ] FINRA compliance
- [ ] Emergency halt system

### Phase 5 (Weeks 20-22): Infrastructure
- [ ] FOREXVPS deployment
- [ ] GCP Cloud Run
- [ ] Secrets vault
- [ ] VPS monitoring

### Phase 6 (Weeks 23-27): Analytics
- [ ] Execution quality metrics
- [ ] Multi-broker reconciliation
- [ ] Advanced performance tracking

---

## 🤝 Team

**Mansa Capital Partners, LLC**  
**Moor Capital Trust**  
**Developed by:** Winston Williams III

---

## 📞 Support

### Issues
- Database: Check Railway connection at nozomi.proxy.rlwy.net:54537
- Services: Run `.\fix_services.ps1`
- API: Check Vercel deployment logs

### Resources
- GitHub: [winstonwilliamsiii/BBBot](https://github.com/winstonwilliamsiii/BBBot)
- Streamlit Cloud: [bbbot305.streamlit.app](https://bbbot305.streamlit.app)
- Service Dashboard: [open_dashboard.ps1](open_dashboard.ps1)

---

**Ready to build the Control Center?** Start with [CONTROL_CENTER_QUICK_START.md](docs/CONTROL_CENTER_QUICK_START.md)
