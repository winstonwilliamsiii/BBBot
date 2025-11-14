"""
Windows-compatible Airflow configuration and wrapper
Fixes the 'register_at_fork' error on Windows systems
"""
import os
import sys
import warnings

# Monkey patch os.register_at_fork for Windows compatibility
if not hasattr(os, 'register_at_fork'):
    def register_at_fork(*, before=None, after_in_parent=None, after_in_child=None):
        """Dummy implementation of register_at_fork for Windows."""
        pass
    os.register_at_fork = register_at_fork
    print("Applied Windows compatibility patch for os.register_at_fork")

# Set environment variables for Windows compatibility
os.environ.setdefault('AIRFLOW__CORE__MP_START_METHOD', 'spawn')
os.environ.setdefault('AIRFLOW__CORE__EXECUTOR', 'LocalExecutor')
os.environ.setdefault('AIRFLOW_HOME', r'C:\Users\winst\BentleyBudgetBot\airflow_config')

# Suppress Windows warning
warnings.filterwarnings("ignore", message=".*can be run on POSIX-compliant.*")

try:
    import airflow
    from airflow import settings
    print(f"✅ Airflow {airflow.__version__} loaded successfully with Windows compatibility")
    
    # Test configuration
    from airflow.configuration import conf
    mp_method = conf.get('core', 'mp_start_method', fallback='fork')
    executor = conf.get('core', 'executor', fallback='SequentialExecutor')
    print(f"📋 Configuration: MP Method={mp_method}, Executor={executor}")
    
except Exception as e:
    print(f"❌ Error loading Airflow: {e}")
    sys.exit(1)

def test_mysql_connection():
    """Test MySQL connection before initializing Airflow."""
    try:
        from airflow.configuration import conf
        sql_conn = conf.get('core', 'sql_alchemy_conn')
        
        if 'mysql' in sql_conn:
            import pymysql
            from urllib.parse import urlparse
            
            # Parse connection string
            parsed = urlparse(sql_conn.replace('mysql+pymysql://', 'mysql://'))
            
            connection = pymysql.connect(
                host=parsed.hostname,
                port=parsed.port or 3306,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/'),
                charset='utf8mb4'
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                print(f"✅ MySQL connection successful: {version[0]}")
            
            connection.close()
            return True
        else:
            print("🔍 Using non-MySQL database, skipping connection test")
            return True
            
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        print("💡 Make sure MySQL is running and database 'mansa_bot' exists")
        return False


def init_airflow_db():
    """Initialize Airflow database safely."""
    try:
        # Test database connection first
        if not test_mysql_connection():
            print("❌ Database connection test failed. Cannot initialize.")
            return
            
        from airflow.utils.db import initdb
        initdb()
        print("✅ Airflow database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("💡 Try: python mysql_setup.py to set up the database")

def list_airflow_config():
    """List Airflow configuration safely."""
    try:
        from airflow.configuration import conf
        print("\n📋 Current Airflow Configuration:")
        for section in conf.sections():
            print(f"[{section}]")
            for key, value in conf.items(section):
                print(f"  {key} = {value}")
            print()
    except Exception as e:
        print(f"❌ Config listing failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "init":
            init_airflow_db()
        elif command == "config":
            list_airflow_config()
        elif command == "test":
            test_mysql_connection()
        else:
            print("Available commands: init, config, test")
    else:
        print("Airflow Windows compatibility wrapper loaded.")
        print("Usage: python airflow_windows.py [init|config]")