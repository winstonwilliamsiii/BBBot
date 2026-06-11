# 🚀 Bentley Bot Platform Architecture
## Multi-Tenant Trading Automation Platform for Mansa Capital Partners, LLC & Moor Capital Trust

**Last Updated:** February 15, 2026  
**Status:** Production-Ready Client Layer | Admin Layer In Development

---

## 📊 Two-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   CLIENT-FACING LAYER                        │
│         (Investors, Portfolio Managers, Users)               │
├─────────────────────────────────────────────────────────────┤
│  Portfolio Dashboard  │  Budget Mgmt  │  Investment Analysis │
│  Crypto Dashboard     │  Plaid Sync   │  Order Placement     │
│  Bot Performance      │  P&L Reports  │  Risk Monitoring     │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    │ API Gateway (FastAPI + Vercel)
                    │
┌───────────────────▼─────────────────────────────────────────┐
│              BENTLEY BOT CONTROL CENTER                      │
│            (Internal Admin & Orchestration)                  │
├─────────────────────────────────────────────────────────────┤
│  Brokerage API      │  Execution Rules    │  ML Bot          │
│  Orchestration      │  & Venue Routing    │  Orchestration   │
│  ─────────────      │  ───────────────    │  ─────────────   │
│  • Alpaca           │  • FTMO → MT5       │  • 13 AI Bots    │
│  • IBKR             │  • Axi → MT5        │  • MLflow        │
│  • MT5              │  • Zenit Adapter    │  • Backtesting   │
│  • Session Mgmt     │  • Prop Rules       │  • Deployment    │
│  • Order Routing    │  • Scaling Plans    │  • Versioning    │
│                     │                     │                  │
│  Risk Engine        │  Infrastructure     │  Monitoring      │
│  ────────────       │  ──────────────     │  ──────────      │
│  • Drawdown Limits  │  • VPS/GCP Deploy   │  • Exec Logs     │
│  • Margin Rules     │  • Docker Mgmt      │  • Error Alerts  │
│  • Position Sizing  │  • Secrets Vault    │  • Health Checks │
│  • FINRA Compliance │  • Key Rotation     │  • Performance   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 Client-Facing Layer (EXISTING - PRODUCTION)

### Current Implementation Status

| Feature | Technology | Status | Access |
|---------|-----------|--------|--------|
| **Portfolio Dashboard** | Streamlit | ✅ Live | [localhost:8501](http://localhost:8501) |
| **Budget Management** | Streamlit | ✅ Live | Multi-tenant + CSV upload |
| **Investment Analysis** | yfinance, pandas | ✅ Live | Stock screener, charts |
| **Trading Dashboard** | Streamlit + broker adapters | 🟡 Partial | Broker-linked workflows |
| **Plaid Integration** | Plaid API | 🟡 Testing | Docker quickstart |
| **Multi-Broker UI** | Streamlit | 🟡 Partial | Order placement |
| **Bot Performance** | Appwrite | ✅ Live | Metrics API |

### Data Flow (Client Layer)
```
User Request → Streamlit UI → Flask API → MySQL/Appwrite → Response
                ↓
         (Optional) Appwrite Functions
```

---

## 🔧 Bentley Bot Control Center (INTERNAL ADMIN)

### 1. 🧠 AI/ML Bot Orchestration

#### Existing Components ✅
```
/trading/strategies/
├── example_strategies.py     # GoldRsiStrategy, UsdCopShortStrategy
├── base_strategy.py          # Abstract strategy class
└── [13 more bots in development]

/workflows/mlflow/
├── MLflow Server (localhost:5000)
├── Experiment tracking
└── Model versioning

/backend/services/
└── Bot lifecycle management [TO BUILD]
```

#### Required Components 🔨
- [ ] **Bot Deployment Manager UI**
  - Start/stop individual bots
  - Deploy new bot versions
  - Rollback capability
  - A/B testing support
  
- [ ] **MLflow Dashboard Integration**
  - Embedded MLflow UI in control center
  - Hyperparameter visualization
  - Experiment comparison
  
- [ ] **Backtesting Engine UI**
  - Historical performance simulation
  - Multi-timeframe analysis
  - Sharpe ratio, max drawdown, win rate
  
- [ ] **Model Registry**
  - Bot version control
  - Production vs. staging environments
  - Feature flag system

---

### 2. 🔌 Multi-Broker API Orchestration

#### Existing Components ✅
```python
/frontend/utils/broker_interface.py
├── BrokerClient (Abstract Base)
├── AlpacaBrokerClient ✅
├── MT5BrokerClient ✅
└── IBKRBrokerClient (stub)

Database: broker_api_credentials table
├── Multi-tenant support ✅
├── Credentials storage ✅
├── Environment switching (sandbox/live) ✅
└── Status tracking ✅
```

#### Broker Integration Status

| Broker | Type | API Status | Execution | Notes |
|--------|------|-----------|-----------|-------|
| **Alpaca** | Equities | ✅ Complete | REST + WebSocket | Pending business account |
| **IBKR** | Multi-asset | 🔨 Stub | TWS API needed | Complex integration |
| **MT5** | Forex/CFDs | ✅ Ready | Python API | Used for broker and prop execution |
| **FTMO** | Prop Firm | ✅ Ready | MT5 bridge | Challenge rule enforcement |
| **Axi Select** | Prop Firm | ✅ Ready | MT5 bridge | Funded account workflow |
| **Zenit** | Prop Firm | 🟡 Planned | External bridge | Adapter under design |

#### Required Components 🔨
- [ ] **Broker Health Dashboard**
  - Real-time connection status
  - API rate limit monitoring
  - Latency metrics per broker
  - Auto-reconnect logic
  
- [ ] **Order Routing Engine**
  - Smart order routing (SOR)
  - Broker selection by asset class
  - Cost optimization
  - Execution quality analytics
  
- [ ] **Session Manager**
  - Token refresh automation
  - OAuth flow handling
  - Multi-account support
  - Credential rotation

---

### 3. 🏢 Prop Firm Execution Layer

#### Existing Components ✅
```
/mt5/
├── experts/
│   ├── BentleyBot_GBP_JPY_EA.mq5 ✅
│   └── BentleyBot_XAU_USD_EA.mq5 ✅
├── scripts/
│   ├── mt5_alpaca_bridge.py ✅   # Python-MT5 connector
│   └── discord_notifier.py ✅
├── libraries/
│   └── BentleyBot.mqh ✅         # Shared MT5 functions
└── docs/
    ├── SETUP.md ✅
    ├── ARCHITECTURE.md ✅
    └── TROUBLESHOOTING.md ✅
```

#### Prop Firm Support Matrix

| Prop Firm | Platform | Status | Execution Method | Rules Engine |
|-----------|----------|--------|-----------------|--------------|
| **FTMO** | MT4/MT5 | ✅ Ready | MT5 Python API | 🔨 To Build |
| **Axi Select** | MT4/MT5 | ✅ Ready | MT5 Python API | 🔨 To Build |
| **Zenit** | NinjaTrader | 🔨 Planned | Rithmic API | 🔨 To Build |

#### Required Components 🔨
- [ ] **Prop Firm Rule Engine**
  ```python
  class PropFirmRuleEngine:
      def check_daily_loss_limit(account, firm)
      def check_max_drawdown(account, firm)
      def check_consistency_rule(account, firm)  # FTMO-specific
      def check_profit_target(account, firm)
      def enforce_news_trading_ban(account, firm)
      def validate_trade_before_execution(order, account, firm)
  ```
  
- [ ] **MT5 Bridge Orchestrator**
  - Auto-start MT5 terminals
  - Multi-account management
  - Symbol mapping (Alpaca → MT5)
  - Execution report parser
  
- [ ] **NinjaTrader Connector**
  - Rithmic API integration
  - Futures contract mapping
  - Automated strategy deployment
  
- [ ] **Payout Tracker**
  - Profit withdrawal scheduling
  - Funded account scaling
  - Challenge progress monitoring
  - Certificate management

---

### 4. 🛡️ Risk & Compliance Engine

#### Existing Components ✅
```
Database Tables:
├── broker_api_credentials (multi-tenant) ✅
├── transactions (trade history) ✅
└── portfolio_positions ✅

Python Strategies:
└── base_strategy.py (basic risk checks) 🟡
```

#### Required Components 🔨
- [ ] **Pre-Trade Risk Checks**
  ```python
  class RiskEngine:
      def validate_position_size(symbol, qty, account)
      def check_margin_requirement(order, account)
      def enforce_concentration_limits(symbol, portfolio)
      def validate_leverage(order, account, rules)
      def check_pattern_day_trader_rule(account)  # FINRA
  ```
  
- [ ] **Real-Time Monitoring**
  - Portfolio-level drawdown alerts
  - Margin call prevention
  - Position concentration monitoring
  - Volatility-adjusted position sizing
  
- [ ] **Prop Firm Compliance**
  - Per-firm rule templates (FTMO, Axi, etc.)
  - Automatic trade halting on violation
  - Daily loss limit tracking
  - Max drawdown enforcement
  
- [ ] **FINRA Compliance Module**
  - Pattern day trader detection
  - Wash sale rule tracking
  - Reg T margin calculations
  - Trade reporting (OATS/CAT)

---

### 5. ⚙️ Infrastructure & Deployment

#### Existing Components ✅
```
Docker Services:
├── bentley-airflow-webserver (localhost:8080) ✅
├── bentley-mlflow (localhost:5000) ✅
├── bentley-airbyte-webapp (localhost:8000) ✅
├── bentley-budget-bot (localhost:8501) ✅
├── bentley-mysql (localhost:3307) ✅
└── bentley-redis (localhost:6379) ✅

Deployment:
├── Streamlit Cloud (bbbot305.streamlit.app) ✅
├── Vercel (API + Frontend) ✅
├── Railway (MySQL) ✅
└── Appwrite (Cloud Functions) ✅

Scripts:
├── manage_services.ps1 ✅
├── fix_services.ps1 ✅
└── open_dashboard.ps1 ✅
```

#### Required Components 🔨
- [ ] **VPS Deployment Manager**
  - FOREXVPS.net integration
  - One-click MT5 bot deployment
  - Windows VPS monitoring
  - Remote desktop management
  
- [ ] **GCP Deployment Pipeline**
  - Cloud Run for Python bots
  - Cloud Functions for webhooks
  - Secrets Manager integration
  - CI/CD with GitHub Actions
  
- [ ] **Container Orchestration UI**
  - Docker Compose dashboard
  - Service health visualization
  - Log aggregation viewer
  - Resource usage metrics
  
- [ ] **Secrets Management**
  - HashiCorp Vault integration
  - Environment variable manager
  - API key rotation scheduler
  - Encrypted credential storage

---

### 6. 📊 Internal Analytics & Monitoring

#### Existing Components ✅
```
Monitoring:
├── Service Dashboard (Admin Control Center → Services) ✅
├── Docker health checks ✅
└── Basic error logging ✅

Data:
├── Airbyte (data ingestion) ✅
├── MLflow (experiment tracking) ✅
└── MySQL (transactional data) ✅
```

#### Required Components 🔨
- [ ] **Execution Analytics Dashboard**
  ```
  Metrics per Broker:
  - Order-to-fill latency
  - Slippage analysis
  - Fill rate percentage
  - Rejection reasons
  - Cost per trade
  ```
  
- [ ] **Bot Performance Dashboard**
  ```
  Metrics per Bot:
  - Sharpe ratio
  - Max drawdown
  - Win rate / profit factor
  - Current exposure
  - P&L (daily, weekly, monthly)
  - Risk-adjusted returns
  ```
  
- [ ] **Error Monitoring System**
  - Sentry integration
  - Discord/Slack alerts
  - Error rate by service
  - Auto-restart failed bots
  - Dead letter queue viewer
  
- [ ] **Multi-Broker Reconciliation**
  - Position sync validator
  - Balance discrepancy alerts
  - Trade matching system
  - End-of-day settlement reports

---

## 🗂️ System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SYSTEMS                             │
├──────────────────────────────────────────────────────────────────┤
│  Brokers:          │  Prop Firms:      │  Data:                  │
│  • Alpaca          │  • FTMO           │  • Yahoo Finance        │
│  • IBKR            │  • Axi Select     │  • Plaid                │
│  • MT5             │  • Zenit          │  • Alpha Vantage        │
│  • Session Layer   │  • Rule Engine    │  • Internal trade logs  │
└──────────┬───────────────────┬──────────────────┬────────────────┘
           │                   │                  │
           ▼                   ▼                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                    BENTLEY BOT CONTROL CENTER                     │
│                        (FastAPI Backend)                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────┐  ┌───────────────┐  ┌────────────────┐     │
│  │ Broker API     │  │ Prop Firm     │  │ ML Bot         │     │
│  │ Orchestrator   │  │ Connector     │  │ Manager        │     │
│  │                │  │               │  │                │     │
│  │ • Route orders │  │ • MT5 Bridge  │  │ • Deploy bots  │     │
│  │ • Health check │  │ • NinjaTrader │  │ • Monitor      │     │
│  │ • Rate limits  │  │ • Rule engine │  │ • MLflow sync  │     │
│  └────────────────┘  └───────────────┘  └────────────────┘     │
│                                                                   │
│  ┌────────────────┐  ┌───────────────┐  ┌────────────────┐     │
│  │ Risk Engine    │  │ Secrets Mgmt  │  │ Monitoring     │     │
│  │                │  │               │  │                │     │
│  │ • Pre-trade    │  │ • Vault       │  │ • Logs         │     │
│  │ • Position     │  │ • Rotation    │  │ • Alerts       │     │
│  │ • Compliance   │  │ • Encryption  │  │ • Analytics    │     │
│  └────────────────┘  └───────────────┘  └────────────────┘     │
│                                                                   │
└───────────┬──────────────────────────────────────────────────────┘
            │
            │ REST API / WebSocket
            │
┌───────────▼──────────────────────────────────────────────────────┐
│                      DATA & INFRASTRUCTURE                        │
├──────────────────────────────────────────────────────────────────┤
│  MySQL (Railway)    │  Appwrite          │  Docker Services      │
│  • Credentials      │  • Auth            │  • Airflow            │
│  • Transactions     │  • Functions       │  • MLflow             │
│  • Positions        │  • Storage         │  • Airbyte            │
│  • Audit logs       │  • Audit logs      │  • Redis              │
└───────────┬──────────────────────────────────────────────────────┘
            │
            │ API Gateway (Next.js API Routes / FastAPI)
            │
┌───────────▼──────────────────────────────────────────────────────┐
│                     CLIENT-FACING LAYER                           │
├──────────────────────────────────────────────────────────────────┤
│  Streamlit App      │  Next.js Frontend  │  Mobile (Future)      │
│  (localhost:8501)   │  (Vercel)          │                       │
│                     │                    │                       │
│  • Portfolio        │  • Investor portal │  • React Native       │
│  • Budget           │  • Bot metrics     │  • Portfolio alerts   │
│  • Trading          │  • Analytics       │                       │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Implementation Roadmap

### Phase 1: Core Admin Infrastructure (4-6 weeks)
**Priority: High | Dependencies: None**

1. **Week 1-2: Control Center Dashboard**
   - [ ] Create FastAPI admin API (`/backend/api/admin/`)
   - [ ] Admin authentication & RBAC
   - [ ] Service health dashboard UI
   - [ ] Docker container management UI
   
2. **Week 3-4: Broker Orchestration**
   - [ ] Complete IBKR integration
   - [ ] Build broker health monitoring
   - [ ] Implement session manager
   
3. **Week 5-6: Monitoring & Logs**
   - [ ] Centralized logging system
   - [ ] Error alerting (Discord/Slack)
   - [ ] Execution analytics dashboard
   - [ ] Multi-broker reconciliation

---

### Phase 2: ML Bot Orchestration (3-4 weeks)
**Priority: High | Dependencies: Phase 1**

1. **Week 1-2: Bot Deployment Manager**
   - [ ] Bot version control system
   - [ ] Start/stop/restart UI
   - [ ] Environment management (dev/staging/prod)
   - [ ] A/B testing framework
   
2. **Week 3-4: MLflow Integration**
   - [ ] Embedded MLflow UI in control center
   - [ ] Experiment comparison tool
   - [ ] Automated model registry
   - [ ] Performance alerting

---

### Phase 3: Prop Firm Execution (4-5 weeks)
**Priority: Medium | Dependencies: Phase 1**

1. **Week 1-2: Prop Firm Rule Engine**
   - [ ] FTMO rule implementation
   - [ ] Axi Select rule implementation
   - [ ] Pre-trade validation system
   - [ ] Real-time violation alerts
   
2. **Week 3-4: MT5 Bridge Enhancement**
   - [ ] Multi-account orchestration
   - [ ] Auto-start/stop terminals
   - [ ] Symbol mapping service
   - [ ] Execution report parser
   
3. **Week 5: NinjaTrader Connector**
   - [ ] Rithmic API integration
   - [ ] Zenit rule implementation
   - [ ] Futures contract mapping

---

### Phase 4: Risk & Compliance (3-4 weeks)
**Priority: High | Dependencies: Phase 2**

1. **Week 1-2: Risk Engine Core**
   - [ ] Pre-trade risk checks
   - [ ] Position sizing validator
   - [ ] Margin requirement calculator
   - [ ] Concentration limit enforcer
   
2. **Week 3-4: Compliance Module**
   - [ ] FINRA rule implementation
   - [ ] Pattern day trader detection
   - [ ] Wash sale tracking
   - [ ] Trade reporting system

---

### Phase 5: Infrastructure & Deployment (2-3 weeks)
**Priority: Medium | Dependencies: Phase 1**

1. **Week 1-2: VPS Management**
   - [ ] FOREXVPS.net API integration
   - [ ] One-click MT5 deployment
   - [ ] VPS monitoring dashboard
   - [ ] Remote desktop connector
   
2. **Week 2-3: Secrets Management**
   - [ ] HashiCorp Vault setup
   - [ ] Credential rotation automation
   - [ ] Environment variable UI
   - [ ] Encryption at rest

---

### Phase 6: Advanced Analytics (4-5 weeks)
**Priority: Low | Dependencies: All above**

1. **Week 1-2: Execution Analytics**
   - [ ] Latency monitoring
   - [ ] Slippage analysis
   - [ ] Fill rate tracking
   - [ ] Cost analysis
   
2. **Week 3-4: Bot Performance Analytics**
   - [ ] Sharpe ratio dashboard
   - [ ] Drawdown visualization
   - [ ] Win rate tracking
   - [ ] Risk-adjusted returns
   
3. **Week 5: Reconciliation System**
   - [ ] Position sync validator
   - [ ] Balance discrepancy alerts
   - [ ] Trade matching engine
   - [ ] Settlement reports

---

## 📂 Directory Structure Update

### Recommended Folder Structure for Control Center

```
/bentley-bot/                          # NEW: Organized control center code
├── bots/                              # All 13 AI/ML trading bots
│   ├── titan.py                       # Titan | Mansa Tech | CNN with Deep Learning
│   ├── vega.py                        # Vega_Bot | Mansa_Retail | Vega Mansa Retail MTF-ML
│   ├── draco.py                       # Draco | Mansa Money Bag | Sentiment Analyzer
│   ├── altair.py                      # Altair | Mansa AI | News Trading
│   ├── procryon.py                    # Procryon | Crypto Fund | Crypto Arbitrage
│   ├── hydra.py                       # Hydra | Mansa Health | Momentum Strategy
│   ├── triton.py                      # Triton | Mansa Transportation | Pending
│   ├── dione.py                       # Dione | Mansa Options | Put Call Parity
│   ├── dogon.py                       # Dogon | Mansa ETF | Portfolio Optimizer
│   ├── rigel.py                       # Rigel | Mansa FOREX | Mean Reversion
│   ├── orion.py                       # Orion | Mansa Minerals | GoldRSI Strategy
│   ├── rhea.py                        # Rhea | Mansa ADI | Intra-Day / Swing
│   └── jupicita.py                    # Jupicita | Mansa_Smalls | Pairs Trading
│
├── brokers/                           # Brokerage and execution clients
│   ├── alpaca_client.py               # Alpaca brokerage client
│   ├── ibkr_client.py                 # Interactive Brokers client
│   ├── mt5_client.py                  # MetaTrader 5 client
│   ├── prop_firm_ftmo.py              # FTMO execution adapter
│   ├── prop_firm_axi.py               # Axi Select execution adapter
│   └── prop_firm_zenit.py             # Zenit execution adapter
│
├── config/                            # Bot runtime profiles
│   └── bots/
│       ├── titan.yml                  # Titan profile
│       ├── ...
│       └── jupicita.yml               # Jupicita profile
│
├── mlflow/                            # ML experiment tracking
│   ├── train.py                       # Model training pipeline
│   ├── backtest.py                    # Backtesting engine
│   └── register.py                    # Model registry operations
│
├── streamlit_app/                     # Streamlit UI modules
│   ├── admin.py                       # Admin control center page
│   ├── investor.py                    # Investor-facing pages
│   └── dashboards.py                  # Reusable dashboard components
│
└── utils/                             # Shared utilities
    ├── risk.py                        # Risk engine functions
    ├── config.py                      # Configuration management
    └── secrets.py                     # Secrets manager
```

### Full Project Structure

```
BentleyBudgetBot/
├── bentley-bot/                       # 🆕 NEW: Organized control center
│   ├── bots/                          # 13 trading bots
│   ├── brokers/                       # Brokerage and prop-firm execution clients
│   ├── config/                        # YAML bot profiles
│   ├── mlflow/                        # ML pipelines
│   ├── streamlit_app/                 # UI modules
│   └── utils/                         # Shared utilities
│
├── frontend/                          # CLIENT-FACING LAYER
│   ├── components/                    # Streamlit UI components ✅
│   ├── pages/                         # Streamlit pages ✅
│   ├── styles/                        # CSS + color scheme ✅
│   └── utils/
│       └── broker_interface.py        # Broker abstraction ✅
│
├── backend/                           # CONTROL CENTER API
│   ├── api/
│   │   ├── app.py                     # Flask application (main)
│   │   ├── admin/                     # 🔨 TO BUILD
│   │   │   ├── __init__.py
│   │   │   ├── bots.py                # Bot management endpoints (Flask Blueprint)
│   │   │   ├── brokers.py             # Broker orchestration (Flask Blueprint)
│   │   │   ├── risk.py                # Risk engine endpoints (Flask Blueprint)
│   │   │   └── monitoring.py          # Logs & analytics (Flask Blueprint)
│   │   └── client/                    # Client-facing API ✅
│   │       ├── portfolio.py
│   │       ├── transactions.py
│   │       └── budget.py
│   ├── services/
│   │   ├── broker_orchestrator.py     # 🔨 TO BUILD
│   │   ├── risk_engine.py             # 🔨 TO BUILD
│   │   ├── prop_firm_connector.py     # 🔨 TO BUILD
│   │   ├── bot_deployment.py          # 🔨 TO BUILD
│   │   └── secrets_manager.py         # 🔨 TO BUILD
│   └── models/                        # SQLAlchemy models ✅
│
├── trading/                           # STRATEGY ENGINE
│   ├── strategies/
│   │   ├── example_strategies.py      # Gold RSI, USD/COP ✅
│   │   └── base_strategy.py           # Abstract base ✅
│   └── bots/                          # 🔨 13 BOTS TO DEPLOY
│
├── mt5/                               # PROP FIRM EXECUTION
│   ├── experts/                       # MT5 EAs ✅
│   ├── scripts/
│   │   ├── mt5_alpaca_bridge.py       # Python-MT5 ✅
│   │   └── prop_firm_rules.py         # 🔨 TO BUILD
│   └── orchestrator/                  # 🔨 TO BUILD
│       └── mt5_manager.py
│
├── workflows/                         # DATA PIPELINE
│   ├── airflow/                       # Orchestration ✅
│   ├── mlflow/                        # Experiment tracking ✅
│   └── airbyte/                       # Data ingestion ✅
│
├── pages/                             # Streamlit pages
│   ├── 99_🔧_Admin_Control_Center.py # 🔨 Streamlit admin dashboard
│   └── [other existing pages]
│
├── admin_ui/                          # 🔨 OPTIONAL HTML UI
│   ├── dashboard.html                 # Alternative admin dashboard
│   └── [other HTML pages if needed]
│
└── docs/
    ├── BENTLEY_BOT_CONTROL_CENTER_ARCHITECTURE.md  # This file
    ├── BROKER_API_COMPLETE.md         # Broker setup ✅
    ├── BROKER_ABSTRACTION_EXPLAINED.md # Strategy guide ✅
    └── RISK_ENGINE_SPEC.md            # 🔨 TO CREATE
```

---

## 🚦 Current System Status

### ✅ Production-Ready Components
- Client-facing Streamlit app
- MySQL multi-tenant database
- Appwrite cloud functions
- Broker abstraction layer (Alpaca, MT5)
- MT5 Expert Advisors (GBP/JPY, XAU/USD)
- MLflow experiment tracking
- Airflow workflow orchestration
- Docker containerization
- Basic service monitoring

### 🟡 Partially Complete
- IBKR integration (stub exists)
- MT5 and prop-firm routing expansion
- Risk engine (basic checks in strategies)
- Admin dashboard includes a native Streamlit Services tab
  - ✅ **NEW:** Control Center Admin UI created (`pages/99_🔧_Admin_Control_Center.py`)

### 🔨 To Build (Priority Order)
1. ~~**Control Center Admin UI**~~ ✅ **COMPLETE** - See `pages/99_🔧_Admin_Control_Center.py`
2. **Broker Health Monitoring** (2 weeks)
3. **Bot Deployment Manager** (3-4 weeks)
4. **Prop Firm Rule Engine** (4-5 weeks)
5. **Risk Engine** (3-4 weeks)
6. **Execution Analytics** (4-5 weeks)

---

## 🔐 Security & Compliance

### Access Control
```
Role Hierarchy:
├── Super Admin (Winston)
│   └── Full access to Control Center
├── Admin (Mansa Partners)
│   └── Bot management, risk monitoring
├── Trader (Team members)
│   └── View-only analytics
└── Client (Investors)
    └── Portfolio dashboard only
```

### Data Protection
- [ ] API keys encrypted at rest (AES-256)
- [ ] TLS 1.3 for all connections
- [ ] HashiCorp Vault for secrets
- [ ] Audit logging for all admin actions
- [ ] IP whitelisting for admin panel
- [ ] 2FA for admin access

### Compliance
- [ ] FINRA Reg T margin calculations
- [ ] Pattern day trader rule enforcement
- [ ] Wash sale tracking
- [ ] OATS/CAT trade reporting (if registered BD)

---

## 📞 Support & Contacts

### Technology Stack Experts
- **Streamlit/FastAPI:** Python team
- **MT5/MQL5:** Trading platform team
- **MLflow/Airflow:** Data engineering team
- **Docker/GCP:** DevOps team

### External Services
- **FOREXVPS.net:** Windows VPS for MT5
- **Railway:** MySQL hosting
- **Vercel:** Frontend deployment
- **Appwrite:** Cloud functions & auth

---

## 📝 Notes

### Design Decisions
1. **Two-layer architecture** separates client UX from admin complexity
2. **Broker abstraction** allows easy addition of new brokers
3. **Prop firm bridging** via MT5/NinjaTrader for firms without public APIs
4. **Docker-first** approach for local dev + scalable cloud deployment
5. **FastAPI** for admin API (high performance, async, auto-docs)

### Future Enhancements (12+ months)
- [ ] Mobile app (React Native)
- [ ] Telegram bot for alerts
- [ ] Automated tax reporting (Form 8949)
- [ ] Social trading (copy trading feature)
- [ ] White-label platform for other prop firms
- [ ] Blockchain settlement for faster transfers

---

**Next Steps:** Review roadmap with team → Prioritize Phase 1 → Start control center UI development

