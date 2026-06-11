-- Migration: Cygnus bot schema enhancements
-- Date: 2026-05-06
-- Purpose: Ensure Cygnus bot metrics and trades appear in dashboard overview/performance queries.

USE bbbot1;

-- Add bot_name support for explicit bot-level reporting in legacy metrics table.
ALTER TABLE performance_metrics
    ADD COLUMN IF NOT EXISTS bot_name VARCHAR(50) NULL AFTER strategy;

ALTER TABLE performance_metrics
    ADD INDEX IF NOT EXISTS idx_perf_bot_name (bot_name),
    ADD INDEX IF NOT EXISTS idx_perf_bot_strategy_date (bot_name, strategy, date);

-- Add bot_name/trade_mode to trade history for consistent cross-bot filtering.
ALTER TABLE trades_history
    ADD COLUMN IF NOT EXISTS bot_name VARCHAR(50) NULL AFTER strategy,
    ADD COLUMN IF NOT EXISTS trade_mode VARCHAR(12) NULL AFTER bot_name;

ALTER TABLE trades_history
    ADD INDEX IF NOT EXISTS idx_trades_bot_name (bot_name),
    ADD INDEX IF NOT EXISTS idx_trades_mode (trade_mode),
    ADD INDEX IF NOT EXISTS idx_trades_bot_ts (bot_name, timestamp);

-- Optional Cygnus feature table for pair analytics snapshots.
CREATE TABLE IF NOT EXISTS cygnus_pair_analytics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    pair_symbol_x VARCHAR(16) NOT NULL,
    pair_symbol_y VARCHAR(16) NOT NULL,
    hedge_ratio DOUBLE,
    zscore DOUBLE,
    bollinger_bandwidth DOUBLE,
    smi DOUBLE,
    smi_signal DOUBLE,
    rsi_divergence DOUBLE,
    cointegration_pvalue DOUBLE,
    nlp_sentiment DOUBLE,
    siamese_similarity DOUBLE,
    signal_action VARCHAR(16) NOT NULL,
    signal_bias VARCHAR(16) NOT NULL,
    composite_score DOUBLE,
    mode VARCHAR(12) NOT NULL DEFAULT 'paper',
    run_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cygnus_pair_time (pair_symbol_x, pair_symbol_y, run_timestamp),
    INDEX idx_cygnus_signal (signal_action, signal_bias)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
