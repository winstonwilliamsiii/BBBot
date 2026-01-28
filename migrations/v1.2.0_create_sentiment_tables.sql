-- Migration v1.2.0: Create Sentiment Pipeline Tables
-- Purpose: Create tables for storing social sentiment data pipeline
-- Database: bbbot1
-- Date: January 27, 2026
-- Author: Bentley Bot System

USE bbbot1;

-- ===================================================================
-- 1. SENTIMENT_MSGS - Raw Sentiment Messages Table
-- ===================================================================
-- Purpose: Store individual sentiment messages from social media/news
-- Stores: Twitter posts, Reddit comments, StockTwits messages, news sentiment
-- Indexing: Fast lookup by ticker and date for decision correlation

CREATE TABLE IF NOT EXISTS sentiment_msgs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique message ID',
    
    -- Message Identification
    source_id VARCHAR(255) UNIQUE COMMENT 'Source ID (e.g., Tweet ID, Reddit post ID)',
    
    -- Ticker Association
    ticker VARCHAR(10) NOT NULL COMMENT 'Stock ticker (e.g., AAPL, GOOGL)',
    
    -- Message Content
    message TEXT NOT NULL COMMENT 'Original message/post text',
    message_url VARCHAR(500) COMMENT 'URL to original message',
    
    -- Source Information
    source VARCHAR(50) NOT NULL COMMENT 'Source: Twitter, Reddit, StockTwits, NewsAPI, Seeking Alpha',
    author VARCHAR(255) COMMENT 'Author/handle of message',
    author_followers INT COMMENT 'Follower count (influence measure)',
    
    -- Sentiment Analysis
    sentiment_score FLOAT NOT NULL COMMENT 'Sentiment score: -1.0 (bearish) to 1.0 (bullish)',
    confidence FLOAT COMMENT 'Confidence of sentiment analysis (0.0-1.0)',
    sentiment_label VARCHAR(20) COMMENT 'Label: bullish, bearish, neutral, mixed',
    
    -- Engagement Metrics
    engagement_score INT DEFAULT 0 COMMENT 'Likes/retweets/upvotes (social amplification)',
    reply_count INT DEFAULT 0 COMMENT 'Number of replies/comments',
    share_count INT DEFAULT 0 COMMENT 'Number of shares/retweets',
    
    -- Processing Metadata
    is_processed BOOLEAN DEFAULT TRUE COMMENT 'Whether sentiment was calculated',
    processing_model VARCHAR(100) COMMENT 'Which NLP model calculated sentiment',
    
    -- Timestamps
    message_timestamp TIMESTAMP COMMENT 'When message was originally posted',
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When we fetched this message',
    
    -- Indexes for performance
    INDEX idx_ticker (ticker),
    INDEX idx_source (source),
    INDEX idx_message_timestamp (message_timestamp),
    INDEX idx_ticker_time (ticker, message_timestamp),
    INDEX idx_sentiment_score (sentiment_score),
    INDEX idx_source_ticker_time (source, ticker, message_timestamp),
    
    COMMENT='Raw sentiment messages from social media and news sources'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ===================================================================
-- 2. SENTIMENT_DAILY - Daily Sentiment Aggregates
-- ===================================================================
-- Purpose: Pre-aggregated daily sentiment for faster analysis
-- Stores: Daily average sentiment, distribution of bullish/bearish/neutral
-- Performance: Pre-computed aggregates avoid slow GROUP BY at query time

CREATE TABLE IF NOT EXISTS sentiment_daily (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Aggregate ID',
    
    -- Time & Ticker
    date_at DATE NOT NULL COMMENT 'Date of aggregation',
    ticker VARCHAR(10) NOT NULL COMMENT 'Stock ticker',
    
    -- Aggregate Statistics
    avg_sentiment FLOAT COMMENT 'Average sentiment for the day (-1 to 1)',
    median_sentiment FLOAT COMMENT 'Median sentiment',
    min_sentiment FLOAT COMMENT 'Minimum sentiment',
    max_sentiment FLOAT COMMENT 'Maximum sentiment',
    std_dev FLOAT COMMENT 'Standard deviation of sentiment',
    
    -- Sentiment Distribution
    total_messages INT NOT NULL DEFAULT 0 COMMENT 'Total messages received',
    bullish_count INT NOT NULL DEFAULT 0 COMMENT 'Messages with bullish sentiment (>0.2)',
    bearish_count INT NOT NULL DEFAULT 0 COMMENT 'Messages with bearish sentiment (<-0.2)',
    neutral_count INT NOT NULL DEFAULT 0 COMMENT 'Messages with neutral sentiment (-0.2 to 0.2)',
    
    -- Weighted Sentiment (by engagement)
    weighted_sentiment FLOAT COMMENT 'Sentiment weighted by engagement/followers',
    
    -- Source Breakdown
    data_sources VARCHAR(500) COMMENT 'Comma-separated source types included',
    source_counts JSON COMMENT 'Count by source as JSON: {"Twitter": 45, "Reddit": 12}',
    
    -- Aggregation Metadata
    aggregated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When this aggregate was calculated',
    aggregated_by VARCHAR(100) COMMENT 'Process that created this aggregate',
    
    -- Unique constraint to prevent duplicate dates
    UNIQUE KEY unique_date_ticker (date_at, ticker),
    
    -- Indexes for queries
    INDEX idx_date (date_at),
    INDEX idx_ticker (ticker),
    INDEX idx_avg_sentiment (avg_sentiment),
    INDEX idx_date_ticker (date_at, ticker),
    
    COMMENT='Pre-computed daily sentiment aggregates for efficient querying'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ===================================================================
-- 3. SENTIMENT_HOURLY - Hourly Sentiment Tracking (Optional)
-- ===================================================================
-- Purpose: Track sentiment changes throughout the day (high granularity)
-- Stores: Hourly sentiment snapshots for intraday analysis
-- Use Case: Detect rapid sentiment shifts for trading signals

CREATE TABLE IF NOT EXISTS sentiment_hourly (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Time & Ticker
    hour_at DATETIME NOT NULL COMMENT 'Hourly bucket timestamp',
    ticker VARCHAR(10) NOT NULL COMMENT 'Stock ticker',
    
    -- Hourly Statistics
    avg_sentiment FLOAT COMMENT 'Average sentiment for the hour',
    message_count INT NOT NULL DEFAULT 0 COMMENT 'Messages in this hour',
    bullish_count INT NOT NULL DEFAULT 0,
    bearish_count INT NOT NULL DEFAULT 0,
    neutral_count INT NOT NULL DEFAULT 0,
    
    -- Sentiment Momentum
    sentiment_change FLOAT COMMENT 'Change from previous hour',
    acceleration FLOAT COMMENT 'Rate of change acceleration',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_hour_ticker (hour_at, ticker),
    INDEX idx_hour (hour_at),
    INDEX idx_ticker (ticker),
    INDEX idx_sentiment_change (sentiment_change),
    
    COMMENT='Hourly sentiment snapshots for intraday sentiment tracking'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ===================================================================
-- 4. SENTIMENT_KEYWORDS - Keyword Tracking for Sentiment
-- ===================================================================
-- Purpose: Track which keywords/terms drive sentiment changes
-- Stores: Keywords, their frequency, association with bullish/bearish sentiment
-- Use Case: Identify important topics affecting stock sentiment

CREATE TABLE IF NOT EXISTS sentiment_keywords (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Keyword Information
    ticker VARCHAR(10) NOT NULL COMMENT 'Stock ticker this keyword relates to',
    keyword VARCHAR(100) NOT NULL COMMENT 'The keyword/phrase',
    keyword_category VARCHAR(50) COMMENT 'Category: earnings, product, scandal, patent, etc.',
    
    -- Keyword Metrics
    frequency INT DEFAULT 0 COMMENT 'How often mentioned',
    avg_sentiment FLOAT COMMENT 'Average sentiment when mentioned',
    
    -- Temporal Info
    first_seen TIMESTAMP COMMENT 'First time keyword was mentioned',
    last_seen TIMESTAMP COMMENT 'Most recent mention',
    
    UNIQUE KEY unique_ticker_keyword (ticker, keyword),
    INDEX idx_ticker (ticker),
    INDEX idx_keyword (keyword),
    INDEX idx_keyword_category (keyword_category),
    INDEX idx_frequency (frequency),
    
    COMMENT='Track keywords and their correlation with sentiment changes'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ===================================================================
-- 5. SENTIMENT_CORRELATION - Correlations Between Tickers
-- ===================================================================
-- Purpose: Track how sentiment in one ticker affects related tickers
-- Stores: Correlation coefficients between sentiment of related tickers
-- Use Case: Identify sector-wide sentiment movements

CREATE TABLE IF NOT EXISTS sentiment_correlation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Ticker Pair
    ticker1 VARCHAR(10) NOT NULL COMMENT 'First ticker',
    ticker2 VARCHAR(10) NOT NULL COMMENT 'Second ticker',
    relationship VARCHAR(100) COMMENT 'Relationship: competitor, supplier, peer, etc.',
    
    -- Correlation Metrics
    sentiment_correlation FLOAT COMMENT 'Correlation coefficient of sentiment',
    lag_periods INT COMMENT 'Optimal lag for correlation (hours)',
    
    -- Date Range
    from_date DATE COMMENT 'Start of correlation period',
    to_date DATE COMMENT 'End of correlation period',
    
    -- Statistical Significance
    sample_size INT COMMENT 'Number of data points in correlation',
    p_value FLOAT COMMENT 'Statistical p-value',
    
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_ticker_pair (ticker1, ticker2),
    INDEX idx_ticker1 (ticker1),
    INDEX idx_ticker2 (ticker2),
    INDEX idx_correlation (sentiment_correlation),
    
    COMMENT='Track correlations in sentiment between related tickers'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ===================================================================
-- 6. SENTIMENT_FEED_SOURCES - Manage Sentiment Data Sources
-- ===================================================================
-- Purpose: Track active sentiment data sources and their status
-- Stores: API endpoints, rate limits, health status
-- Use Case: Monitor data pipeline health

CREATE TABLE IF NOT EXISTS sentiment_feed_sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Source Configuration
    source_name VARCHAR(100) NOT NULL UNIQUE COMMENT 'Data source name',
    source_type VARCHAR(50) COMMENT 'Type: API, RSS, WebScrape, etc.',
    endpoint_url VARCHAR(500) COMMENT 'API endpoint or URL',
    api_key_name VARCHAR(100) COMMENT 'Name of environment variable for API key',
    
    -- Rate Limits
    rate_limit_per_hour INT COMMENT 'Max requests per hour',
    current_hour_calls INT DEFAULT 0 COMMENT 'Calls made this hour',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Whether source is actively fetching',
    last_successful_fetch TIMESTAMP COMMENT 'Last successful data fetch',
    last_error TIMESTAMP COMMENT 'When last error occurred',
    error_message TEXT COMMENT 'Most recent error',
    consecutive_errors INT DEFAULT 0 COMMENT 'Count of consecutive errors',
    
    -- Configuration
    fetch_interval_minutes INT COMMENT 'How often to fetch (in minutes)',
    retry_on_failure BOOLEAN DEFAULT TRUE COMMENT 'Whether to retry on failure',
    max_retries INT DEFAULT 3,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_active (is_active),
    INDEX idx_last_fetch (last_successful_fetch),
    
    COMMENT='Configuration and status of sentiment data sources'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ===================================================================
-- VIEWS FOR SENTIMENT ANALYSIS
-- ===================================================================

-- View: Real-time Sentiment Score
CREATE OR REPLACE VIEW current_sentiment_by_ticker AS
SELECT 
    ticker,
    (SELECT avg_sentiment FROM sentiment_daily 
     WHERE ticker = sd.ticker 
     ORDER BY date_at DESC LIMIT 1) as latest_sentiment,
    (SELECT message_count FROM sentiment_daily 
     WHERE ticker = sd.ticker 
     ORDER BY date_at DESC LIMIT 1) as today_messages,
    (SELECT bullish_count FROM sentiment_daily 
     WHERE ticker = sd.ticker 
     ORDER BY date_at DESC LIMIT 1) as bullish_today,
    (SELECT bearish_count FROM sentiment_daily 
     WHERE ticker = sd.ticker 
     ORDER BY date_at DESC LIMIT 1) as bearish_today
FROM (SELECT DISTINCT ticker FROM sentiment_daily) sd
ORDER BY latest_sentiment DESC;

-- View: Sentiment Trend (7-day moving average)
CREATE OR REPLACE VIEW sentiment_trend_7d AS
SELECT 
    ticker,
    DATE_TRUNC(DATE_TRUNC(date_at,'day'), INTERVAL 7 DAY) as week_start,
    AVG(avg_sentiment) as weekly_avg_sentiment,
    SUM(total_messages) as week_total_messages,
    COUNT(DISTINCT date_at) as days_with_data
FROM sentiment_daily
WHERE date_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY ticker, week_start
ORDER BY week_start DESC;

-- View: Sentiment Extremes (Most Bullish/Bearish)
CREATE OR REPLACE VIEW sentiment_extremes AS
SELECT 
    'Bullish' as direction,
    ticker,
    date_at,
    avg_sentiment,
    message_count
FROM sentiment_daily
WHERE date_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY avg_sentiment DESC
LIMIT 10
UNION ALL
SELECT 
    'Bearish' as direction,
    ticker,
    date_at,
    avg_sentiment,
    message_count
FROM sentiment_daily
WHERE date_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY avg_sentiment ASC
LIMIT 10;


-- ===================================================================
-- INSERT SEED DATA FOR TESTING
-- ===================================================================

INSERT INTO sentiment_feed_sources (source_name, source_type, endpoint_url, api_key_name, rate_limit_per_hour, fetch_interval_minutes, is_active)
VALUES 
    ('Twitter_API', 'API', 'https://api.twitter.com/2/tweets/search/recent', 'TWITTER_API_KEY', 300, 15, TRUE),
    ('RedditAPI', 'API', 'https://oauth.reddit.com', 'REDDIT_API_KEY', 1000, 30, TRUE),
    ('NewsAPI', 'API', 'https://newsapi.org/v2/everything', 'NEWS_API_KEY', 100, 60, TRUE),
    ('StockTwits', 'API', 'https://api.stocktwits.com/api/v2', 'STOCKTWITS_API_KEY', 500, 30, TRUE);


-- ===================================================================
-- MIGRATION COMPLETE
-- ===================================================================

-- Record migration
INSERT INTO bbbot1.migration_history (migration_version, migration_name, notes) VALUES (
    'v1.2.0',
    'Create Sentiment Pipeline Tables',
    'Created sentiment_msgs, sentiment_daily, sentiment_hourly, sentiment_keywords, sentiment_correlation, sentiment_feed_sources'
);

SELECT '=== SENTIMENT TABLES MIGRATION COMPLETE ===' as Status;
SHOW TABLES FROM bbbot1 LIKE 'sentiment%';
