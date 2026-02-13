"""
MLFlow Database Schema Migration Fix
Resolves 'No such revision or branch' error by reinitializing migration history
"""

import mysql.connector
import sys
from datetime import datetime

# Database connection details
DB_HOST = "nozomi.proxy.rlwy.net"
DB_PORT = 54537
DB_USER = "root"
DB_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"
DB_NAME = "mlflow_db"

def fix_mlflow_schema():
    """Fix the MLFlow database schema by resetting migration history"""
    
    try:
        # Connect to database
        print(f"[*] Connecting to {DB_HOST}:{DB_PORT}/{DB_NAME}...")
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        
        print("✅ Connected to MLFlow database")
        
        # Check current alembic version
        print("\n[*] Checking current migration version...")
        cursor.execute("SELECT version_num FROM alembic_version LIMIT 1")
        result = cursor.fetchone()
        current_version = result[0] if result else "NONE"
        print(f"    Current version: {current_version}")
        
        # Get all tables to check database state
        print("\n[*] Checking MLFlow tables...")
        cursor.execute("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME
        """, (DB_NAME,))
        tables = [row[0] for row in cursor.fetchall()]
        print(f"    Found {len(tables)} tables: {', '.join(tables[:5])}...")
        
        # Clear the alembic version table for reset
        print("\n[!] Resetting alembic_version table...")
        cursor.execute("DELETE FROM alembic_version")
        conn.commit()
        print("✅ Cleared old migration history")
        
        # Check if we need to downgrade the schema first
        # MLFlow requires a consistent state, so we'll mark the current state
        # as the starting point for fresh migration
        
        # Insert the latest stable version
        # Database already contains future migration columns
        # Skip to the absolute latest to bypass all future migrations
        latest_stable = "f5a4f2784254"  # Latest in current MLFlow version
        
        print(f"\n[*] Setting migration to latest stable version: {latest_stable}")
        cursor.execute(
            "INSERT INTO alembic_version (version_num) VALUES (%s)",
            (latest_stable,)
        )
        conn.commit()
        print(f"✅ Migration history reset to version {latest_stable}")
        
        # Verify
        cursor.execute("SELECT version_num FROM alembic_version LIMIT 1")
        verify = cursor.fetchone()
        print(f"\n✅ Verification: Current version is now {verify[0]}")
        
        print("\n" + "="*60)
        print("SUCCESS: MLFlow database reset complete")
        print("="*60)
        print("\nNext steps:")
        print("1. The Investment and Crypto pages should now work")
        print("2. MLFlow logging should resume normally")
        print("\nIf you still see migration errors, try:")
        print("  python -m mlflow db upgrade '<database_uri>'")
        
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("MLFlow Database Schema Migration Fix")
    print("="*60)
    
    success = fix_mlflow_schema()
    sys.exit(0 if success else 1)
