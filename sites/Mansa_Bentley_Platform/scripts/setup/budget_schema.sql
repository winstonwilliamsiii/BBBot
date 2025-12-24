-- Budget Schema for Plaid Integration
-- Database: mydb (127.0.0.1:3306)
-- Purpose: Personal budget analysis with user-specific transaction tracking

USE mydb;

-- ==============================================================================
-- 1. Update existing transactions table to add user_id
-- ==============================================================================

-- Add user_id column if it doesn't exist
ALTER TABLE transactions 
ADD COLUMN IF NOT EXISTS user_id INT AFTER transaction_id;

-- Add index for efficient user-based queries
ALTER TABLE transactions 
ADD INDEX IF NOT EXISTS idx_user_date (user_id, date);

-- Add index for category filtering
ALTER TABLE transactions 
ADD INDEX IF NOT EXISTS idx_user_category (user_id, category);

-- ==============================================================================
-- 2. Budget Categories Table
-- ==============================================================================

CREATE TABLE IF NOT EXISTS budget_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    parent_category VARCHAR(100),
    monthly_budget DECIMAL(10,2) DEFAULT 0.00,
    color_hex VARCHAR(7) DEFAULT '#FF8C00',
    icon VARCHAR(50) DEFAULT '💰',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_category (user_id, category_name),
    INDEX idx_user (user_id),
    INDEX idx_active (user_id, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- 3. Budget Tracking Table (Monthly Budget vs Actual)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS budget_tracking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    month DATE NOT NULL COMMENT 'First day of the month',
    category VARCHAR(100) NOT NULL,
    budgeted DECIMAL(10,2) DEFAULT 0.00,
    actual DECIMAL(10,2) DEFAULT 0.00,
    variance DECIMAL(10,2) GENERATED ALWAYS AS (budgeted - actual) STORED,
    variance_pct DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE 
            WHEN budgeted = 0 THEN 0
            ELSE ((budgeted - actual) / budgeted * 100)
        END
    ) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_month_category (user_id, month, category),
    INDEX idx_user_month (user_id, month),
    INDEX idx_category (user_id, category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- 4. Plaid Access Tokens Table (Secure Storage)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS user_plaid_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    access_token TEXT NOT NULL COMMENT 'Encrypted Plaid access token',
    item_id VARCHAR(255) NOT NULL,
    institution_id VARCHAR(100),
    institution_name VARCHAR(100),
    last_sync TIMESTAMP NULL,
    cursor VARCHAR(255) COMMENT 'For incremental transaction sync',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_active (user_id, is_active),
    INDEX idx_last_sync (last_sync)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- 5. Cash Flow Summary Table (Monthly Aggregates)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS cash_flow_summary (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    month DATE NOT NULL COMMENT 'First day of the month',
    total_income DECIMAL(10,2) DEFAULT 0.00,
    total_expenses DECIMAL(10,2) DEFAULT 0.00,
    net_cash_flow DECIMAL(10,2) GENERATED ALWAYS AS (total_income - total_expenses) STORED,
    transaction_count INT DEFAULT 0,
    avg_transaction DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_month (user_id, month),
    INDEX idx_user_month (user_id, month),
    INDEX idx_month (month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- 6. Transaction Notes Table (User annotations)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS transaction_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(255) NOT NULL,
    user_id INT NOT NULL,
    note TEXT,
    tags JSON COMMENT 'Array of user-defined tags',
    is_recurring BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_transaction (transaction_id, user_id),
    INDEX idx_user (user_id),
    INDEX idx_transaction (transaction_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- 7. Update users table to track Plaid connection status
-- ==============================================================================

-- Add Plaid status columns to users table if they don't exist
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS plaid_connected BOOLEAN DEFAULT FALSE AFTER password_hash;

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS plaid_last_sync TIMESTAMP NULL AFTER plaid_connected;

ALTER TABLE users 
ADD INDEX IF NOT EXISTS idx_plaid_connected (plaid_connected);

-- ==============================================================================
-- 8. Insert Default Budget Categories
-- ==============================================================================

-- This will be populated per user, but here are common defaults
-- These can be inserted when a user first connects their bank account

-- Sample categories (will be inserted via application logic per user)
-- Categories follow Plaid's category taxonomy:
-- Income, Food and Drink, Shopping, Transportation, Travel, 
-- Transfer, Payment, Recreation, Service, Healthcare, etc.

-- ==============================================================================
-- 9. Views for Easy Querying
-- ==============================================================================

-- View: Monthly spending by category for all users
CREATE OR REPLACE VIEW v_monthly_spending AS
SELECT 
    t.user_id,
    DATE_FORMAT(t.date, '%Y-%m-01') AS month,
    t.category,
    COUNT(*) AS transaction_count,
    SUM(t.amount) AS total_amount,
    AVG(t.amount) AS avg_amount,
    MIN(t.date) AS first_transaction,
    MAX(t.date) AS last_transaction
FROM transactions t
WHERE t.amount < 0  -- Expenses are negative
GROUP BY t.user_id, month, t.category;

-- View: User budget health dashboard
CREATE OR REPLACE VIEW v_budget_health AS
SELECT 
    bt.user_id,
    bt.month,
    bt.category,
    bt.budgeted,
    bt.actual,
    bt.variance,
    bt.variance_pct,
    CASE 
        WHEN bt.actual <= bt.budgeted * 0.8 THEN 'Under Budget'
        WHEN bt.actual <= bt.budgeted THEN 'On Track'
        WHEN bt.actual <= bt.budgeted * 1.1 THEN 'Slightly Over'
        ELSE 'Over Budget'
    END AS status,
    bc.color_hex,
    bc.icon
FROM budget_tracking bt
LEFT JOIN budget_categories bc ON bt.user_id = bc.user_id AND bt.category = bc.category_name
WHERE bc.is_active = TRUE;

-- View: Recent transactions with enriched data
CREATE OR REPLACE VIEW v_recent_transactions AS
SELECT 
    t.transaction_id,
    t.user_id,
    t.date,
    t.name,
    t.merchant_name,
    t.amount,
    t.category,
    t.pending,
    tn.note,
    tn.tags,
    tn.is_recurring,
    bc.color_hex AS category_color,
    bc.icon AS category_icon
FROM transactions t
LEFT JOIN transaction_notes tn ON t.transaction_id = tn.transaction_id AND t.user_id = tn.user_id
LEFT JOIN budget_categories bc ON t.user_id = bc.user_id AND t.category = bc.category_name
ORDER BY t.date DESC;

-- ==============================================================================
-- 10. Stored Procedures for Common Operations
-- ==============================================================================

-- Procedure: Update monthly cash flow summary for a user
DELIMITER //

CREATE PROCEDURE IF NOT EXISTS update_cash_flow_summary(
    IN p_user_id INT,
    IN p_month DATE
)
BEGIN
    INSERT INTO cash_flow_summary (user_id, month, total_income, total_expenses, transaction_count, avg_transaction)
    SELECT 
        p_user_id,
        p_month,
        COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) AS total_income,
        COALESCE(ABS(SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END)), 0) AS total_expenses,
        COUNT(*) AS transaction_count,
        AVG(ABS(amount)) AS avg_transaction
    FROM transactions
    WHERE user_id = p_user_id 
        AND DATE_FORMAT(date, '%Y-%m-01') = p_month
    ON DUPLICATE KEY UPDATE
        total_income = VALUES(total_income),
        total_expenses = VALUES(total_expenses),
        transaction_count = VALUES(transaction_count),
        avg_transaction = VALUES(avg_transaction),
        updated_at = CURRENT_TIMESTAMP;
END //

-- Procedure: Update budget tracking for a user and month
CREATE PROCEDURE IF NOT EXISTS update_budget_tracking(
    IN p_user_id INT,
    IN p_month DATE
)
BEGIN
    -- Update actual spending per category
    INSERT INTO budget_tracking (user_id, month, category, budgeted, actual)
    SELECT 
        p_user_id,
        p_month,
        t.category,
        COALESCE(bc.monthly_budget, 0),
        ABS(SUM(t.amount))
    FROM transactions t
    LEFT JOIN budget_categories bc ON t.user_id = bc.user_id AND t.category = bc.category_name
    WHERE t.user_id = p_user_id 
        AND DATE_FORMAT(t.date, '%Y-%m-01') = p_month
        AND t.amount < 0  -- Only expenses
    GROUP BY t.category, bc.monthly_budget
    ON DUPLICATE KEY UPDATE
        actual = VALUES(actual),
        updated_at = CURRENT_TIMESTAMP;
END //

DELIMITER ;

-- ==============================================================================
-- 11. Sample Data for Testing (Optional)
-- ==============================================================================

-- Uncomment to insert sample categories for user_id = 1
/*
INSERT INTO budget_categories (user_id, category_name, parent_category, monthly_budget, color_hex, icon) VALUES
(1, 'Food and Drink', NULL, 800.00, '#FF6B6B', '🍔'),
(1, 'Restaurants', 'Food and Drink', 400.00, '#FF6B6B', '🍽️'),
(1, 'Groceries', 'Food and Drink', 400.00, '#4ECDC4', '🛒'),
(1, 'Transportation', NULL, 500.00, '#95E1D3', '🚗'),
(1, 'Gas', 'Transportation', 200.00, '#95E1D3', '⛽'),
(1, 'Public Transit', 'Transportation', 150.00, '#95E1D3', '🚇'),
(1, 'Shopping', NULL, 600.00, '#F38181', '🛍️'),
(1, 'Clothing', 'Shopping', 300.00, '#F38181', '👕'),
(1, 'Electronics', 'Shopping', 300.00, '#F38181', '💻'),
(1, 'Bills and Utilities', NULL, 1500.00, '#AA96DA', '📱'),
(1, 'Rent', 'Bills and Utilities', 1200.00, '#AA96DA', '🏠'),
(1, 'Internet', 'Bills and Utilities', 100.00, '#AA96DA', '🌐'),
(1, 'Electricity', 'Bills and Utilities', 150.00, '#AA96DA', '💡'),
(1, 'Healthcare', NULL, 300.00, '#FCBAD3', '🏥'),
(1, 'Entertainment', NULL, 200.00, '#FFFFD2', '🎬'),
(1, 'Income', NULL, 0.00, '#90EE90', '💵')
ON DUPLICATE KEY UPDATE category_name = category_name;
*/

-- ==============================================================================
-- 12. Indexes for Performance
-- ==============================================================================

-- Additional composite indexes for common queries
ALTER TABLE transactions 
ADD INDEX IF NOT EXISTS idx_user_date_category (user_id, date, category);

ALTER TABLE transactions 
ADD INDEX IF NOT EXISTS idx_user_pending (user_id, pending);

-- ==============================================================================
-- Success Message
-- ==============================================================================

SELECT 'Budget schema setup completed successfully!' AS status;
SELECT 'Tables created: budget_categories, budget_tracking, user_plaid_tokens, cash_flow_summary, transaction_notes' AS tables_created;
SELECT 'Views created: v_monthly_spending, v_budget_health, v_recent_transactions' AS views_created;
SELECT 'Stored procedures created: update_cash_flow_summary, update_budget_tracking' AS procedures_created;
