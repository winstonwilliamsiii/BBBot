-- ML Trading Bot Database Schema
-- Run this script to create required tables for automated trading

USE bentleybot;

-- Market data storage
CREATE TABLE IF NOT EXISTS market_data_latest (
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    Open FLOAT,
    High FLOAT,
    Low FLOAT,
    Close FLOAT,
    Volume BIGINT,
    PRIMARY KEY (date, ticker),
    INDEX idx_ticker (ticker),
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Trading signals
CREATE TABLE IF NOT EXISTS trading_signals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    signal INT NOT NULL COMMENT '1=BUY, -1=SELL, 0=HOLD',
    price FLOAT NOT NULL,
    timestamp DATETIME NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    INDEX idx_ticker (ticker),
    INDEX idx_timestamp (timestamp),
    INDEX idx_strategy (strategy)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Trades history
CREATE TABLE IF NOT EXISTS trades_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    action VARCHAR(10) NOT NULL COMMENT 'BUY or SELL',
    shares INT NOT NULL,
    price FLOAT NOT NULL,
    value FLOAT NOT NULL,
    timestamp DATETIME NOT NULL,
    status VARCHAR(20) NOT NULL COMMENT 'SIMULATED or EXECUTED',
    order_id VARCHAR(50),
    strategy VARCHAR(50) NOT NULL,
    INDEX idx_ticker (ticker),
    INDEX idx_timestamp (timestamp),
    INDEX idx_status (status),
    INDEX idx_strategy (strategy)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Performance metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    total_trades INT NOT NULL,
    buy_trades INT NOT NULL,
    sell_trades INT NOT NULL,
    total_value FLOAT NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    INDEX idx_date (date),
    INDEX idx_strategy (strategy)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Bot status tracking
CREATE TABLE IF NOT EXISTS bot_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    status VARCHAR(20) NOT NULL COMMENT 'active, inactive, error',
    strategy VARCHAR(50),
    timestamp DATETIME NOT NULL,
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Daily reports
CREATE TABLE IF NOT EXISTS daily_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATETIME NOT NULL,
    report TEXT,
    signals_count INT,
    strategy VARCHAR(50),
    INDEX idx_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Portfolio positions (optional - for tracking current holdings)
CREATE TABLE IF NOT EXISTS portfolio_positions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    shares INT NOT NULL,
    avg_price FLOAT NOT NULL,
    current_value FLOAT,
    last_updated DATETIME NOT NULL,
    strategy VARCHAR(50),
    UNIQUE KEY unique_ticker_strategy (ticker, strategy),
    INDEX idx_ticker (ticker)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Model performance tracking (for Random Forest experiments)
CREATE TABLE IF NOT EXISTS model_performance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    ticker VARCHAR(10),
    r2_score FLOAT,
    mse FLOAT,
    train_date DATETIME NOT NULL,
    feature_count INT,
    parameters JSON,
    mlflow_run_id VARCHAR(100),
    INDEX idx_model_name (model_name),
    INDEX idx_ticker (ticker),
    INDEX idx_train_date (train_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Initialize bot status
INSERT INTO bot_status (status, strategy, timestamp)
VALUES ('inactive', 'mean_reversion', NOW())
ON DUPLICATE KEY UPDATE timestamp = NOW();

-- Verification queries
SELECT 'Tables created successfully!' AS status;

SELECT 
    TABLE_NAME, 
    TABLE_ROWS, 
    CREATE_TIME
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'bentleybot'
AND TABLE_NAME IN (
    'market_data_latest',
    'trading_signals',
    'trades_history',
    'performance_metrics',
    'bot_status',
    'daily_reports',
    'portfolio_positions',
    'model_performance'
)
ORDER BY TABLE_NAME;
