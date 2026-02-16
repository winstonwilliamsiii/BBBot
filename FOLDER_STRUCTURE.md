# Bentley Bot Control Center - Folder Structure

## 📂 Organized Control Center Structure

This structure consolidates all control center code into a clean, modular organization under `/bentley-bot/`.

```
/bentley-bot/                          # Control Center Root Directory
├── bots/                              # Trading Bot Modules (13 bots)
│   ├── __init__.py
│   ├── bot1.py                        # Bot 1: GoldRSI Strategy
│   ├── bot2.py                        # Bot 2: USD/COP Short Strategy
│   ├── bot3.py                        # Bot 3: Portfolio Optimizer
│   ├── bot4.py                        # Bot 4: Sentiment Analyzer
│   ├── bot5.py                        # Bot 5: Technical Indicator Bot
│   ├── bot6.py                        # Bot 6: Multi-timeframe Strategy
│   ├── bot7.py                        # Bot 7: Crypto Arbitrage
│   ├── bot8.py                        # Bot 8: Mean Reversion
│   ├── bot9.py                        # Bot 9: Momentum Strategy
│   ├── bot10.py                       # Bot 10: Options Strategy
│   ├── bot11.py                       # Bot 11: Pairs Trading
│   ├── bot12.py                       # Bot 12: News Trading
│   └── bot13.py                       # Bot 13: ML Ensemble
│
├── brokers/                           # Broker API Clients
│   ├── __init__.py
│   ├── alpaca.py                      # Alpaca Markets API client
│   ├── schwab.py                      # Schwab/TD Ameritrade API client
│   ├── ibkr.py                        # Interactive Brokers TWS client
│   ├── binance.py                     # Binance crypto API client
│   └── coinbase.py                    # Coinbase Advanced Trade API client
│
├── prop_firms/                        # Prop Firm Execution Connectors
│   ├── __init__.py
│   ├── ftmo_mt5.py                    # FTMO challenge account via MT5
│   ├── axi_mt5.py                     # Axi Select via MT5
│   └── zenit_ninja.py                 # Zenit via NinjaTrader bridge
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
- Examples: GoldRSI (bot1), USD/COP Short (bot2), ML Ensemble (bot13)

### Broker Clients (`/brokers/`)
- Standardized interface for multi-broker execution
- Inherits from `BrokerClient` abstract base class in `frontend/utils/broker_interface.py`
- Handles authentication, order placement, position tracking
- Supports equities (Alpaca, Schwab, IBKR) and crypto (Binance, Coinbase)

### Prop Firm Connectors (`/prop_firms/`)
- Bridge to prop firm challenge accounts (no public APIs)
- FTMO & Axi: MT5 Python bridge (`MetaTrader5` package)
- Zenit: NinjaTrader C# automation or REST API
- Enforces prop firm rules (max drawdown, daily loss limits, forbidden instruments)

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
touch __init__.py bot{1..13}.py
cd ../..

# Create broker clients
mkdir -p bentley-bot/brokers
cd bentley-bot/brokers
touch __init__.py alpaca.py schwab.py ibkr.py binance.py coinbase.py
cd ../..

# Create prop firm connectors
mkdir -p bentley-bot/prop_firms
cd bentley-bot/prop_firms
touch __init__.py ftmo_mt5.py axi_mt5.py zenit_ninja.py
cd ../..

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
3. **Week 4-5**: Implement broker clients using patterns from `frontend/utils/broker_interface.py`
4. **Week 6-8**: Build prop firm connectors (MT5 bridge for FTMO/Axi)
5. **Week 9-12**: Create Streamlit admin UI and Flask API endpoints
6. **Week 13+**: MLflow integration, risk engine, VPS automation

## 📊 Success Metrics

- **Code Modularity**: Each bot/broker/prop firm is independently testable
- **Reusability**: Streamlit dashboard components shared across admin + investor UIs
- **Scalability**: Add new bots by creating `bot14.py` following existing pattern
- **Maintainability**: Clear separation of concerns (trading logic, execution, UI, risk)

## 🔗 Related Documentation

- [BENTLEY_BOT_CONTROL_CENTER_ARCHITECTURE.md](docs/BENTLEY_BOT_CONTROL_CENTER_ARCHITECTURE.md) - Full system design
- [CONTROL_CENTER_QUICK_START.md](docs/CONTROL_CENTER_QUICK_START.md) - Week-by-week implementation guide
- [CONTROL_CENTER_IMPLEMENTATION_CHECKLIST.md](docs/CONTROL_CENTER_IMPLEMENTATION_CHECKLIST.md) - 300+ task checklist
- [FLASK_STREAMLIT_UPDATE.md](docs/FLASK_STREAMLIT_UPDATE.md) - Tech stack migration guide
