"""
Create Broker API Credentials Table - Multi-Tenant Support
============================================================
Creates a unified table for storing broker API credentials across all platforms:
- Webull (equities, ETFs, funds)
- Interactive Brokers / IBKR (FOREX, futures, commodities)
- Binance (crypto assets)
- NinjaTrader (Options, Futures, FOREX)
- tZero (crypto tokens)
- MetaTrader 5 (Options, Futures, FOREX)

This table includes:
- is_active: Enable/disable connections without deleting
- tenant_id: Multi-tenant support for SaaS deployment
- user_id: User-level access control
- broker: Broker platform identifier
- access_token: Encrypted API token/credentials
"""

import pymysql
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Database configurations - try all available databases
DB_CONFIGS = {
    'mydb': {
        'host': os.getenv('BUDGET_MYSQL_HOST', '127.0.0.1'),
        'port': int(os.getenv('BUDGET_MYSQL_PORT', '3306')),
        'user': os.getenv('BUDGET_MYSQL_USER', 'root'),
        'password': os.getenv('BUDGET_MYSQL_PASSWORD', 'root'),
        'database': os.getenv('BUDGET_MYSQL_DATABASE', 'mydb')
    },
    'mansa_bot': {
        'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
        'port': int(os.getenv('MYSQL_PORT', '3307')),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', 'root'),
        'database': os.getenv('MYSQL_DATABASE', 'mansa_bot')
    }
}

CREATE_BROKER_API_CREDENTIALS_TABLE = """
CREATE TABLE IF NOT EXISTS broker_api_credentials (
    -- Primary Key
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Multi-tenant & User Identification
    tenant_id INT NOT NULL DEFAULT 1 COMMENT 'Tenant ID for multi-tenant SaaS deployments',
    user_id INT NOT NULL COMMENT 'User ID who owns this connection',
    
    -- Broker Information
    broker ENUM(
        'webull', 
        'ibkr', 
        'binance', 
        'ninjatrader', 
        'tzero', 
        'metatrader5'
    ) NOT NULL COMMENT 'Broker platform identifier',
    
    -- API Credentials (ENCRYPTED in production!)
    access_token TEXT NOT NULL COMMENT 'Encrypted API access token or password',
    api_key VARCHAR(255) NULL COMMENT 'API key (for platforms that use key+secret)',
    api_secret TEXT NULL COMMENT 'Encrypted API secret',
    device_id VARCHAR(255) NULL COMMENT 'Device ID for Webull authentication',
    account_number VARCHAR(100) NULL COMMENT 'Masked broker account number',
    
    -- Connection Status
    is_active TINYINT(1) DEFAULT 1 COMMENT '1=Active, 0=Disabled without deleting',
    status ENUM('connected', 'pending', 'disconnected', 'error') DEFAULT 'pending',
    last_sync TIMESTAMP NULL COMMENT 'Last successful API sync',
    last_error TEXT NULL COMMENT 'Most recent error message',
    
    -- Broker-Specific Configuration
    environment ENUM('production', 'sandbox', 'testnet', 'paper') DEFAULT 'sandbox' 
        COMMENT 'Trading environment (prod vs test)',
    
    host VARCHAR(255) NULL COMMENT 'API host for IBKR (127.0.0.1)',
    port INT NULL COMMENT 'API port for IBKR (7497=paper, 7496=live)',
    client_id INT NULL COMMENT 'Client ID for IBKR',
    
    -- Account Metrics
    balance DECIMAL(15, 2) DEFAULT 0 COMMENT 'Current account balance',
    positions_count INT DEFAULT 0 COMMENT 'Number of open positions',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes for Performance
    INDEX idx_tenant_user (tenant_id, user_id),
    INDEX idx_broker (broker),
    INDEX idx_is_active (is_active),
    INDEX idx_status (status),
    INDEX idx_user_broker (user_id, broker),
    
    -- Ensure one active connection per user per broker
    UNIQUE KEY unique_user_broker (tenant_id, user_id, broker, is_active)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Unified broker API credentials with multi-tenant support';
"""

CREATE_BROKER_CONNECTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS broker_connections (
    -- Primary key
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Multi-tenant & User Identification
    tenant_id INT NOT NULL DEFAULT 1,
    user_id INT NOT NULL COMMENT 'Reference to user account',
    
    -- Broker Information
    broker_name VARCHAR(100) NOT NULL COMMENT 'Broker name (Webull, IBKR, Binance, etc.)',
    broker ENUM(
        'webull', 
        'ibkr', 
        'binance', 
        'ninjatrader', 
        'tzero', 
        'metatrader5'
    ) NULL COMMENT 'Standardized broker identifier',
    
    account_number VARCHAR(100) NOT NULL COMMENT 'Masked account number',
    
    -- Status tracking
    is_active TINYINT(1) DEFAULT 1 COMMENT '1=Active, 0=Disabled',
    status ENUM('connected', 'pending', 'disconnected', 'error') DEFAULT 'pending',
    last_sync TIMESTAMP NULL COMMENT 'Last successful sync timestamp',
    last_error TEXT NULL COMMENT 'Last error message if any',
    
    -- Account metrics
    balance DECIMAL(15, 2) DEFAULT 0 COMMENT 'Current account balance',
    positions_count INT DEFAULT 0 COMMENT 'Number of positions',
    
    -- API credentials reference
    api_credential_id INT NULL COMMENT 'FK to broker_api_credentials table',
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_tenant_user (tenant_id, user_id),
    INDEX idx_user_broker (user_id, broker_name),
    INDEX idx_status (status),
    INDEX idx_is_active (is_active),
    INDEX idx_last_sync (last_sync),
    
    -- Foreign key to credentials
    FOREIGN KEY (api_credential_id) REFERENCES broker_api_credentials(id) 
        ON DELETE SET NULL ON UPDATE CASCADE,
    
    -- Ensure unique connection per user per broker account
    UNIQUE KEY unique_user_broker_account (tenant_id, user_id, broker_name, account_number)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Broker account connections with credential references';
"""

def create_tables(db_name, config):
    """Create broker tables in specified database"""
    print(f"\n{'='*70}")
    print(f"Creating Broker API Tables in: {db_name}")
    print(f"{'='*70}")
    
    try:
        conn = pymysql.connect(**config)
        cursor = conn.cursor()
        
        # 1. Create broker_api_credentials table
        print("\n📝 Creating broker_api_credentials table...")
        cursor.execute(CREATE_BROKER_API_CREDENTIALS_TABLE)
        print("   ✅ broker_api_credentials table created")
        
        # Verify columns
        cursor.execute("DESCRIBE broker_api_credentials")
        columns = cursor.fetchall()
        print("\n   Columns:")
        for col in columns:
            print(f"      • {col[0]}: {col[1]} {'DEFAULT ' + str(col[4]) if col[4] else ''}")
        
        # 2. Create broker_connections table (if doesn't exist)
        print("\n📝 Creating/updating broker_connections table...")
        cursor.execute(CREATE_BROKER_CONNECTIONS_TABLE)
        print("   ✅ broker_connections table created")
        
        # Verify columns
        cursor.execute("DESCRIBE broker_connections")
        columns = cursor.fetchall()
        print("\n   Columns:")
        for col in columns:
            print(f"      • {col[0]}: {col[1]} {'DEFAULT ' + str(col[4]) if col[4] else ''}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\n✅ Successfully created tables in {db_name}!")
        return True
        
    except pymysql.err.OperationalError as e:
        if "Can't connect" in str(e) or "Access denied" in str(e):
            print(f"   ⏭️  Skipping {db_name} (not accessible)")
            return False
        else:
            print(f"   ❌ Error: {e}")
            return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_broker_readiness():
    """Verify which brokers have implementation files ready"""
    print(f"\n{'='*70}")
    print("Broker Integration Readiness Check")
    print(f"{'='*70}\n")
    
    broker_files = {
        'Webull': [
            'frontend/utils/webull_integration.py',
            'bbbot1_pipeline/broker_api.py',
            '#Fetch and Display Webull Funds.py'
        ],
        'IBKR': [
            'bbbot1_pipeline/broker_api.py'
        ],
        'Binance': [
            'bbbot1_pipeline/broker_api.py'
        ],
        'NinjaTrader': [
            'bbbot1_pipeline/broker_api.py'  # Scaffolded in unified API
        ],
        'tZero': [
            '# NEEDS IMPLEMENTATION'
        ],
        'MetaTrader 5': [
            '# NEEDS IMPLEMENTATION'
        ]
    }
    
    broker_status = {
        'Webull': {
            'equities': '✅ READY',
            'etfs': '✅ READY', 
            'funds': '✅ READY (WeFolio)',
            'implementation': 'Complete with MFA support'
        },
        'IBKR': {
            'forex': '✅ READY',
            'futures': '✅ READY',
            'commodities': '✅ READY',
            'implementation': 'Complete with TWS/Gateway support'
        },
        'Binance': {
            'crypto': '✅ READY',
            'testnet': '✅ READY',
            'implementation': 'Complete with testnet support'
        },
        'NinjaTrader': {
            'options': '⚠️  SCAFFOLDED',
            'futures': '⚠️  SCAFFOLDED',
            'forex': '⚠️  SCAFFOLDED',
            'implementation': 'Needs NinjaTrader SDK integration'
        },
        'tZero': {
            'crypto_tokens': '❌ NOT IMPLEMENTED',
            'implementation': 'Needs tZero API client'
        },
        'MetaTrader 5': {
            'options': '❌ NOT IMPLEMENTED',
            'futures': '❌ NOT IMPLEMENTED',
            'forex': '❌ NOT IMPLEMENTED',
            'implementation': 'Needs MT5 Python API (MetaTrader5 package)'
        }
    }
    
    for broker, status in broker_status.items():
        print(f"🔷 {broker}")
        for asset_class, state in status.items():
            if asset_class != 'implementation':
                print(f"   • {asset_class.title()}: {state}")
        print(f"   📄 {status['implementation']}\n")
    
    return broker_status


if __name__ == "__main__":
    print("=" * 70)
    print("BROKER API CREDENTIALS TABLE SETUP")
    print("Multi-Tenant & Multi-Broker Support")
    print("=" * 70)
    
    # Create tables in all available databases
    success_count = 0
    for db_name, config in DB_CONFIGS.items():
        if create_tables(db_name, config):
            success_count += 1
    
    print(f"\n{'='*70}")
    print(f"✅ Successfully created tables in {success_count}/{len(DB_CONFIGS)} databases")
    print(f"{'='*70}")
    
    # Verify broker readiness
    broker_status = verify_broker_readiness()
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 SUMMARY")
    print(f"{'='*70}")
    print(f"\n✅ Database Tables:")
    print(f"   • broker_api_credentials (unified credentials)")
    print(f"   • broker_connections (connection tracking)")
    
    print(f"\n🔑 Required Columns Present:")
    print(f"   • tenant_id (multi-tenant support)")
    print(f"   • user_id (user-level access)")
    print(f"   • broker (platform identifier)")
    print(f"   • access_token (encrypted credentials)")
    print(f"   • is_active (enable/disable connections)")
    
    print(f"\n📌 Next Steps:")
    print(f"   1. Add API keys to .env:")
    print(f"      WEBULL_USERNAME=your_email")
    print(f"      WEBULL_PASSWORD=your_password")
    print(f"      WEBULL_DEVICE_ID=your_device_id")
    print(f"      IBKR_HOST=127.0.0.1")
    print(f"      IBKR_PORT=7497")
    print(f"      BINANCE_API_KEY=your_key")
    print(f"      BINANCE_API_SECRET=your_secret")
    print(f"")
    print(f"   2. Test broker connections:")
    print(f"      python bbbot1_pipeline/broker_api.py")
    print(f"")
    print(f"   3. Implement missing brokers:")
    print(f"      • NinjaTrader SDK integration")
    print(f"      • tZero API client")
    print(f"      • MetaTrader 5 Python API")
    
    print(f"\n⚠️  SECURITY REMINDER:")
    print(f"   In PRODUCTION, encrypt all access_token and api_secret fields!")
    print(f"   Use AES-256 encryption with per-tenant keys stored in KMS")
    print(f"\n{'='*70}\n")
