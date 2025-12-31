-- ============================================================================
-- Plaid Integration - MySQL Schema with RBAC & Multi-Tenant Support
-- ============================================================================
-- Database: mansa_bot (primary), mydb (fallback)
-- Purpose: Store Plaid-connected bank accounts and access tokens
-- Multi-Tenant: YES (tenant_id scoping)
-- RBAC: YES (user_id scoping + tenant_id)
-- ============================================================================

-- Create plaid_items table with RBAC fields
CREATE TABLE IF NOT EXISTS plaid_items (
    -- Primary Key
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- RBAC / Multi-Tenant Fields (matching broker_api_credentials pattern)
    tenant_id INT NOT NULL DEFAULT 1 COMMENT 'Tenant ID for multi-tenant deployments',
    user_id INT NOT NULL COMMENT 'User ID who owns this connection',
    
    -- Plaid Identifiers
    item_id VARCHAR(128) NOT NULL UNIQUE COMMENT 'Unique Plaid Item ID from API',
    access_token TEXT NOT NULL COMMENT 'Long-lived Plaid access token (should be encrypted)',
    institution_id VARCHAR(64) COMMENT 'Plaid Institution ID (e.g., ins_123456)',
    institution_name VARCHAR(255) COMMENT 'Human-readable institution name (e.g., Chase, Bank of America)',
    
    -- Account Information
    account_number VARCHAR(100) COMMENT 'Masked account number for display',
    account_type VARCHAR(50) COMMENT 'Account type (checking, savings, credit)',
    account_subtype VARCHAR(50) COMMENT 'Account subtype (e.g., money market)',
    
    -- Sync / State Management
    is_active TINYINT(1) DEFAULT 1 COMMENT '1 = active connection, 0 = revoked/disconnected',
    is_syncing TINYINT(1) DEFAULT 0 COMMENT 'Flag to prevent concurrent sync operations',
    last_sync TIMESTAMP NULL COMMENT 'Timestamp of last successful transaction sync',
    sync_cursor VARCHAR(255) COMMENT 'Plaid sync cursor for incremental transaction fetches',
    next_cursor_required TINYINT(1) DEFAULT 0 COMMENT 'Flag if cursor refresh needed',
    
    -- Audit Trail
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When connection was established',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last update timestamp',
    
    -- Metadata / Debugging
    raw_json JSON COMMENT 'Store full Plaid API response for debugging and historical tracking',
    error_log JSON COMMENT 'Track sync errors and retry attempts',
    
    -- Indexes for optimal query performance
    INDEX idx_plaid_tenant_user (tenant_id, user_id) COMMENT 'Fast lookup by tenant and user',
    INDEX idx_plaid_item (item_id) COMMENT 'Fast lookup by item ID',
    INDEX idx_plaid_active (tenant_id, is_active) COMMENT 'Find active connections per tenant',
    INDEX idx_plaid_syncing (user_id, is_syncing) COMMENT 'Find items currently syncing',
    INDEX idx_plaid_last_sync (last_sync) COMMENT 'Find recently synced items',
    
    -- Unique constraint for RBAC + business logic
    UNIQUE KEY unique_tenant_user_item (tenant_id, user_id, item_id) COMMENT 'One Plaid connection per user per institution'
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Plaid-connected bank accounts with multi-tenant RBAC support';

-- ============================================================================
-- Plaid Transactions Table (linked to plaid_items)
-- ============================================================================
-- Purpose: Cache Plaid transactions for fast querying
-- Notes: 
--   - Synced incrementally from Plaid API
--   - Immutable after sync (transactions don't change)
--   - Use sync_cursor for pagination
-- ============================================================================

CREATE TABLE IF NOT EXISTS plaid_transactions (
    -- Primary Key
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Foreign Key to plaid_items
    plaid_item_id INT NOT NULL COMMENT 'Reference to plaid_items.id',
    
    -- RBAC / Multi-Tenant (denormalized for query performance)
    tenant_id INT NOT NULL COMMENT 'Denormalized tenant_id for filtering',
    user_id INT NOT NULL COMMENT 'Denormalized user_id for filtering',
    
    -- Transaction Identifiers (from Plaid API)
    transaction_id VARCHAR(128) NOT NULL UNIQUE COMMENT 'Unique Plaid transaction ID',
    
    -- Transaction Details
    amount DECIMAL(15, 2) NOT NULL COMMENT 'Transaction amount (positive = debit, negative = credit)',
    currency VARCHAR(3) DEFAULT 'USD' COMMENT 'Currency code (ISO 4217)',
    name VARCHAR(500) NOT NULL COMMENT 'Transaction merchant or description',
    merchant_name VARCHAR(255) COMMENT 'Standardized merchant name (Plaid enriched)',
    category VARCHAR(100) COMMENT 'Category (Plaid enriched: Shopping, Food, Transfer, etc)',
    subcategory VARCHAR(100) COMMENT 'Subcategory for more granular analysis',
    
    -- Transaction Timing
    date DATE NOT NULL COMMENT 'Posted date of transaction',
    authorized_date DATE COMMENT 'Authorized date (may differ from posted)',
    datetime TIMESTAMP NULL COMMENT 'Full timestamp if available',
    
    -- Transaction Status
    pending TINYINT(1) DEFAULT 0 COMMENT '1 = pending, 0 = posted',
    
    -- Plaid-Specific Metadata
    transaction_type VARCHAR(50) COMMENT 'Type: PLACE, DIGITAL, TRANSFER, etc',
    account_owner VARCHAR(255) COMMENT 'Account owner name if available',
    
    -- Audit Trail
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When this transaction was synced',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Raw Plaid data
    raw_json JSON COMMENT 'Full Plaid transaction response for audit/debugging',
    
    -- Indexes for optimal query performance
    INDEX idx_plaid_trans_item (plaid_item_id) COMMENT 'Find transactions for specific account',
    INDEX idx_plaid_trans_user_date (tenant_id, user_id, date) COMMENT 'Find user transactions by date range',
    INDEX idx_plaid_trans_date (date) COMMENT 'Find transactions by date',
    INDEX idx_plaid_trans_category (category) COMMENT 'Aggregate by category',
    INDEX idx_plaid_trans_pending (pending) COMMENT 'Find pending transactions',
    
    -- Foreign Key (optional - enable if plaid_items is guaranteed to exist)
    -- CONSTRAINT fk_plaid_trans_item FOREIGN KEY (plaid_item_id) REFERENCES plaid_items(id) ON DELETE CASCADE
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Cached Plaid transactions for fast budget queries';

-- ============================================================================
-- Plaid Sync Status Table (monitoring & debugging)
-- ============================================================================
-- Purpose: Track sync health and catch issues
-- ============================================================================

CREATE TABLE IF NOT EXISTS plaid_sync_status (
    -- Primary Key
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Reference
    plaid_item_id INT NOT NULL COMMENT 'Reference to plaid_items.id',
    tenant_id INT NOT NULL COMMENT 'Tenant for filtering',
    user_id INT NOT NULL COMMENT 'User for filtering',
    
    -- Sync Status
    status ENUM('success', 'failed', 'in_progress') DEFAULT 'in_progress' COMMENT 'Latest sync result',
    sync_started_at TIMESTAMP NULL COMMENT 'When sync started',
    sync_completed_at TIMESTAMP NULL COMMENT 'When sync finished',
    duration_seconds INT COMMENT 'How long sync took',
    
    -- Error Tracking
    error_code VARCHAR(50) COMMENT 'Plaid error code if failed',
    error_message TEXT COMMENT 'Human-readable error message',
    retry_count INT DEFAULT 0 COMMENT 'Number of retry attempts',
    next_retry_at TIMESTAMP NULL COMMENT 'When to retry if failed',
    
    -- Results
    transactions_synced INT DEFAULT 0 COMMENT 'Number of transactions synced',
    transactions_failed INT DEFAULT 0 COMMENT 'Number of transaction sync failures',
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_sync_item (plaid_item_id),
    INDEX idx_sync_user (tenant_id, user_id),
    INDEX idx_sync_status (status),
    INDEX idx_sync_next_retry (next_retry_at)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Plaid sync monitoring and error tracking';

-- ============================================================================
-- Sample Data for Testing (Development Only)
-- ============================================================================
-- DELETE these before production deployment
-- ============================================================================

-- INSERT INTO plaid_items (tenant_id, user_id, item_id, access_token, institution_id, institution_name, is_active, raw_json)
-- VALUES (
--     1,
--     1,
--     'item_test_sandbox_123456',
--     'access-sandbox-test-token-abc123xyz789',
--     'ins_109508',
--     'Chase',
--     1,
--     JSON_OBJECT(
--         'institution_id', 'ins_109508',
--         'institution_name', 'Chase',
--         'accounts', JSON_ARRAY(
--             JSON_OBJECT('account_id', 'acc_123', 'name', 'Checking', 'type', 'depository', 'mask', '4242')
--         )
--     )
-- );

-- ============================================================================
-- GRANT Statements for Application Users
-- ============================================================================
-- Uncomment and adjust as needed for your database users
-- ============================================================================

-- GRANT SELECT, INSERT, UPDATE, DELETE ON mansa_bot.plaid_items TO 'mansa_app'@'localhost';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON mansa_bot.plaid_transactions TO 'mansa_app'@'localhost';
-- GRANT SELECT, INSERT ON mansa_bot.plaid_sync_status TO 'mansa_app'@'localhost';

-- GRANT SELECT ON mansa_bot.plaid_items TO 'mansa_analytics'@'localhost';
-- GRANT SELECT ON mansa_bot.plaid_transactions TO 'mansa_analytics'@'localhost';
-- GRANT SELECT ON mansa_bot.plaid_sync_status TO 'mansa_analytics'@'localhost';
