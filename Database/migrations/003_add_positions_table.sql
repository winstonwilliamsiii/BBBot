-- Migration 003: Add portfolio positions and broker integration tables
-- Description: Creates tables for investment portfolio tracking and broker API integration
-- Date: 2025-12-29

-- Portfolio positions table
CREATE TABLE IF NOT EXISTS portfolio_positions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(15, 4) NOT NULL DEFAULT 0,
    average_cost DECIMAL(15, 4) NOT NULL DEFAULT 0,
    current_price DECIMAL(15, 4),
    market_value DECIMAL(15, 2) GENERATED ALWAYS AS (quantity * current_price) STORED,
    cost_basis DECIMAL(15, 2) GENERATED ALWAYS AS (quantity * average_cost) STORED,
    unrealized_gain DECIMAL(15, 2) GENERATED ALWAYS AS ((quantity * current_price) - (quantity * average_cost)) STORED,
    asset_type ENUM('stock', 'etf', 'crypto', 'fund', 'forex', 'futures', 'options', 'token') DEFAULT 'stock',
    broker VARCHAR(50) COMMENT 'webull, ibkr, binance, ninjatrader, tzero, metatrader5',
    account_number VARCHAR(100),
    is_active TINYINT(1) DEFAULT 1,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_symbol (user_id, symbol),
    INDEX idx_broker (broker),
    INDEX idx_is_active (is_active),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Broker API credentials table
CREATE TABLE IF NOT EXISTS broker_api_credentials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1 COMMENT 'Multi-tenant identifier',
    user_id INT NOT NULL,
    broker ENUM('webull', 'ibkr', 'binance', 'ninjatrader', 'tzero', 'metatrader5') NOT NULL,
    access_token TEXT NOT NULL COMMENT 'Encrypted API token',
    api_key VARCHAR(255),
    api_secret TEXT COMMENT 'Encrypted API secret',
    device_id VARCHAR(255),
    account_number VARCHAR(100),
    is_active TINYINT(1) DEFAULT 1,
    status ENUM('connected', 'pending', 'disconnected', 'error') DEFAULT 'pending',
    last_sync TIMESTAMP NULL,
    last_error TEXT,
    environment ENUM('production', 'sandbox', 'testnet', 'paper') DEFAULT 'sandbox',
    host VARCHAR(255),
    port INT,
    client_id INT,
    balance DECIMAL(15, 2) DEFAULT 0,
    positions_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_tenant_user (tenant_id, user_id),
    INDEX idx_broker (broker),
    INDEX idx_is_active (is_active),
    INDEX idx_status (status),
    INDEX idx_user_broker (user_id, broker),
    UNIQUE KEY unique_user_broker (tenant_id, user_id, broker, is_active),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Broker connections table
CREATE TABLE IF NOT EXISTS broker_connections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,
    user_id INT NOT NULL,
    broker_name VARCHAR(100) NOT NULL,
    broker ENUM('webull', 'ibkr', 'binance', 'ninjatrader', 'tzero', 'metatrader5'),
    account_number VARCHAR(100) NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    status ENUM('connected', 'pending', 'disconnected', 'error') DEFAULT 'pending',
    last_sync TIMESTAMP NULL,
    last_error TEXT,
    balance DECIMAL(15, 2) DEFAULT 0,
    positions_count INT DEFAULT 0,
    api_credential_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_tenant_user (tenant_id, user_id),
    INDEX idx_user_broker (user_id, broker_name),
    INDEX idx_status (status),
    INDEX idx_is_active (is_active),
    INDEX idx_last_sync (last_sync),
    UNIQUE KEY unique_user_broker_account (tenant_id, user_id, broker_name, account_number),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (api_credential_id) REFERENCES broker_api_credentials(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Plaid items table (new structure)
CREATE TABLE IF NOT EXISTS plaid_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    item_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    access_token TEXT NOT NULL,
    institution_id VARCHAR(255),
    institution_name VARCHAR(255),
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_item_id (item_id),
    INDEX idx_is_active (is_active),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- WeFolio funds table (Webull funds)
CREATE TABLE IF NOT EXISTS wefolio_funds (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    nav DECIMAL(10, 2),
    shares DECIMAL(15, 4),
    value DECIMAL(15, 2),
    daily_change DECIMAL(15, 2),
    daily_change_pct DECIMAL(5, 2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_last_updated (last_updated),
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
