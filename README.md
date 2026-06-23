# 🏛️ Bentley Budget Bot - Financial Portfolio & Trading Platform

<div align="center">

![Process Flow](https://github.com/user-attachments/assets/433b4e08-945b-4ec0-b9f9-9a7b8085e602)

**Multi-Platform Financial Dashboard with Unified Broker Integration**

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://bbbot305.streamlit.app)
[![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![Railway](https://img.shields.io/badge/Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)](https://railway.app)
[![Appwrite](https://img.shields.io/badge/Appwrite-F02E65?style=for-the-badge&logo=appwrite&logoColor=white)](https://appwrite.io)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

[Live Demo](https://bbbot305.streamlit.app/) • [Documentation](#-documentation) • [API Reference](#-api-integrations) • [Setup Guide](#-quick-start) • [Titan Bot README](docs/root/TITAN_README.md) • [Dogon Bot README](docs/root/DOGON_README.md) • [Cygnus Bot README](docs/root/CYGNUS_README.md)

</div>

---

## 📊 Overview

Bentley Budget Bot is a comprehensive financial management platform that combines personal budgeting, multi-broker trading, portfolio analytics, and real-time market data visualization. Built for **Bot Name and Description** and **Moor Capital Trust**, with support for personal accounts.

### 🎯 Key Features

- **Multi-Tenant Portfolio Management** - Track Bot Name and Description, Moor Trust, and personal accounts
- **Unified Broker Integration** - Seamlessly trade across 6+ brokerages (Alpaca, IBKR, Schwab, Binance, MT5, TradeStation)
- **Real-Time Market Data** - Live crypto prices, stock quotes, and forex rates
- **Banking Integration** - Plaid API for automated transaction syncing
- **Budget Tracking** - Comprehensive expense categorization and forecasting
- **ML-Powered Analytics** - MLflow experiments for trading strategies
- **Workflow Automation** - Airflow DAGs for data pipelines

---

## 🏗️ Architecture

### Tech Stack

#### Frontend
- **Streamlit** - Main web interface (`streamlit_app.py`)
- **React/Next.js** - Vercel-hosted frontend (in development)
- **CSS Modules** - Custom styling with color scheme system

#### Backend
- **Python 3.12+** - Core application logic
- **FastAPI** - Primary local control-center and bot API (`Main.py`)
- **Vercel Functions** - Stateless edge/serverless endpoints (`api/index.py`)
- **MySQL 8.0** - Primary database (Railway + Local Port 3307)
- **Appwrite** - Authentication, storage, and cloud functions

#### Data & Analytics
- **Airflow** - Workflow orchestration
- **MLflow** - ML experiment tracking
- **DBT** - Data transformation pipelines
- **Airbyte** - Data ingestion connectors

#### Infrastructure
- **Docker** - Containerized services
- **Railway** - MySQL hosting (nozomi.proxy.rlwy.net:54537)
- **Vercel** - Frontend deployment
- **Streamlit Cloud** - [bbbot305.streamlit.app](https://bbbot305.streamlit.app)

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Bentley Budget Bot                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │  Streamlit   │      │   Vercel     │      │   Appwrite   │ │
│  │  Dashboard   │◄────►│   Frontend   │◄────►│   Functions  │ │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘ │
│         │                     │                      │          │
│         └─────────────────────┼──────────────────────┘          │
│                               │                                 │
│                    ┌──────────▼──────────┐                     │
│                    │   API Layer         │                     │
│                    │   (Vercel/FastAPI)  │                     │
│                    └──────────┬──────────┘                     │
│                               │                                 │
│         ┌─────────────────────┼─────────────────────┐          │
│         │                     │                     │          │
│    ┌────▼─────┐         ┌────▼─────┐         ┌────▼─────┐   │
│    │  MySQL   │         │  Broker  │         │  Banking │   │
│    │ Railway  │         │   APIs   │         │   APIs   │   │
│    │ Port3307 │         │          │         │          │   │
│    └──────────┘         └──────────┘         └──────────┘   │
│         │                     │                     │          │
│    ┌────▼─────────────────────▼─────────────────────▼────┐   │
│    │             Data Processing Layer                    │   │
│    │  • Airflow (DAGs)  • MLflow (Experiments)           │   │
│    │  • DBT (Transform) • Airbyte (Ingestion)            │   │
│    └──────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Branching Strategy
- **main/** → Production (Streamlit Cloud). Auto-deploys via GitHub Actions.
- **dev/** → Development (localhost). Sandbox for experiments.
- **feature/** → Experimental branches. Merged into `dev` first.
- **hotfix/** → Emergency fixes for production.

---

## ⚡ Streamlit Caching
- `@st.cache_data` used for expensive API calls.
- Manual "🔄 Refresh Data" button clears cache when fresh data is required.
- Ensures fast UI while keeping portfolio/trade data up-to-date.

---

## 🗂️ Folder Structure

```text
BentleyBudgetBot/
├── api/                          # Vercel and service API entrypoints
├── config/                       # Shared configuration and secrets templates
│   ├── database/
│   ├── env/
│   ├── secrets/
│   └── streamlit/
├── data/                         # Local datasets and generated data assets
├── docs/                         # Project documentation and reference material
│   ├── guides/
│   ├── requirements/
│   ├── reports/
│   ├── root/
│   ├── setup-guides/
│   ├── status-reports/
│   └── summaries/
├── docker/                       # Container definitions and compose stacks
├── frontend/                     # Shared frontend utilities and styling
├── pages/                        # Streamlit multipage routes
├── scripts/                      # Automation, deployment, and repair scripts
├── src/                          # Core source code
│   ├── analytics/
│   ├── bots/
│   ├── integrations/
│   └── services/
│       └── appwrite/
├── tests/                        # Automated tests and validation scripts
├── workflows/                    # Orchestration and pipeline assets
├── Main.py                       # FastAPI application entrypoint
└── streamlit_app.py              # Main Streamlit dashboard
```

---

## 🔐 Secrets
- `.env.dev` → Alpaca paper keys
- `.env.prod` → Alpaca live keys
- Secrets managed via GitHub + Streamlit Cloud

---

## ✅ Deployment
- Push to `main` → GitHub Actions runs tests + deploys to Streamlit Cloud
- Push to `dev` → Local development only

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- MySQL 8.0 (or use Railway MySQL)
- Docker & Docker Compose (optional)
- Node.js 18+ (for frontend development)

### Installation

#### 1. Clone Repository
```bash
git clone https://github.com/yourusername/BentleyBudgetBot.git
cd BentleyBudgetBot
```

#### 2. Set Up Local Python Environments
```bash
# Streamlit dashboard
python -m venv .venv-streamlit
.venv-streamlit\Scripts\activate
pip install -r requirements-streamlit.txt
deactivate

# FastAPI control-center/API service
python -m venv .venv-api
.venv-api\Scripts\activate
pip install -r requirements-api.txt
deactivate

# Rhea local service
python -m venv .venv-rhea
.venv-rhea\Scripts\activate
pip install -r docs/requirements/requirements-rhea.txt
deactivate

# Shared bot runtime
python -m venv .venv-bots
.venv-bots\Scripts\activate
pip install -r requirements-bots.txt
deactivate

# TensorFlow bot environment
python -m venv .venv-tf
.venv-tf\Scripts\activate
pip install -r docs/requirements/requirements-tf.txt
deactivate

# Dogon isolated runtime/training environment
python -m venv .venv-dogon
.venv-dogon\Scripts\activate
pip install -r docs/requirements/requirements-dogon.txt
deactivate
```

Use one venv per local Python project to avoid dependency drift across Dashboard/API/ML workflows.
Keep Docker for infrastructure services only (MySQL, Redis, MLflow, Airflow, Airbyte).
Use shared bot framework envs where possible: PyTorch -> `.venv-bots`, TensorFlow -> `.venv-tf`, Dogon -> `.venv-dogon`.
See [docs/setup-guides/SIX_ENVIRONMENT_POLICY.md](docs/setup-guides/SIX_ENVIRONMENT_POLICY.md) for the canonical six-env map.

Dependency entrypoints at repo root:
- `requirements.txt` -> minimal Streamlit Cloud-safe entrypoint (delegates to `requirements-streamlit.txt`)
- `requirements-streamlit.txt` -> dashboard/runtime dependencies (including local editable packages)
- `requirements-api.txt` -> FastAPI control center dependency entrypoint
- `requirements-bots.txt` -> shared bot runtime dependency entrypoint

Root cleanup note:
- Legacy loose root artifacts were archived to `archive/root_loose_files/` to keep root startup/config files focused.

#### 3. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
# Required: MySQL, Appwrite, Broker APIs
```

#### 4. Initialize Database
```bash
# Deploy unified broker schema
python deploy_broker_schema.py

# Run migrations
python setup_mysql_database.py
```

#### 5. Run Application
```bash
# Start Streamlit app
streamlit run streamlit_app.py

# Access at http://localhost:8501
```

#### 5b. Start Control Center API (Admin Dashboard Backend)
```bash
# Windows PowerShell helper script for the unified FastAPI app
powershell -ExecutionPolicy Bypass -File .\start_control_center_api.ps1

# Health check
curl http://localhost:5001/health

# FastAPI docs
# http://localhost:5001/docs
```

#### 6. Run FastAPI Directly (Optional Alternate Startup)
```bash
# Install local dependencies (includes FastAPI)
pip install -r requirements-local.txt

# Start the same FastAPI app with auto-reload
python -m uvicorn Main:app --host 0.0.0.0 --port 5001 --reload

# Or use npm script
npm run api:dev

# API Docs
# http://localhost:5001/docs
```

### 6b. Hydra Bot Quick Start

Hydra is the Mansa Health momentum bot with FastAPI endpoints, Airbyte feed configuration, an Airflow DAG, and MLflow logging.

```bash
# Start the shared FastAPI control center app
powershell -ExecutionPolicy Bypass -File .\start_control_center_api.ps1

# Bootstrap Hydra demo state
curl http://localhost:5001/hydra/bootstrap

# Analyze a healthcare ticker
curl -X POST http://localhost:5001/hydra/analyze \
   -H "Content-Type: application/json" \
   -d '{"ticker":"UNH","news_headlines":["Analysts upgrade healthcare leaders"]}'
```

Reference: [docs/setup-guides/HYDRA_QUICK_START.md](docs/setup-guides/HYDRA_QUICK_START.md)

Platform reference: [docs/setup-guides/CONTROL_CENTER_PLATFORM.md](docs/setup-guides/CONTROL_CENTER_PLATFORM.md)

### 6c. Triton Bot Quick Start

Triton is the Mansa Transportation swing bot. It runs through the shared FastAPI control center, uses the Bentley UI launch contract, can log signal runs to MLflow, and is wired for Alpaca or IBKR execution.

```bash
# Start the shared FastAPI control center app
powershell -ExecutionPolicy Bypass -File .\start_control_center_api.ps1

# Bootstrap Triton demo state
curl -X POST http://localhost:5001/triton/bootstrap

# Run a transportation analysis
curl -X POST http://localhost:5001/triton/analyze \
   -H "Content-Type: application/json" \
   -d '{"ticker":"IYT","news_headlines":["Freight demand rebounds across major rail and parcel names"]}'

# Toggle Triton from the launcher contract
powershell -ExecutionPolicy Bypass -File .\start_bot_mode.ps1 -Bot Triton -Mode ON -Broker Alpaca -TradingMode paper
```

Triton architecture alignment:
- FastAPI routes: `/triton/*` on `http://localhost:5001`
- Bentley UI quick-launch: Streamlit quick-launch buttons now include Triton
- MLflow: logs to `MLFLOW_TRACKING_URI` or `TRITON_MLFLOW_TRACKING_URI`
- MySQL, Railway, Appwrite, Docker: inherited from the shared platform health and deployment stack already used by the control center

### 🤖 Dogon ETF ML Training (Biweekly)

Use the new Dogon training pipeline to run a Gradient Boosted Trees baseline plus LSTM and TCN models for `Mansa_ETF`.

```bash
# Create isolated training environment (recommended)
python -m venv .venv-dogon

# Activate on Windows
.venv-dogon\Scripts\activate

# Install Dogon-only training dependencies
pip install -r docs/requirements/requirements-dogon.txt

# Run a local Dogon training cycle
python scripts/train_dogon_models.py --symbols SPY,QQQ,IWM,DIA,XLK,XLF --days 730 --min-accuracy 0.53
```

Why isolate: this avoids package conflicts between ML training dependencies and live-trading dependencies (for example, `websockets` requirements used by different integrations).

Airflow schedule:
- DAG: `dogon_etf_biweekly_training`
- Interval: every 14 days
- Gate: run fails if best model accuracy is below `--min-accuracy` (default `0.53`)

### Docker Setup (Optional)

```bash
# Start the Streamlit app container
docker compose -f docker/docker-compose.yml up -d

# Start MLflow and data services as needed
docker compose -f docker/docker-compose-consolidated.yml up -d mysql mlflow

# View logs
docker compose -f docker/docker-compose.yml logs -f

# Stop services
docker compose -f docker/docker-compose.yml down
```

---

## 📁 Project Structure

```
BentleyBudgetBot/
├── 🎨 Frontend
│   ├── streamlit_app.py          # Main Streamlit application
│   ├── pages/                    # Multi-page app routes
│   │   ├── 01_💰_Personal_Budget.py
│   │   ├── 02_📈_Investment_Analysis.py
│   │   ├── 03_🔴_Live_Crypto_Dashboard.py
│   │   ├── 04_💼_Broker_Trading.py
│   │   ├── 05_🌐_Multi_Broker_Trading.py
│   │   ├── 06_🏦_Plaid_Test.py
│   │   ├── 07_🤖_Trading_Bot.py
│   │   └── 08_Investment_Portfolio.py
│   ├── frontend/                 # React/Next.js components
│   └── vercel-frontend/          # Vercel deployment
│
├── 🔧 Backend
│   ├── api/                      # Vercel serverless functions
│   ├── services/                 # Broker connectors & utilities
│   ├── bentleybot/               # Core business logic
│   │   ├── sql/                  # Database schemas
│   │   └── utils/                # Helper functions
│   └── src/services/appwrite/    # Appwrite cloud functions
│
├── 🗄️ Database
│   ├── bentleybot/sql/
│   │   ├── schema.sql            # Main database schema
│   │   └── #MySQL for UNIFIED BROKER Schema.sql
│   ├── migrations/               # Database migrations
│   └── mysql_config/             # MySQL configurations
│
├── 🔌 Integrations
│   ├── integrations/
│   │   ├── alpaca/               # Alpaca Markets
│   │   ├── plaid/                # Banking APIs
│   │   └── binance/              # Cryptocurrency
│   └── sdk/                      # Custom SDK modules
│
├── 📊 Data Pipelines
│   ├── workflows/
│   │   ├── airflow/              # Airflow DAGs
│   │   ├── airbyte/              # Data connectors
│   │   └── mlflow/               # ML experiments
│   ├── dbt_project/              # DBT transformations
│   └── bbbot1_pipeline/          # Custom data pipelines
│
├── 🧪 Testing & Scripts
│   ├── tests/                    # Test suites
│   ├── test_*.py                 # Integration tests
│   └── scripts/                  # Utility scripts
│
├── 📚 Documentation
│   ├── README.md                 # This file
│   ├── PROJECT_STRUCTURE.md      # Detailed structure
│   ├── UNIFIED_BROKER_SCHEMA_GUIDE.md
│   ├── MYSQL_CONSOLIDATION_REPORT.md
│   └── BROKER_SETUP_GUIDE.md
│
└── 🐳 DevOps
    ├── docker-compose.yml        # Docker orchestration
    ├── Dockerfile                # Container definition
    ├── .github/workflows/        # CI/CD pipelines
    └── railway.json              # Railway deployment
```

---

## 💼 API Integrations

### ✅ Trading & Brokerage APIs

| Broker | Asset Class | Status | Environment |
|--------|-------------|--------|-------------|
| **Alpaca Markets** | US Equities | ✅ Connected | Paper Trading |
| **Interactive Brokers** | Multi-Asset | ✅ Configured | Production Ready |
| **Charles Schwab** | US Equities | ⚙️ In Progress | Sandbox |
| **Binance** | Cryptocurrency | ✅ Connected | Production |
| **TradeStation** | Equities/Futures | ⚙️ Configured | Sandbox |
| **MetaTrader 5** | Forex/Commodities | ✅ Connected | Demo Account |

### ✅ Banking & Payment APIs

| Service | Purpose | Status |
|---------|---------|--------|
| **Plaid** | Transaction Sync | ✅ Sandbox Active |
| **Capital One DevExchange** | Banking APIs | ⚙️ Ready |
| **Bank of America CashPro** | Corporate Banking | ⏳ Pending Approval |

### ✅ Market Data Providers

| Provider | Data Type | Status |
|----------|-----------|--------|
| **Tiingo** | Real-time Equities | ✅ Connected |
| **Alpha Vantage** | Fundamentals | ✅ Active |
| **yfinance** | Historical Data | ✅ Active |
| **CoinGecko** | Crypto Prices | ✅ Active |

### ✅ Infrastructure & Tools

| Service | Purpose | Status |
|---------|---------|--------|
| **Appwrite** | Auth & Functions | ✅ 11 Functions Deployed |
| **Railway** | MySQL Hosting | ✅ Running (Port 54537) |
| **Vercel** | Frontend Hosting | ✅ Deployed |
| **Streamlit Cloud** | App Hosting | ✅ [bbbot305.streamlit.app](https://bbbot305.streamlit.app) |

---

## 🎨 Features

### 📊 Portfolio Dashboard
- Real-time portfolio valuation across all accounts
- Multi-tenant view (Bot Name and Description, Moor Trust, Personal)
- Asset allocation charts and P&L tracking
- Position monitoring with live prices

### 💰 Budget Management
- Personal expense tracking with categorization
- CSV import from bank statements
- Budget vs. actual analysis
- Plaid integration for automatic transaction sync

### 📈 Investment Analysis
- Stock screener with technical indicators
- Fundamental analysis (P/E, EPS, dividends)
- Historical price charts with indicators
- Earnings calendar and news feed

### 🔴 Live Crypto Dashboard
- Real-time cryptocurrency prices
- Portfolio tracking for multiple wallets
- Trading interface for Binance
- Market cap rankings and trends

### 💼 Multi-Broker Trading
- Unified order placement across 6 brokers
- Order status tracking and fills
- Position reconciliation
- Execution analytics

### 🤖 Trading Bot
- Automated strategy execution
- Backtesting framework with MLflow
- Risk management rules
- Performance metrics tracking

---

## 🗄️ Database Architecture

### Consolidated MySQL (Port 3307)

The project uses a **single consolidated MySQL instance** running on Port 3307 with the following databases:

| Database | Purpose | Tables | Status |
|----------|---------|--------|--------|
| **mansa_bot** | Trading operations, broker data | 46 | ✅ Primary |
| **bbbot1** | Market data bulk storage | 42 | ✅ Active |
| **mydb** | Personal budget & Plaid data | 19 | ✅ Active |
| **mlflow_db** | ML experiments & Airflow metadata | 34 | ✅ Active |
| **mgrp_schema** | Historical price data | 5 | ✅ Active |

### Unified Broker Schema

Supports **multi-tenant, normalized trading operations**:

- **brokers** - Broker configurations (Alpaca, IBKR, MT5, etc.)
- **accounts** - Multi-tenant accounts (Bot Name and Description, Moor Trust, Personal)
- **positions** - Current holdings with P&L tracking
- **orders** - Order lifecycle from submission to fill
- **order_executions** - Individual fill details

See [UNIFIED_BROKER_SCHEMA_GUIDE.md](./UNIFIED_BROKER_SCHEMA_GUIDE.md) for full details.

---

## 🔐 Configuration

### Environment Variables

Required variables in `.env`:

```bash
# MySQL Configuration (Consolidated Port 3307)
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=mansa_bot

# Appwrite Configuration
APPWRITE_ENDPOINT=https://fra.cloud.appwrite.io/v1
APPWRITE_PROJECT_ID=68869ef500017ca73772
APPWRITE_API_KEY=your_api_key

# Broker APIs
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
BINANCE_API_KEY=your_binance_key
BINANCE_SECRET_KEY=your_binance_secret

# Banking APIs
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret
PLAID_ENV=sandbox

# Market Data
TIINGO_API_KEY=your_tiingo_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# Railway (Production)
RAILWAY_MYSQL_HOST=nozomi.proxy.rlwy.net
RAILWAY_MYSQL_PORT=54537
RAILWAY_MYSQL_PASSWORD=<from_railway_dashboard>
```

### Broker Configuration

See [BROKER_SETUP_GUIDE.md](./BROKER_SETUP_GUIDE.md) for detailed broker API setup instructions.

### Plaid Sync Export + Load (One Command)

Use the reusable utility script to run Plaid `transactions/sync`, export a full JSON artifact, and upsert into MySQL in one command:

```bash
python scripts/plaid_sync_export_load.py --access-token <access_token>
```

Output:
- JSON artifact in `data/plaid/transactions_sync_<timestamp>.json`
- Upsert into `mydb.plaid_transactions`

#### Local/Host MySQL mode

```bash
python scripts/plaid_sync_export_load.py \
   --access-token <access_token> \
   --db-host 127.0.0.1 --db-port 3306 \
   --db-user root --db-password <password> \
   --db-name mydb
```

#### Docker MySQL mode (recommended for this repo)

```bash
python scripts/plaid_sync_export_load.py \
   --access-token <access_token> \
   --db-name mydb \
   --docker-container bentley-mysql \
   --docker-mysql-user root \
   --docker-mysql-password root
```

Environment fallbacks used by the script:
- Plaid: `PLAID_CLIENT_ID`, `PLAID_SECRET`
- MySQL: `BUDGET_MYSQL_*`, then `MYSQL_*`

---

## 🧪 Testing

### Run All Tests
```bash
# Python unit tests
pytest tests/

# API connection tests
python test_api_connections.py

# MySQL connection verification
python verify_mysql_status.py

# Multi-broker integration
python test_multi_broker.py
```

### Test Coverage
- ✅ MySQL connection tests (all 5 databases)
- ✅ API integration tests (Tiingo, Alpaca, Plaid)
- ✅ Broker adapter tests
- ✅ Budget calculation tests
- ✅ Data pipeline tests

---

## 🚀 Deployment

### Streamlit Cloud
Current deployment: [https://bbbot305.streamlit.app](https://bbbot305.streamlit.app)

```bash
# Configure secrets in Streamlit Cloud dashboard
# Add all .env variables to secrets.toml format
```

### Vercel Frontend
```bash
cd vercel-frontend
vercel --prod
```

### Railway MySQL
Database is already deployed at:
- Host: `nozomi.proxy.rlwy.net`
- Port: `54537`
- Database: `mansa_bot`

### Docker Deployment
```bash
# Build and deploy all services
docker-compose -f docker-compose.prod.yml up -d

# View service status
docker-compose ps

# View logs
docker-compose logs -f streamlit
```

---

## 📚 Documentation

### Core Documentation
- [Project Structure](./PROJECT_STRUCTURE.md) - Complete directory overview
- [Unified Broker Schema Guide](./UNIFIED_BROKER_SCHEMA_GUIDE.md) - Database architecture
- [MySQL Consolidation Report](./MYSQL_CONSOLIDATION_REPORT.md) - Database migration details
- [Broker Setup Guide](./BROKER_SETUP_GUIDE.md) - Broker API configuration

### API Documentation
- [Trade API Summary](./TRADE_API_SUMMARY.md) - Trading API reference
- [Broker Adapters](./BROKER_ADAPTERS_IMPLEMENTATION.md) - Adapter implementation guide
- [Broker Mapping](./BROKER_MAPPING.md) - Broker feature matrix

### Quick References
- [Quick Reference](./QUICK_REFERENCE.md) - Common commands and troubleshooting
- [Broker Quick Reference](./BROKER_QUICK_REFERENCE.md) - Broker-specific notes
- [Broker Schema Summary](./BROKER_SCHEMA_SUMMARY.md) - Schema quick start

---

## 🤝 Contributing

### Development Workflow

1. **Fork & Clone**
   ```bash
   git clone https://github.com/yourusername/BentleyBudgetBot.git
   cd BentleyBudgetBot
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes & Test**
   ```bash
   pytest tests/
   python test_api_connections.py
   ```

4. **Commit & Push**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**

### Code Style
- **Python:** PEP 8 (use `black` formatter)
- **JavaScript:** ESLint + Prettier
- **SQL:** Use proper indentation and comments
- **Commit Messages:** Follow [Conventional Commits](https://www.conventionalcommits.org/)

---

## 🐛 Troubleshooting

### Common Issues

#### MySQL Connection Errors
```bash
# Verify MySQL is running on Port 3307
python verify_mysql_status.py

# Test all database connections
python test_api_connections.py
```

#### Broker API Failures
```bash
# Test broker connections
python test_alpaca_connection.py

# Check API credentials in .env file
python check_env.py
```

#### Streamlit Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python version (requires 3.12+)
python --version
```

### Diagnostic Tools
- `diagnose_streamlit.py` - Streamlit environment diagnostics
- `diagnose_mysql_duplication.py` - MySQL database analysis
- `check_env.py` - Environment variable validation

---

## 📈 Roadmap

### Q1 2026
- [ ] Complete Charles Schwab integration
- [ ] Add TradeStation live trading
- [ ] Implement risk management module
- [ ] Deploy to production Railway environment

### Q2 2026
- [ ] Add options trading support
- [ ] Build mobile app (React Native)
- [ ] Integrate additional banks via Plaid
- [ ] Add advanced charting with TradingView

### Q3 2026
- [ ] Launch tZERO ATS integration
- [ ] Add fractional ownership tokenization
- [ ] Implement compliance KYC/AML flows
- [ ] Deploy TerraMar token SDK

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

## 👥 Team

**Bot Name and Description**  
Multi-asset investment management

**Moor Capital Trust**  
Trust account management

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/BentleyBudgetBot/issues)
- **Documentation:** [Project Wiki](https://github.com/yourusername/BentleyBudgetBot/wiki)
- **Email:** support@mansacapital.com

---

## 🙏 Acknowledgments

- **Streamlit** - Interactive web framework
- **Appwrite** - Backend-as-a-Service platform
- **Railway** - MySQL hosting
- **Vercel** - Frontend deployment
- **All API Providers** - Market data and broker integrations

---

## 📊 Process Flow

[Interactive Diagram](https://app.diagrams.net/#G1puqYkLeP-SrmQ8khMA-ualIAiFyEnBJj#%7B%22pageId%22%3A%22V-6in7jooW1nca1V13b-%22%7D)

![Process Flow Diagram](https://github.com/user-attachments/assets/433b4e08-945b-4ec0-b9f9-9a7b8085e602)

---

<div align="center">

**Built with ❤️ using Python, Streamlit, Docker, and Modern Cloud Infrastructure**

⭐ Star this repo if you find it helpful! ⭐

[Report Bug](https://github.com/yourusername/BentleyBudgetBot/issues) • [Request Feature](https://github.com/yourusername/BentleyBudgetBot/issues) • [Documentation](./PROJECT_STRUCTURE.md)

</div>
