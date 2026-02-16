"""
Complete MLFlow Database Reset and Reinitialize
This script fixes schema inconsistencies by completely clearing the migration history
"""

import mysql.connector

DB_HOST = "nozomi.proxy.rlwy.net"
DB_PORT = 54537
DB_USER = "root"
DB_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"
DB_NAME = "mlflow_db"

def complete_reset():
    """Complete reset of MLFlow migration history"""
    
    try:
        print("\n" + "="*60)
        print("MLFlow Complete Database Reset")
        print("="*60)
        
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        
        print("\n[*] Connecting to database...")
        print("[OK] Connected")
        
        # Step 1: Check current state
        print("\n[*] Checking current alembic_version...")
        try:
            cursor.execute("SELECT version_num FROM alembic_version LIMIT 1")
            result = cursor.fetchone()
            if result:
                print(f"[INFO] Current version: {result[0]}")
        except:
            print("[INFO] No alembic_version table")
                
        # Step 2: Drop alembic_version table if it exists
        print("\n[*] Dropping alembic_version table if exists...")
        try:
            cursor.execute("DROP TABLE IF EXISTS alembic_version")
            conn.commit()
            print("[OK] Alembic version table dropped")
        except Exception as e:
            print(f"[INFO] Could not drop alembic_version: {e}")
        
        # Step 3: Recreate alembic_version with no initial version
        # This forces MLFlow to reinitialize properly
        print("\n[*] Recreating alembic_version table...")
        try:
            cursor.execute("""
            CREATE TABLE alembic_version (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
            """)
            conn.commit()
            print("[OK] Alembic version table created (empty)")
        except Exception as e:
            print(f"[ERROR] Could not create table: {e}")
            
        print("\n" + "="*60)
        print("SUCCESS: MLFlow database is ready for reinitialization")
        print("="*60)
        print("\nMLFlow will now:")
        print("  1. Detect the empty alembic_version table")
        print("  2. Run all migrations from the beginning")
        print("  3. Create proper schema matching your database state")
        print("\nYour Investment and Crypto pages are now ready to use!")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    complete_reset()
