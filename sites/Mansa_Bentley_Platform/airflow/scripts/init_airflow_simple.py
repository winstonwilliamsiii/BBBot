"""
Simple Airflow Database Initialization for Windows
Bypasses the ThreadPoolExecutor issue by using direct database initialization
"""
import os
import sys

# Apply Windows compatibility patches
if not hasattr(os, 'register_at_fork'):
    def register_at_fork(*, before=None, after_in_parent=None, after_in_child=None):
        pass
    os.register_at_fork = register_at_fork

# Set environment variables
os.environ.setdefault('AIRFLOW__CORE__MP_START_METHOD', 'spawn')
os.environ.setdefault('AIRFLOW__CORE__EXECUTOR', 'LocalExecutor')
os.environ.setdefault('AIRFLOW_HOME', r'C:\Users\winst\BentleyBudgetBot\airflow_config')

def init_airflow_db_simple():
    """Initialize Airflow database using a simplified approach."""
    try:
        print("🚀 Initializing Airflow database...")
        
        # Import Airflow components
        from airflow import settings
        from airflow.models import DagBag
        from sqlalchemy import create_engine, text
        
        # Get database URL from configuration
        from airflow.configuration import conf
        sql_conn = conf.get('core', 'sql_alchemy_conn')
        
        print(f"📋 Database URL: {sql_conn.replace('://root:', '://root:***@')}")
        
        # Create engine and test connection
        engine = create_engine(sql_conn)
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT VERSION()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to MySQL: {version}")
        
        # Try to initialize database
        try:
            from airflow.utils.db import initdb
            initdb()
            print("✅ Airflow database initialized successfully!")
            
            # Test by creating a simple query
            with engine.connect() as connection:
                result = connection.execute(text("SHOW TABLES LIKE 'airflow_%'"))
                tables = result.fetchall()
                print(f"✅ Created {len(tables)} Airflow tables")
                
            return True
            
        except Exception as e:
            print(f"❌ Standard initialization failed: {e}")
            print("🔄 Trying alternative initialization...")
            
            # Alternative: Create tables manually
            from airflow.models.base import Base
            from airflow import settings
            
            Base.metadata.create_all(settings.engine)
            print("✅ Database tables created using alternative method!")
            
            return True
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def verify_installation():
    """Verify that Airflow is properly set up."""
    try:
        from airflow import __version__
        from airflow.configuration import conf
        
        print(f"\n📊 Airflow Installation Summary:")
        print(f"   Version: {__version__}")
        print(f"   Database: {conf.get('core', 'sql_alchemy_conn').split('@')[1]}")
        print(f"   Executor: {conf.get('core', 'executor')}")
        print(f"   DAGs Folder: {conf.get('core', 'dags_folder')}")
        
        return True
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("Airflow Database Initialization for Windows")
    print("=" * 50)
    
    if init_airflow_db_simple():
        print("\n" + "=" * 50)
        verify_installation()
        print("\n✅ Setup Complete!")
        print("\nNext steps:")
        print("1. Test configuration: .\\airflow.bat config")
        print("2. Start webserver: .\\airflow.bat webserver")
        print("3. View UI at: http://localhost:8080")
    else:
        print("\n❌ Setup failed. Check the errors above.")