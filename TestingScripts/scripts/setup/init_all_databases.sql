-- ============================================================================
-- BentleyBudgetBot Database Initialization Script
-- Creates all required databases and tables for the application
-- ============================================================================
-- Version: 2.0
-- Date: December 14, 2025
-- Run as: mysql -u root -p < scripts/setup/init_all_databases.sql
-- ============================================================================

-- ============================================================================
-- STEP 1: Create Databases
-- ============================================================================

CREATE DATABASE IF NOT EXISTS mydb 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci 
    COMMENT 'Personal budget and Plaid transaction data';

CREATE DATABASE IF NOT EXISTS mansa_bot 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci 
    COMMENT 'Application metrics, trading data, dbt staging';

CREATE DATABASE IF NOT EXISTS mansa_quant 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci 
    COMMENT 'Quantitative analysis: fundamentals, sentiment, technicals';

CREATE DATABASE IF NOT EXISTS mlflow_db 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci 
    COMMENT 'MLFlow experiments and Airflow metadata';

CREATE DATABASE IF NOT EXISTS mrgp_schema 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci 
    COMMENT 'Bulk equities and crypto historical data';

-- Show created databases
SELECT 
    SCHEMA_NAME as 'Database',
    DEFAULT_CHARACTER_SET_NAME as 'Charset',
    DEFAULT_COLLATION_NAME as 'Collation'
FROM information_schema.SCHEMATA
WHERE SCHEMA_NAME IN ('mydb', 'mansa_bot', 'mansa_quant', 'mlflow_db', 'mrgp_schema')
ORDER BY SCHEMA_NAME;

-- ============================================================================
-- STEP 2: mansa_bot Database Schema (Metrics & Trading)
-- ============================================================================

USE mansa_bot;

-- System Metrics Tables
CREATE TABLE IF NOT EXISTS api_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL DEFAULT 'GET',
    response_time_ms INT NOT NULL,
    status_code INT NOT NULL,
    error_message TEXT,
    user_id VARCHAR(50),
    ip_address VARCHAR(45),
    INDEX idx_timestamp (timestamp),
    INDEX idx_endpoint (endpoint),
    INDEX idx_status_code (status_code)
) ENGINE=InnoDB COMMENT='API request metrics for monitoring';

CREATE TABLE IF NOT EXISTS system_health (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    cpu_percent DECIMAL(5,2),
    memory_percent DECIMAL(5,2),
    memory_available_gb DECIMAL(10,2),
    disk_percent DECIMAL(5,2),
    disk_free_gb DECIMAL(10,2),
    active_connections INT DEFAULT 0,
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB COMMENT='System resource utilization metrics';

CREATE TABLE IF NOT EXISTS data_freshness (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_source VARCHAR(100) NOT NULL UNIQUE,
    last_update DATETIME NOT NULL,
    record_count BIGINT DEFAULT 0,
    status ENUM('healthy', 'stale', 'error') DEFAULT 'healthy',
    error_message TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_last_update (last_update),
    INDEX idx_status (status)
) ENGINE=InnoDB COMMENT='Track data pipeline freshness';

-- Trading Tables
CREATE TABLE IF NOT EXISTS trades (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    trade_date DATETIME NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    side ENUM('BUY', 'SELL') NOT NULL,
    entry_price DECIMAL(12,4) NOT NULL,
    exit_price DECIMAL(12,4),
    quantity INT NOT NULL,
    pnl DECIMAL(12,2),
    pnl_percent DECIMAL(8,4),
    fees DECIMAL(10,2) DEFAULT 0,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_trade_date (trade_date),
    INDEX idx_ticker (ticker),
    INDEX idx_strategy (strategy),
    INDEX idx_pnl (pnl)
) ENGINE=InnoDB COMMENT='Trading bot transaction history';

CREATE TABLE IF NOT EXISTS portfolio_positions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL UNIQUE,
    quantity INT NOT NULL DEFAULT 0,
    avg_cost DECIMAL(12,4) NOT NULL,
    current_price DECIMAL(12,4),
    market_value DECIMAL(14,2),
    unrealized_pnl DECIMAL(12,2),
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ticker (ticker),
    INDEX idx_unrealized_pnl (unrealized_pnl)
) ENGINE=InnoDB COMMENT='Current portfolio holdings';

CREATE TABLE IF NOT EXISTS portfolio_performance (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    snapshot_date DATETIME NOT NULL,
    total_value DECIMAL(14,2) NOT NULL,
    cash_balance DECIMAL(14,2) NOT NULL DEFAULT 0,
    daily_pnl DECIMAL(12,2),
    cumulative_pnl DECIMAL(14,2),
    win_rate DECIMAL(5,2),
    sharpe_ratio DECIMAL(6,4),
    max_drawdown DECIMAL(8,4),
    INDEX idx_snapshot_date (snapshot_date)
) ENGINE=InnoDB COMMENT='Daily portfolio performance snapshots';

-- dbt Staging Tables
CREATE TABLE IF NOT EXISTS stg_fundamentals (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    report_date DATE NOT NULL,
    revenue DECIMAL(18,2),
    net_income DECIMAL(18,2),
    eps DECIMAL(10,4),
    pe_ratio DECIMAL(8,2),
    loaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ticker_date (ticker, report_date),
    INDEX idx_ticker (ticker),
    INDEX idx_report_date (report_date)
) ENGINE=InnoDB COMMENT='Staged fundamental data for dbt processing';

CREATE TABLE IF NOT EXISTS stg_prices (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    price_date DATE NOT NULL,
    open DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    close DECIMAL(12,4) NOT NULL,
    volume BIGINT,
    loaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ticker_date (ticker, price_date),
    INDEX idx_ticker (ticker),
    INDEX idx_price_date (price_date)
) ENGINE=InnoDB COMMENT='Staged price data for dbt processing';

CREATE TABLE IF NOT EXISTS stg_sentiment (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    sentiment_date DATETIME NOT NULL,
    source VARCHAR(50) NOT NULL,
    sentiment_score DECIMAL(5,4),
    message_count INT DEFAULT 0,
    loaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ticker (ticker),
    INDEX idx_sentiment_date (sentiment_date),
    INDEX idx_source (source)
) ENGINE=InnoDB COMMENT='Staged sentiment data for dbt processing';

-- ============================================================================
-- STEP 3: mansa_quant Database Schema (Quantitative Analysis)
-- ============================================================================

USE mansa_quant;

-- Fundamental Data
CREATE TABLE IF NOT EXISTS stock_fundamentals (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    report_date DATE NOT NULL,
    period_type ENUM('Q', 'Y') NOT NULL,
    revenue DECIMAL(18,2),
    gross_profit DECIMAL(18,2),
    operating_income DECIMAL(18,2),
    net_income DECIMAL(18,2),
    ebitda DECIMAL(18,2),
    eps DECIMAL(10,4),
    total_assets DECIMAL(18,2),
    total_liabilities DECIMAL(18,2),
    shareholders_equity DECIMAL(18,2),
    cash_flow_operating DECIMAL(18,2),
    cash_flow_investing DECIMAL(18,2),
    cash_flow_financing DECIMAL(18,2),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ticker_date_period (ticker, report_date, period_type),
    INDEX idx_ticker (ticker),
    INDEX idx_report_date (report_date)
) ENGINE=InnoDB COMMENT='Company financial statements';

CREATE TABLE IF NOT EXISTS earnings_reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    report_date DATE NOT NULL,
    fiscal_quarter INT NOT NULL,
    fiscal_year INT NOT NULL,
    actual_eps DECIMAL(10,4),
    estimated_eps DECIMAL(10,4),
    surprise_percent DECIMAL(8,4),
    actual_revenue DECIMAL(18,2),
    estimated_revenue DECIMAL(18,2),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ticker_quarter_year (ticker, fiscal_quarter, fiscal_year),
    INDEX idx_ticker (ticker),
    INDEX idx_report_date (report_date)
) ENGINE=InnoDB COMMENT='Quarterly earnings reports and estimates';

CREATE TABLE IF NOT EXISTS company_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL UNIQUE,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap DECIMAL(18,2),
    description TEXT,
    ceo VARCHAR(255),
    employees INT,
    founded_year INT,
    headquarters VARCHAR(255),
    website VARCHAR(255),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_sector (sector),
    INDEX idx_industry (industry)
) ENGINE=InnoDB COMMENT='Company profile and metadata';

-- Sentiment Analysis
CREATE TABLE IF NOT EXISTS stocktwits_sentiment (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    message_id VARCHAR(50) UNIQUE,
    created_at DATETIME NOT NULL,
    sentiment ENUM('Bullish', 'Bearish', 'Neutral'),
    message TEXT,
    user_followers INT,
    likes INT DEFAULT 0,
    loaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ticker (ticker),
    INDEX idx_created_at (created_at),
    INDEX idx_sentiment (sentiment)
) ENGINE=InnoDB COMMENT='StockTwits social sentiment data';

CREATE TABLE IF NOT EXISTS news_sentiment (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    published_at DATETIME NOT NULL,
    headline VARCHAR(500) NOT NULL,
    source VARCHAR(100),
    sentiment_score DECIMAL(5,4),
    sentiment_label ENUM('positive', 'negative', 'neutral'),
    url TEXT,
    loaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ticker (ticker),
    INDEX idx_published_at (published_at),
    INDEX idx_sentiment_label (sentiment_label)
) ENGINE=InnoDB COMMENT='News article sentiment analysis';

CREATE TABLE IF NOT EXISTS reddit_sentiment (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    post_id VARCHAR(50) UNIQUE,
    subreddit VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL,
    title VARCHAR(500),
    score INT DEFAULT 0,
    num_comments INT DEFAULT 0,
    sentiment_score DECIMAL(5,4),
    loaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ticker (ticker),
    INDEX idx_subreddit (subreddit),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB COMMENT='Reddit mentions and sentiment';

-- Technical Analysis
CREATE TABLE IF NOT EXISTS technical_indicators (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    calc_date DATE NOT NULL,
    rsi_14 DECIMAL(6,2),
    macd DECIMAL(10,4),
    macd_signal DECIMAL(10,4),
    macd_histogram DECIMAL(10,4),
    sma_20 DECIMAL(12,4),
    sma_50 DECIMAL(12,4),
    sma_200 DECIMAL(12,4),
    ema_12 DECIMAL(12,4),
    ema_26 DECIMAL(12,4),
    bollinger_upper DECIMAL(12,4),
    bollinger_middle DECIMAL(12,4),
    bollinger_lower DECIMAL(12,4),
    atr_14 DECIMAL(12,4),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ticker_date (ticker, calc_date),
    INDEX idx_ticker (ticker),
    INDEX idx_calc_date (calc_date)
) ENGINE=InnoDB COMMENT='Technical indicator calculations';

CREATE TABLE IF NOT EXISTS price_patterns (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    detected_date DATE NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    pattern_strength DECIMAL(5,2),
    price_target DECIMAL(12,4),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ticker (ticker),
    INDEX idx_detected_date (detected_date),
    INDEX idx_pattern_type (pattern_type)
) ENGINE=InnoDB COMMENT='Chart pattern detection results';

-- ============================================================================
-- STEP 4: mrgp_schema Database Schema (Bulk Historical Data)
-- ============================================================================

USE mrgp_schema;

-- Equities
CREATE TABLE IF NOT EXISTS stock_prices_bulk (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    price_date DATE NOT NULL,
    open DECIMAL(12,4) NOT NULL,
    high DECIMAL(12,4) NOT NULL,
    low DECIMAL(12,4) NOT NULL,
    close DECIMAL(12,4) NOT NULL,
    adj_close DECIMAL(12,4),
    volume BIGINT NOT NULL,
    UNIQUE KEY uk_ticker_date (ticker, price_date),
    INDEX idx_ticker (ticker),
    INDEX idx_price_date (price_date)
) ENGINE=InnoDB COMMENT='Historical daily OHLCV data (years of history)';

CREATE TABLE IF NOT EXISTS intraday_prices (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    timestamp DATETIME NOT NULL,
    open DECIMAL(12,4) NOT NULL,
    high DECIMAL(12,4) NOT NULL,
    low DECIMAL(12,4) NOT NULL,
    close DECIMAL(12,4) NOT NULL,
    volume INT NOT NULL,
    UNIQUE KEY uk_ticker_timestamp (ticker, timestamp),
    INDEX idx_ticker (ticker),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB COMMENT='Intraday price bars (1min, 5min intervals)';

CREATE TABLE IF NOT EXISTS stock_splits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    split_date DATE NOT NULL,
    split_ratio VARCHAR(20) NOT NULL,
    UNIQUE KEY uk_ticker_date (ticker, split_date),
    INDEX idx_ticker (ticker),
    INDEX idx_split_date (split_date)
) ENGINE=InnoDB COMMENT='Stock split events';

CREATE TABLE IF NOT EXISTS dividends (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    ex_date DATE NOT NULL,
    payment_date DATE,
    amount DECIMAL(10,4) NOT NULL,
    UNIQUE KEY uk_ticker_ex_date (ticker, ex_date),
    INDEX idx_ticker (ticker),
    INDEX idx_ex_date (ex_date)
) ENGINE=InnoDB COMMENT='Dividend payment history';

-- Cryptocurrency
CREATE TABLE IF NOT EXISTS crypto_prices (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp DATETIME NOT NULL,
    open DECIMAL(18,8) NOT NULL,
    high DECIMAL(18,8) NOT NULL,
    low DECIMAL(18,8) NOT NULL,
    close DECIMAL(18,8) NOT NULL,
    volume DECIMAL(24,8) NOT NULL,
    quote_volume DECIMAL(24,8),
    UNIQUE KEY uk_symbol_timestamp (symbol, timestamp),
    INDEX idx_symbol (symbol),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB COMMENT='Cryptocurrency OHLCV data';

CREATE TABLE IF NOT EXISTS crypto_orderbook (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp DATETIME NOT NULL,
    side ENUM('BID', 'ASK') NOT NULL,
    price DECIMAL(18,8) NOT NULL,
    quantity DECIMAL(18,8) NOT NULL,
    INDEX idx_symbol (symbol),
    INDEX idx_timestamp (timestamp),
    INDEX idx_side (side)
) ENGINE=InnoDB COMMENT='Cryptocurrency orderbook snapshots';

CREATE TABLE IF NOT EXISTS crypto_trades (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    trade_id VARCHAR(50) UNIQUE,
    timestamp DATETIME NOT NULL,
    price DECIMAL(18,8) NOT NULL,
    quantity DECIMAL(18,8) NOT NULL,
    side ENUM('BUY', 'SELL'),
    INDEX idx_symbol (symbol),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB COMMENT='Real-time crypto trade data from WebSocket';

-- Reference Data
CREATE TABLE IF NOT EXISTS ticker_master (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL UNIQUE,
    asset_type ENUM('stock', 'etf', 'crypto', 'index') NOT NULL,
    exchange VARCHAR(50),
    currency VARCHAR(3) DEFAULT 'USD',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ticker (ticker),
    INDEX idx_asset_type (asset_type),
    INDEX idx_exchange (exchange)
) ENGINE=InnoDB COMMENT='Master list of all tradeable symbols';

CREATE TABLE IF NOT EXISTS exchange_holidays (
    id INT AUTO_INCREMENT PRIMARY KEY,
    exchange VARCHAR(50) NOT NULL,
    holiday_date DATE NOT NULL,
    holiday_name VARCHAR(100) NOT NULL,
    UNIQUE KEY uk_exchange_date (exchange, holiday_date),
    INDEX idx_exchange (exchange),
    INDEX idx_holiday_date (holiday_date)
) ENGINE=InnoDB COMMENT='Market holiday calendar';

-- ============================================================================
-- STEP 5: Summary and Verification
-- ============================================================================

-- Show table counts per database
SELECT 
    table_schema AS 'Database',
    COUNT(*) AS 'Table Count',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.tables
WHERE table_schema IN ('mydb', 'mansa_bot', 'mansa_quant', 'mlflow_db', 'mrgp_schema')
GROUP BY table_schema
ORDER BY table_schema;

-- Show all tables created
SELECT 
    table_schema AS 'Database',
    table_name AS 'Table',
    engine AS 'Engine',
    table_rows AS 'Rows',
    table_comment AS 'Comment'
FROM information_schema.tables
WHERE table_schema IN ('mydb', 'mansa_bot', 'mansa_quant', 'mlflow_db', 'mrgp_schema')
ORDER BY table_schema, table_name;

SELECT '✅ Database initialization complete!' AS Status;
SELECT 'Next steps:' AS 'Action';
SELECT '1. Run budget_schema.sql to create budget tables in mydb' AS 'Step 1';
SELECT '2. Update .env file with correct database names' AS 'Step 2';
SELECT '3. Run python test_database_connections.py to verify' AS 'Step 3';
