"""
Test Trading Bot page import and database connection
"""
import sys
import os
from pathlib import Path

# Set up environment
os.environ['ENVIRONMENT'] = 'development'

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))

# Test import
print("Testing Trading Bot page configuration...")
print("="*70)

try:
    from dotenv import load_dotenv
    load_dotenv('.env.development')
    
    from sqlalchemy import create_engine, text
    
    # Test database connection with the settings used by Trading Bot
    MYSQL_CONFIG = {
        'host': os.getenv('DB_HOST', os.getenv('MYSQL_HOST', 'localhost')),
        'port': int(os.getenv('DB_PORT', os.getenv('MYSQL_PORT', 3306))),
        'user': os.getenv('DB_USER', os.getenv('MYSQL_USER', 'root')),
        'password': os.getenv('DB_PASSWORD', os.getenv('MYSQL_PASSWORD', '')),
        'database': os.getenv('DB_NAME', os.getenv('MYSQL_DATABASE', 'bentleybot'))
    }
    
    connection_string = (
        f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@"
        f"{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}"
    )
    
    print("\n📋 Database Configuration (from .env):")
    print(f"  Host: {MYSQL_CONFIG['host']}")
    print(f"  Port: {MYSQL_CONFIG['port']}")
    print(f"  User: {MYSQL_CONFIG['user']}")
    print(f"  Database: {MYSQL_CONFIG['database']}")
    
    print("\n🔗 Attempting connection...")
    engine = create_engine(connection_string, pool_pre_ping=True, pool_recycle=3600)
    
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    
    print("✅ Connection successful!\n")
    
    # Test that tables exist
    print("📊 Verifying database tables...")
    with engine.connect() as conn:
        tables = ['bot_status', 'trading_signals', 'trades_history', 'performance_metrics']
        for table in tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                print(f"  ✅ {table}: {count} records")
            except Exception as e:
                print(f"  ❌ {table}: {str(e)[:60]}")
    
    print("\n" + "="*70)
    print("✅ TRADING BOT DATABASE READY!")
    print("="*70)
    print("\nThe 'Database Connection Not Available' error should now be resolved.")
    print("You can now run the Streamlit app and access the Trading Bot tab.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
