-- Create missing Plaid tokens table for BBBot

USE mydb;

-- Create user_plaid_tokens table if it doesn't exist
CREATE TABLE IF NOT EXISTS user_plaid_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    access_token TEXT NOT NULL COMMENT 'Encrypted Plaid access token',
    item_id VARCHAR(255) NOT NULL,
    institution_id VARCHAR(100),
    institution_name VARCHAR(100),
    last_sync TIMESTAMP NULL,
    sync_cursor VARCHAR(255) COMMENT 'For incremental transaction sync',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_active (user_id, is_active),
    INDEX idx_last_sync (last_sync)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Show confirmation
SELECT 'user_plaid_tokens table created successfully' AS status;
SHOW TABLES LIKE '%plaid%';
