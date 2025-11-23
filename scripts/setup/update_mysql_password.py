"""
MySQL Password Update Script for Airflow Configuration
This script helps you update the MySQL password in your Airflow configuration safely.
"""
import os
import sys
from getpass import getpass

def update_mysql_password():
    """Update MySQL password in Airflow configuration."""
    
    config_file = r'C:\Users\winst\BentleyBudgetBot\airflow_config\airflow.cfg'
    
    print("🔧 MySQL Password Update for Airflow")
    print("=" * 40)
    
    # Get password securely
    print("Enter your MySQL root password (characters won't be shown):")
    password = getpass("MySQL Password: ")
    
    if not password:
        print("❌ Password cannot be empty!")
        return False
    
    try:
        # Read current configuration
        with open(config_file, 'r') as file:
            content = file.read()
        
        # Replace password placeholders
        old_conn = "sql_alchemy_conn = mysql+pymysql://root:password@localhost:3306/mansa_bot"
        new_conn = f"sql_alchemy_conn = mysql+pymysql://root:{password}@localhost:3306/mansa_bot"
        
        old_backend = "result_backend = db+mysql+pymysql://root:password@localhost:3306/mansa_bot"
        new_backend = f"result_backend = db+mysql+pymysql://root:{password}@localhost:3306/mansa_bot"
        
        # Update content
        content = content.replace(old_conn, new_conn)
        content = content.replace(old_backend, new_backend)
        
        # Write back to file
        with open(config_file, 'w') as file:
            file.write(content)
        
        print("✅ Password updated successfully!")
        print(f"📁 Updated file: {config_file}")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_file}")
        return False
    except Exception as e:
        print(f"❌ Error updating password: {e}")
        return False

def test_connection():
    """Test MySQL connection after password update."""
    print("\n🧪 Testing MySQL connection...")
    os.system(r'.\airflow.bat test')

def main():
    """Main function."""
    print("This script will help you update your MySQL password for Airflow.\n")
    
    if update_mysql_password():
        print("\n" + "=" * 50)
        print("✅ Configuration updated!")
        print("\nNext steps:")
        print("1. Test connection: .\\airflow.bat test")
        print("2. Initialize database: .\\airflow.bat init")
        print("3. Start Airflow: .\\airflow.bat webserver")
        
        # Ask if user wants to test connection now
        test_now = input("\nWould you like to test the connection now? (y/n): ").lower()
        if test_now == 'y':
            test_connection()
    else:
        print("❌ Password update failed. Please check the error above.")

if __name__ == "__main__":
    main()
    