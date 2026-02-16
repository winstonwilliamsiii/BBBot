-- Migration: Prediction Analytics Tables
-- Database: Bentley_Bot
-- Schema: mansa_quant
-- Purpose: Add sentiment + probability analysis for Polymarket/Kalshi feeds
-- Date: 2026-01-26

USE Bentley_Bot;

-- Probability engine outputs
CREATE TABLE IF NOT EXISTS mansa_quant.prediction_probabilities (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contract_id VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL,         -- 'Kalshi' or 'Polymarket'
    implied_probability DECIMAL(5,2) NOT NULL, -- 0 to 100
    confidence_score DECIMAL(5,2),    -- model confidence
    rationale TEXT,              -- AI-generated explanation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_contract_id (contract_id),
    INDEX idx_source (source),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sentiment signals (Alphascope-style)
CREATE TABLE IF NOT EXISTS mansa_quant.sentiment_signals (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contract_id VARCHAR(100) NOT NULL,
    sentiment_score DECIMAL(5,2) NOT NULL, -- -1 to +1
    signal_strength VARCHAR(50) NOT NULL,  -- 'weak', 'moderate', 'strong'
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_contract_id (contract_id),
    INDEX idx_source (source),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Composite view for prediction + sentiment analysis
CREATE TABLE IF NOT EXISTS mansa_quant.prediction_sentiment_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contract_id VARCHAR(100) NOT NULL,
    prediction_id BIGINT,
    sentiment_id BIGINT,
    combined_score DECIMAL(5,2),  -- Weighted combination of probability + sentiment
    recommendation VARCHAR(50),    -- 'BUY', 'SELL', 'HOLD', 'RESEARCH'
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (prediction_id) REFERENCES mansa_quant.prediction_probabilities(id) ON DELETE SET NULL,
    FOREIGN KEY (sentiment_id) REFERENCES mansa_quant.sentiment_signals(id) ON DELETE SET NULL,
    INDEX idx_contract_id (contract_id),
    INDEX idx_recommendation (recommendation)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- INGESTION LAYER - Airbyte Connectors
-- ============================================================================

-- Event Contracts - Normalized feed from Polymarket + Kalshi
CREATE TABLE IF NOT EXISTS mansa_quant.event_contracts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contract_id VARCHAR(100) NOT NULL UNIQUE,
    contract_name VARCHAR(500) NOT NULL,
    description TEXT,
    source VARCHAR(50) NOT NULL,          -- 'Polymarket' or 'Kalshi'
    source_connector VARCHAR(100),        -- Airbyte connector name (e.g., 'polymarket-gamma', 'kalshi-websocket')
    category VARCHAR(100),                -- Event category (e.g., 'politics', 'markets', 'sports')
    resolution_date DATETIME,
    status VARCHAR(50),                   -- 'OPEN', 'RESOLVED', 'CANCELLED'
    yes_price DECIMAL(5,4),               -- Current YES price
    no_price DECIMAL(5,4),                -- Current NO price
    volume_24h DECIMAL(15,2),             -- 24-hour trading volume
    liquidity_usd DECIMAL(15,2),          -- Total liquidity in USD
    external_data_source VARCHAR(200),    -- External reference (e.g., Kalshi API URL)
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_source_contract (source, contract_id),
    INDEX idx_status (status),
    INDEX idx_category (category),
    INDEX idx_source (source),
    INDEX idx_resolution_date (resolution_date),
    INDEX idx_last_synced (last_synced)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Orderbook Data - Real-time order book snapshots (Polymarket CLOB / Kalshi FIX)
CREATE TABLE IF NOT EXISTS mansa_quant.orderbook_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contract_id VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL,          -- 'Polymarket' or 'Kalshi'
    feed_type VARCHAR(50),                -- 'GAMMA' (Polymarket), 'CLOB' (Polymarket), 'FIX' (Kalshi), 'WebSocket'
    side VARCHAR(10),                     -- 'BID' or 'ASK'
    price DECIMAL(5,4) NOT NULL,          -- Order price
    quantity DECIMAL(15,2) NOT NULL,      -- Order quantity
    timestamp TIMESTAMP NOT NULL,         -- Market timestamp (not server time)
    raw_data JSON,                        -- Raw API response for debugging
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES mansa_quant.event_contracts(contract_id) ON DELETE CASCADE,
    INDEX idx_contract_id (contract_id),
    INDEX idx_source_timestamp (source, timestamp),
    INDEX idx_price_timestamp (price, timestamp),
    INDEX idx_ingestion_timestamp (ingestion_timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Ingestion Log - Track Airbyte sync operations
CREATE TABLE IF NOT EXISTS mansa_quant.ingestion_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    connector_name VARCHAR(100) NOT NULL,  -- 'polymarket-gamma', 'polymarket-clob', 'kalshi-websocket', 'kalshi-fix'
    source VARCHAR(50) NOT NULL,           -- 'Polymarket' or 'Kalshi'
    feed_type VARCHAR(50),                 -- 'GAMMA', 'CLOB', 'FIX', 'WebSocket'
    sync_status VARCHAR(50),               -- 'SUCCESS', 'FAILED', 'PARTIAL', 'RUNNING'
    records_synced INT,
    records_inserted INT,
    records_updated INT,
    error_message TEXT,
    sync_start_time DATETIME,
    sync_end_time DATETIME,
    duration_seconds INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_connector (connector_name),
    INDEX idx_sync_status (sync_status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- ANALYTICS LAYER - Enriched Data
-- ============================================================================

-- NLP Sentiment Analysis Results
CREATE TABLE IF NOT EXISTS mansa_quant.nlp_sentiment_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contract_id VARCHAR(100) NOT NULL,
    source_text TEXT NOT NULL,            -- Original text analyzed (tweet, Discord message, etc.)
    text_source VARCHAR(50),              -- 'twitter', 'discord', 'reddit', 'news'
    sentiment_score DECIMAL(5,2) NOT NULL, -- -1.0 to +1.0
    emotion_labels JSON,                  -- {"bullish": 0.85, "fear": 0.15, ...}
    confidence_score DECIMAL(5,2),        -- Model confidence (0-1)
    model_version VARCHAR(50),            -- NLP model used (e.g., 'sentiment-v2.1')
    author_influence_score DECIMAL(5,2),  -- Social influence weighting
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_contract_id (contract_id),
    INDEX idx_sentiment_score (sentiment_score),
    INDEX idx_text_source (text_source),
    INDEX idx_analyzed_at (analyzed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Probability Engine Inputs (for auditability)
CREATE TABLE IF NOT EXISTS mansa_quant.probability_engine_inputs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contract_id VARCHAR(100) NOT NULL,
    calculation_method VARCHAR(100),      -- 'lmsr', 'amm', 'orderbook_midpoint', etc.
    yes_price DECIMAL(5,4),
    no_price DECIMAL(5,4),
    order_volume_24h DECIMAL(15,2),
    sentiment_average DECIMAL(5,2),
    liquidity_usd DECIMAL(15,2),
    external_odds_source VARCHAR(200),    -- Reference odds from external sources
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_contract_id (contract_id),
    INDEX idx_calculated_at (calculated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Daily Aggregated Signals (for reporting + ML features)
CREATE TABLE IF NOT EXISTS mansa_quant.daily_signal_aggregates (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contract_id VARCHAR(100) NOT NULL,
    date_utc DATE NOT NULL,
    avg_implied_probability DECIMAL(5,2),
    avg_sentiment_score DECIMAL(5,2),
    sentiment_signal_strength VARCHAR(50),
    orderbook_volume_usd DECIMAL(15,2),
    price_volatility DECIMAL(5,4),
    tweet_volume_24h INT,
    nlp_sentiment_tweets DECIMAL(5,2),
    prediction_id BIGINT,
    sentiment_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES mansa_quant.event_contracts(contract_id) ON DELETE CASCADE,
    FOREIGN KEY (prediction_id) REFERENCES mansa_quant.prediction_probabilities(id) ON DELETE SET NULL,
    FOREIGN KEY (sentiment_id) REFERENCES mansa_quant.sentiment_signals(id) ON DELETE SET NULL,
    UNIQUE KEY uk_contract_date (contract_id, date_utc),
    INDEX idx_date (date_utc),
    INDEX idx_contract_id (contract_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- BOT CONSUMPTION LAYER - Trade Bot Logs & Decisions
-- ============================================================================

-- Passive Income Bot Logs - Track all bot trading decisions
CREATE TABLE IF NOT EXISTS mansa_quant.passive_income_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    bot_id VARCHAR(100) NOT NULL,
    contract_id VARCHAR(100) NOT NULL,
    prediction_id BIGINT,
    sentiment_id BIGINT,
    trade_action VARCHAR(50) NOT NULL,     -- 'BUY', 'SELL', 'HOLD', 'SKIP'
    position_size DECIMAL(15,2),
    entry_price DECIMAL(5,4),
    exit_price DECIMAL(5,4),
    profit_loss DECIMAL(15,2),
    profit_loss_pct DECIMAL(5,2),
    trade_rationale TEXT,                  -- Why bot made this decision
    implied_probability_at_entry DECIMAL(5,2),
    sentiment_score_at_entry DECIMAL(5,2),
    combined_signal_score DECIMAL(5,2),
    confidence_threshold_met BOOLEAN,
    broker VARCHAR(50),                    -- 'Polymarket', 'Kalshi', 'Alpaca', etc.
    trade_status VARCHAR(50),              -- 'EXECUTED', 'PENDING', 'FAILED', 'CANCELLED'
    execution_timestamp TIMESTAMP,
    resolution_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES mansa_quant.event_contracts(contract_id) ON DELETE CASCADE,
    FOREIGN KEY (prediction_id) REFERENCES mansa_quant.prediction_probabilities(id) ON DELETE SET NULL,
    FOREIGN KEY (sentiment_id) REFERENCES mansa_quant.sentiment_signals(id) ON DELETE SET NULL,
    INDEX idx_bot_id (bot_id),
    INDEX idx_contract_id (contract_id),
    INDEX idx_trade_action (trade_action),
    INDEX idx_trade_status (trade_status),
    INDEX idx_execution_timestamp (execution_timestamp),
    INDEX idx_profit_loss (profit_loss)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bot Decision Audit Trail
CREATE TABLE IF NOT EXISTS mansa_quant.bot_decision_audit (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    bot_id VARCHAR(100) NOT NULL,
    contract_id VARCHAR(100) NOT NULL,
    decision_type VARCHAR(50),             -- 'TRADE_SIGNAL', 'RISK_CHECK', 'THRESHOLD_EVALUATION'
    decision_result VARCHAR(50),
    input_data JSON,                       -- All inputs used for decision
    output_data JSON,                      -- Decision output
    execution_time_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_bot_id (bot_id),
    INDEX idx_decision_type (decision_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bot Performance Metrics (Daily Aggregates)
CREATE TABLE IF NOT EXISTS mansa_quant.bot_performance_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    bot_id VARCHAR(100) NOT NULL,
    date_utc DATE NOT NULL,
    total_trades INT DEFAULT 0,
    winning_trades INT DEFAULT 0,
    losing_trades INT DEFAULT 0,
    win_rate DECIMAL(5,2),
    total_profit_loss DECIMAL(15,2),
    avg_profit_per_trade DECIMAL(15,2),
    max_drawdown DECIMAL(15,2),
    sharpe_ratio DECIMAL(5,2),
    contracts_traded INT,
    avg_confidence_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_bot_date (bot_id, date_utc),
    INDEX idx_bot_id (bot_id),
    INDEX idx_date (date_utc),
    INDEX idx_win_rate (win_rate)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
