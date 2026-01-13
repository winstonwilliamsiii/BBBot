#!/usr/bin/env python3
"""
MySQL Database Migration Tool
Migrates unique databases from Port 3306 to Port 3307
Author: Bentley Budget Bot Development Team
"""
import mysql.connector
import subprocess
import os
from datetime import datetime

def export_database(host, port, user, password, database, output_file):
    """Export database using mysqldump"""
    try:
        cmd = [
            'mysqldump',
            f'--host={host}',
            f'--port={port}',
            f'--user={user}',
            f'--password={password}',
            '--databases', database,
            '--routines',
            '--triggers',
            '--events',
            '--single-transaction',
            '--quick',
            '--lock-tables=false',
            f'--result-file={output_file}'
        ]
        
        print(f"   Exporting {database}...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            file_size = os.path.getsize(output_file) / 1024  # KB
            print(f"   ✅ Exported to {output_file} ({file_size:.2f} KB)")
            return True
        else:
            print(f"   ❌ Export failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"   ❌ Export timeout after 5 minutes")
        return False
    except Exception as e:
        print(f"   ❌ Export error: {e}")
        return False

def import_database(host, port, user, password, input_file):
    """Import database using mysql command"""
    try:
        cmd = [
            'mysql',
            f'--host={host}',
            f'--port={port}',
            f'--user={user}',
            f'--password={password}',
        ]
        
        print(f"   Importing from {input_file}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            result = subprocess.run(cmd, stdin=f, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"   ✅ Import successful")
            return True
        else:
            print(f"   ❌ Import failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"   ❌ Import timeout after 5 minutes")
        return False
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False

def verify_migration(host, port, user, password, database):
    """Verify database exists and has tables"""
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
        
        print(f"   ✅ Verified: {table_count} tables, {total_rows:,} rows")
        return True, table_count, total_rows
    except Exception as e:
        print(f"   ❌ Verification failed: {e}")
        return False, 0, 0

if __name__ == "__main__":
    print("=" * 100)
    print("MySQL DATABASE MIGRATION TOOL")
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
    
    # Create backup directory
    backup_dir = "mysql_migration_backup"
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("📋 Migration Plan:")
    print(f"   Source: Port {SOURCE_PORT}")
    print(f"   Destination: Port {DEST_PORT}")
    print(f"   Databases: {', '.join(databases_to_migrate)}")
    print(f"   Backup Directory: {backup_dir}/")
    print()
    
    # Check if mysqldump is available
    try:
        subprocess.run(['mysqldump', '--version'], capture_output=True, check=True)
        print("✅ mysqldump is available")
    except:
        print("❌ ERROR: mysqldump not found in PATH")
        print("   Please ensure MySQL client tools are installed and in PATH")
        print("   Download from: https://dev.mysql.com/downloads/mysql/")
        exit(1)
    
    print()
    results = []
    
    for database in databases_to_migrate:
        print(f"🔄 Migrating database: {database}")
        print("-" * 100)
        
        # Step 1: Export from source
        export_file = os.path.join(backup_dir, f"{database}_{timestamp}.sql")
        export_success = export_database(
            SOURCE_HOST, SOURCE_PORT, USER, PASSWORD, database, export_file
        )
        
        if not export_success:
            print(f"   ⚠️  Skipping {database} due to export failure\n")
            results.append((database, False, "Export failed"))
            continue
        
        # Step 2: Import to destination
        import_success = import_database(
            DEST_HOST, DEST_PORT, USER, PASSWORD, export_file
        )
        
        if not import_success:
            print(f"   ⚠️  Import failed for {database}\n")
            results.append((database, False, "Import failed"))
            continue
        
        # Step 3: Verify migration
        verify_success, table_count, row_count = verify_migration(
            DEST_HOST, DEST_PORT, USER, PASSWORD, database
        )
        
        if verify_success:
            print(f"   🎉 Migration successful!\n")
            results.append((database, True, f"{table_count} tables, {row_count} rows"))
        else:
            print(f"   ⚠️  Verification failed for {database}\n")
            results.append((database, False, "Verification failed"))
    
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
    print(f"Backup Location: {os.path.abspath(backup_dir)}/")
    
    if successful == total:
        print("\n🎉 MIGRATION COMPLETE!")
        print("\n📋 Next Steps:")
        print("   1. Run: python update_env_to_3307.py")
        print("   2. Test API connections: python test_api_connections.py")
        print("   3. If successful, shut down MySQL on Port 3306")
        print(f"\n💾 Keep backups in: {backup_dir}/")
    else:
        print("\n⚠️  MIGRATION INCOMPLETE")
        print("   Review errors above and retry failed databases")
    
    print("\n" + "=" * 100)
