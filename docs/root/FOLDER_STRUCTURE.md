# Bentley Bot Control Center - Folder Structure

## 📂 Organized Control Center Structure

This structure consolidates all control center code into a clean, modular organization under `/bentley-bot/`.

```
/bentley-bot/                          # Control Center Root Directory
├── bots/                              # Trading Bot Modules (13 bots)
│   ├── __init__.py
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
├── brokers/                           # Brokerage & Execution Clients
│   ├── __init__.py
│   ├── alpaca_client.py               # Alpaca markets brokerage client
│   ├── ibkr_client.py                 # Interactive Brokers TWS client
│   ├── mt5_client.py                  # MetaTrader 5 execution client
│   ├── prop_firm_ftmo.py              # FTMO execution adapter
│   ├── prop_firm_axi.py               # Axi Select execution adapter
│   └── prop_firm_zenit.py             # Zenit execution adapter
│
├── config/                            # Bot strategy and execution profiles
│   └── bots/
│       ├── titan.yml                  # Titan runtime profile
│       ├── vega.yml                   # Vega runtime profile
│       ├── draco.yml                  # Draco runtime profile
│       ├── altair.yml                 # Altair runtime profile
│       ├── procryon.yml               # Procryon runtime profile
│       ├── hydra.yml                  # Hydra runtime profile
│       ├── triton.yml                 # Triton runtime profile
│       ├── dione.yml                  # Dione runtime profile
│       ├── dogon.yml                  # Dogon runtime profile
│       ├── rigel.yml                  # Rigel runtime profile
│       ├── orion.yml                  # Orion runtime profile
│       ├── rhea.yml                   # Rhea runtime profile
│       └── jupicita.yml               # Jupicita runtime profile
│
├── mlflow/                            # ML Experiment Tracking & Training
│   ├── __init__.py
│   ├── train.py                       # Bot training pipeline
│   ├── backtest.py                    # Backtesting engine
│   └── register.py                    # Model registry operations
│
├── streamlit_app/                     # Streamlit UI Modules
│   ├── __init__.py
│   ├── admin.py                       # Admin control center page
│   ├── investor.py                    # Investor-facing pages
│   └── dashboards.py                  # Reusable dashboard components
│
└── utils/                             # Shared Utilities
    ├── __init__.py
    ├── risk.py                        # Risk engine functions
    ├── config.py                      # Configuration management
    └── secrets.py                     # Secrets/credentials manager
```

## 🎯 Purpose & Design Rationale

### Bot Modules (`/bots/`)
- Each bot is a standalone module implementing specific trading strategies
- Common interface: `start()`, `stop()`, `get_status()`, `configure()`
- Can be deployed independently or as ensembles
- Modules are organized by bot name, with the fund name and strategy documented alongside each file
- Examples: Titan (Mansa Tech, CNN with Deep Learning), Orion (Mansa Minerals, GoldRSI Strategy), Jupicita (Mansa_Smalls, Pairs Trading)

### Brokerage Clients (`/brokers/`)
- Unified execution layer for broker and prop-firm connectivity
- Inherits from `BrokerClient` abstract base class in `frontend/utils/broker_interface.py` where practical
- Handles authentication, order placement, position tracking, and venue-specific execution rules
- Current supported adapters: Alpaca, IBKR, MT5, FTMO, Axi Select, and Zenit

### Bot Config YAML (`/config/bots/`)
- One YAML profile per bot for strategy metadata, broker routing, and runtime defaults
- Keeps strategy configuration separate from secrets and infrastructure credentials
- Mirrors the existing repo pattern where bot profiles live in YAML and credentials remain in environment variables

### MLflow Integration (`/mlflow/`)
- Training pipeline: Feature engineering → model training → hyperparameter tuning
- Backtesting: Historical validation with Sharpe ratio, max drawdown, win rate
- Registry: Model versioning, staging, production promotion

### Streamlit UI (`/streamlit_app/`)
- **admin.py**: Internal control center (bot deployment, broker health, risk controls)
- **investor.py**: Client-facing analytics (portfolio performance, P&L breakdown)
- **dashboards.py**: Reusable components (metric cards, charts, tables)

### Utilities (`/utils/`)
- **risk.py**: Pre-trade checks, exposure limits, circuit breakers
- **config.py**: Environment-specific settings (dev/staging/prod)
- **secrets.py**: Credential management (Railway MySQL, Appwrite, broker API keys)

## 🚀 Integration with Existing Structure

This `/bentley-bot/` folder complements the existing project structure:

```
BentleyBudgetBot/
├── bentley-bot/           # 🆕 Organized control center code
├── frontend/              # Existing Streamlit client UI
├── backend/               # Flask API (admin endpoints)
├── docker/                # Airflow, MLflow, Airbyte containers
├── trading/               # Legacy trading scripts
├── mt5/                   # MT5 Expert Advisors (.ex5 compiled)
├── appwrite-functions/    # Appwrite cloud functions
└── docs/                  # Architecture documentation
```

## 📋 Setup Instructions

### Automated Setup (Recommended)
```bash
# Run the setup script
.\setup_bentley_bot_structure.ps1
```

### Manual Setup
```bash
# Create main directory
mkdir -p bentley-bot

# Create bot modules
mkdir -p bentley-bot/bots
cd bentley-bot/bots
touch __init__.py titan.py vega.py draco.py altair.py procryon.py hydra.py triton.py dione.py dogon.py rigel.py orion.py rhea.py jupicita.py
cd ../..

# Create brokerage clients
mkdir -p bentley-bot/brokers
cd bentley-bot/brokers
touch __init__.py alpaca_client.py ibkr_client.py mt5_client.py prop_firm_ftmo.py prop_firm_axi.py prop_firm_zenit.py
cd ../..

# Create bot config YAML files
mkdir -p bentley-bot/config/bots
cd bentley-bot/config/bots
touch titan.yml vega.yml draco.yml altair.yml procryon.yml hydra.yml triton.yml dione.yml dogon.yml rigel.yml orion.yml rhea.yml jupicita.yml
cd ../../..

# Create MLflow pipelines
mkdir -p bentley-bot/mlflow
cd bentley-bot/mlflow
touch __init__.py train.py backtest.py register.py
cd ../..

# Create Streamlit modules
mkdir -p bentley-bot/streamlit_app
cd bentley-bot/streamlit_app
touch __init__.py admin.py investor.py dashboards.py
cd ../..

# Create utilities
mkdir -p bentley-bot/utils
cd bentley-bot/utils
touch __init__.py risk.py config.py secrets.py
cd ../..
```

## 🔄 Migration Strategy

1. **Week 1**: Create folder structure, stub out modules
2. **Week 2-3**: Migrate existing bot code from `/trading/` to `/bentley-bot/bots/`
3. **Week 4-5**: Implement brokerage clients using patterns from `frontend/utils/broker_interface.py`
4. **Week 6-8**: Extend brokerage adapters for MT5 and prop firm execution rules
5. **Week 9-12**: Create Streamlit admin UI and Flask API endpoints
6. **Week 13+**: MLflow integration, risk engine, VPS automation

## 📊 Success Metrics

- **Code Modularity**: Each bot and brokerage adapter is independently testable
- **Reusability**: Streamlit dashboard components shared across admin + investor UIs
- **Scalability**: Add new bots by creating a new named module that follows the same bot-name, fund-name, strategy convention
- **Maintainability**: Clear separation of concerns (trading logic, execution, UI, risk)

## 🔗 Related Documentation

- [BENTLEY_BOT_CONTROL_CENTER_ARCHITECTURE.md](docs/BENTLEY_BOT_CONTROL_CENTER_ARCHITECTURE.md) - Full system design
- [CONTROL_CENTER_QUICK_START.md](docs/CONTROL_CENTER_QUICK_START.md) - Week-by-week implementation guide
- [CONTROL_CENTER_IMPLEMENTATION_CHECKLIST.md](docs/CONTROL_CENTER_IMPLEMENTATION_CHECKLIST.md) - 300+ task checklist
- [FLASK_STREAMLIT_UPDATE.md](docs/FLASK_STREAMLIT_UPDATE.md) - Tech stack migration guide
