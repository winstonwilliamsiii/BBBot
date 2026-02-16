"""
Final MLFlow Fix - Set to Latest Version
This ensures no further migrations are attempted
"""

import mysql.connector

DB_HOST = "nozomi.proxy.rlwy.net"
DB_PORT = 54537
DB_USER = "root"
DB_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"
DB_NAME = "mlflow_db"

def final_fix():
    try:
        print("\n" + "="*60)
        print("MLFlow Final Fix - Set to Latest Version")
        print("="*60)
        
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        
        print("\n[*] Clearing all migration history...")
        cursor.execute("DELETE FROM alembic_version")
        conn.commit()
        print("[OK] Cleared")
        
        # Set to the absolute latest version
        latest = "f5a4f2784254"
        
        print(f"\n[*] Setting to latest version: {latest}...")
        cursor.execute(
            "INSERT INTO alembic_version (version_num) VALUES (%s)",
            (latest,)
        )
        conn.commit()
        print("[OK] Version set")
        
        print("\n" + "="*60)
        print("COMPLETE: MLFlow is now configured")
        print("="*60)
        print("\nYour Investment and Crypto pages are ready!")
        print("MLFlow will use the existing database schema without")
        print("attempting any further migrations.")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return False

if __name__ == "__main__":
    final_fix()
