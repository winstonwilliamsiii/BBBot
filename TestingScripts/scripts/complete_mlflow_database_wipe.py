#!/usr/bin/env python3
"""
Complete MLFlow Database Wipe and Reinitialize
Drops ALL MLFlow tables and starts completely fresh
"""
import mysql.connector
import time
import os

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'nozomi.proxy.rlwy.net')
DB_PORT = int(os.getenv('DB_PORT', 54537))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'cBlIUSygvPJCgPbNKHePJekQlClRamri')
DB_NAME = os.getenv('DB_NAME', 'mlflow_db')

print("=" * 70)
print("MLFlow Complete Database Wipe & Reinitialize")
print("=" * 70)

try:
    print("\n[*] Connecting to database...")
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor()
    print("[OK] Connected")

    # Get all tables first
    print("\n[*] Fetching list of all MLFlow tables...")
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA=%s", (DB_NAME,))
    tables = [row[0] for row in cursor.fetchall()]
    print(f"[OK] Found {len(tables)} tables")

    # Drop all tables
    if tables:
        print("\n[*] Disabling foreign key checks...")
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        print("[OK] Foreign key checks disabled")

        print("\n[*] Dropping all tables...")
        for table in tables:
            print(f"    - Dropping {table}...")
            cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
            conn.commit()
        print(f"[OK] All {len(tables)} tables dropped")

        print("\n[*] Re-enabling foreign key checks...")
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")
        print("[OK] Foreign key checks re-enabled")
    
    conn.commit()
    cursor.close()
    conn.close()

    print("\n" + "=" * 70)
    print("SUCCESS: Database completely wiped and ready for fresh MLFlow setup")
    print("=" * 70)
    print("\nNext step: Run the MLFlow database upgrade command")
    print('$ mlflow db upgrade "mysql+pymysql://root:cBlIUSygvPJCgPbNKHePJekQlClRamri@nozomi.proxy.rlwy.net:54537/mlflow_db"')
    print("\nThis will:")
    print("  1. Create all MLFlow tables from scratch")
    print("  2. Initialize alembic_version with current migrations")
    print("  3. Ensure schema consistency with current MLFlow version")
    print("\n" + "=" * 70)

except mysql.connector.Error as err:
    print(f"\n[ERROR] Database error: {err}")
    exit(1)
except Exception as e:
    print(f"\n[ERROR] Unexpected error: {e}")
    exit(1)
