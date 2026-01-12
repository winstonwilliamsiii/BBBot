-- ============================================================================
-- UNIFIED BROKER SCHEMA for Bentley Budget Bot
-- ============================================================================
-- Database: mansa_bot (MySQL Port 3307)
-- Railway Deployment: Synced via connection string from Railway MySQL
-- Appwrite Integration: Broker credentials stored in Appwrite Database
--                       (broker_api_credentials, broker_connections tables)
-- ============================================================================
-- Purpose: Orchestrate multi-broker trading activities across:
--          - Alpaca (Equities)
--          - IBKR (Interactive Brokers - Equities/Options)
--          - Charles Schwab (Equities)
--          - Binance (Crypto)
--          - TradeStation (Equities/Futures)
--          - MetaTrader 5 (Forex/Commodities)
-- ============================================================================
-- Key Features:
--   ✅ Normalization: Broker-specific API IDs (account_api_id, order_api_id)
--   ✅ Multi-tenant: Owner field tracks Mansa Capital, Moor Capital Trust, Personal
--   ✅ Auditability: created_at/updated_at timestamps for lifecycle tracking
--   ✅ Extensibility: Designed for future tables (transactions, logs, strategies)
-- ============================================================================

-- Drop existing tables if recreating (use with caution in production)
-- DROP TABLE IF EXISTS order_executions;
-- DROP TABLE IF EXISTS orders;
-- DROP TABLE IF EXISTS positions;
-- DROP TABLE IF EXISTS accounts;
-- DROP TABLE IF EXISTS brokers;

-- ============================================================================
-- TABLE: brokers
-- ============================================================================
-- Stores broker configurations and metadata
-- Links to: accounts, positions, orders
-- Appwrite Sync: broker_connections table mirrors this for API credentials
-- ============================================================================
CREATE TABLE IF NOT EXISTS brokers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,      -- 'alpaca', 'ibkr', 'mt5', 'binance', 'schwab', 'tradestation'
    display_name VARCHAR(100),             -- 'Interactive Brokers', 'Charles Schwab'
    type VARCHAR(50) NOT NULL,             -- 'equities', 'forex', 'crypto', 'futures', 'options'
    api_base_url VARCHAR(255),             -- e.g., 'https://paper-api.alpaca.markets'
    is_active BOOLEAN DEFAULT TRUE,        -- Enable/disable broker without deletion
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_name (name),
    INDEX idx_type (type),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Broker configurations - synced with Appwrite broker_connections';

-- ============================================================================
-- TABLE: accounts
-- ============================================================================
-- Stores broker account details with multi-tenant support
-- Links to: brokers (parent), positions, orders
-- Owner Field: Tracks entity ownership (Mansa Capital, Moor Capital, Personal)
-- ============================================================================
CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    broker_id INT NOT NULL,
    account_api_id VARCHAR(100) NOT NULL,  -- Broker-specific account ID (e.g., Alpaca account number)
    account_number VARCHAR(50),            -- Human-readable account number
    owner VARCHAR(100) NOT NULL,           -- 'Mansa Capital Partners', 'Moor Capital Trust', 'Personal'
    owner_type ENUM('corporate', 'trust', 'personal', 'joint') DEFAULT 'personal',
    account_type VARCHAR(50),              -- 'cash', 'margin', 'retirement', 'custodial'
    balance DECIMAL(18,2) DEFAULT 0.00,
    buying_power DECIMAL(18,2),            -- Available for trading
    cash DECIMAL(18,2),                    -- Cash balance
    portfolio_value DECIMAL(18,2),         -- Total account value
    currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(50) DEFAULT 'active',   -- 'active', 'inactive', 'restricted', 'closed'
    is_pattern_day_trader BOOLEAN DEFAULT FALSE, -- PDT flag for equity accounts
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (broker_id) REFERENCES brokers(id) ON DELETE CASCADE,
    UNIQUE KEY unique_broker_account (broker_id, account_api_id),
    INDEX idx_owner (owner),
    INDEX idx_owner_type (owner_type),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Multi-tenant broker accounts - tracks Mansa Capital, Moor Trust, Personal accounts';

-- ============================================================================
-- TABLE: positions
-- ============================================================================
-- Stores current positions across all brokers and accounts
-- Links to: brokers, accounts
-- Updated frequently via broker API sync jobs
-- ============================================================================
CREATE TABLE IF NOT EXISTS positions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    broker_id INT NOT NULL,
    account_id INT NOT NULL,
    symbol VARCHAR(20) NOT NULL,           -- Ticker symbol (e.g., 'AAPL', 'BTC/USD', 'EURUSD')
    asset_type VARCHAR(20),                -- 'stock', 'crypto', 'forex', 'option', 'future'
    qty DECIMAL(18,6) NOT NULL,            -- Position size (use 6 decimals for crypto)
    avg_entry_price DECIMAL(18,6),         -- Average entry price
    current_price DECIMAL(18,6),           -- Current market price
    market_value DECIMAL(18,2),            -- Current position value
    cost_basis DECIMAL(18,2),              -- Total cost basis
    unrealized_pnl DECIMAL(18,2),          -- Unrealized profit/loss
    unrealized_pnl_pct DECIMAL(8,4),       -- Unrealized P&L percentage
    realized_pnl DECIMAL(18,2),            -- Realized profit/loss (closed portions)
    side ENUM('long', 'short') DEFAULT 'long',
    position_api_id VARCHAR(100),          -- Broker-specific position ID
    last_synced_at TIMESTAMP,              -- Last time synced from broker API
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (broker_id) REFERENCES brokers(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    UNIQUE KEY unique_position (broker_id, account_id, symbol, side),
    INDEX idx_symbol (symbol),
    INDEX idx_account (account_id),
    INDEX idx_pnl (unrealized_pnl),
    INDEX idx_last_synced (last_synced_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Current positions across all brokers - synced via API jobs';

-- ============================================================================
-- TABLE: orders
-- ============================================================================
-- Stores order history and status across all brokers
-- Links to: brokers, accounts
-- Tracks full order lifecycle from submission to completion/cancellation
-- ============================================================================
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    broker_id INT NOT NULL,
    account_id INT NOT NULL,
    order_api_id VARCHAR(100) NOT NULL,    -- Broker-specific order ID (e.g., Alpaca order ID)
    client_order_id VARCHAR(100),          -- Client-assigned order ID for tracking
    symbol VARCHAR(20) NOT NULL,
    asset_type VARCHAR(20),                -- 'stock', 'crypto', 'forex', 'option'
    qty DECIMAL(18,6) NOT NULL,
    filled_qty DECIMAL(18,6) DEFAULT 0,    -- Quantity filled so far
    side ENUM('buy', 'sell') NOT NULL,
    order_type VARCHAR(50),                -- 'market', 'limit', 'stop', 'stop_limit', 'trailing_stop'
    time_in_force VARCHAR(50),             -- 'day', 'gtc', 'ioc', 'fok'
    limit_price DECIMAL(18,6),             -- For limit orders
    stop_price DECIMAL(18,6),              -- For stop orders
    avg_fill_price DECIMAL(18,6),          -- Average execution price
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'new', 'partially_filled', 'filled', 'cancelled', 'rejected', 'expired'
    status_message TEXT,                   -- Additional status details
    submitted_at TIMESTAMP,                -- When order was submitted to broker
    filled_at TIMESTAMP,                   -- When order was fully filled
    cancelled_at TIMESTAMP,                -- When order was cancelled
    expired_at TIMESTAMP,                  -- When order expired
    strategy_id INT,                       -- Link to trading strategy (future extensibility)
    notes TEXT,                            -- Trading notes or rationale
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (broker_id) REFERENCES brokers(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    UNIQUE KEY unique_order (broker_id, order_api_id),
    INDEX idx_account_orders (account_id, created_at),
    INDEX idx_symbol_orders (symbol, created_at),
    INDEX idx_status (status),
    INDEX idx_client_order (client_order_id),
    INDEX idx_submitted (submitted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Order history across all brokers - tracks full order lifecycle';

-- ============================================================================
-- TABLE: order_executions
-- ============================================================================
-- Stores individual order execution details (fills)
-- Links to: orders
-- One order can have multiple executions (partial fills)
-- ============================================================================
CREATE TABLE IF NOT EXISTS order_executions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    execution_api_id VARCHAR(100),         -- Broker-specific execution/trade ID
    qty DECIMAL(18,6) NOT NULL,            -- Quantity executed in this fill
    price DECIMAL(18,6) NOT NULL,          -- Execution price
    commission DECIMAL(10,4) DEFAULT 0,    -- Commission charged
    fees DECIMAL(10,4) DEFAULT 0,          -- Other fees
    liquidity_flag VARCHAR(20),            -- 'maker', 'taker', 'unknown'
    executed_at TIMESTAMP NOT NULL,        -- Execution timestamp from broker
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_order_execs (order_id, executed_at),
    INDEX idx_execution_time (executed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Individual order executions - tracks partial fills and trade details';

-- ============================================================================
-- EXTENSIBILITY PLACEHOLDERS
-- ============================================================================
-- Future tables to add:
--   - transactions: General ledger of all account transactions
--   - trading_strategies: Strategy definitions and parameters
--   - strategy_signals: Trading signals generated by strategies
--   - risk_limits: Risk management rules per account/strategy
--   - performance_metrics: Daily/monthly performance tracking
--   - audit_log: User action audit trail
--   - market_data_cache: Cached market data for backtesting
-- ============================================================================

-- ============================================================================
-- RAILWAY DEPLOYMENT NOTES
-- ============================================================================
-- This schema runs on Railway MySQL (Port 54537) in production
-- Connection: RAILWAY_MYSQL_HOST=nozomi.proxy.rlwy.net
-- Local Development: Port 3307 (mansa_bot database)
-- To deploy to Railway:
--   1. Update railway service with this schema
--   2. Run migrations via Railway CLI or MySQL Workbench
--   3. Verify connection in .env: RAILWAY_MYSQL_* variables
-- ============================================================================

-- ============================================================================
-- APPWRITE INTEGRATION NOTES
-- ============================================================================
-- Appwrite Database (694481eb003c0a14151d - Bentley_Mansa) contains:
--   - broker_api_credentials: Encrypted API keys/secrets
--   - broker_connections: Active broker connection status
-- These tables work in tandem with this MySQL schema:
--   - MySQL: Stores transactional/operational data (orders, positions, accounts)
--   - Appwrite: Stores configuration/credentials (API keys, connection settings)
-- Sync Pattern:
--   1. Appwrite stores broker.name → API credentials
--   2. MySQL brokers table references same broker.name
--   3. API services read credentials from Appwrite, write data to MySQL
-- ============================================================================

-- ============================================================================
-- SEED DATA (Optional - for initial setup)
-- ============================================================================
-- Uncomment to insert initial broker configurations

/*
INSERT INTO brokers (name, display_name, type, api_base_url) VALUES
    ('alpaca', 'Alpaca Markets', 'equities', 'https://paper-api.alpaca.markets'),
    ('ibkr', 'Interactive Brokers', 'equities', 'https://api.ibkr.com'),
    ('schwab', 'Charles Schwab', 'equities', 'https://api.schwab.com'),
    ('binance', 'Binance', 'crypto', 'https://api.binance.com'),
    ('tradestation', 'TradeStation', 'equities', 'https://api.tradestation.com'),
    ('mt5', 'MetaTrader 5', 'forex', 'http://localhost:8000')
ON DUPLICATE KEY UPDATE
    display_name = VALUES(display_name),
    api_base_url = VALUES(api_base_url),
    updated_at = CURRENT_TIMESTAMP;
*/

-- ============================================================================
-- MAINTENANCE QUERIES
-- ============================================================================
-- View all accounts with their brokers and owners:
--   SELECT a.id, b.name AS broker, a.account_number, a.owner, a.balance 
--   FROM accounts a JOIN brokers b ON a.broker_id = b.id;
--
-- View open positions with P&L:
--   SELECT p.symbol, b.name AS broker, p.qty, p.unrealized_pnl 
--   FROM positions p JOIN brokers b ON p.broker_id = b.id
--   WHERE p.qty != 0;
--
-- View recent orders by status:
--   SELECT o.symbol, b.name AS broker, o.side, o.qty, o.status, o.created_at
--   FROM orders o JOIN brokers b ON o.broker_id = b.id
--   ORDER BY o.created_at DESC LIMIT 50;
-- ============================================================================