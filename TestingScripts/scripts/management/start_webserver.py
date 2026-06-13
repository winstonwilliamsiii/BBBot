#!/usr/bin/env python3
"""
Simple Airflow Webserver Starter for Windows
Handles all compatibility issues and starts the webserver properly
"""
import os
import sys
import warnings
import time

# Apply Windows compatibility patch FIRST
if not hasattr(os, 'register_at_fork'):
    def register_at_fork(*, before=None, after_in_parent=None, after_in_child=None):
        pass
    os.register_at_fork = register_at_fork
    print("✅ Applied Windows compatibility patch")

# Set up environment
os.environ.setdefault('AIRFLOW_HOME', r'C:\Users\winst\BentleyBudgetBot\airflow_config')
os.environ.setdefault('AIRFLOW__CORE__MP_START_METHOD', 'spawn')
os.environ.setdefault('AIRFLOW__CORE__EXECUTOR', 'LocalExecutor')
os.environ.setdefault('AIRFLOW__CORE__LOAD_EXAMPLES', 'False')
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

# Suppress warnings
warnings.filterwarnings("ignore", message=".*can be run on POSIX-compliant.*")

print("🔧 Bentley Budget Bot - Airflow Webserver Startup")
print("=" * 50)
print(f"📍 AIRFLOW_HOME: {os.environ['AIRFLOW_HOME']}")
print(f"🔧 MP_START_METHOD: {os.environ['AIRFLOW__CORE__MP_START_METHOD']}")
print(f"⚡ EXECUTOR: {os.environ['AIRFLOW__CORE__EXECUTOR']}")

def test_mysql_connection():
    """Test MySQL connection first"""
    try:
        import pymysql
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='root',  # Update with actual password
            database='mansa_bot',
            charset='utf8mb4'
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ MySQL connection successful: {version[0]}")
        connection.close()
        return True
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        return False

def start_webserver():
    """Start the Airflow webserver with proper error handling"""
    try:
        print("\n🧪 Testing MySQL connection...")
        if not test_mysql_connection():
            print("⚠️  MySQL connection failed, but continuing...")
        
        print("📦 Loading Airflow...")
        import airflow
        print(f"✅ Airflow {airflow.__version__} loaded successfully")
        
        print("🌐 Starting webserver on port 8080...")
        print("🎯 Access the UI at: http://localhost:8080")
        print("⏹️  Press Ctrl+C to stop")
        
        # Import and start webserver
        from airflow.cli.commands.webserver_command import webserver
        webserver(['-p', '8080', '--debug'])
        
    except KeyboardInterrupt:
        print("\n🛑 Webserver stopped by user")
    except Exception as e:
        print(f"❌ Error starting webserver: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure MySQL is running")
        print("2. Verify database 'mansa_bot' exists")
        print("3. Run: python airflow_windows.py init")
        return False
    
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--test-only':
        print("🧪 Testing connections only...")
        test_mysql_connection()
        try:
            import airflow
            print(f"✅ Airflow import successful: {airflow.__version__}")
        except Exception as e:
            print(f"❌ Airflow import failed: {e}")
    else:
        start_webserver()