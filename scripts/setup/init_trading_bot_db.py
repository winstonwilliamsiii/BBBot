"""
Initialize Trading Bot Database Schema
Creates necessary tables for the ML Trading Bot Dashboard
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def load_env():
    """Load environment variables"""
    env_file = Path(__file__).parent.parent.parent / '.env.development'
    if env_file.exists():
        load_dotenv(env_file)
    else:
        load_dotenv()

def get_engine(database=None):
    """Create database engine"""
    host = os.getenv('DB_HOST', os.getenv('MYSQL_HOST', 'localhost'))
    port = int(os.getenv('DB_PORT', os.getenv('MYSQL_PORT', 3306)))
    user = os.getenv('DB_USER', os.getenv('MYSQL_USER', 'root'))
    password = os.getenv('DB_PASSWORD', os.getenv('MYSQL_PASSWORD', ''))
    
    if database is None:
        database = os.getenv('DB_NAME', os.getenv('MYSQL_DATABASE', 'bentley_bot_dev'))
    
    connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    return create_engine(connection_string, pool_pre_ping=True, pool_recycle=3600)

def create_schema():
    """Create required tables for trading bot"""
    # First, create the database if it doesn't exist
    database_name = os.getenv('DB_NAME', os.getenv('MYSQL_DATABASE', 'bentley_bot_dev'))
    
    try:
        # Connect to MySQL without specifying a database to create it
        engine_root = get_engine('mysql')
        with engine_root.connect() as conn:
            print(f"\nCreating database '{database_name}' if not exists...")
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{database_name}`"))
            conn.commit()
        print(f"✅ Database '{database_name}' ready")
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False
    
    # Now connect to the actual database
    engine = get_engine()
    
    print("\n" + "="*70)
    print("TRADING BOT DATABASE SCHEMA INITIALIZATION")
    print("="*70)
    
    schema_sql = """
    CREATE TABLE IF NOT EXISTS bot_status (
        id INT AUTO_INCREMENT PRIMARY KEY,
        status VARCHAR(50) NOT NULL DEFAULT 'inactive',
        strategy VARCHAR(100),
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_timestamp (timestamp)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    
    CREATE TABLE IF NOT EXISTS trading_signals (
        id INT AUTO_INCREMENT PRIMARY KEY,
        ticker VARCHAR(10) NOT NULL,
        signal_type INT NOT NULL,
        price DECIMAL(15, 4) NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        strategy VARCHAR(100),
        confidence DECIMAL(5, 4),
        INDEX idx_ticker_timestamp (ticker, timestamp),
        INDEX idx_strategy (strategy)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    
    CREATE TABLE IF NOT EXISTS trades_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        ticker VARCHAR(10) NOT NULL,
        action VARCHAR(10) NOT NULL,
        shares DECIMAL(15, 4) NOT NULL,
        price DECIMAL(15, 4) NOT NULL,
        value DECIMAL(15, 4) NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(20) DEFAULT 'EXECUTED',
        order_id VARCHAR(50),
        strategy VARCHAR(100),
        INDEX idx_ticker_timestamp (ticker, timestamp),
        INDEX idx_strategy (strategy)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    
    CREATE TABLE IF NOT EXISTS performance_metrics (
        id INT AUTO_INCREMENT PRIMARY KEY,
        date DATE NOT NULL,
        total_trades INT DEFAULT 0,
        buy_trades INT DEFAULT 0,
        sell_trades INT DEFAULT 0,
        total_value DECIMAL(15, 4) DEFAULT 0,
        strategy VARCHAR(100),
        win_rate DECIMAL(5, 4),
        INDEX idx_date (date),
        INDEX idx_strategy (strategy),
        UNIQUE KEY unique_date_strategy (date, strategy)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    try:
        with engine.connect() as conn:
            for statement in schema_sql.split(';'):
                if statement.strip():
                    print(f"\nExecuting: {statement[:50]}...")
                    conn.execute(text(statement))
            conn.commit()
        
        print("\n✅ Trading Bot Database Schema Created Successfully!")
        print("\nTables created:")
        print("  - bot_status")
        print("  - trading_signals")
        print("  - trades_history")
        print("  - performance_metrics")
        
        return True
    
    except Exception as e:
        print(f"\n❌ Error creating schema: {e}")
        return False

if __name__ == "__main__":
    load_env()
    success = create_schema()
    sys.exit(0 if success else 1)
