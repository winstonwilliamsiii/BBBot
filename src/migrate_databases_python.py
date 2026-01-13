#!/usr/bin/env python3
"""
Python-based MySQL Database Migration Tool
Migrates databases using pure Python (no mysqldump required)
Author: Bentley Budget Bot Development Team
"""
import mysql.connector
import os
from datetime import datetime

def get_create_statements(source_conn, database):
    """Get CREATE statements for all tables in a database"""
    cursor = source_conn.cursor()
    cursor.execute(f"USE `{database}`")
    
    # Get all tables
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    
    create_statements = {}
    for table in tables:
        cursor.execute(f"SHOW CREATE TABLE `{table}`")
        result = cursor.fetchone()
        # Handle both tuple (table_name, create_sql) and single value returns
        if isinstance(result, tuple) and len(result) >= 2:
            create_sql = result[1]
        else:
            create_sql = result[0] if result else None
        
        if create_sql:
            create_statements[table] = create_sql
    
    return tables, create_statements

def copy_table_data(source_conn, dest_conn, database, table):
    """Copy all data from one table to another"""
    src_cursor = source_conn.cursor()
    dest_cursor = dest_conn.cursor()
    
    # Get column names
    src_cursor.execute(f"DESCRIBE `{table}`")
    columns = [col[0] for col in src_cursor.fetchall()]
    column_str = ", ".join(f"`{col}`" for col in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    
    # Fetch all data
    src_cursor.execute(f"SELECT {column_str} FROM `{table}`")
    rows = src_cursor.fetchall()
    
    if rows:
        # Insert data in batches
        insert_sql = f"INSERT INTO `{table}` ({column_str}) VALUES ({placeholders})"
        dest_cursor.executemany(insert_sql, rows)
        dest_conn.commit()
    
    return len(rows)

def migrate_database(source_host, source_port, dest_host, dest_port, user, password, database):
    """Migrate entire database from source to destination"""
    try:
        # Connect to source
        print(f"   📡 Connecting to source ({source_host}:{source_port})...")
        source_conn = mysql.connector.connect(
            host=source_host,
            port=source_port,
            user=user,
            password=password,
            database=database,
            connect_timeout=10
        )
        
        # Connect to destination
        print(f"   📡 Connecting to destination ({dest_host}:{dest_port})...")
        dest_conn = mysql.connector.connect(
            host=dest_host,
            port=dest_port,
            user=user,
            password=password,
            connect_timeout=10
        )
        
        # Create database if it doesn't exist
        dest_cursor = dest_conn.cursor()
        print(f"   🗄️  Creating database {database}...")
        dest_cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}`")
        dest_cursor.execute(f"USE `{database}`")
        
        # Get table structures
        print(f"   📋 Reading table structures...")
        tables, create_statements = get_create_statements(source_conn, database)
        print(f"   Found {len(tables)} tables")
        
        # Create tables
        print(f"   🔨 Creating tables...")
        for table in tables:
            try:
                dest_cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
                dest_cursor.execute(create_statements[table])
                print(f"      ✅ Created table: {table}")
            except mysql.connector.Error as e:
                print(f"      ⚠️  Error creating {table}: {e}")
        
        # Copy data
        print(f"   📦 Copying data...")
        total_rows = 0
        for table in tables:
            try:
                rows_copied = copy_table_data(source_conn, dest_conn, database, table)
                total_rows += rows_copied
                print(f"      ✅ {table}: {rows_copied:,} rows")
            except mysql.connector.Error as e:
                print(f"      ⚠️  Error copying {table}: {e}")
        
        # Close connections
        source_conn.close()
        dest_conn.close()
        
        print(f"   ✅ Migration successful: {len(tables)} tables, {total_rows:,} rows")
        return True, len(tables), total_rows
        
    except mysql.connector.Error as e:
        print(f"   ❌ MySQL Error: {e}")
        return False, 0, 0
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, 0, 0

def verify_migration(host, port, user, password, database):
    """Verify database exists and has correct data"""
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
        
        # Count tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        table_count = len(tables)
        
        # Count total rows
        total_rows = 0
        for (table,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            total_rows += cursor.fetchone()[0]
        
        conn.close()
        return True, table_count, total_rows
    except Exception as e:
        return False, 0, 0

if __name__ == "__main__":
    print("=" * 100)
    print("PYTHON-BASED MySQL DATABASE MIGRATION TOOL")
    print("Migrating from Port 3306 (Bentley_Budget) to Port 3307 (Demo_Bots)")
    print("=" * 100)
    print()
    
    # Configuration
    SOURCE_HOST = "127.0.0.1"
    SOURCE_PORT = 3306
    DEST_HOST = "127.0.0.1"
    DEST_PORT = 3307
    USER = "root"
    PASSWORD = "root"
    
    # Databases to migrate
    databases_to_migrate = ['mydb', 'mgrp_schema']
    
    print("📋 Migration Plan:")
    print(f"   Source: {SOURCE_HOST}:{SOURCE_PORT}")
    print(f"   Destination: {DEST_HOST}:{DEST_PORT}")
    print(f"   Databases: {', '.join(databases_to_migrate)}")
    print(f"   Method: Pure Python (no external tools required)")
    print()
    
    input("⚠️  Press ENTER to start migration (or Ctrl+C to cancel)...")
    print()
    
    results = []
    
    for database in databases_to_migrate:
        print(f"🔄 Migrating database: {database}")
        print("-" * 100)
        
        # Perform migration
        success, table_count, row_count = migrate_database(
            SOURCE_HOST, SOURCE_PORT,
            DEST_HOST, DEST_PORT,
            USER, PASSWORD,
            database
        )
        
        if success:
            # Verify migration
            print(f"   🔍 Verifying migration...")
            verify_success, verify_tables, verify_rows = verify_migration(
                DEST_HOST, DEST_PORT, USER, PASSWORD, database
            )
            
            if verify_success and verify_tables == table_count and verify_rows == row_count:
                print(f"   🎉 Verification successful!")
                results.append((database, True, f"{table_count} tables, {row_count:,} rows"))
            else:
                print(f"   ⚠️  Verification mismatch")
                results.append((database, False, "Verification failed"))
        else:
            results.append((database, False, "Migration failed"))
        
        print()
    
    # Summary
    print("=" * 100)
    print("📊 MIGRATION SUMMARY")
    print("=" * 100)
    print()
    
    successful = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for database, success, message in results:
        status = "✅" if success else "❌"
        print(f"{status} {database}: {message}")
    
    print()
    print(f"Success Rate: {successful}/{total} databases migrated")
    
    if successful == total:
        print("\n🎉 MIGRATION COMPLETE!")
        print("\n📋 Next Steps:")
        print("   1. Run: python update_env_to_3307.py")
        print("   2. Test connections: python test_api_connections.py")
        print("   3. If successful, shut down MySQL on Port 3306")
    else:
        print("\n⚠️  MIGRATION INCOMPLETE")
        print("   Review errors above and retry if needed")
    
    print("\n" + "=" * 100)
