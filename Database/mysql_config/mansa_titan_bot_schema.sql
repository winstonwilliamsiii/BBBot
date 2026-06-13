-- Mansa Tech - Titan Bot schema
-- Uses the workspace-standard MySQL container config:
-- host 127.0.0.1, port 3307, database mansa_bot

CREATE DATABASE IF NOT EXISTS mansa_bot;
USE mansa_bot;

CREATE TABLE IF NOT EXISTS titan_trades (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    qty DECIMAL(18, 6) NOT NULL,
    price_source VARCHAR(40),
    status VARCHAR(20) NOT NULL,
    order_id VARCHAR(80),
    prediction_label INT,
    prediction_probability DECIMAL(10, 6),
    strategy VARCHAR(100),
    notes VARCHAR(255),
    INDEX idx_titan_timestamp (timestamp),
    INDEX idx_titan_symbol (symbol),
    INDEX idx_titan_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS titan_service_health (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    service_name VARCHAR(40) NOT NULL,
    status VARCHAR(20) NOT NULL,
    endpoint VARCHAR(255),
    detail TEXT,
    INDEX idx_service_time (timestamp),
    INDEX idx_service_name (service_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT 'Titan schema ready' AS status;
