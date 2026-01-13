-- Active: 1763499046791@@127.0.0.1@3306@mansa_bot
-- ============================================================
-- Multi-Broker Trading Orchestration Database Schema
-- Database: mansa_bot
-- Created: January 11, 2026
-- Purpose: Unified tracking for MT5, Alpaca, IBKR, Webull
-- ============================================================

USE mansa_bot;

-- ============================================================
-- 1. BROKERS - Master broker configuration
-- ============================================================
CREATE TABLE IF NOT EXISTS brokers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,  -- 'alpaca', 'ibkr', 'mt5', 'webull'
    display_name VARCHAR(100),          -- 'MetaTrader 5', 'Interactive Brokers'
    type VARCHAR(50) NOT NULL,          -- 'equities', 'forex', 'crypto', 'futures', 'options'
    region VARCHAR(10) DEFAULT 'US',    -- 'US', 'EU', 'GLOBAL'
    api_endpoint VARCHAR(255),          -- API base URL
    is_active BOOLEAN DEFAULT TRUE,
    supports_paper_trading BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_type (type),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Broker configuration and metadata';

-- ============================================================
-- 2. ACCOUNTS - Broker-specific trading accounts
-- ============================================================
CREATE TABLE IF NOT EXISTS accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    broker_id INT NOT NULL,
    account_api_id VARCHAR(100) NOT NULL,  -- Broker-specific account ID
    account_number VARCHAR(100),            -- Display account number
    owner VARCHAR(100) NOT NULL DEFAULT 'Mansa Capital Partners',
    account_type ENUM('live', 'paper', 'demo') DEFAULT 'paper',
    balance DECIMAL(18,2) DEFAULT 0.00,
    equity DECIMAL(18,2) DEFAULT 0.00,
    buying_power DECIMAL(18,2) DEFAULT 0.00,
    margin_used DECIMAL(18,2) DEFAULT 0.00,
    currency VARCHAR(10) DEFAULT 'USD',
    is_active BOOLEAN DEFAULT TRUE,
    last_sync_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (broker_id) REFERENCES brokers(id) ON DELETE CASCADE,
    UNIQUE KEY unique_broker_account (broker_id, account_api_id),
    INDEX idx_broker (broker_id),
    INDEX idx_owner (owner),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Trading accounts across all brokers';

-- ============================================================
-- 3. ORDERS - All order requests (filled and unfilled)
-- ============================================================
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    broker_id INT NOT NULL,
    account_id INT NOT NULL,
    order_api_id VARCHAR(100) NOT NULL,     -- Broker's order ID
    client_order_id VARCHAR(100),           -- Our internal order ID
    symbol VARCHAR(20) NOT NULL,
    asset_type ENUM('stock', 'option', 'future', 'forex', 'crypto') DEFAULT 'stock',
    qty DECIMAL(18,4) NOT NULL,
    filled_qty DECIMAL(18,4) DEFAULT 0.0000,
    side ENUM('buy', 'sell') NOT NULL,
    order_type ENUM('market', 'limit', 'stop', 'stop_limit') DEFAULT 'market',
    limit_price DECIMAL(18,4) NULL,
    stop_price DECIMAL(18,4) NULL,
    time_in_force ENUM('day', 'gtc', 'ioc', 'fok') DEFAULT 'day',
    status VARCHAR(50) NOT NULL,            -- pending, filled, partially_filled, canceled, rejected
    avg_fill_price DECIMAL(18,4) NULL,
    commission DECIMAL(18,4) DEFAULT 0.0000,
    notes TEXT,
    placed_at TIMESTAMP NULL,
    filled_at TIMESTAMP NULL,
    canceled_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (broker_id) REFERENCES brokers(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    UNIQUE KEY unique_broker_order (broker_id, order_api_id),
    INDEX idx_client_order (client_order_id),
    INDEX idx_symbol (symbol),
    INDEX idx_status (status),
    INDEX idx_placed_at (placed_at),
    INDEX idx_broker_account (broker_id, account_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='All order requests across brokers';

-- ============================================================
-- 4. POSITIONS - Current open positions
-- ============================================================
CREATE TABLE IF NOT EXISTS positions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    broker_id INT NOT NULL,
    account_id INT NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    asset_type ENUM('stock', 'option', 'future', 'forex', 'crypto') DEFAULT 'stock',
    qty DECIMAL(18,4) NOT NULL,
    avg_entry_price DECIMAL(18,4) NOT NULL,
    current_price DECIMAL(18,4) NULL,
    market_value DECIMAL(18,4) NULL,
    cost_basis DECIMAL(18,4) NULL,
    unrealized_pnl DECIMAL(18,4) DEFAULT 0.0000,
    realized_pnl DECIMAL(18,4) DEFAULT 0.0000,
    side ENUM('long', 'short') DEFAULT 'long',
    opened_at TIMESTAMP NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (broker_id) REFERENCES brokers(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    UNIQUE KEY unique_position (broker_id, account_id, symbol),
    INDEX idx_broker_account (broker_id, account_id),
    INDEX idx_symbol (symbol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Current open positions across all brokers';

-- ============================================================
-- 5. TRADES - Executed trade history (filled orders)
-- ============================================================
CREATE TABLE IF NOT EXISTS trades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    broker_id INT NOT NULL,
    account_id INT NOT NULL,
    trade_api_id VARCHAR(100),              -- Broker's execution ID
    symbol VARCHAR(20) NOT NULL,
    asset_type ENUM('stock', 'option', 'future', 'forex', 'crypto') DEFAULT 'stock',
    qty DECIMAL(18,4) NOT NULL,
    price DECIMAL(18,4) NOT NULL,
    side ENUM('buy', 'sell') NOT NULL,
    commission DECIMAL(18,4) DEFAULT 0.0000,
    fees DECIMAL(18,4) DEFAULT 0.0000,
    total_cost DECIMAL(18,4) NOT NULL,      -- qty * price + commission + fees
    executed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL,
    FOREIGN KEY (broker_id) REFERENCES brokers(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    INDEX idx_symbol (symbol),
    INDEX idx_executed_at (executed_at),
    INDEX idx_broker_account (broker_id, account_id),
    INDEX idx_order (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Historical trade executions';

-- ============================================================
-- 6. BROKER_API_LOGS - API call tracking and debugging
-- ============================================================
CREATE TABLE IF NOT EXISTS broker_api_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    broker_id INT NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    method ENUM('GET', 'POST', 'PUT', 'DELETE', 'PATCH') NOT NULL,
    request_payload TEXT,
    response_status INT,
    response_body TEXT,
    error_message TEXT,
    latency_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (broker_id) REFERENCES brokers(id) ON DELETE CASCADE,
    INDEX idx_broker_created (broker_id, created_at),
    INDEX idx_status (response_status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='API request/response logging for debugging';

-- ============================================================
-- 7. PORTFOLIO_SNAPSHOTS - Historical portfolio tracking
-- ============================================================
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    broker_id INT NOT NULL,
    total_value DECIMAL(18,2) NOT NULL,
    cash_balance DECIMAL(18,2) NOT NULL,
    equity DECIMAL(18,2) NOT NULL,
    buying_power DECIMAL(18,2) NOT NULL,
    positions_count INT DEFAULT 0,
    daily_pnl DECIMAL(18,4) DEFAULT 0.0000,
    total_pnl DECIMAL(18,4) DEFAULT 0.0000,
    snapshot_date DATE NOT NULL,
    snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (broker_id) REFERENCES brokers(id) ON DELETE CASCADE,
    UNIQUE KEY unique_daily_snapshot (account_id, snapshot_date),
    INDEX idx_account_date (account_id, snapshot_date),
    INDEX idx_broker_date (broker_id, snapshot_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Daily portfolio value snapshots for performance tracking';

-- ============================================================
-- 8. ALERTS - Trading alerts and notifications
-- ============================================================
CREATE TABLE IF NOT EXISTS trading_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    broker_id INT,
    account_id INT,
    alert_type ENUM('order_filled', 'order_rejected', 'position_closed', 'margin_call', 'api_error', 'custom') NOT NULL,
    severity ENUM('info', 'warning', 'error', 'critical') DEFAULT 'info',
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    related_order_id INT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (broker_id) REFERENCES brokers(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (related_order_id) REFERENCES orders(id) ON DELETE SET NULL,
    INDEX idx_created (created_at),
    INDEX idx_unread (is_read, created_at),
    INDEX idx_severity (severity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Trading alerts and notifications';

-- ============================================================
-- INITIAL DATA: Seed broker configurations
-- ============================================================
INSERT INTO brokers (name, display_name, type, region, api_endpoint, supports_paper_trading) VALUES
('mt5', 'MetaTrader 5', 'forex', 'GLOBAL', 'http://localhost:8000', TRUE),
('alpaca', 'Alpaca Markets', 'equities', 'US', 'https://paper-api.alpaca.markets', TRUE),
('ibkr', 'Interactive Brokers', 'equities', 'GLOBAL', 'https://localhost:5000', TRUE),
('webull', 'Webull', 'equities', 'US', 'https://us-openapi-alb.uat.webullbroker.com', TRUE)
ON DUPLICATE KEY UPDATE
    display_name = VALUES(display_name),
    api_endpoint = VALUES(api_endpoint),
    updated_at = CURRENT_TIMESTAMP;

-- ============================================================
-- VIEWS: Convenient portfolio aggregation
-- ============================================================

-- Portfolio summary by broker
CREATE OR REPLACE VIEW v_portfolio_summary AS
SELECT 
    b.name AS broker_name,
    b.display_name AS broker_display_name,
    a.account_number,
    a.owner,
    a.balance,
    a.equity,
    a.buying_power,
    COUNT(DISTINCT p.id) AS positions_count,
    SUM(p.market_value) AS total_positions_value,
    SUM(p.unrealized_pnl) AS total_unrealized_pnl,
    a.last_sync_at
FROM accounts a
JOIN brokers b ON a.broker_id = b.id
LEFT JOIN positions p ON a.id = p.account_id
WHERE a.is_active = TRUE AND b.is_active = TRUE
GROUP BY a.id, b.name, b.display_name, a.account_number, a.owner, a.balance, a.equity, a.buying_power, a.last_sync_at;

-- Recent orders summary
CREATE OR REPLACE VIEW v_recent_orders AS
SELECT 
    o.id,
    b.display_name AS broker,
    a.account_number,
    o.symbol,
    o.side,
    o.order_type,
    o.qty,
    o.filled_qty,
    o.status,
    o.avg_fill_price,
    o.placed_at,
    o.filled_at
FROM orders o
JOIN brokers b ON o.broker_id = b.id
JOIN accounts a ON o.account_id = a.id
ORDER BY o.placed_at DESC
LIMIT 100;

-- All positions across brokers
CREATE OR REPLACE VIEW v_all_positions AS
SELECT 
    p.id,
    b.display_name AS broker,
    a.account_number,
    p.symbol,
    p.asset_type,
    p.qty,
    p.avg_entry_price,
    p.current_price,
    p.market_value,
    p.unrealized_pnl,
    p.side,
    p.opened_at,
    p.last_updated
FROM positions p
JOIN brokers b ON p.broker_id = b.id
JOIN accounts a ON p.account_id = a.id
ORDER BY p.market_value DESC;

-- ============================================================
-- SUCCESS MESSAGE
-- ============================================================
SELECT 'Multi-Broker Trading Database Schema Created Successfully!' AS status,
       'Tables: brokers, accounts, orders, positions, trades, broker_api_logs, portfolio_snapshots, trading_alerts' AS tables_created,
       'Views: v_portfolio_summary, v_recent_orders, v_all_positions' AS views_created;    