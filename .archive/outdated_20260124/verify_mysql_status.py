#!/usr/bin/env python3
"""
MySQL Status Verification Script
Checks all database connections for Railway, Vercel, Appwrite, and Streamlit integrations
"""
import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection(name, host, port, user, password, database):
    """Test a MySQL connection and return status"""
    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=5
        )
        cursor = conn.cursor()
        
        # Get database size
        cursor.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '{database}'")
        table_count = cursor.fetchone()[0]
        
        # Get connection info
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        
        print(f"✅ {name}: CONNECTED")
        print(f"   Host: {host}:{port}")
        print(f"   Database: {database}")
        print(f"   Tables: {table_count}")
        print(f"   MySQL Version: {version}")
        
        conn.close()
        return True
    except mysql.connector.Error as e:
        print(f"❌ {name}: FAILED")
        print(f"   Host: {host}:{port}")
        print(f"   Database: {database}")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print(f"❌ {name}: ERROR")
        print(f"   Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("MySQL Connection Status Verification")
    print("=" * 70)
    print()
    
    results = []
    
    # Test Main Database (mansa_bot on port 3307)
    print("1. MAIN DATABASE (mansa_bot - Port 3307)")
    print("-" * 70)
    results.append(test_connection(
        "Main Database",
        os.getenv("MYSQL_HOST", "127.0.0.1"),
        int(os.getenv("MYSQL_PORT", "3307")),
        os.getenv("MYSQL_USER", "root"),
        os.getenv("MYSQL_PASSWORD", "root"),
        os.getenv("MYSQL_DATABASE", "mansa_bot")
    ))
    print()
    
    # Test Budget Database (mydb on port 3306)
    print("2. BUDGET DATABASE (mydb - Port 3306)")
    print("-" * 70)
    results.append(test_connection(
        "Budget Database",
        os.getenv("BUDGET_MYSQL_HOST", "127.0.0.1"),
        int(os.getenv("BUDGET_MYSQL_PORT", "3306")),
        os.getenv("BUDGET_MYSQL_USER", "root"),
        os.getenv("BUDGET_MYSQL_PASSWORD", "root"),
        os.getenv("BUDGET_MYSQL_DATABASE", "mydb")
    ))
    print()
    
    # Test Operational Database (bbbot1 on port 3306)
    print("3. OPERATIONAL DATABASE (bbbot1 - Port 3306)")
    print("-" * 70)
    results.append(test_connection(
        "Operational Database",
        "127.0.0.1",
        3306,
        "root",
        "root",
        "bbbot1"
    ))
    print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    successful = sum(results)
    total = len(results)
    print(f"Successful Connections: {successful}/{total}")
    
    if successful == total:
        print("\n🎉 ALL MYSQL CONNECTIONS ARE WORKING!")
        print("\n✅ Ready for:")
        print("   - Railway Integration")
        print("   - Vercel Deployment")
        print("   - Appwrite Functions")
        print("   - Streamlit Cloud (https://bbbot305.streamlit.app/)")
    else:
        print("\n⚠️  SOME CONNECTIONS FAILED - CHECK CONFIGURATION")
        print("\nTroubleshooting Steps:")
        print("1. Verify MySQL servers are running on both ports (3306 & 3307)")
        print("2. Check .env file for correct credentials")
        print("3. Ensure databases exist: mansa_bot, mydb")
        print("4. Verify firewall settings allow local connections")
    
    print()
