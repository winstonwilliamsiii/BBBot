"""
MySQL Database Setup for Airflow - Mansa Bot
Creates the mansa_bot database and configures it for Airflow
"""
import os
import sys
import pymysql
from urllib.parse import quote_plus

# Database configuration
DB_HOST = 'localhost'
DB_PORT = 3306
DB_NAME = 'mansa_bot'
DB_USER = 'root'  # Change this to your MySQL username
DB_PASSWORD = 'password'  # Change this to your MySQL password

def create_database():
    """Create the mansa_bot database if it doesn't exist."""
    try:
        # Connect without specifying database to create it
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ Database '{DB_NAME}' created successfully")
            
            # Create airflow user with proper privileges
            airflow_user = 'airflow'
            airflow_password = 'airflow123'
            
            cursor.execute(f"DROP USER IF EXISTS '{airflow_user}'@'localhost'")
            cursor.execute(f"CREATE USER '{airflow_user}'@'localhost' IDENTIFIED BY '{airflow_password}'")
            cursor.execute(f"GRANT ALL PRIVILEGES ON {DB_NAME}.* TO '{airflow_user}'@'localhost'")
            cursor.execute("FLUSH PRIVILEGES")
            
            print(f"✅ Airflow user '{airflow_user}' created with privileges")
            
        connection.commit()
        connection.close()
        
        return True
        
    except pymysql.Error as e:
        print(f"❌ MySQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_connection():
    """Test connection to the mansa_bot database."""
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user='airflow',  # Use airflow user
            password='airflow123',
            database=DB_NAME,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ Connected to MySQL {version[0]}")
            
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def update_airflow_config():
    """Update Airflow configuration with the correct connection string."""
    config_path = r'C:\Users\winst\BentleyBudgetBot\airflow_config\airflow.cfg'
    
    # Build connection string with proper encoding
    encoded_password = quote_plus('airflow123')
    connection_string = f"mysql+pymysql://airflow:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        with open(config_path, 'r') as file:
            content = file.read()
        
        # Replace the connection string
        old_pattern = "sql_alchemy_conn = mysql+pymysql://root:password@localhost:3306/mansa_bot"
        new_pattern = f"sql_alchemy_conn = {connection_string}"
        
        content = content.replace(old_pattern, new_pattern)
        
        # Also update result_backend
        old_backend = "result_backend = db+mysql+pymysql://root:password@localhost:3306/mansa_bot"
        new_backend = f"result_backend = db+{connection_string}"
        
        content = content.replace(old_backend, new_backend)
        
        with open(config_path, 'w') as file:
            file.write(content)
        
        print(f"✅ Airflow configuration updated with connection: {connection_string}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update config: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up MySQL for Airflow - Mansa Bot")
    print("=" * 50)
    
    print("\n1. Creating database and user...")
    if not create_database():
        print("❌ Database setup failed. Please check your MySQL credentials.")
        return False
    
    print("\n2. Testing database connection...")
    if not test_connection():
        print("❌ Connection test failed.")
        return False
    
    print("\n3. Updating Airflow configuration...")
    if not update_airflow_config():
        print("❌ Configuration update failed.")
        return False
    
    print("\n" + "=" * 50)
    print("✅ MySQL setup completed successfully!")
    print("\nDatabase Details:")
    print(f"  Host: {DB_HOST}:{DB_PORT}")
    print(f"  Database: {DB_NAME}")
    print(f"  User: airflow")
    print(f"  Password: airflow123")
    
    print("\nNext steps:")
    print("1. Initialize Airflow database: .\\airflow.bat init")
    print("2. Start Airflow webserver: .\\airflow.bat webserver")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "create":
            create_database()
        elif command == "test":
            test_connection()
        elif command == "config":
            update_airflow_config()
        else:
            print("Available commands: create, test, config")
    else:
        main()