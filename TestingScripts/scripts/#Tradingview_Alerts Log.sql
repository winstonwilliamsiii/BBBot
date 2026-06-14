#Tradingview_Alerts Log 

CREATE TABLE alerts_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  symbol VARCHAR(20) NOT NULL,
  change_percent DECIMAL(6,2) NOT NULL,
  price DECIMAL(12,2),
  currency VARCHAR(10) DEFAULT 'USD',
  alert_type VARCHAR(50) NOT NULL,   -- 'portfolio', 'gainer', 'loser'
  discord_delivered BOOLEAN DEFAULT FALSE,
  discord_error TEXT,
  sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_symbol (symbol),
  INDEX idx_sent_at (sent_at),
  INDEX idx_alert_type (alert_type)
);