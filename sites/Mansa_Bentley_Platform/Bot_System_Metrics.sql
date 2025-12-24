-- Active: 1763499046791@@127.0.0.1@3306@mansa_bot
-- API Metrics tracking
CREATE TABLE api_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    response_time_ms INT,
    status_code INT,
    error_message TEXT,
    INDEX idx_timestamp (timestamp),
    INDEX idx_endpoint (endpoint)
);

-- Trading records
CREATE TABLE trades (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    trade_date DATETIME,
    ticker VARCHAR(10),
    strategy VARCHAR(50),
    entry_price DECIMAL(10,2),
    exit_price DECIMAL(10,2),
    quantity INT,
    pnl DECIMAL(10,2),
    INDEX idx_trade_date (trade_date),
    INDEX idx_ticker (ticker)
);

-- Stock prices cache
CREATE TABLE stock_prices (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ticker VARCHAR(10),
    price DECIMAL(10,2),
    volume BIGINT,
    INDEX idx_timestamp (timestamp),
    INDEX idx_ticker (ticker)
);