-- Rhea Bot Schema — Mansa ADI / Intra-Day Swing
-- Database: bbbot1
-- Apply with: mysql -h 127.0.0.1 -P 3307 -u root -p bbbot1 < sql_scripts/rhea_schema.sql

USE bbbot1;

-- ─── Signal Events ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rhea_signal_events (
    id                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    ticker              VARCHAR(16)     NOT NULL,
    signal_type         VARCHAR(32)     NOT NULL COMMENT 'BUY | SELL | HOLD | ALERT',
    composite_score     DECIMAL(6,4)    DEFAULT NULL,
    volume_score        DECIMAL(6,4)    DEFAULT NULL,
    adi_score           DECIMAL(6,4)    DEFAULT NULL,
    sentiment_score     DECIMAL(6,4)    DEFAULT NULL,
    quality_score       DECIMAL(6,4)    DEFAULT NULL,
    price_at_signal     DECIMAL(14,4)   DEFAULT NULL,
    strategy            VARCHAR(64)     NOT NULL DEFAULT 'ADI_Divergence_Swing',
    mlflow_run_id       VARCHAR(64)     DEFAULT NULL,
    airflow_run_id      VARCHAR(128)    DEFAULT NULL,
    broker              VARCHAR(32)     DEFAULT 'ALPACA',
    mode                VARCHAR(8)      NOT NULL DEFAULT 'paper' COMMENT 'paper | live',
    notes               TEXT            DEFAULT NULL,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_ticker_created (ticker, created_at),
    INDEX idx_signal_type (signal_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Rhea Bot ADI Divergence signal events';

-- ─── Trade Events ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rhea_trade_events (
    id                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    ticker              VARCHAR(16)     NOT NULL,
    action              VARCHAR(8)      NOT NULL COMMENT 'BUY | SELL',
    quantity            DECIMAL(14,4)   NOT NULL,
    price               DECIMAL(14,4)   DEFAULT NULL,
    notional            DECIMAL(16,4)   DEFAULT NULL,
    broker              VARCHAR(32)     NOT NULL DEFAULT 'ALPACA',
    broker_order_id     VARCHAR(128)    DEFAULT NULL,
    mode                VARCHAR(8)      NOT NULL DEFAULT 'paper' COMMENT 'paper | live',
    dry_run             TINYINT(1)      NOT NULL DEFAULT 1,
    status              VARCHAR(32)     NOT NULL DEFAULT 'SIMULATED'
                        COMMENT 'SIMULATED | SUBMITTED | FILLED | CANCELLED | FAILED',
    signal_event_id     BIGINT UNSIGNED DEFAULT NULL,
    discord_notified    TINYINT(1)      NOT NULL DEFAULT 0,
    mlflow_run_id       VARCHAR(64)     DEFAULT NULL,
    notes               TEXT            DEFAULT NULL,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_ticker_created (ticker, created_at),
    INDEX idx_action (action),
    INDEX idx_status (status),
    INDEX idx_signal_event (signal_event_id),
    CONSTRAINT fk_rhea_trade_signal
        FOREIGN KEY (signal_event_id)
        REFERENCES rhea_signal_events (id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Rhea Bot executed and simulated trade events';

-- ─── Bot State ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS rhea_bot_state (
    id                  INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    is_active           TINYINT(1)      NOT NULL DEFAULT 0,
    mode                VARCHAR(8)      NOT NULL DEFAULT 'paper',
    broker              VARCHAR(32)     NOT NULL DEFAULT 'ALPACA',
    last_run_at         DATETIME        DEFAULT NULL,
    last_signal_at      DATETIME        DEFAULT NULL,
    total_signals       INT UNSIGNED    NOT NULL DEFAULT 0,
    total_trades        INT UNSIGNED    NOT NULL DEFAULT 0,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Rhea Bot operational state';

-- Seed a single state row if not present
INSERT IGNORE INTO rhea_bot_state (id, is_active, mode, broker)
VALUES (1, 0, 'paper', 'ALPACA');
