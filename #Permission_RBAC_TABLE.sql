#Permission_RBAC_TABLE

CREATE TABLE team_members (
    team_id VARCHAR(255),
    user_id VARCHAR(255),
    PRIMARY KEY (team_id, user_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Add created_at and updated_at timestamps to all tables
ALTER TABLE transactions
ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

ALTER TABLE equities_bulk
ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

-- Ensure indexes are added for user_id, symbol, and date in high-volume tables
CREATE INDEX idx_user_id ON transactions(user_id);
CREATE INDEX idx_symbol_date ON equities_bulk(symbol, date);