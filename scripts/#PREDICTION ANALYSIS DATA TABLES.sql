#PREDICTION ANALYSIS DATA TABLES

-- Probability engine outputs
CREATE TABLE prediction_probabilities (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contract_id VARCHAR(100),
    source VARCHAR(50),         -- 'Kalshi' or 'Polymarket'
    implied_probability DECIMAL(5,2), -- 0 to 100
    confidence_score DECIMAL(5,2),    -- model confidence
    rationale TEXT,              -- AI-generated explanation
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sentiment signals (Alphascope-style)
CREATE TABLE sentiment_signals (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contract_id VARCHAR(100),
    sentiment_score DECIMAL(5,2), -- -1 to +1
    signal_strength VARCHAR(50),  -- 'weak', 'moderate', 'strong'
    source VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);