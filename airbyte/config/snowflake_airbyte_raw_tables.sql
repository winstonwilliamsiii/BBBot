-- ============================================
-- Raw Data Tables for Airbyte Ingestion
-- Database: MARKET_DATA (Snowflake)
-- Schema: PUBLIC
-- Purpose: Store raw data from API sources
-- ============================================

USE DATABASE MARKET_DATA;
USE SCHEMA PUBLIC;

-- ============================================
-- 1. PRICES_DAILY
-- Daily OHLC price data from Tiingo API
-- ============================================
CREATE TABLE IF NOT EXISTS PRICES_DAILY (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    TICKER VARCHAR(10) NOT NULL,
    DATE DATE NOT NULL,
    OPEN NUMBER(18, 4),
    HIGH NUMBER(18, 4),
    LOW NUMBER(18, 4),
    CLOSE NUMBER(18, 4) NOT NULL,
    VOLUME NUMBER(20, 0),
    ADJ_OPEN NUMBER(18, 4),
    ADJ_HIGH NUMBER(18, 4),
    ADJ_LOW NUMBER(18, 4),
    ADJ_CLOSE NUMBER(18, 4),
    ADJ_VOLUME NUMBER(20, 0),
    SPLIT_FACTOR NUMBER(10, 6) DEFAULT 1.0,
    DIVIDEND_AMOUNT NUMBER(10, 4),
    
    -- Metadata
    SOURCE VARCHAR(50) DEFAULT 'tiingo' COMMENT 'Data source: tiingo, yfinance, polygon',
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Constraints
    CONSTRAINT UNIQUE_TICKER_DATE UNIQUE (TICKER, DATE)
)
COMMENT='Daily OHLC price data loaded by Airbyte from Tiingo API';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS IDX_PRICES_TICKER ON PRICES_DAILY(TICKER);
CREATE INDEX IF NOT EXISTS IDX_PRICES_DATE ON PRICES_DAILY(DATE);
CREATE INDEX IF NOT EXISTS IDX_PRICES_CREATED_AT ON PRICES_DAILY(CREATED_AT);

-- ============================================
-- 2. FUNDAMENTALS_RAW
-- Financial statement data from AlphaVantage/yfinance
-- ============================================
CREATE TABLE IF NOT EXISTS FUNDAMENTALS_RAW (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    TICKER VARCHAR(10) NOT NULL,
    REPORT_DATE DATE NOT NULL,
    FISCAL_PERIOD VARCHAR(10) COMMENT 'Q1, Q2, Q3, Q4, FY',
    
    -- Income Statement
    REVENUE NUMBER(18, 2),
    GROSS_PROFIT NUMBER(18, 2),
    OPERATING_INCOME NUMBER(18, 2),
    NET_INCOME NUMBER(18, 2) NOT NULL,
    EBIT NUMBER(18, 2) NOT NULL,
    EBITDA NUMBER(18, 2) NOT NULL,
    EPS NUMBER(10, 4),
    
    -- Balance Sheet
    TOTAL_ASSETS NUMBER(18, 2) NOT NULL,
    TOTAL_EQUITY NUMBER(18, 2) NOT NULL,
    TOTAL_LIABILITIES NUMBER(18, 2) NOT NULL,
    CURRENT_ASSETS NUMBER(18, 2),
    CURRENT_LIABILITIES NUMBER(18, 2),
    CASH_AND_EQUIVALENTS NUMBER(18, 2) NOT NULL,
    INVENTORY NUMBER(18, 2),
    ACCOUNTS_RECEIVABLE NUMBER(18, 2),
    ACCOUNTS_PAYABLE NUMBER(18, 2),
    
    -- Cash Flow
    OPERATING_CASH_FLOW NUMBER(18, 2),
    INVESTING_CASH_FLOW NUMBER(18, 2),
    FINANCING_CASH_FLOW NUMBER(18, 2),
    FREE_CASH_FLOW NUMBER(18, 2),
    
    -- Share Information
    SHARES_OUTSTANDING NUMBER(20, 0) NOT NULL,
    MARKET_CAP NUMBER(18, 2),
    
    -- Metadata
    SOURCE VARCHAR(50) DEFAULT 'alphavantage' COMMENT 'Data source: alphavantage, yfinance, financial_modeling_prep',
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Constraints
    CONSTRAINT UNIQUE_TICKER_REPORT UNIQUE (TICKER, REPORT_DATE)
)
COMMENT='Raw fundamental financial data loaded by Airbyte from AlphaVantage/yfinance';

-- Create indexes
CREATE INDEX IF NOT EXISTS IDX_FUNDAMENTALS_TICKER ON FUNDAMENTALS_RAW(TICKER);
CREATE INDEX IF NOT EXISTS IDX_FUNDAMENTALS_REPORT_DATE ON FUNDAMENTALS_RAW(REPORT_DATE);
CREATE INDEX IF NOT EXISTS IDX_FUNDAMENTALS_CREATED_AT ON FUNDAMENTALS_RAW(CREATED_AT);

-- ============================================
-- 3. SENTIMENT_MSGS
-- Social sentiment messages from StockTwits/Twitter
-- ============================================
CREATE TABLE IF NOT EXISTS SENTIMENT_MSGS (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    TICKER VARCHAR(10) NOT NULL,
    TIMESTAMP TIMESTAMP_NTZ NOT NULL,
    MESSAGE_ID VARCHAR(100) UNIQUE COMMENT 'External message ID from source',
    
    -- Message Content
    MESSAGE_TEXT VARCHAR(16777216), -- Snowflake's max VARCHAR length
    SENTIMENT_SCORE NUMBER(5, 4) COMMENT 'Sentiment score -1 to 1',
    SENTIMENT_LABEL VARCHAR(20) COMMENT 'bullish, bearish, neutral',
    
    -- Engagement Metrics
    LIKES_COUNT NUMBER DEFAULT 0,
    RETWEETS_COUNT NUMBER DEFAULT 0,
    REPLIES_COUNT NUMBER DEFAULT 0,
    
    -- User Information
    USER_ID VARCHAR(100),
    USERNAME VARCHAR(100),
    USER_FOLLOWERS NUMBER,
    USER_VERIFIED BOOLEAN DEFAULT FALSE,
    
    -- Message Metadata
    SOURCE VARCHAR(50) DEFAULT 'stocktwits' COMMENT 'Data source: stocktwits, twitter, reddit',
    LANGUAGE VARCHAR(10) DEFAULT 'en',
    HAS_LINK BOOLEAN DEFAULT FALSE,
    HAS_MEDIA BOOLEAN DEFAULT FALSE,
    
    -- Aggregation Fields (for dbt)
    MESSAGE_COUNT NUMBER DEFAULT 1,
    BULLISH_COUNT NUMBER DEFAULT 0,
    BEARISH_COUNT NUMBER DEFAULT 0,
    
    -- Metadata
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT='Social sentiment messages loaded by Airbyte from StockTwits/Twitter';

-- Create indexes
CREATE INDEX IF NOT EXISTS IDX_SENTIMENT_TICKER ON SENTIMENT_MSGS(TICKER);
CREATE INDEX IF NOT EXISTS IDX_SENTIMENT_TIMESTAMP ON SENTIMENT_MSGS(TIMESTAMP);
CREATE INDEX IF NOT EXISTS IDX_SENTIMENT_LABEL ON SENTIMENT_MSGS(SENTIMENT_LABEL);
CREATE INDEX IF NOT EXISTS IDX_SENTIMENT_SOURCE ON SENTIMENT_MSGS(SOURCE);
CREATE INDEX IF NOT EXISTS IDX_SENTIMENT_CREATED_AT ON SENTIMENT_MSGS(CREATED_AT);

-- ============================================
-- 4. TECHNICALS_RAW
-- Technical indicators and derived metrics
-- ============================================
CREATE TABLE IF NOT EXISTS TECHNICALS_RAW (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    TICKER VARCHAR(10) NOT NULL,
    DATE DATE NOT NULL,
    
    -- Moving Averages
    SMA_20 NUMBER(18, 4) COMMENT '20-day Simple Moving Average',
    SMA_50 NUMBER(18, 4) COMMENT '50-day Simple Moving Average',
    SMA_200 NUMBER(18, 4) COMMENT '200-day Simple Moving Average',
    EMA_12 NUMBER(18, 4) COMMENT '12-day Exponential Moving Average',
    EMA_26 NUMBER(18, 4) COMMENT '26-day Exponential Moving Average',
    
    -- Momentum Indicators
    RSI_14 NUMBER(5, 2) COMMENT 'Relative Strength Index (14-day)',
    MACD NUMBER(18, 4) COMMENT 'MACD Line',
    MACD_SIGNAL NUMBER(18, 4) COMMENT 'MACD Signal Line',
    MACD_HISTOGRAM NUMBER(18, 4) COMMENT 'MACD Histogram',
    
    -- Volatility Indicators
    BOLLINGER_UPPER NUMBER(18, 4) COMMENT 'Bollinger Band Upper',
    BOLLINGER_MIDDLE NUMBER(18, 4) COMMENT 'Bollinger Band Middle',
    BOLLINGER_LOWER NUMBER(18, 4) COMMENT 'Bollinger Band Lower',
    ATR_14 NUMBER(18, 4) COMMENT 'Average True Range (14-day)',
    
    -- Volume Indicators
    VOLUME_SMA_20 NUMBER(20, 0) COMMENT '20-day Volume Moving Average',
    OBV NUMBER(20, 0) COMMENT 'On-Balance Volume',
    
    -- Trend Indicators
    ADX_14 NUMBER(5, 2) COMMENT 'Average Directional Index (14-day)',
    STOCHASTIC_K NUMBER(5, 2) COMMENT 'Stochastic %K',
    STOCHASTIC_D NUMBER(5, 2) COMMENT 'Stochastic %D',
    
    -- Price Action
    PRICE_CHANGE_1D NUMBER(10, 4) COMMENT '1-day price change %',
    PRICE_CHANGE_5D NUMBER(10, 4) COMMENT '5-day price change %',
    PRICE_CHANGE_20D NUMBER(10, 4) COMMENT '20-day price change %',
    
    -- Support/Resistance
    PIVOT_POINT NUMBER(18, 4),
    RESISTANCE_1 NUMBER(18, 4),
    RESISTANCE_2 NUMBER(18, 4),
    SUPPORT_1 NUMBER(18, 4),
    SUPPORT_2 NUMBER(18, 4),
    
    -- Metadata
    SOURCE VARCHAR(50) DEFAULT 'calculated' COMMENT 'Data source: calculated, talib, tradingview',
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    
    -- Constraints
    CONSTRAINT UNIQUE_TICKER_DATE_TECH UNIQUE (TICKER, DATE)
)
COMMENT='Technical indicators calculated from price data';

-- Create indexes
CREATE INDEX IF NOT EXISTS IDX_TECHNICALS_TICKER ON TECHNICALS_RAW(TICKER);
CREATE INDEX IF NOT EXISTS IDX_TECHNICALS_DATE ON TECHNICALS_RAW(DATE);
CREATE INDEX IF NOT EXISTS IDX_TECHNICALS_CREATED_AT ON TECHNICALS_RAW(CREATED_AT);

-- ============================================
-- Create or Replace Schemas for dbt
-- ============================================

-- Staging schema for dbt views
CREATE SCHEMA IF NOT EXISTS STAGING
    COMMENT='dbt staging layer - cleaned and standardized data';

-- Marts schema for dbt tables
CREATE SCHEMA IF NOT EXISTS MARTS
    COMMENT='dbt marts layer - feature engineering and business logic';

-- ============================================
-- Verification Queries
-- ============================================

-- Show all tables
SHOW TABLES IN SCHEMA PUBLIC;

-- Check table info
SELECT 
    TABLE_CATALOG,
    TABLE_SCHEMA,
    TABLE_NAME,
    ROW_COUNT,
    CREATED AS CREATE_TIME,
    COMMENT
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'PUBLIC'
  AND TABLE_NAME IN ('PRICES_DAILY', 'FUNDAMENTALS_RAW', 'SENTIMENT_MSGS', 'TECHNICALS_RAW')
ORDER BY TABLE_NAME;

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA PUBLIC TO ROLE AIRBYTE_ROLE;
-- GRANT SELECT ON ALL TABLES IN SCHEMA PUBLIC TO ROLE DBT_ROLE;
-- GRANT ALL ON SCHEMA STAGING TO ROLE DBT_ROLE;
-- GRANT ALL ON SCHEMA MARTS TO ROLE DBT_ROLE;
