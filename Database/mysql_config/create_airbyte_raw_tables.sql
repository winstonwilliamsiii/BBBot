-- ============================================
-- Raw Data Tables for Airbyte Ingestion
-- Database: bbbot1 (MySQL)
-- Purpose: Store raw data from API sources
-- ============================================

USE bbbot1;

-- ============================================
-- 1. PRICES_DAILY
-- Daily OHLC price data from Tiingo API
-- ============================================
CREATE TABLE IF NOT EXISTS prices_daily (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(18, 4),
    high DECIMAL(18, 4),
    low DECIMAL(18, 4),
    close DECIMAL(18, 4) NOT NULL,
    volume BIGINT,
    adj_open DECIMAL(18, 4),
    adj_high DECIMAL(18, 4),
    adj_low DECIMAL(18, 4),
    adj_close DECIMAL(18, 4),
    adj_volume BIGINT,
    split_factor DECIMAL(10, 6) DEFAULT 1.0,
    dividend_amount DECIMAL(10, 4),
    
    -- Metadata
    source VARCHAR(50) DEFAULT 'tiingo' COMMENT 'Data source: tiingo, yfinance, polygon',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE KEY unique_ticker_date (ticker, date),
    INDEX idx_ticker (ticker),
    INDEX idx_date (date),
    INDEX idx_ticker_date (ticker, date),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Daily OHLC price data loaded by Airbyte from Tiingo API';

-- ============================================
-- 2. FUNDAMENTALS_RAW
-- Financial statement data from AlphaVantage/yfinance
-- ============================================
CREATE TABLE IF NOT EXISTS fundamentals_raw (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    report_date DATE NOT NULL,
    fiscal_period VARCHAR(10) COMMENT 'Q1, Q2, Q3, Q4, FY',
    
    -- Income Statement
    revenue DECIMAL(18, 2),
    gross_profit DECIMAL(18, 2),
    operating_income DECIMAL(18, 2),
    net_income DECIMAL(18, 2) NOT NULL,
    ebit DECIMAL(18, 2) NOT NULL,
    ebitda DECIMAL(18, 2) NOT NULL,
    eps DECIMAL(10, 4),
    
    -- Balance Sheet
    total_assets DECIMAL(18, 2) NOT NULL,
    total_equity DECIMAL(18, 2) NOT NULL,
    total_liabilities DECIMAL(18, 2) NOT NULL,
    current_assets DECIMAL(18, 2),
    current_liabilities DECIMAL(18, 2),
    cash_and_equivalents DECIMAL(18, 2) NOT NULL,
    inventory DECIMAL(18, 2),
    accounts_receivable DECIMAL(18, 2),
    accounts_payable DECIMAL(18, 2),
    
    -- Cash Flow
    operating_cash_flow DECIMAL(18, 2),
    investing_cash_flow DECIMAL(18, 2),
    financing_cash_flow DECIMAL(18, 2),
    free_cash_flow DECIMAL(18, 2),
    
    -- Share Information
    shares_outstanding BIGINT NOT NULL,
    market_cap DECIMAL(18, 2),
    
    -- Metadata
    source VARCHAR(50) DEFAULT 'alphavantage' COMMENT 'Data source: alphavantage, yfinance, financial_modeling_prep',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE KEY unique_ticker_report (ticker, report_date),
    INDEX idx_ticker (ticker),
    INDEX idx_report_date (report_date),
    INDEX idx_ticker_date (ticker, report_date),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Raw fundamental financial data loaded by Airbyte from AlphaVantage/yfinance';

-- ============================================
-- 3. SENTIMENT_MSGS
-- Social sentiment messages from StockTwits/Twitter
-- ============================================
CREATE TABLE IF NOT EXISTS sentiment_msgs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    timestamp DATETIME NOT NULL,
    message_id VARCHAR(100) UNIQUE COMMENT 'External message ID from source',
    
    -- Message Content
    message_text TEXT,
    sentiment_score DECIMAL(5, 4) COMMENT 'Sentiment score -1 to 1',
    sentiment_label VARCHAR(20) COMMENT 'bullish, bearish, neutral',
    
    -- Engagement Metrics
    likes_count INT DEFAULT 0,
    retweets_count INT DEFAULT 0,
    replies_count INT DEFAULT 0,
    
    -- User Information
    user_id VARCHAR(100),
    username VARCHAR(100),
    user_followers INT,
    user_verified BOOLEAN DEFAULT FALSE,
    
    -- Message Metadata
    source VARCHAR(50) DEFAULT 'stocktwits' COMMENT 'Data source: stocktwits, twitter, reddit',
    language VARCHAR(10) DEFAULT 'en',
    has_link BOOLEAN DEFAULT FALSE,
    has_media BOOLEAN DEFAULT FALSE,
    
    -- Aggregation Fields (for dbt)
    message_count INT DEFAULT 1,
    bullish_count INT DEFAULT 0,
    bearish_count INT DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Constraints
    INDEX idx_ticker (ticker),
    INDEX idx_timestamp (timestamp),
    INDEX idx_ticker_timestamp (ticker, timestamp),
    INDEX idx_sentiment_label (sentiment_label),
    INDEX idx_source (source),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Social sentiment messages loaded by Airbyte from StockTwits/Twitter';

-- ============================================
-- 4. TECHNICALS_RAW
-- Technical indicators and derived metrics
-- ============================================
CREATE TABLE IF NOT EXISTS technicals_raw (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    
    -- Moving Averages
    sma_20 DECIMAL(18, 4) COMMENT '20-day Simple Moving Average',
    sma_50 DECIMAL(18, 4) COMMENT '50-day Simple Moving Average',
    sma_200 DECIMAL(18, 4) COMMENT '200-day Simple Moving Average',
    ema_12 DECIMAL(18, 4) COMMENT '12-day Exponential Moving Average',
    ema_26 DECIMAL(18, 4) COMMENT '26-day Exponential Moving Average',
    
    -- Momentum Indicators
    rsi_14 DECIMAL(5, 2) COMMENT 'Relative Strength Index (14-day)',
    macd DECIMAL(18, 4) COMMENT 'MACD Line',
    macd_signal DECIMAL(18, 4) COMMENT 'MACD Signal Line',
    macd_histogram DECIMAL(18, 4) COMMENT 'MACD Histogram',
    
    -- Volatility Indicators
    bollinger_upper DECIMAL(18, 4) COMMENT 'Bollinger Band Upper',
    bollinger_middle DECIMAL(18, 4) COMMENT 'Bollinger Band Middle',
    bollinger_lower DECIMAL(18, 4) COMMENT 'Bollinger Band Lower',
    atr_14 DECIMAL(18, 4) COMMENT 'Average True Range (14-day)',
    
    -- Volume Indicators
    volume_sma_20 BIGINT COMMENT '20-day Volume Moving Average',
    obv BIGINT COMMENT 'On-Balance Volume',
    
    -- Trend Indicators
    adx_14 DECIMAL(5, 2) COMMENT 'Average Directional Index (14-day)',
    stochastic_k DECIMAL(5, 2) COMMENT 'Stochastic %K',
    stochastic_d DECIMAL(5, 2) COMMENT 'Stochastic %D',
    
    -- Price Action
    price_change_1d DECIMAL(10, 4) COMMENT '1-day price change %',
    price_change_5d DECIMAL(10, 4) COMMENT '5-day price change %',
    price_change_20d DECIMAL(10, 4) COMMENT '20-day price change %',
    
    -- Support/Resistance
    pivot_point DECIMAL(18, 4),
    resistance_1 DECIMAL(18, 4),
    resistance_2 DECIMAL(18, 4),
    support_1 DECIMAL(18, 4),
    support_2 DECIMAL(18, 4),
    
    -- Metadata
    source VARCHAR(50) DEFAULT 'calculated' COMMENT 'Data source: calculated, talib, tradingview',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE KEY unique_ticker_date (ticker, date),
    INDEX idx_ticker (ticker),
    INDEX idx_date (date),
    INDEX idx_ticker_date (ticker, date),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Technical indicators calculated from price data';

-- ============================================
-- Verification Queries
-- ============================================

-- Check table structures
SHOW TABLES WHERE Tables_in_bbbot1 LIKE '%raw' 
   OR Tables_in_bbbot1 = 'prices_daily' 
   OR Tables_in_bbbot1 = 'sentiment_msgs' 
   OR Tables_in_bbbot1 = 'technicals_raw';

-- Check table info
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    CREATE_TIME,
    TABLE_COMMENT
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'bbbot1'
  AND TABLE_NAME IN ('prices_daily', 'fundamentals_raw', 'sentiment_msgs', 'technicals_raw')
ORDER BY TABLE_NAME;
