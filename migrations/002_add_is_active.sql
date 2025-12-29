-- Migration 002: Add is_active column to tables
-- Description: Adds is_active column for soft deletes and enable/disable functionality
-- Date: 2025-12-29

-- Add is_active to transactions (if not exists)
ALTER TABLE transactions 
ADD COLUMN IF NOT EXISTS is_active TINYINT(1) DEFAULT 1
COMMENT '1=Active, 0=Soft deleted';

ALTER TABLE transactions
ADD INDEX IF NOT EXISTS idx_is_active (is_active);

-- Add is_active to budgets (if not exists)
ALTER TABLE budgets
ADD COLUMN IF NOT EXISTS is_active TINYINT(1) DEFAULT 1
COMMENT '1=Active, 0=Soft deleted';

ALTER TABLE budgets
ADD INDEX IF NOT EXISTS idx_is_active (is_active);

-- Add is_active to accounts (if not exists)
ALTER TABLE accounts
ADD COLUMN IF NOT EXISTS is_active TINYINT(1) DEFAULT 1
COMMENT '1=Active, 0=Soft deleted';

ALTER TABLE accounts
ADD INDEX IF NOT EXISTS idx_is_active (is_active);

-- Update existing queries to respect is_active flag
-- Note: Application code should be updated to filter by is_active=1

-- Add comment to users table is_active for consistency
ALTER TABLE users 
MODIFY COLUMN is_active TINYINT(1) DEFAULT 1 
COMMENT '1=Active account, 0=Deactivated';
