# BentleyBudgetBot - MySQL Database Architecture
**Date:** December 14, 2025  
**Version:** 2.0 (Post-bbbot1 Migration)

---

## 🏗️ Database Schema Layout

### Connection Details
- **Host:** 127.0.0.1 (localhost)
- **Port:** 3306
- **Root User:** root
- **Character Set:** utf8mb4
- **Collation:** utf8mb4_unicode_ci

---

## 📊 Database Breakdown

### 1. **mydb** - Personal Budget & Plaid Integration
**Purpose:** User budget tracking, Plaid transactions, personal finance management

**Environment Variables:**
```bash
BUDGET_MYSQL_HOST=127.0.0.1
BUDGET_MYSQL_PORT=3306
BUDGET_MYSQL_USER=root
BUDGET_MYSQL_PASSWORD=root
BUDGET_MYSQL_DATABASE=mydb
```

**Tables:**
- `budget_categories` - Budget category definitions
- `budget_tracking` - Monthly budget allocations
- `cash_flow_summary` - Aggregated income/expense summaries
- `user_plaid_tokens` - Plaid access tokens and item IDs
- `transaction_notes` - User annotations on transactions
- `plaid_transactions` - Raw transaction data from Plaid
- `plaid_accounts` - Bank account information
- `users` - User authentication (RBAC)
- `user_permissions` - Role-based permissions

**Primary Features:**
- Personal Budget page (pages/01_💰_Personal_Budget.py)
- Plaid Link integration
- Cash flow analysis
- Transaction categorization

**Schema Location:** `scripts/setup/budget_schema.sql`

---

### 2. **mansa_bot** - Metrics, Models & dbt Staging
**Purpose:** Application metrics, ML model metadata, dbt pipeline staging tables

**Environment Variables:**
```bash
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=mansa_bot
```

**Tables:**

#### System Metrics
- `api_metrics` - Request/latency/error tracking
- `system_health` - CPU, memory, disk usage logs
- `data_freshness` - Last update timestamps for data sources

#### Trading & P&L
- `trades` - Trading bot transaction history
- `portfolio_positions` - Current holdings
- `portfolio_performance` - Historical P&L snapshots

#### dbt Staging
- `stg_fundamentals` - Staged fundamental data
- `stg_prices` - Staged price data
- `stg_sentiment` - Staged sentiment data

**Primary Features:**
- System Metrics dashboard (pages/06_📊_System_Metrics.py)
- Trading P&L dashboard (pages/07_💰_Trading_PnL.py)
- Bot Health monitoring (pages/08_🏥_Bot_Health.py)
- dbt data transformations

**Schema Location:** `scripts/setup/mansa_bot_schema.sql` (to be created)

---

### 3. **mansa_quant** - Quantitative Analysis Datasets
**Purpose:** Fundamentals, sentiment analysis, technical indicators

**Environment Variables:**
```bash
QUANT_MYSQL_DATABASE=mansa_quant
```

**Tables:**

#### Fundamental Data
- `stock_fundamentals` - Balance sheet, income statement, ratios
- `earnings_reports` - Quarterly earnings data
- `company_info` - Company metadata (sector, industry, description)

#### Sentiment Analysis
- `stocktwits_sentiment` - Social sentiment from StockTwits
- `news_sentiment` - News article sentiment scores
- `reddit_sentiment` - Reddit mentions and sentiment

#### Technical Analysis
- `technical_indicators` - RSI, MACD, moving averages
- `price_patterns` - Chart patterns detection
- `volume_analysis` - Volume-based indicators

**Primary Features:**
- Investment Analysis page (pages/02_📈_Investment_Analysis.py)
- Quantitative screening
- Sentiment dashboards

**Schema Location:** `scripts/setup/mansa_quant_schema.sql` (to be created)

---

### 4. **mlflow_db** - MLFlow & Airflow Metadata
**Purpose:** Machine learning experiment tracking, Airflow DAG metadata

**Environment Variables:**
```bash
MLFLOW_MYSQL_DATABASE=mlflow_db
MLFLOW_TRACKING_URI=mysql+pymysql://root:root@127.0.0.1:3306/mlflow_db
```

**Tables (MLFlow Native):**
- `experiments` - ML experiment definitions
- `runs` - Individual experiment runs
- `metrics` - Run metrics (accuracy, loss, etc.)
- `params` - Hyperparameters
- `tags` - Run metadata tags
- `model_versions` - Model registry versions

**Tables (Airflow Metadata):**
- `dag_runs` - DAG execution history
- `task_instances` - Individual task executions
- `task_logs` - Task execution logs

**Primary Features:**
- MLFlow experiment tracking
- Airflow pipeline orchestration
- Model versioning and registry

**Schema Location:** MLFlow auto-creates tables on first run

---

### 5. **mrgp_schema** - Bulk Equities & Crypto Datasets
**Purpose:** High-volume market data storage (prices, volume, orderbook)

**Environment Variables:**
```bash
BULK_MYSQL_DATABASE=mrgp_schema
```

**Tables:**

#### Equities
- `stock_prices_bulk` - Historical OHLCV data (years of data)
- `intraday_prices` - Minute/5-minute bars
- `stock_splits` - Stock split events
- `dividends` - Dividend payment history

#### Crypto
- `crypto_prices` - Cryptocurrency OHLCV data
- `crypto_orderbook` - Orderbook snapshots
- `crypto_trades` - Real-time trade data from WebSocket
- `exchange_info` - Exchange metadata

#### Reference Data
- `ticker_master` - Master list of all tickers
- `exchange_holidays` - Market holiday calendar

**Primary Features:**
- Historical backtesting
- Data pipelines (Airbyte ingestion)
- Bulk data exports for analysis

**Schema Location:** `scripts/setup/mrgp_schema.sql` (to be created)

---

## 🔄 Migration from bbbot1

### Old Architecture (DEPRECATED)
```
bbbot1 → Everything in one database ❌
├─ Fundamentals
├─ Prices
├─ Sentiment
├─ Budget data
└─ Metrics
```

**Problems:**
- ❌ No separation of concerns
- ❌ Difficult to backup selectively
- ❌ Performance issues with large tables
- ❌ Hard to scale individual components

### New Architecture (CURRENT)
```
mydb          → Budget & personal finance
mansa_bot     → App metrics & dbt staging
mansa_quant   → Quantitative analysis datasets
mlflow_db     → ML experiments & Airflow
mrgp_schema   → Bulk historical data
```

**Benefits:**
- ✅ Logical separation of data domains
- ✅ Independent backup/restore
- ✅ Easier to scale (e.g., move mrgp_schema to separate server)
- ✅ Clear ownership and access control
- ✅ Better performance (smaller databases)

---

## 🔧 Code Migration Required

### Files Referencing bbbot1 (Need Updates)

#### 1. Airflow DAGs
- `airflow/dags/bbbot1_master_pipeline.py` → Rename to `mansa_master_pipeline.py`
- Update all `from bbbot1_pipeline` imports

#### 2. Pipeline Code
- `bbbot1_pipeline/` directory → Rename to `mansa_pipeline/`
- Update package name throughout codebase

#### 3. Legacy Scripts
- `#alphavantage_fundamentals.py` - Update connection string
- `#yfinance_fundamentals.py` - Update imports
- `#stock_pipeline_DAG.py` - Update database references

#### 4. SQL Scripts
- `bbbot1_pipeline/sql/create_indexes.sql` → Update to reference correct databases

---

## 📝 Environment Variable Mapping

### Complete .env Configuration

```bash
# ============================================================================
# MySQL Database Configuration
# ============================================================================

# Main Application Database (metrics, models, staging)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=mansa_bot

# Personal Budget Database (Plaid integration)
BUDGET_MYSQL_HOST=127.0.0.1
BUDGET_MYSQL_PORT=3306
BUDGET_MYSQL_USER=root
BUDGET_MYSQL_PASSWORD=root
BUDGET_MYSQL_DATABASE=mydb

# Quantitative Analysis Database
QUANT_MYSQL_DATABASE=mansa_quant

# MLFlow & Airflow Database
MLFLOW_MYSQL_DATABASE=mlflow_db
MLFLOW_TRACKING_URI=mysql+pymysql://root:root@127.0.0.1:3306/mlflow_db

# Bulk Data Storage
BULK_MYSQL_DATABASE=mrgp_schema

# ============================================================================
# Airbyte Configuration (for data ingestion)
# ============================================================================
AIRBYTE_MYSQL_USER=airbyte
AIRBYTE_MYSQL_PASSWORD=airbyte_secure_password_2025
```

---

## 🔐 User Access Control

### Recommended User Setup

```sql
-- Application user (read/write)
CREATE USER 'mansa_app'@'localhost' IDENTIFIED BY 'secure_app_password';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'mansa_app'@'localhost';
GRANT ALL PRIVILEGES ON mydb.* TO 'mansa_app'@'localhost';
GRANT ALL PRIVILEGES ON mansa_quant.* TO 'mansa_app'@'localhost';

-- Read-only analytics user
CREATE USER 'mansa_analytics'@'localhost' IDENTIFIED BY 'analytics_password';
GRANT SELECT ON mansa_bot.* TO 'mansa_analytics'@'localhost';
GRANT SELECT ON mansa_quant.* TO 'mansa_analytics'@'localhost';
GRANT SELECT ON mrgp_schema.* TO 'mansa_analytics'@'localhost';

-- Airbyte ingestion user
CREATE USER 'airbyte'@'%' IDENTIFIED BY 'airbyte_secure_password_2025';
GRANT SELECT, INSERT, UPDATE ON mansa_quant.* TO 'airbyte'@'%';
GRANT SELECT, INSERT, UPDATE ON mrgp_schema.* TO 'airbyte'@'%';

FLUSH PRIVILEGES;
```

---

## 📦 Backup Strategy

### Individual Database Backups

```bash
# Budget data (most critical for users)
mysqldump -u root -p mydb > backups/mydb_$(date +%Y%m%d).sql

# Application data (metrics, models)
mysqldump -u root -p mansa_bot > backups/mansa_bot_$(date +%Y%m%d).sql

# Quantitative data (can be re-fetched from APIs)
mysqldump -u root -p mansa_quant > backups/mansa_quant_$(date +%Y%m%d).sql

# MLFlow experiments
mysqldump -u root -p mlflow_db > backups/mlflow_db_$(date +%Y%m%d).sql

# Bulk data (optional, very large)
# mysqldump -u root -p mrgp_schema > backups/mrgp_schema_$(date +%Y%m%d).sql
```

### Restore Priority
1. **mydb** (Critical) - User budget data
2. **mansa_bot** (High) - Application metrics
3. **mlflow_db** (Medium) - ML experiments
4. **mansa_quant** (Low) - Can re-fetch from APIs
5. **mrgp_schema** (Low) - Bulk historical data

---

## 🚀 Database Initialization Checklist

### 1. Create Databases
```sql
CREATE DATABASE IF NOT EXISTS mydb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS mansa_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS mansa_quant CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS mlflow_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS mrgp_schema CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Run Schema Scripts
```bash
# Budget tables
mysql -u root -p mydb < scripts/setup/budget_schema.sql

# Application tables
mysql -u root -p mansa_bot < scripts/setup/mansa_bot_schema.sql

# Quantitative tables
mysql -u root -p mansa_quant < scripts/setup/mansa_quant_schema.sql

# MLFlow (auto-creates on first run)
# Just ensure MLFLOW_TRACKING_URI is set correctly

# Bulk data tables
mysql -u root -p mrgp_schema < scripts/setup/mrgp_schema.sql
```

### 3. Verify Schema
```bash
# Check table counts
mysql -u root -p -e "SELECT table_schema, COUNT(*) as table_count FROM information_schema.tables WHERE table_schema IN ('mydb', 'mansa_bot', 'mansa_quant', 'mlflow_db', 'mrgp_schema') GROUP BY table_schema;"
```

### 4. Test Connections
```bash
python test_database_connections.py
```

---

## 🔗 Appwrite Integration Plan

**Your Future State:**
```
Appwrite Cloud
├─ User authentication
├─ API gateway
├─ Real-time subscriptions
└─ File storage

MySQL (Local/AWS RDS)
├─ mydb (budget transactions)
├─ mansa_bot (metrics)
├─ mansa_quant (market data)
├─ mlflow_db (ML experiments)
└─ mrgp_schema (bulk data)
```

**Migration Path:**
1. **Phase 1:** Keep MySQL for data storage, use Appwrite for auth
2. **Phase 2:** Move user tables to Appwrite Database
3. **Phase 3:** Use Appwrite Functions for API endpoints
4. **Phase 4:** MySQL becomes pure data warehouse

---

## 📊 Database Size Estimates

| Database | Expected Size | Growth Rate |
|----------|---------------|-------------|
| mydb | 10-50 MB | Low (user transactions) |
| mansa_bot | 100-500 MB | Medium (metrics logs) |
| mansa_quant | 1-5 GB | Medium (fundamentals/sentiment) |
| mlflow_db | 500 MB - 2 GB | Low (experiment metadata) |
| mrgp_schema | 10-100 GB | High (historical OHLCV) |

**Total:** ~12-108 GB (depends on historical data retention)

---

## ✅ Next Steps

1. ✅ Create missing schema files (`mansa_bot_schema.sql`, `mansa_quant_schema.sql`, `mrgp_schema.sql`)
2. ✅ Run migration script to create all databases
3. ✅ Update all `bbbot1` references to use new database names
4. ✅ Test each application feature with new schema
5. ✅ Document connection patterns for each database
6. ✅ Set up automated backups
7. ✅ Create database monitoring dashboard

---

**Last Updated:** December 14, 2025  
**Schema Version:** 2.0  
**Migration Status:** In Progress
