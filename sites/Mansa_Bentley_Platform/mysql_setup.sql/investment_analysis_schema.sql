-- WeFolio Funds Table Schema
-- Stores fund information for portfolio tracking

CREATE TABLE IF NOT EXISTS wefolio_funds (
    -- Primary key
    id VARCHAR(50) PRIMARY KEY COMMENT 'Unique fund identifier',
    
    -- Fund details
    name VARCHAR(255) NOT NULL COMMENT 'Fund display name',
    nav DECIMAL(10, 2) COMMENT 'Net Asset Value per share',
    shares DECIMAL(15, 4) COMMENT 'Number of shares held',
    value DECIMAL(15, 2) COMMENT 'Total position value (NAV * shares)',
    
    -- Performance metrics
    daily_change DECIMAL(15, 2) COMMENT 'Daily change in dollars',
    daily_change_pct DECIMAL(5, 2) COMMENT 'Daily change percentage',
    
    -- Metadata
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP 
        COMMENT 'Last sync timestamp',
    
    -- Indexes for performance
    INDEX idx_last_updated (last_updated),
    INDEX idx_name (name),
    INDEX idx_value (value)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='WeFolio fund positions';


-- Broker Connections Table
-- Tracks connected broker accounts and their status

CREATE TABLE IF NOT EXISTS broker_connections (
    -- Primary key
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Connection details
    user_id INT NOT NULL COMMENT 'Reference to user account',
    broker_name VARCHAR(100) NOT NULL COMMENT 'Broker name (IBKR, Binance, etc.)',
    account_number VARCHAR(100) NOT NULL COMMENT 'Masked account number',
    
    -- Status tracking
    status ENUM('connected', 'pending', 'disconnected', 'error') DEFAULT 'pending' 
        COMMENT 'Connection status',
    last_sync TIMESTAMP NULL COMMENT 'Last successful sync timestamp',
    last_error TEXT NULL COMMENT 'Last error message if any',
    
    -- Account metrics
    balance DECIMAL(15, 2) DEFAULT 0 COMMENT 'Current account balance',
    positions_count INT DEFAULT 0 COMMENT 'Number of positions',
    
    -- API credentials (encrypted)
    api_token_encrypted TEXT NULL COMMENT 'Encrypted API token',
    api_credentials_encrypted TEXT NULL COMMENT 'Encrypted additional credentials JSON',
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_user_broker (user_id, broker_name),
    INDEX idx_status (status),
    INDEX idx_last_sync (last_sync),
    
    -- Ensure unique connection per user per broker account
    UNIQUE KEY unique_user_broker_account (user_id, broker_name, account_number)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Broker account connections';


-- Users Table (for RBAC system)
-- Stores user accounts with roles and compliance status

CREATE TABLE IF NOT EXISTS users (
    -- Primary key
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Authentication
    username VARCHAR(100) NOT NULL UNIQUE COMMENT 'Login username',
    password_hash VARCHAR(255) NOT NULL COMMENT 'Hashed password (bcrypt/argon2)',
    email VARCHAR(255) UNIQUE COMMENT 'User email address',
    
    -- Role and permissions
    role ENUM('guest', 'client', 'investor', 'admin') DEFAULT 'guest' 
        COMMENT 'User role',
    
    -- Compliance tracking
    kyc_completed BOOLEAN DEFAULT FALSE COMMENT 'KYC verification status',
    kyc_date TIMESTAMP NULL COMMENT 'KYC completion date',
    investment_agreement_signed BOOLEAN DEFAULT FALSE COMMENT 'Investment agreement status',
    agreement_date TIMESTAMP NULL COMMENT 'Agreement signature date',
    
    -- Account status
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Account active status',
    is_verified BOOLEAN DEFAULT FALSE COMMENT 'Email verified status',
    
    -- Profile
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL COMMENT 'Last login timestamp',
    
    -- Indexes
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_kyc_status (kyc_completed, investment_agreement_signed)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='User accounts with RBAC';


-- Audit Log Table
-- Tracks authentication and authorization events

CREATE TABLE IF NOT EXISTS audit_log (
    -- Primary key
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- Event details
    user_id INT NULL COMMENT 'User ID if authenticated',
    username VARCHAR(100) NULL COMMENT 'Username (for failed auth)',
    event_type ENUM('login', 'logout', 'login_failed', 'permission_denied', 'data_access') 
        NOT NULL COMMENT 'Event type',
    
    -- Context
    permission_checked VARCHAR(100) NULL COMMENT 'Permission that was checked',
    resource_accessed VARCHAR(255) NULL COMMENT 'Resource that was accessed',
    
    -- Result
    success BOOLEAN NOT NULL COMMENT 'Whether action succeeded',
    failure_reason TEXT NULL COMMENT 'Reason for failure if applicable',
    
    -- Request metadata
    ip_address VARCHAR(45) NULL COMMENT 'IP address',
    user_agent TEXT NULL COMMENT 'Browser user agent',
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_user_id (user_id),
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at),
    INDEX idx_success (success)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Audit log for security events';


-- Fund History Table
-- Tracks historical fund values for performance analysis

CREATE TABLE IF NOT EXISTS wefolio_fund_history (
    -- Primary key
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- Fund reference
    fund_id VARCHAR(50) NOT NULL COMMENT 'Reference to wefolio_funds.id',
    
    -- Historical values
    nav DECIMAL(10, 2) NOT NULL COMMENT 'NAV at this point in time',
    shares DECIMAL(15, 4) NOT NULL COMMENT 'Shares held',
    value DECIMAL(15, 2) NOT NULL COMMENT 'Total value',
    
    -- Performance
    daily_change DECIMAL(15, 2),
    daily_change_pct DECIMAL(5, 2),
    
    -- Timestamp
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When this snapshot was taken',
    
    -- Indexes
    INDEX idx_fund_id (fund_id),
    INDEX idx_recorded_at (recorded_at),
    INDEX idx_fund_date (fund_id, recorded_at),
    
    -- Foreign key
    FOREIGN KEY (fund_id) REFERENCES wefolio_funds(id) ON DELETE CASCADE
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Historical fund values for tracking performance';


-- Insert demo users (for development/testing)
-- Production: Remove these and use proper user registration

INSERT INTO users (username, password_hash, email, role, kyc_completed, kyc_date, investment_agreement_signed, agreement_date)
VALUES 
    (
        'guest',
        -- SHA-256 hash of 'guest123' (replace with bcrypt in production)
        '84edc8e1e0c6cb8cbb4c35d6c8e6e25ef2e7f6b2c1f51fd5b8b8b8b8b8b8b8b8',
        'guest@example.com',
        'guest',
        FALSE,
        NULL,
        FALSE,
        NULL
    ),
    (
        'client',
        -- SHA-256 hash of 'client123'
        'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3',
        'client@bentleybot.com',
        'client',
        TRUE,
        DATE_SUB(NOW(), INTERVAL 30 DAY),
        TRUE,
        DATE_SUB(NOW(), INTERVAL 30 DAY)
    ),
    (
        'investor',
        -- SHA-256 hash of 'investor123'
        'b03ddf3ca2e714a6548e7495e2a03f5e824eaac9837cd7f159c67b90fb4b7342',
        'investor@bentleybot.com',
        'investor',
        TRUE,
        DATE_SUB(NOW(), INTERVAL 60 DAY),
        TRUE,
        DATE_SUB(NOW(), INTERVAL 60 DAY)
    ),
    (
        'admin',
        -- SHA-256 hash of 'admin123'
        '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9',
        'admin@bentleybot.com',
        'admin',
        TRUE,
        DATE_SUB(NOW(), INTERVAL 90 DAY),
        TRUE,
        DATE_SUB(NOW(), INTERVAL 90 DAY)
    )
ON DUPLICATE KEY UPDATE updated_at = NOW();


-- Views for common queries

-- View: Active client connections
CREATE OR REPLACE VIEW v_active_connections AS
SELECT 
    u.username,
    u.role,
    bc.broker_name,
    bc.account_number,
    bc.status,
    bc.balance,
    bc.positions_count,
    bc.last_sync
FROM broker_connections bc
JOIN users u ON bc.user_id = u.id
WHERE bc.status = 'connected'
    AND u.is_active = TRUE
ORDER BY bc.last_sync DESC;


-- View: Fund portfolio summary
CREATE OR REPLACE VIEW v_fund_portfolio_summary AS
SELECT 
    COUNT(*) as total_funds,
    SUM(value) as total_value,
    SUM(daily_change) as total_daily_change,
    AVG(daily_change_pct) as avg_daily_change_pct,
    MAX(last_updated) as last_update
FROM wefolio_funds;


-- View: User compliance status
CREATE OR REPLACE VIEW v_user_compliance AS
SELECT 
    username,
    email,
    role,
    kyc_completed,
    investment_agreement_signed,
    CASE 
        WHEN kyc_completed AND investment_agreement_signed THEN 'Compliant'
        ELSE 'Incomplete'
    END as compliance_status,
    kyc_date,
    agreement_date
FROM users
WHERE is_active = TRUE;
