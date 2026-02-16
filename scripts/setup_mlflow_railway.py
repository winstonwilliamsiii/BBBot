#!/usr/bin/env python3
"""
Setup MLflow Database on Railway MySQL
Creates mlflow_db database and initializes MLflow tracking tables
"""

import os
import sys
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import mlflow
from mlflow.tracking import MlflowClient

# Load environment variables
load_dotenv()

# Railway MySQL Configuration
RAILWAY_CONFIG = {
    'host': os.getenv('RAILWAY_MYSQL_HOST', 'nozomi.proxy.rlwy.net'),
    'port': int(os.getenv('RAILWAY_MYSQL_PORT', '54537')),
    'user': os.getenv('RAILWAY_MYSQL_USER', 'root'),
    'password': os.getenv('RAILWAY_MYSQL_PASSWORD', 'cBlIUSygvPJCgPbNKHePJekQlClRamri')
}

MLFLOW_DATABASE = 'mlflow_db'

def create_mlflow_database():
    """Create mlflow_db database on Railway MySQL"""
    print("=" * 60)
    print("🚀 Setting up MLflow Database on Railway MySQL")
    print("=" * 60)
    
    try:
        # Connect to Railway MySQL (without database specified)
        print(f"\n📡 Connecting to Railway MySQL...")
        print(f"   Host: {RAILWAY_CONFIG['host']}")
        print(f"   Port: {RAILWAY_CONFIG['port']}")
        print(f"   User: {RAILWAY_CONFIG['user']}")
        
        connection = mysql.connector.connect(
            host=RAILWAY_CONFIG['host'],
            port=RAILWAY_CONFIG['port'],
            user=RAILWAY_CONFIG['user'],
            password=RAILWAY_CONFIG['password']
        )
        
        if connection.is_connected():
            print(f"✅ Connected to Railway MySQL")
            
            cursor = connection.cursor()
            
            # Check if mlflow_db exists
            cursor.execute("SHOW DATABASES LIKE %s", (MLFLOW_DATABASE,))
            result = cursor.fetchone()
            
            if result:
                print(f"\n⚠️  Database '{MLFLOW_DATABASE}' already exists")
                print(f"   Verifying MLflow tables...")
            else:
                # Create mlflow_db database
                print(f"\n📦 Creating database: {MLFLOW_DATABASE}")
                cursor.execute(f"CREATE DATABASE {MLFLOW_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"✅ Database '{MLFLOW_DATABASE}' created successfully")
            
            # Use the mlflow_db database
            cursor.execute(f"USE {MLFLOW_DATABASE}")
            
            # Check for MLflow tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            print(f"\n📊 Current tables in '{MLFLOW_DATABASE}':")
            if table_names:
                for table in table_names:
                    print(f"   - {table}")
            else:
                print(f"   (No tables yet - MLflow will create them on first use)")
            
            cursor.close()
            connection.close()
            
            return True
            
    except Error as e:
        print(f"\n❌ Error connecting to Railway MySQL: {e}")
        return False

def initialize_mlflow_tracking():
    """Initialize MLflow tracking with Railway MySQL backend"""
    print("\n" + "=" * 60)
    print("🔬 Initializing MLflow Tracking")
    print("=" * 60)
    
    try:
        # Build MLflow tracking URI for Railway MySQL
        tracking_uri = (
            f"mysql+pymysql://{RAILWAY_CONFIG['user']}:{RAILWAY_CONFIG['password']}"
            f"@{RAILWAY_CONFIG['host']}:{RAILWAY_CONFIG['port']}/{MLFLOW_DATABASE}"
        )
        
        print(f"\n📍 Setting MLflow tracking URI:")
        print(f"   mysql+pymysql://{RAILWAY_CONFIG['user']}:***@{RAILWAY_CONFIG['host']}:{RAILWAY_CONFIG['port']}/{MLFLOW_DATABASE}")
        
        # Set tracking URI
        mlflow.set_tracking_uri(tracking_uri)
        
        # Create/Set experiment
        experiment_name = "bentley_bot_analysis"
        print(f"\n🧪 Creating experiment: {experiment_name}")
        mlflow.set_experiment(experiment_name)
        
        # Get MLflow client
        client = MlflowClient()
        
        # List experiments to verify connection
        experiments = client.search_experiments()
        print(f"\n✅ MLflow connected successfully!")
        print(f"\n📋 Experiments in MLflow:")
        for exp in experiments:
            print(f"   - {exp.name} (ID: {exp.experiment_id})")
        
        # Verify database tables were created
        print(f"\n🔍 Verifying MLflow tables on Railway...")
        verify_mlflow_tables()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error initializing MLflow: {e}")
        print(f"\n💡 Tip: Make sure 'pymysql' is installed:")
        print(f"   pip install pymysql")
        return False

def verify_mlflow_tables():
    """Verify MLflow tables were created"""
    try:
        connection = mysql.connector.connect(
            host=RAILWAY_CONFIG['host'],
            port=RAILWAY_CONFIG['port'],
            user=RAILWAY_CONFIG['user'],
            password=RAILWAY_CONFIG['password'],
            database=MLFLOW_DATABASE
        )
        
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        expected_tables = [
            'experiments',
            'runs',
            'metrics',
            'params',
            'tags',
            'registered_models',
            'model_versions'
        ]
        
        print(f"\n📊 MLflow Tables Created:")
        for table in table_names:
            status = "✅" if table in expected_tables else "📝"
            print(f"   {status} {table}")
        
        missing_tables = [t for t in expected_tables if t not in table_names]
        if missing_tables:
            print(f"\n⏳ Pending tables (will be created on first use):")
            for table in missing_tables:
                print(f"   - {table}")
        
        cursor.close()
        connection.close()
        
    except Error as e:
        print(f"\n⚠️  Could not verify tables: {e}")

def print_connection_info():
    """Print connection information for Streamlit secrets"""
    print("\n" + "=" * 60)
    print("📋 Streamlit Cloud Secrets Configuration")
    print("=" * 60)
    print(f"""
Add these to your Streamlit Cloud secrets:

[mlflow]
MLFLOW_MYSQL_HOST = "{RAILWAY_CONFIG['host']}"
MLFLOW_MYSQL_PORT = "{RAILWAY_CONFIG['port']}"
MLFLOW_MYSQL_DATABASE = "{MLFLOW_DATABASE}"
MLFLOW_MYSQL_USER = "{RAILWAY_CONFIG['user']}"
MLFLOW_MYSQL_PASSWORD = "{RAILWAY_CONFIG['password']}"

[mlflow_tracking]
MLFLOW_TRACKING_URI = "mysql+pymysql://{RAILWAY_CONFIG['user']}:{RAILWAY_CONFIG['password']}@{RAILWAY_CONFIG['host']}:{RAILWAY_CONFIG['port']}/{MLFLOW_DATABASE}"
""")
    print("=" * 60)

def main():
    """Main setup function"""
    print("\n🚀 Bentley Budget Bot - MLflow Railway Setup\n")
    
    # Check password
    if RAILWAY_CONFIG['password'] == '<from_streamlit_secrets>':
        print("❌ ERROR: Railway MySQL password not set!")
        print("Please update RAILWAY_MYSQL_PASSWORD in your .env file")
        print("Password can be found in Railway → MySQL service → Variables tab")
        sys.exit(1)
    
    # Step 1: Create database
    if not create_mlflow_database():
        print("\n❌ Failed to create database")
        sys.exit(1)
    
    # Step 2: Initialize MLflow tracking
    if not initialize_mlflow_tracking():
        print("\n❌ Failed to initialize MLflow tracking")
        sys.exit(1)
    
    # Step 3: Print connection info
    print_connection_info()
    
    print("\n" + "=" * 60)
    print("✅ MLflow Railway Setup Complete!")
    print("=" * 60)
    print("\n🎯 Next Steps:")
    print("1. Add the secrets above to Streamlit Cloud")
    print("2. Update bbbot1_pipeline/mlflow_config.py to support Railway")
    print("3. Test Investment Analysis page on Streamlit Cloud")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
