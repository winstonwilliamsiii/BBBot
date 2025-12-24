-- Budget Schema for Plaid Integration - MySQL 8.0 Compatible
-- Database: mydb
-- Purpose: Personal budget analysis with user-specific transaction tracking

-- ==============================================================================
-- 1. Budget Categories Table
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
-- 2. Budget Tracking Table (Monthly Budget vs Actual)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS budget_tracking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    month DATE NOT NULL COMMENT 'First day of the month',
    category VARCHAR(100) NOT NULL,
    budgeted DECIMAL(10,2) DEFAULT 0.00,
    actual DECIMAL(10,2) DEFAULT 0.00,
    variance DECIMAL(10,2) GENERATED ALWAYS AS (budgeted - actual) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_month_category (user_id, month, category),
    INDEX idx_user_month (user_id, month),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- 3. Cash Flow Summary Table
-- ==============================================================================

CREATE TABLE IF NOT EXISTS cash_flow_summary (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    month DATE NOT NULL COMMENT 'First day of the month',
    total_income DECIMAL(10,2) DEFAULT 0.00,
    total_expenses DECIMAL(10,2) DEFAULT 0.00,
    net_cash_flow DECIMAL(10,2) GENERATED ALWAYS AS (total_income - total_expenses) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_month (user_id, month),
    INDEX idx_user (user_id),
    INDEX idx_month (month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- 4. User Plaid Tokens Table (Encrypted storage)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS user_plaid_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    access_token TEXT NOT NULL COMMENT 'Encrypted Plaid access token',
    item_id VARCHAR(255),
    institution_id VARCHAR(255),
    institution_name VARCHAR(255),
    last_sync TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_institution (institution_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- 5. Transaction Notes Table
-- ==============================================================================

CREATE TABLE IF NOT EXISTS transaction_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(255) NOT NULL,
    user_id INT NOT NULL,
    note TEXT,
    tags JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_transaction (transaction_id),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- 6. Insert Default Budget Categories
-- ==============================================================================

INSERT INTO budget_categories (user_id, category_name, parent_category, monthly_budget, color_hex, icon) VALUES
(1, 'Food and Drink', NULL, 500.00, '#FF6B6B', '🍽️'),
(1, 'Groceries', 'Food and Drink', 400.00, '#4ECDC4', '🛒'),
(1, 'Restaurants', 'Food and Drink', 100.00, '#FFE66D', '🍔'),
(1, 'Transportation', NULL, 300.00, '#95E1D3', '🚗'),
(1, 'Gas', 'Transportation', 150.00, '#F38181', '⛽'),
(1, 'Public Transit', 'Transportation', 100.00, '#AA96DA', '🚇'),
(1, 'Shopping', NULL, 200.00, '#FCBAD3', '🛍️'),
(1, 'Clothing', 'Shopping', 100.00, '#FFFFD2', '👕'),
(1, 'Entertainment', NULL, 150.00, '#A8D8EA', '🎬'),
(1, 'Streaming', 'Entertainment', 50.00, '#FFCCAC', '📺'),
(1, 'Utilities', NULL, 250.00, '#CADEEF', '💡'),
(1, 'Internet', 'Utilities', 80.00, '#C7CEEA', '🌐'),
(1, 'Electric', 'Utilities', 100.00, '#FFDAC1', '⚡'),
(1, 'Healthcare', NULL, 200.00, '#FFB7B2', '🏥'),
(1, 'Income', NULL, 0.00, '#00D000', '💰'),
(1, 'Salary', 'Income', 0.00, '#00FF00', '💵')
ON DUPLICATE KEY UPDATE monthly_budget = VALUES(monthly_budget);

-- ==============================================================================
-- 7. Views for Common Queries
-- ==============================================================================

-- View: Monthly spending by category
CREATE OR REPLACE VIEW v_monthly_category_spending AS
SELECT 
    bt.user_id,
    bt.month,
    bt.category,
    bc.parent_category,
    bt.budgeted,
    bt.actual,
    bt.variance,
    CASE 
        WHEN bt.actual <= bt.budgeted THEN 'Under Budget'
        WHEN bt.actual <= (bt.budgeted * 1.1) THEN 'On Track'
        ELSE 'Over Budget'
    END as status
FROM budget_tracking bt
LEFT JOIN budget_categories bc ON bt.user_id = bc.user_id AND bt.category = bc.category_name;

-- View: User budget overview
CREATE OR REPLACE VIEW v_user_budget_overview AS
SELECT 
    bc.user_id,
    COUNT(DISTINCT bc.category_name) as total_categories,
    SUM(bc.monthly_budget) as total_monthly_budget,
    SUM(CASE WHEN bc.is_active THEN 1 ELSE 0 END) as active_categories
FROM budget_categories bc
GROUP BY bc.user_id;

-- Success message
SELECT 'Budget tables created successfully!' as status;
