# 🏛️ Bentley Budget Bot - Financial Portfolio & Trading Platform

<div align="center">

![Process Flow](https://github.com/user-attachments/assets/433b4e08-945b-4ec0-b9f9-9a7b8085e602)

**Multi-Platform Financial Dashboard with Unified Broker Integration**

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://bbbot305.streamlit.app)
[![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![Railway](https://img.shields.io/badge/Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)](https://railway.app)
[![Appwrite](https://img.shields.io/badge/Appwrite-F02E65?style=for-the-badge&logo=appwrite&logoColor=white)](https://appwrite.io)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

[Live Demo](https://bbbot305.streamlit.app/) • [Documentation](#-documentation) • [API Reference](#-api-integrations) • [Setup Guide](#-quick-start)

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
- **FastAPI/Vercel Functions** - Serverless API endpoints
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
- src/                → Core trading logic
- config/dev/         → Localhost configs (.env.dev, settings.json)
- config/prod/        → Production configs (.env.prod, settings.json)
- tests/              → Unit + integration tests
- .github/workflows/  → CI/CD pipeline

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

#### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

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

### Docker Setup (Optional)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
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
│   └── appwrite-functions/       # 11 deployed cloud functions
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
│   ├── webull-sdk/               # Webull integration
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
# Test individual broker connections
python test_alpaca_connection.py
python test_webull_connection.py

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
