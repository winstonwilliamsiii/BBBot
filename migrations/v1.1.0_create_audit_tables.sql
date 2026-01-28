-- Migration v1.1.0: Create Audit Tables for Compliance & Monitoring
-- Purpose: Create audit log tables for data ingestion, bot decisions, and ML experiments
-- Database: bentley_bot (mansa_quant), mlflow_db
-- Date: January 27, 2026
-- Author: Bentley Bot System

-- ===================================================================
-- 1. INGESTION_LOG TABLE - Data Connector Audit Trail
-- ===================================================================
-- Purpose: Track all data ingestion events (yFinance, Plaid, Alpaca, etc.)
-- Stores: Which data was fetched, when, by whom, and if it succeeded
-- Compliance: SOX 404, audit trail for data quality monitoring

USE bentley_bot;

CREATE TABLE IF NOT EXISTS ingestion_log (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique audit entry ID',
    
    -- Connector Information
    connector_type VARCHAR(50) NOT NULL COMMENT 'Data source: yfinance, plaid, alpaca, tradingview',
    user_id INT COMMENT 'User who triggered the ingestion (if applicable)',
    source_system VARCHAR(100) COMMENT 'Specific system: Alpha Vantage, Yahoo Finance, etc.',
    
    -- Ingestion Details
    tickers VARCHAR(1000) COMMENT 'Comma-separated list of tickers fetched',
    record_count INT NOT NULL COMMENT 'Number of records ingested',
    success_flag BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Whether ingestion succeeded',
    
    -- Error Tracking
    error_code VARCHAR(50) COMMENT 'Error code if failed (API_TIMEOUT, RATE_LIMIT, etc.)',
    error_message TEXT COMMENT 'Human-readable error message',
    
    -- Performance Metrics
    sync_duration_ms INT COMMENT 'How long ingestion took in milliseconds',
    start_time TIMESTAMP COMMENT 'When ingestion started',
    end_time TIMESTAMP COMMENT 'When ingestion ended',
    
    -- Audit Fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When this audit entry was created',
    ip_address VARCHAR(45) COMMENT 'Source IP if applicable',
    
    -- Indexes for fast querying
    INDEX idx_connector_type (connector_type),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_success_flag (success_flag),
    INDEX idx_date_range (created_at, connector_type),
    
    COMMENT='Audit trail for data ingestion operations across all connectors'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ===================================================================
-- 2. BOT_DECISION_AUDIT TABLE - Trading Decision Audit Trail
-- ===================================================================
-- Purpose: Track all trading decisions made by bots
-- Stores: What decision was made, why, confidence level, and whether it executed
-- Compliance: MiFID II (Markets in Financial Instruments Directive), decision audit for regulators

CREATE TABLE IF NOT EXISTS bot_decision_audit (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique decision audit ID',
    
    -- Bot & Decision Information
    bot_id VARCHAR(100) NOT NULL COMMENT 'Bot that made the decision: demo_bot, staging_bot, bentley_bot',
    decision_type ENUM('BUY', 'SELL', 'HOLD') NOT NULL COMMENT 'Type of decision made',
    ticker VARCHAR(10) NOT NULL COMMENT 'Stock ticker symbol (e.g., AAPL, GOOGL)',
    
    -- Decision Details
    quantity INT COMMENT 'Number of shares for BUY/SELL (NULL for HOLD)',
    target_price DECIMAL(15, 4) COMMENT 'Target price for order execution',
    
    -- Decision Rationale
    reason TEXT NOT NULL COMMENT 'Human-readable reason for decision',
    
    -- ML & Signal Inputs
    ml_confidence FLOAT COMMENT 'ML model confidence (0.0 - 1.0)',
    rsi_value FLOAT COMMENT 'RSI indicator value (0-100)',
    macd_value FLOAT COMMENT 'MACD indicator value',
    sentiment_score FLOAT COMMENT 'Sentiment analysis score (-1.0 to 1.0)',
    
    -- Execution Information
    executed_flag BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Whether decision was executed',
    execution_time TIMESTAMP NULL COMMENT 'When decision was executed',
    execution_price DECIMAL(15, 4) COMMENT 'Actual execution price',
    execution_qty INT COMMENT 'Actual executed quantity',
    
    -- Post-Execution Results
    result_status ENUM('SUCCESS', 'PARTIAL', 'FAILED', 'PENDING', NULL) COMMENT 'Execution outcome',
    result_message TEXT COMMENT 'Details about execution result',
    realized_pnl DECIMAL(15, 2) COMMENT 'Realized profit/loss if executed',
    
    -- Audit Fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Decision timestamp',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes for analysis
    INDEX idx_bot_id (bot_id),
    INDEX idx_ticker (ticker),
    INDEX idx_decision_type (decision_type),
    INDEX idx_created_at (created_at),
    INDEX idx_bot_date (bot_id, created_at),
    INDEX idx_executed (executed_flag),
    INDEX idx_sentiment (sentiment_score),
    
    COMMENT='Audit trail for all bot trading decisions with full rationale and execution details'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ===================================================================
-- 3. SENTIMENT_MSGS TABLE - Social Sentiment Data Audit
-- ===================================================================
-- Purpose: Track sentiment messages and scores used in decision-making
-- Stores: Social media posts, news sentiment, sentiment scores
-- Compliance: Decision traceability for trading algorithms

CREATE TABLE IF NOT EXISTS sentiment_msgs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique sentiment message ID',
    
    -- Message Metadata
    ticker VARCHAR(10) NOT NULL COMMENT 'Stock ticker this sentiment relates to',
    message TEXT NOT NULL COMMENT 'Original sentiment message/post',
    source VARCHAR(50) NOT NULL COMMENT 'Source: Twitter, Reddit, StockTwits, NewsAPI, etc.',
    
    -- Sentiment Analysis
    sentiment_score FLOAT NOT NULL COMMENT 'Calculated sentiment (-1.0 to 1.0)',
    confidence FLOAT COMMENT 'Confidence of sentiment analysis (0.0 to 1.0)',
    sentiment_label VARCHAR(20) COMMENT 'Label: bullish, bearish, neutral',
    
    -- Message Details
    author VARCHAR(255) COMMENT 'Author of message if applicable',
    message_url VARCHAR(500) COMMENT 'URL to original message',
    engagement_score INT COMMENT 'Likes, retweets, etc. (if applicable)',
    
    -- Audit Fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When sentiment was posted',
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When we ingested this message',
    
    -- Indexes
    INDEX idx_ticker (ticker),
    INDEX idx_created_at (created_at),
    INDEX idx_source (source),
    INDEX idx_sentiment_score (sentiment_score),
    INDEX idx_ticker_time (ticker, created_at),
    
    COMMENT='Social sentiment messages and their analyzed sentiment scores for decision support'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ===================================================================
-- 4. SENTIMENT_DAILY_AGGREGATE - Daily Sentiment Summary
-- ===================================================================
-- Purpose: Pre-aggregated daily sentiment for faster lookups
-- Stores: Daily average sentiment, bullish/bearish count
-- Performance: Faster than aggregating sentiment_msgs at query time

CREATE TABLE IF NOT EXISTS sentiment_daily (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    date_at DATE NOT NULL COMMENT 'Date of aggregation',
    ticker VARCHAR(10) NOT NULL COMMENT 'Stock ticker',
    
    -- Sentiment Aggregates
    avg_sentiment FLOAT COMMENT 'Average sentiment for the day',
    median_sentiment FLOAT COMMENT 'Median sentiment',
    message_count INT NOT NULL DEFAULT 0 COMMENT 'Total messages received',
    
    -- Sentiment Distribution
    bullish_count INT NOT NULL DEFAULT 0 COMMENT 'Messages with positive sentiment',
    bearish_count INT NOT NULL DEFAULT 0 COMMENT 'Messages with negative sentiment',
    neutral_count INT NOT NULL DEFAULT 0 COMMENT 'Messages with neutral sentiment',
    
    -- Aggregation Details
    data_sources VARCHAR(200) COMMENT 'Comma-separated sources included',
    aggregated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_date_ticker (date_at, ticker),
    INDEX idx_date (date_at),
    INDEX idx_ticker (ticker),
    INDEX idx_avg_sentiment (avg_sentiment),
    
    COMMENT='Pre-aggregated daily sentiment data for efficient querying'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ===================================================================
-- 5. BOT_PERFORMANCE_METRICS - Daily P&L and Performance Tracking
-- ===================================================================
-- Purpose: Track daily performance metrics and P&L for each bot
-- Stores: Profit/loss, Sharpe ratio, max drawdown, win rate, etc.
-- Compliance: Performance monitoring and regulatory reporting

CREATE TABLE IF NOT EXISTS bot_performance_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique metric entry ID',
    
    -- Bot & Date
    bot_id VARCHAR(100) NOT NULL COMMENT 'Bot ID',
    date_at DATE NOT NULL COMMENT 'Metric date',
    
    -- Performance Metrics
    daily_pnl DECIMAL(15, 2) COMMENT 'Daily profit/loss',
    cumulative_pnl DECIMAL(15, 2) COMMENT 'Cumulative profit/loss to date',
    
    -- Risk Metrics
    sharpe_ratio FLOAT COMMENT 'Sharpe ratio (risk-adjusted return)',
    max_drawdown FLOAT COMMENT 'Maximum drawdown from peak',
    volatility FLOAT COMMENT 'Daily volatility',
    
    -- Trade Metrics
    total_trades INT COMMENT 'Total trades executed',
    winning_trades INT COMMENT 'Number of winning trades',
    losing_trades INT COMMENT 'Number of losing trades',
    win_rate FLOAT COMMENT 'Percentage of winning trades',
    
    -- Position Metrics
    avg_position_size DECIMAL(15, 2) COMMENT 'Average position size',
    portfolio_value DECIMAL(15, 2) COMMENT 'Total portfolio value',
    cash_balance DECIMAL(15, 2) COMMENT 'Available cash',
    
    -- Meta Information
    status VARCHAR(50) COMMENT 'Bot status: running, paused, error',
    notes TEXT COMMENT 'Additional notes about the day',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_bot_date (bot_id, date_at),
    INDEX idx_bot_id (bot_id),
    INDEX idx_date (date_at),
    INDEX idx_daily_pnl (daily_pnl),
    INDEX idx_sharpe (sharpe_ratio),
    
    COMMENT='Daily performance metrics for monitoring bot profitability'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ===================================================================
-- Now switch to mlflow_db for ML experiment audit
-- ===================================================================

USE mlflow_db;

-- ===================================================================
-- 6. EXPERIMENT_AUDIT - MLflow Experiment Tracking Audit
-- ===================================================================
-- Purpose: Audit trail for ML experiments and model training
-- Stores: Experiment parameters, metrics, accuracy, duration
-- Compliance: Model governance and reproducibility

CREATE TABLE IF NOT EXISTS experiment_audit (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Audit entry ID',
    
    -- Experiment Information
    experiment_id INT NOT NULL COMMENT 'MLflow experiment ID',
    experiment_name VARCHAR(255) NOT NULL COMMENT 'Experiment name',
    run_id VARCHAR(100) NOT NULL COMMENT 'MLflow run ID (unique per training)',
    
    -- Model Information
    model_type VARCHAR(100) NOT NULL COMMENT 'Type: RandomForest, LSTM, XGBoost, etc.',
    model_version INT COMMENT 'Model version number',
    
    -- Performance Metrics
    accuracy FLOAT COMMENT 'Model accuracy on test set',
    f1_score FLOAT COMMENT 'F1 score for classification',
    precision FLOAT COMMENT 'Precision metric',
    recall FLOAT COMMENT 'Recall metric',
    auc FLOAT COMMENT 'AUC score',
    
    -- Backtest Results
    backtest_return FLOAT COMMENT 'Returns in backtest period',
    backtest_sharpe FLOAT COMMENT 'Sharpe ratio in backtest',
    backtest_max_dd FLOAT COMMENT 'Max drawdown in backtest',
    
    -- Training Details
    training_duration_ms INT COMMENT 'Training time in milliseconds',
    dataset_size INT COMMENT 'Number of training samples',
    feature_count INT COMMENT 'Number of features used',
    
    -- Parameters (stored as JSON)
    hyperparameters JSON COMMENT 'Model hyperparameters',
    training_config JSON COMMENT 'Training configuration',
    
    -- User & Audit
    user_id INT COMMENT 'User who ran experiment',
    git_commit VARCHAR(100) COMMENT 'Git commit hash',
    environment VARCHAR(50) COMMENT 'Environment: demo, staging, prod',
    
    -- Status
    status ENUM('SUCCESS', 'FAILED', 'IN_PROGRESS') NOT NULL DEFAULT 'IN_PROGRESS',
    error_message TEXT COMMENT 'Error message if failed',
    
    -- Timestamps
    started_at TIMESTAMP COMMENT 'When training started',
    completed_at TIMESTAMP COMMENT 'When training completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_experiment_id (experiment_id),
    INDEX idx_run_id (run_id),
    INDEX idx_model_type (model_type),
    INDEX idx_user_id (user_id),
    INDEX idx_environment (environment),
    INDEX idx_accuracy (accuracy),
    INDEX idx_created_at (created_at),
    
    COMMENT='Audit trail for ML experiment training and validation'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ===================================================================
-- Back to bentley_bot for final setup
-- ===================================================================

USE bentley_bot;

-- Create views for easy querying

-- View: Recent Ingestion Errors
CREATE OR REPLACE VIEW recent_ingestion_errors AS
SELECT 
    connector_type,
    COUNT(*) as error_count,
    MAX(created_at) as latest_error,
    error_code,
    error_message
FROM ingestion_log
WHERE success_flag = FALSE
AND created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
GROUP BY connector_type, error_code
ORDER BY error_count DESC;

-- View: Daily Sentiment Summary by Ticker
CREATE OR REPLACE VIEW daily_sentiment_summary AS
SELECT 
    date_at,
    ticker,
    avg_sentiment,
    bullish_count,
    bearish_count,
    neutral_count,
    message_count,
    CASE 
        WHEN avg_sentiment > 0.3 THEN 'Bullish'
        WHEN avg_sentiment < -0.3 THEN 'Bearish'
        ELSE 'Neutral'
    END as sentiment_direction
FROM sentiment_daily
ORDER BY date_at DESC, ticker;

-- View: Bot Decision Success Rate
CREATE OR REPLACE VIEW bot_decision_metrics AS
SELECT 
    bot_id,
    COUNT(*) as total_decisions,
    SUM(CASE WHEN executed_flag = TRUE THEN 1 ELSE 0 END) as executed_count,
    SUM(CASE WHEN result_status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_executions,
    AVG(ml_confidence) as avg_confidence,
    AVG(CASE WHEN realized_pnl IS NOT NULL THEN realized_pnl ELSE 0 END) as avg_pnl
FROM bot_decision_audit
GROUP BY bot_id;

-- ===================================================================
-- Audit Log Summary - Document what was created
-- ===================================================================

-- Create migration history table
CREATE TABLE IF NOT EXISTS migration_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    migration_version VARCHAR(50) NOT NULL,
    migration_name VARCHAR(255),
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('SUCCESS', 'FAILED') DEFAULT 'SUCCESS',
    notes TEXT,
    UNIQUE KEY unique_version (migration_version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Record this migration
INSERT INTO migration_history (migration_version, migration_name, notes) VALUES (
    'v1.1.0',
    'Create Audit Tables for Compliance & Monitoring',
    'Created ingestion_log, bot_decision_audit, sentiment_msgs, sentiment_daily, bot_performance_metrics, and experiment_audit tables'
);

-- Display summary
SELECT '=== AUDIT TABLE MIGRATION COMPLETE ===' as Status;
SELECT CONCAT('Tables created in bentley_bot: ', 
    (SELECT COUNT(*) FROM information_schema.TABLES 
     WHERE TABLE_SCHEMA = 'bentley_bot' AND TABLE_NAME IN 
     ('ingestion_log', 'bot_decision_audit', 'sentiment_msgs', 'sentiment_daily', 'bot_performance_metrics'))
) as CreatedTables;

SHOW TABLES FROM bentley_bot LIKE '%log%';
SHOW TABLES FROM bentley_bot LIKE '%sentiment%';
SHOW TABLES FROM bentley_bot LIKE '%metrics%';
SHOW TABLES FROM mlflow_db LIKE '%audit%';
