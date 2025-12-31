#!/usr/bin/env python3
"""
Plaid Integration - MySQL Schema Migration Script
Applies plaid_items, plaid_transactions, and plaid_sync_status tables
Supports both mansa_bot (primary) and mydb (fallback) databases
"""

import mysql.connector
import os
from dotenv import load_dotenv
import sys
from datetime import datetime

load_dotenv(override=True)

# Database configurations (try both primary and fallback)
DB_CONFIGS = {
    'mansa_bot': {
        'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
        'port': int(os.getenv('MYSQL_PORT', '3307')),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', 'root'),
        'database': os.getenv('MYSQL_DATABASE', 'mansa_bot')
    },
    'mydb': {
        'host': os.getenv('BUDGET_MYSQL_HOST', '127.0.0.1'),
        'port': int(os.getenv('BUDGET_MYSQL_PORT', '3306')),
        'user': os.getenv('BUDGET_MYSQL_USER', 'root'),
        'password': os.getenv('BUDGET_MYSQL_PASSWORD', 'root'),
        'database': os.getenv('BUDGET_MYSQL_DATABASE', 'mydb')
    }
}

# SQL Schema
CREATE_PLAID_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS plaid_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- RBAC / Multi-Tenant Fields
    tenant_id INT NOT NULL DEFAULT 1 COMMENT 'Tenant ID for multi-tenant deployments',
    user_id INT NOT NULL COMMENT 'User ID who owns this connection',
    
    -- Plaid Identifiers
    item_id VARCHAR(128) NOT NULL UNIQUE COMMENT 'Unique Plaid Item ID from API',
    access_token TEXT NOT NULL COMMENT 'Long-lived Plaid access token (should be encrypted)',
    institution_id VARCHAR(64) COMMENT 'Plaid Institution ID',
    institution_name VARCHAR(255) COMMENT 'Human-readable institution name',
    
    -- Account Information
    account_number VARCHAR(100) COMMENT 'Masked account number for display',
    account_type VARCHAR(50) COMMENT 'Account type (checking, savings, credit)',
    account_subtype VARCHAR(50) COMMENT 'Account subtype',
    
    -- Sync / State Management
    is_active TINYINT(1) DEFAULT 1 COMMENT '1 = active, 0 = revoked',
    is_syncing TINYINT(1) DEFAULT 0 COMMENT 'Prevent concurrent syncs',
    last_sync TIMESTAMP NULL COMMENT 'Last successful transaction sync',
    sync_cursor VARCHAR(255) COMMENT 'Plaid sync cursor for incremental fetches',
    next_cursor_required TINYINT(1) DEFAULT 0 COMMENT 'Flag if cursor refresh needed',
    
    -- Audit Trail
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Metadata
    raw_json JSON COMMENT 'Store full Plaid API response',
    error_log JSON COMMENT 'Track sync errors',
    
    -- Indexes
    INDEX idx_plaid_tenant_user (tenant_id, user_id),
    INDEX idx_plaid_item (item_id),
    INDEX idx_plaid_active (tenant_id, is_active),
    INDEX idx_plaid_syncing (user_id, is_syncing),
    INDEX idx_plaid_last_sync (last_sync),
    
    -- Unique constraint
    UNIQUE KEY unique_tenant_user_item (tenant_id, user_id, item_id)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Plaid-connected bank accounts with RBAC support'
"""

CREATE_PLAID_TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS plaid_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Foreign Key
    plaid_item_id INT NOT NULL COMMENT 'Reference to plaid_items.id',
    
    -- RBAC (denormalized for performance)
    tenant_id INT NOT NULL COMMENT 'Denormalized tenant_id',
    user_id INT NOT NULL COMMENT 'Denormalized user_id',
    
    -- Transaction Identifiers
    transaction_id VARCHAR(128) NOT NULL UNIQUE COMMENT 'Unique Plaid transaction ID',
    
    -- Transaction Details
    amount DECIMAL(15, 2) NOT NULL COMMENT 'Transaction amount',
    currency VARCHAR(3) DEFAULT 'USD',
    name VARCHAR(500) NOT NULL COMMENT 'Transaction description',
    merchant_name VARCHAR(255) COMMENT 'Standardized merchant name',
    category VARCHAR(100) COMMENT 'Category (Plaid enriched)',
    subcategory VARCHAR(100) COMMENT 'Subcategory',
    
    -- Transaction Timing
    date DATE NOT NULL COMMENT 'Posted date',
    authorized_date DATE COMMENT 'Authorized date',
    datetime TIMESTAMP NULL,
    
    -- Transaction Status
    pending TINYINT(1) DEFAULT 0 COMMENT '1 = pending, 0 = posted',
    
    -- Plaid Metadata
    transaction_type VARCHAR(50) COMMENT 'Type: PLACE, DIGITAL, TRANSFER, etc',
    account_owner VARCHAR(255) COMMENT 'Account owner name',
    
    -- Audit
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    raw_json JSON COMMENT 'Full Plaid response',
    
    -- Indexes
    INDEX idx_plaid_trans_item (plaid_item_id),
    INDEX idx_plaid_trans_user_date (tenant_id, user_id, date),
    INDEX idx_plaid_trans_date (date),
    INDEX idx_plaid_trans_category (category),
    INDEX idx_plaid_trans_pending (pending)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Cached Plaid transactions for budget queries'
"""

CREATE_PLAID_SYNC_STATUS_TABLE = """
CREATE TABLE IF NOT EXISTS plaid_sync_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Reference
    plaid_item_id INT NOT NULL COMMENT 'Reference to plaid_items.id',
    tenant_id INT NOT NULL COMMENT 'Tenant for filtering',
    user_id INT NOT NULL COMMENT 'User for filtering',
    
    -- Sync Status
    status ENUM('success', 'failed', 'in_progress') DEFAULT 'in_progress',
    sync_started_at TIMESTAMP NULL,
    sync_completed_at TIMESTAMP NULL,
    duration_seconds INT COMMENT 'Duration of sync',
    
    -- Error Tracking
    error_code VARCHAR(50) COMMENT 'Plaid error code',
    error_message TEXT COMMENT 'Error message',
    retry_count INT DEFAULT 0,
    next_retry_at TIMESTAMP NULL,
    
    -- Results
    transactions_synced INT DEFAULT 0,
    transactions_failed INT DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_sync_item (plaid_item_id),
    INDEX idx_sync_user (tenant_id, user_id),
    INDEX idx_sync_status (status),
    INDEX idx_sync_next_retry (next_retry_at)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Plaid sync monitoring and error tracking'
"""


def apply_schema(db_name: str, config: dict) -> bool:
    """Apply Plaid schema to specified database"""
    try:
        print(f"\n{'='*70}")
        print(f"Connecting to {db_name}...")
        print(f"{'='*70}")
        
        conn = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
        
        cursor = conn.cursor()
        
        print(f"✅ Connected to {db_name}")
        
        # Create tables
        tables = [
            ("plaid_items", CREATE_PLAID_ITEMS_TABLE),
            ("plaid_transactions", CREATE_PLAID_TRANSACTIONS_TABLE),
            ("plaid_sync_status", CREATE_PLAID_SYNC_STATUS_TABLE)
        ]
        
        for table_name, sql in tables:
            try:
                print(f"\n📋 Creating {table_name}...")
                cursor.execute(sql)
                conn.commit()
                print(f"✅ {table_name} table created/verified")
            except mysql.connector.Error as e:
                if "already exists" in str(e):
                    print(f"⚠️  {table_name} already exists (skipping)")
                else:
                    print(f"❌ Error creating {table_name}: {e}")
                    conn.rollback()
                    return False
        
        # Verify tables
        print(f"\n🔍 Verifying tables...")
        cursor.execute(f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='{config['database']}'")
        tables_found = cursor.fetchall()
        plaid_tables = [t[0] for t in tables_found if 'plaid' in t[0]]
        
        for table in plaid_tables:
            print(f"  ✅ {table}")
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ {db_name} schema migration completed successfully!")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Database error for {db_name}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error for {db_name}: {e}")
        return False


def main():
    """Main function"""
    print("\n" + "="*70)
    print("PLAID INTEGRATION - MYSQL SCHEMA MIGRATION")
    print("="*70)
    print(f"Timestamp: {datetime.now().isoformat()}\n")
    
    results = {}
    
    for db_name, config in DB_CONFIGS.items():
        results[db_name] = apply_schema(db_name, config)
    
    # Summary
    print(f"\n{'='*70}")
    print("MIGRATION SUMMARY")
    print(f"{'='*70}")
    
    successful = sum(1 for v in results.values() if v)
    total = len(results)
    
    for db_name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status}: {db_name}")
    
    print(f"\nTotal: {successful}/{total} databases updated")
    
    if successful == total:
        print(f"\n🎉 All Plaid tables created successfully!")
        return 0
    else:
        print(f"\n⚠️  Some migrations failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
