#!/usr/bin/env python3
"""
MySQL Dual Instance Diagnostic Tool
Identifies database duplication and maps schema across two MySQL instances
Author: Bentley Budget Bot Development Team
"""
import mysql.connector
import os
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

def get_databases_and_tables(host, port, user, password):
    """Get all databases and tables from a MySQL instance"""
    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            connect_timeout=5
        )
        cursor = conn.cursor()
        
        # Get all databases
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall() 
                    if db[0] not in ('information_schema', 'mysql', 'performance_schema', 'sys')]
        
        db_info = {}
        for database in databases:
            cursor.execute(f"USE {database}")
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            
            # Get table sizes
            table_info = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                row_count = cursor.fetchone()[0]
                table_info[table] = row_count
            
            db_info[database] = table_info
        
        conn.close()
        return db_info, None
    except mysql.connector.Error as e:
        return None, str(e)
    except Exception as e:
        return None, str(e)

def analyze_duplication(instance1_data, instance2_data):
    """Analyze database duplication between two instances"""
    duplicates = []
    unique_to_instance1 = []
    unique_to_instance2 = []
    
    # Find common databases
    dbs1 = set(instance1_data.keys())
    dbs2 = set(instance2_data.keys())
    
    common_dbs = dbs1.intersection(dbs2)
    unique_dbs1 = dbs1 - dbs2
    unique_dbs2 = dbs2 - dbs1
    
    for db in common_dbs:
        tables1 = set(instance1_data[db].keys())
        tables2 = set(instance2_data[db].keys())
        common_tables = tables1.intersection(tables2)
        
        if common_tables:
            duplicates.append({
                'database': db,
                'common_tables': list(common_tables),
                'instance1_only': list(tables1 - tables2),
                'instance2_only': list(tables2 - tables1)
            })
    
    return {
        'duplicates': duplicates,
        'unique_to_instance1': list(unique_dbs1),
        'unique_to_instance2': list(unique_dbs2),
        'common_databases': list(common_dbs)
    }

if __name__ == "__main__":
    print("=" * 100)
    print("MySQL DUAL INSTANCE DIAGNOSTIC TOOL")
    print("=" * 100)
    print()
    
    # Instance 1: Port 3307 (Demo_Bots)
    print("🔍 SCANNING INSTANCE 1: Port 3307 (Demo_Bots)")
    print("-" * 100)
    instance1_data, error1 = get_databases_and_tables(
        host="127.0.0.1",
        port=3307,
        user="root",
        password="root"
    )
    
    if instance1_data:
        print(f"✅ Connected to Port 3307")
        print(f"   Databases found: {list(instance1_data.keys())}")
        for db, tables in instance1_data.items():
            total_rows = sum(tables.values())
            print(f"   - {db}: {len(tables)} tables, {total_rows:,} total rows")
    else:
        print(f"❌ Failed to connect to Port 3307")
        print(f"   Error: {error1}")
    print()
    
    # Instance 2: Port 3306 (Bentley_Budget)
    print("🔍 SCANNING INSTANCE 2: Port 3306 (Bentley_Budget)")
    print("-" * 100)
    instance2_data, error2 = get_databases_and_tables(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="root"
    )
    
    if instance2_data:
        print(f"✅ Connected to Port 3306")
        print(f"   Databases found: {list(instance2_data.keys())}")
        for db, tables in instance2_data.items():
            total_rows = sum(tables.values())
            print(f"   - {db}: {len(tables)} tables, {total_rows:,} total rows")
    else:
        print(f"❌ Failed to connect to Port 3306")
        print(f"   Error: {error2}")
    print()
    
    # Analyze duplication if both instances are accessible
    if instance1_data and instance2_data:
        print("=" * 100)
        print("📊 DUPLICATION ANALYSIS")
        print("=" * 100)
        print()
        
        analysis = analyze_duplication(instance1_data, instance2_data)
        
        # Show duplicate databases
        print("🔴 DUPLICATE DATABASES (exist on both instances):")
        print("-" * 100)
        if analysis['common_databases']:
            for db in analysis['common_databases']:
                print(f"   ⚠️  {db}")
                print(f"       Port 3307: {len(instance1_data[db])} tables, "
                      f"{sum(instance1_data[db].values()):,} rows")
                print(f"       Port 3306: {len(instance2_data[db])} tables, "
                      f"{sum(instance2_data[db].values()):,} rows")
        else:
            print("   ✅ No duplicate databases found")
        print()
        
        # Show detailed table comparison for duplicates
        if analysis['duplicates']:
            print("🔍 DETAILED TABLE COMPARISON:")
            print("-" * 100)
            for dup in analysis['duplicates']:
                db = dup['database']
                print(f"   Database: {db}")
                if dup['common_tables']:
                    print(f"      Duplicate tables: {', '.join(dup['common_tables'])}")
                if dup['instance1_only']:
                    print(f"      Only on 3307: {', '.join(dup['instance1_only'])}")
                if dup['instance2_only']:
                    print(f"      Only on 3306: {', '.join(dup['instance2_only'])}")
                print()
        
        # Show unique databases
        print("🔵 UNIQUE TO PORT 3307 (Demo_Bots):")
        print("-" * 100)
        if analysis['unique_to_instance1']:
            for db in analysis['unique_to_instance1']:
                print(f"   - {db}: {len(instance1_data[db])} tables")
        else:
            print("   None")
        print()
        
        print("🟢 UNIQUE TO PORT 3306 (Bentley_Budget):")
        print("-" * 100)
        if analysis['unique_to_instance2']:
            for db in analysis['unique_to_instance2']:
                print(f"   - {db}: {len(instance2_data[db])} tables")
        else:
            print("   None")
        print()
        
        # Recommendation
        print("=" * 100)
        print("💡 RECOMMENDATIONS")
        print("=" * 100)
        
        # Count total databases and data
        total_dbs_3307 = len(instance1_data)
        total_dbs_3306 = len(instance2_data)
        total_rows_3307 = sum(sum(tables.values()) for tables in instance1_data.values())
        total_rows_3306 = sum(sum(tables.values()) for tables in instance2_data.values())
        
        print(f"\n📈 Current State:")
        print(f"   Port 3307: {total_dbs_3307} databases, {total_rows_3307:,} total rows")
        print(f"   Port 3306: {total_dbs_3306} databases, {total_rows_3306:,} total rows")
        print(f"   Duplicate databases: {len(analysis['common_databases'])}")
        
        # Determine which instance to keep as primary
        if total_rows_3307 > total_rows_3306:
            primary = "3307"
            primary_name = "Demo_Bots"
            secondary = "3306"
        else:
            primary = "3306"
            primary_name = "Bentley_Budget"
            secondary = "3307"
        
        print(f"\n✅ RECOMMENDED PRIMARY INSTANCE: Port {primary} ({primary_name})")
        print(f"   Reason: Contains more data ({max(total_rows_3307, total_rows_3306):,} rows)")
        print(f"\n📋 Action Plan:")
        print(f"   1. Use Port {primary} as your primary MySQL instance")
        print(f"   2. Migrate any unique databases from Port {secondary} to Port {primary}")
        print(f"   3. Update .env file to use Port {primary} for all connections")
        print(f"   4. Shut down MySQL instance on Port {secondary}")
        print(f"   5. Update API connections (Plaid, Alpaca, Tiingo) to use Port {primary}")
        
    else:
        print("⚠️  Cannot complete analysis - one or both MySQL instances are not accessible")
        print("\nTroubleshooting:")
        print("1. Ensure both MySQL servers are running")
        print("2. Check that ports 3306 and 3307 are not blocked by firewall")
        print("3. Verify MySQL credentials in .env file")
    
    print("\n" + "=" * 100)
    print("END OF DIAGNOSTIC REPORT")
    print("=" * 100)
