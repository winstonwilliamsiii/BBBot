-- Stocktwits Sentiment Data Table Schema
-- Table for storing sentiment scores from Stocktwits

CREATE TABLE IF NOT EXISTS stocktwits_sentiment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    sentiment_score DECIMAL(5, 4),
    bullish_count INT,
    bearish_count INT,
    total_messages INT,
    scraped_at TIMESTAMP NOT NULL,
    url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ticker (ticker),
    INDEX idx_scraped_at (scraped_at),
    INDEX idx_ticker_date (ticker, scraped_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Grant permissions to Airbyte users
GRANT SELECT, INSERT, UPDATE ON mansa_bot.stocktwits_sentiment TO 'airbyte'@'%';
