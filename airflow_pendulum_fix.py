"""
Airflow Pendulum Compatibility Fix
Fixes the Pendulum 3.x compatibility issue with Airflow on Python 3.12
"""
import os
import sys
import warnings

# Apply pendulum compatibility patch before importing airflow
def patch_pendulum():
    """Patch pendulum to work with Airflow."""
    try:
        import pendulum
        
        # If pendulum 3.x, patch the timezone function
        if hasattr(pendulum, '__version__') and pendulum.__version__.startswith('3.'):
            print("⚠️  Detected Pendulum 3.x - applying compatibility patch...")
            
            # Monkey patch the timezone function
            if hasattr(pendulum, 'tz'):
                # Store original timezone function
                original_timezone = getattr(pendulum.tz, 'timezone', None)
                
                if original_timezone is None or not callable(original_timezone):
                    # Create a wrapper that makes tz.timezone callable
                    def timezone_wrapper(name):
                        import zoneinfo
                        return zoneinfo.ZoneInfo(name)
                    
                    pendulum.tz.timezone = timezone_wrapper
                    print("✅ Applied Pendulum timezone compatibility patch")
                    
    except ImportError:
        print("⚠️  Pendulum not installed")
    except Exception as e:
        print(f"⚠️  Could not patch Pendulum: {e}")

# Apply the patch before any other imports
patch_pendulum()

# Now set up Airflow environment
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

def test_airflow_import():
    """Test if Airflow can be imported successfully."""
    try:
        import airflow
        from airflow import settings
        print(f"✅ Airflow {airflow.__version__} loaded successfully")
        
        # Test configuration
        from airflow.configuration import conf
        mp_method = conf.get('core', 'mp_start_method', fallback='fork')
        executor = conf.get('core', 'executor', fallback='SequentialExecutor')
        print(f"📋 Configuration: MP Method={mp_method}, Executor={executor}")
        return True
        
    except Exception as e:
        print(f"❌ Error loading Airflow: {e}")
        return False

def test_mysql_connection():
    """Test MySQL connection before initializing Airflow."""
    try:
        from airflow.configuration import conf
        sql_conn = conf.get('core', 'sql_alchemy_conn')
        
        if 'mysql' in sql_conn:
            try:
                import pymysql
            except ImportError:
                print("❌ 'pymysql' is not installed. Please run: pip install pymysql")
                return False

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
        if not test_airflow_import():
            return
            
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
        if not test_airflow_import():
            return
            
        from airflow.configuration import conf
        print("\n📋 Current Airflow Configuration:")
        for section in conf.sections():
            print(f"[{section}]")
            for key, value in conf.items(section):
                # Mask passwords in output
                if 'password' in key.lower() or 'secret' in key.lower():
                    value = '***MASKED***'
                print(f"  {key} = {value}")
            print()
    except Exception as e:
        print(f"❌ Config listing failed: {e}")

if __name__ == "__main__":
    print("🔧 Airflow Pendulum Compatibility Fix")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "init":
            init_airflow_db()
        elif command == "config":
            list_airflow_config()
        elif command == "test":
            print("Testing Airflow import...")
            if test_airflow_import():
                print("Testing MySQL connection...")
                test_mysql_connection()
        else:
            print("Available commands: init, config, test")
    else:
        print("Testing Airflow compatibility...")
        if test_airflow_import():
            print("\n✅ Airflow is working! You can now use:")
            print("  python airflow_pendulum_fix.py init    - Initialize database")
            print("  python airflow_pendulum_fix.py config  - Show configuration") 
            print("  python airflow_pendulum_fix.py test    - Test connections")
        else:
            print("\n❌ Airflow compatibility issues detected")