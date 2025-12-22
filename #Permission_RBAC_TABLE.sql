-- =====================================================
-- MANSA CAPITAL RBAC (ROLE-BASED ACCESS CONTROL) SYSTEM
-- Integrates with Appwrite Authentication & Authorization
-- =====================================================

-- =====================================================
-- 1. CORE RBAC TABLES
-- =====================================================

-- Teams Table (Maps to Appwrite Teams)
CREATE TABLE IF NOT EXISTS teams (
    team_id VARCHAR(255) PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    appwrite_team_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Roles Table (Maps to Appwrite Roles)
CREATE TABLE IF NOT EXISTS roles (
    role_id VARCHAR(255) PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    appwrite_role VARCHAR(100),
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Collections Table (Appwrite Collections/Database Tables)
CREATE TABLE IF NOT EXISTS collections (
    collection_id VARCHAR(255) PRIMARY KEY,
    collection_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    appwrite_collection_id VARCHAR(255),
    is_sensitive BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Permissions Table (CRUD Operations)
CREATE TABLE IF NOT EXISTS permissions (
    permission_id VARCHAR(255) PRIMARY KEY,
    permission_name VARCHAR(50) NOT NULL,
    operation_type ENUM('CREATE', 'READ', 'UPDATE', 'DELETE', 'MANAGE') NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 2. RELATIONSHIP TABLES
-- =====================================================

-- Team Members (Links Users to Teams)
CREATE TABLE IF NOT EXISTS team_members (
    team_id VARCHAR(255),
    user_id VARCHAR(255),
    role_id VARCHAR(255),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (team_id, user_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Role Permissions (What each role can do)
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id VARCHAR(255),
    collection_id VARCHAR(255),
    permission_id VARCHAR(255),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (role_id, collection_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE,
    FOREIGN KEY (collection_id) REFERENCES collections(collection_id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(permission_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User Permissions Override (Specific user permissions)
CREATE TABLE IF NOT EXISTS user_permissions (
    user_id VARCHAR(255),
    collection_id VARCHAR(255),
    permission_id VARCHAR(255),
    granted_by VARCHAR(255),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (user_id, collection_id, permission_id),
    FOREIGN KEY (collection_id) REFERENCES collections(collection_id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(permission_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 3. MANSA CAPITAL TEAMS (Appwrite Teams)
-- =====================================================

INSERT INTO teams (team_id, team_name, description, appwrite_team_id) VALUES
('team_admin', 'Admin', 'Full system administrators with complete access', 'admin_team'),
('team_investor', 'Investor', 'External investors viewing portfolio performance', 'investor_team'),
('team_client', 'Client', 'End clients accessing personal financial data', 'client_team'),
('team_analyst', 'Analyst', 'Data analysts working with market research', 'analyst_team'),
('team_devops', 'DevOps', 'Development team managing technical infrastructure', 'devops_team');

-- =====================================================
-- 4. MANSA CAPITAL ROLES (Appwrite Roles)
-- =====================================================

INSERT INTO roles (role_id, role_name, description, appwrite_role, is_admin) VALUES
('role_admin', 'Admin', 'System administrator with full access', 'role:admin', TRUE),
('role_investor', 'Investor', 'External investor with portfolio view access', 'role:user', FALSE),
('role_client', 'Client', 'Client with personal finance access', 'role:user', FALSE),
('role_analyst', 'Analyst', 'Data analyst with research tools access', 'role:user', FALSE),
('role_developer', 'Developer', 'Technical team member with system access', 'role:user', FALSE);

-- =====================================================
-- 5. APPWRITE COLLECTIONS (Database Tables)
-- =====================================================

INSERT INTO collections (collection_id, collection_name, description, appwrite_collection_id, is_sensitive) VALUES
-- Admin Collections
('coll_users', 'users', 'User management and authentication', 'users_collection', TRUE),
('coll_teams', 'teams', 'Team and organization management', 'teams_collection', TRUE),
('coll_roles', 'roles', 'Role and permission definitions', 'roles_collection', TRUE),
('coll_permissions', 'permissions', 'Permission matrix and access control', 'permissions_collection', TRUE),
('coll_functions', 'functions', 'Serverless functions and API management', 'functions_collection', TRUE),

-- Financial Collections
('coll_kyc', 'kyc', 'Know Your Customer verification data', 'kyc_collection', TRUE),
('coll_payments', 'payments', 'Payment processing and transaction records', 'payments_collection', TRUE),
('coll_auditlogs', 'auditlogs', 'System audit trails and compliance logs', 'auditlogs_collection', TRUE),
('coll_transactions', 'transactions', 'Financial transactions and transfers', 'transactions_collection', TRUE),
('coll_portfolios', 'portfolios', 'Investment portfolios and holdings', 'portfolios_collection', FALSE),
('coll_budgets', 'budgets', 'Personal and business budgets', 'budgets_collection', FALSE),

-- Performance Collections  
('coll_bot_metrics', 'bot_metrics', 'Trading bot performance metrics', 'bot_metrics_collection', FALSE),
('coll_experiments', 'experiments', 'A/B testing and strategy experiments', 'experiments_collection', FALSE),
('coll_runs', 'runs', 'Experiment execution runs and results', 'runs_collection', FALSE),

-- Market Data Collections
('coll_fundamentals', 'fundamentals', 'Company fundamental analysis data', 'fundamentals_collection', FALSE),
('coll_technicals', 'technicals', 'Technical analysis indicators', 'technicals_collection', FALSE),
('coll_sentiment', 'sentiment', 'Market sentiment and social media data', 'sentiment_collection', FALSE),

-- DevOps Collections
('coll_mlflow_db', 'mlflow_db', 'Machine learning experiment tracking', 'mlflow_collection', FALSE),
('coll_airflow_dags', 'airflow_dags', 'Data pipeline orchestration', 'airflow_collection', FALSE),
('coll_staging_trades', 'staging_trades', 'Pre-production trading simulations', 'staging_collection', FALSE);

-- =====================================================
-- 6. CRUD PERMISSIONS
-- =====================================================

INSERT INTO permissions (permission_id, permission_name, operation_type, description) VALUES
('perm_create', 'Create', 'CREATE', 'Create new records in collection'),
('perm_read', 'Read', 'READ', 'View and query collection data'),
('perm_update', 'Update', 'UPDATE', 'Modify existing collection records'),
('perm_delete', 'Delete', 'DELETE', 'Remove records from collection'),
('perm_manage', 'Manage', 'MANAGE', 'Full administrative control over collection');

-- =====================================================
-- 7. ROLE-COLLECTION-PERMISSION MATRIX
-- =====================================================

-- ADMIN ROLE: Full CRUD on all collections
INSERT INTO role_permissions (role_id, collection_id, permission_id) 
SELECT 'role_admin', collection_id, permission_id 
FROM collections 
CROSS JOIN permissions;

-- INVESTOR ROLE: Read portfolios, bot_metrics, transactions
INSERT INTO role_permissions (role_id, collection_id, permission_id) VALUES
('role_investor', 'coll_portfolios', 'perm_read'),
('role_investor', 'coll_bot_metrics', 'perm_read'),
('role_investor', 'coll_transactions', 'perm_read');

-- CLIENT ROLE: Read budgets, transactions (own only), auditlogs (own only)
INSERT INTO role_permissions (role_id, collection_id, permission_id) VALUES
('role_client', 'coll_budgets', 'perm_read'),
('role_client', 'coll_transactions', 'perm_read'),
('role_client', 'coll_auditlogs', 'perm_read');

-- ANALYST ROLE: Read/Write analytics, experiments, market data
INSERT INTO role_permissions (role_id, collection_id, permission_id) VALUES
('role_analyst', 'coll_fundamentals', 'perm_read'),
('role_analyst', 'coll_fundamentals', 'perm_create'),
('role_analyst', 'coll_fundamentals', 'perm_update'),
('role_analyst', 'coll_technicals', 'perm_read'),
('role_analyst', 'coll_technicals', 'perm_create'),
('role_analyst', 'coll_technicals', 'perm_update'),
('role_analyst', 'coll_sentiment', 'perm_read'),
('role_analyst', 'coll_sentiment', 'perm_create'),
('role_analyst', 'coll_sentiment', 'perm_update'),
('role_analyst', 'coll_experiments', 'perm_read'),
('role_analyst', 'coll_experiments', 'perm_create'),
('role_analyst', 'coll_experiments', 'perm_update'),
('role_analyst', 'coll_runs', 'perm_read'),
('role_analyst', 'coll_runs', 'perm_create'),
('role_analyst', 'coll_runs', 'perm_update');

-- DEVELOPER ROLE: Manage MLFlow, Airflow, Staging
INSERT INTO role_permissions (role_id, collection_id, permission_id) VALUES
('role_developer', 'coll_mlflow_db', 'perm_manage'),
('role_developer', 'coll_airflow_dags', 'perm_manage'),
('role_developer', 'coll_staging_trades', 'perm_manage');

-- =====================================================
-- 8. HELPER VIEWS FOR RBAC QUERIES
-- =====================================================

-- View: User Effective Permissions
CREATE OR REPLACE VIEW user_effective_permissions AS
SELECT DISTINCT 
    tm.user_id,
    tm.team_id,
    t.team_name,
    r.role_name,
    c.collection_name,
    p.permission_name,
    p.operation_type,
    'role' as permission_source
FROM team_members tm
JOIN teams t ON tm.team_id = t.team_id
JOIN roles r ON tm.role_id = r.role_id
JOIN role_permissions rp ON r.role_id = rp.role_id
JOIN collections c ON rp.collection_id = c.collection_id
JOIN permissions p ON rp.permission_id = p.permission_id
WHERE tm.is_active = TRUE AND rp.is_active = TRUE

UNION ALL

SELECT DISTINCT
    up.user_id,
    NULL as team_id,
    NULL as team_name,
    'Direct Grant' as role_name,
    c.collection_name,
    p.permission_name,
    p.operation_type,
    'direct' as permission_source
FROM user_permissions up
JOIN collections c ON up.collection_id = c.collection_id
JOIN permissions p ON up.permission_id = p.permission_id
WHERE up.is_active = TRUE 
AND (up.expires_at IS NULL OR up.expires_at > NOW());

-- View: Collection Access Matrix
CREATE OR REPLACE VIEW collection_access_matrix AS
SELECT 
    c.collection_name,
    r.role_name,
    GROUP_CONCAT(p.operation_type ORDER BY p.operation_type) as permissions
FROM collections c
JOIN role_permissions rp ON c.collection_id = rp.collection_id
JOIN roles r ON rp.role_id = r.role_id
JOIN permissions p ON rp.permission_id = p.permission_id
WHERE rp.is_active = TRUE
GROUP BY c.collection_name, r.role_name
ORDER BY c.collection_name, r.role_name;

-- =====================================================
-- 9. RBAC UTILITY FUNCTIONS
-- =====================================================

-- Function: Check User Permission
DELIMITER //
CREATE FUNCTION check_user_permission(
    p_user_id VARCHAR(255),
    p_collection_name VARCHAR(100),
    p_operation_type VARCHAR(10)
) RETURNS BOOLEAN
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE permission_count INT DEFAULT 0;
    
    SELECT COUNT(*) INTO permission_count
    FROM user_effective_permissions
    WHERE user_id = p_user_id
    AND collection_name = p_collection_name
    AND operation_type = p_operation_type;
    
    RETURN permission_count > 0;
END //
DELIMITER ;

-- =====================================================
-- 10. INDEXES FOR PERFORMANCE
-- =====================================================

-- Team Members Indexes
CREATE INDEX idx_team_members_user ON team_members(user_id);
CREATE INDEX idx_team_members_team ON team_members(team_id);
CREATE INDEX idx_team_members_role ON team_members(role_id);

-- Role Permissions Indexes
CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_collection ON role_permissions(collection_id);
CREATE INDEX idx_role_permissions_permission ON role_permissions(permission_id);

-- User Permissions Indexes
CREATE INDEX idx_user_permissions_user ON user_permissions(user_id);
CREATE INDEX idx_user_permissions_collection ON user_permissions(collection_id);
CREATE INDEX idx_user_permissions_expires ON user_permissions(expires_at);

-- Collections Indexes
CREATE INDEX idx_collections_appwrite ON collections(appwrite_collection_id);
CREATE INDEX idx_collections_sensitive ON collections(is_sensitive);

-- =====================================================
-- 11. APPWRITE INTEGRATION REFERENCE
-- =====================================================

/*
APPWRITE INTEGRATION GUIDE:

⚠️  IMPORTANT: This MySQL schema is for LOCAL TRACKING only!
    Appwrite has its own internal permission system that must be configured separately.

APPWRITE PERMISSION STRINGS FOR REFERENCE:

Admin Permissions:
- read("role:admin")
- write("role:admin") 
- create("role:admin")
- update("role:admin")
- delete("role:admin")

Team-based Permissions:
- read("team:investor_team")
- read("team:client_team") 
- read("team:analyst_team")
- write("team:devops_team")

User-specific Permissions:
- read("user:{user_id}")  // Client can only read own data
- write("user:{user_id}") // Client can only write own data

Example Appwrite Collection Permissions:
portfolios: ["read(role:admin)", "read(team:investor_team)", "write(role:admin)"]
transactions: ["read(role:admin)", "read(team:investor_team)", "read(team:client_team)", "write(role:admin)"]  
auditlogs: ["read(role:admin)", "read(user:self)", "write(role:admin)"]

TO SYNC WITH APPWRITE UI:
1. Create teams in Appwrite Console or via API
2. Assign users to teams
3. Configure collection permissions using the strings above
4. Update this MySQL schema to mirror your Appwrite setup
*/

-- =====================================================
-- 12. DATA MIGRATION & CLEANUP
-- =====================================================

-- Add timestamps to existing tables if not present
ALTER TABLE transactions 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

ALTER TABLE equities_bulk
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

-- Performance indexes for high-volume tables
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_equities_symbol_date ON equities_bulk(symbol, date);

-- =====================================================
-- END OF MANSA CAPITAL RBAC SYSTEM
-- =====================================================