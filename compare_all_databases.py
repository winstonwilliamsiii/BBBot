"""
Multi-Database Schema Comparison Tool
======================================
Compares schemas across multiple databases:
- Local mydb (port 3306)
- Local mansa_bot (port 3307)
- Railway MySQL (if credentials available)

Usage:
    python compare_all_databases.py
"""

import pymysql
import os
from pprint import pprint
from dotenv import load_dotenv
from typing import Dict, List, Any, Tuple

load_dotenv()

# -----------------------------
# CONFIGURE YOUR CONNECTIONS
# -----------------------------

DATABASES = {
    "mydb": {
        "host": os.getenv("BUDGET_MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("BUDGET_MYSQL_PORT", "3306")),
        "user": os.getenv("BUDGET_MYSQL_USER", "root"),
        "password": os.getenv("BUDGET_MYSQL_PASSWORD", "root"),
        "database": os.getenv("BUDGET_MYSQL_DATABASE", "mydb")
    },
    "mansa_bot": {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3307")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "root"),
        "database": os.getenv("MYSQL_DATABASE", "mansa_bot")
    },
    "railway": {
        "host": os.getenv("RAILWAY_MYSQL_HOST", ""),
        "port": int(os.getenv("RAILWAY_MYSQL_PORT", "3306")) if os.getenv("RAILWAY_MYSQL_PORT") else 3306,
        "user": os.getenv("RAILWAY_MYSQL_USER", ""),
        "password": os.getenv("RAILWAY_MYSQL_PASSWORD", ""),
        "database": os.getenv("RAILWAY_MYSQL_DATABASE", "railway")
    }
}

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def get_schema(conn_params: Dict, db_name: str = "Unknown") -> Tuple[Dict, bool]:
    """
    Fetch complete schema from database
    
    Returns:
        Tuple of (schema dict, success boolean)
    """
    try:
        if not conn_params.get("password"):
            print(f"   ⏭️  Skipping {db_name} (no credentials)")
            return None, False
        
        print(f"\n🔍 Connecting to {db_name}...")
        print(f"   Host: {conn_params['host']}:{conn_params['port']}")
        print(f"   Database: {conn_params['database']}")
        
        conn = pymysql.connect(**conn_params)
        cursor = conn.cursor()

        cursor.execute("SHOW TABLES;")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"   ✅ Found {len(tables)} tables")

        schema = {}

        for table in tables:
            # Escape table names that might be MySQL keywords
            escaped_table = f"`{table}`"
            
            cursor.execute(f"DESCRIBE {escaped_table};")
            columns = cursor.fetchall()
            
            cursor.execute(f"SHOW INDEX FROM {escaped_table};")
            indexes = cursor.fetchall()
            
            schema[table] = {
                "columns": {
                    col[0]: {
                        "type": col[1],
                        "null": col[2],
                        "key": col[3],
                        "default": col[4],
                        "extra": col[5],
                    }
                    for col in columns
                },
                "indexes": [idx[2] for idx in indexes]  # Index names
            }

        cursor.close()
        conn.close()
        return schema, True
        
    except pymysql.err.OperationalError as e:
        print(f"   ❌ Connection failed: {e}")
        return None, False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None, False


def find_common_tables(schemas: Dict[str, Dict]) -> List[str]:
    """Find tables that exist in ALL databases"""
    if not schemas:
        return []
    
    table_sets = [set(schema.keys()) for schema in schemas.values()]
    common = set.intersection(*table_sets)
    return sorted(list(common))


def find_unique_tables(schemas: Dict[str, Dict]) -> Dict[str, List[str]]:
    """Find tables unique to each database"""
    unique = {}
    all_tables = set()
    
    for db_name, schema in schemas.items():
        all_tables.update(schema.keys())
    
    for db_name, schema in schemas.items():
        other_tables = set()
        for other_db, other_schema in schemas.items():
            if other_db != db_name:
                other_tables.update(other_schema.keys())
        
        unique[db_name] = sorted(list(set(schema.keys()) - other_tables))
    
    return unique


def compare_table_structure(table_name: str, schemas: Dict[str, Dict]):
    """Compare structure of a specific table across databases"""
    print(f"\n📋 Table: {table_name}")
    
    # Check which databases have this table
    dbs_with_table = [db for db, schema in schemas.items() if table_name in schema]
    
    if len(dbs_with_table) == 1:
        print(f"   ℹ️  Only exists in: {dbs_with_table[0]}")
        return
    
    # Compare columns
    all_columns = set()
    for db in dbs_with_table:
        all_columns.update(schemas[db][table_name]["columns"].keys())
    
    column_presence = {}
    for col in sorted(all_columns):
        column_presence[col] = {}
        for db in dbs_with_table:
            if col in schemas[db][table_name]["columns"]:
                col_info = schemas[db][table_name]["columns"][col]
                column_presence[col][db] = col_info["type"]
            else:
                column_presence[col][db] = "MISSING"
    
    # Print column comparison
    for col, presence in column_presence.items():
        values = list(presence.values())
        if len(set(values)) > 1:  # Differences found
            print(f"   ⚠️  Column '{col}':")
            for db, type_info in presence.items():
                symbol = "❌" if type_info == "MISSING" else "📝"
                print(f"      {symbol} {db}: {type_info}")


def print_comprehensive_report(schemas: Dict[str, Dict]):
    """Print comprehensive comparison report"""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE DATABASE SCHEMA COMPARISON")
    print("=" * 80)
    
    print(f"\n📊 Databases Analyzed: {len(schemas)}")
    for db_name, schema in schemas.items():
        print(f"   • {db_name}: {len(schema)} tables")
    
    # Common tables
    common_tables = find_common_tables(schemas)
    print(f"\n✅ Tables in ALL databases ({len(common_tables)}):")
    if common_tables:
        for table in common_tables[:10]:  # Show first 10
            print(f"   • {table}")
        if len(common_tables) > 10:
            print(f"   ... and {len(common_tables) - 10} more")
    else:
        print("   (none)")
    
    # Unique tables
    unique_tables = find_unique_tables(schemas)
    print(f"\n🔷 Unique Tables:")
    for db_name, tables in unique_tables.items():
        if tables:
            print(f"\n   {db_name} ONLY ({len(tables)}):")
            for table in tables[:5]:  # Show first 5
                print(f"      • {table}")
            if len(tables) > 5:
                print(f"      ... and {len(tables) - 5} more")
    
    # Detailed comparison for important tables
    important_tables = [
        "plaid_items",
        "user_plaid_tokens", 
        "broker_api_credentials",
        "broker_connections",
        "users",
        "transactions"
    ]
    
    print(f"\n🔍 Detailed Structure Comparison:")
    for table in important_tables:
        # Check if table exists in any database
        if any(table in schema for schema in schemas.values()):
            compare_table_structure(table, schemas)
    
    print("\n" + "=" * 80)


# -----------------------------
# MAIN EXECUTION
# -----------------------------

if __name__ == "__main__":
    print("=" * 80)
    print("Multi-Database Schema Comparison Tool")
    print("=" * 80)
    
    # Fetch all schemas
    schemas = {}
    for db_name, conn_params in DATABASES.items():
        schema, success = get_schema(conn_params, db_name)
        if success and schema:
            schemas[db_name] = schema
    
    if not schemas:
        print("\n❌ No databases could be accessed")
        exit(1)
    
    # Print comprehensive report
    print_comprehensive_report(schemas)
    
    # Save detailed report
    report_file = "schema_comparison_report.txt"
    print(f"\n💾 Saving detailed report to {report_file}...")
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("DATABASE SCHEMA COMPARISON REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        for db_name, schema in schemas.items():
            f.write(f"\n{db_name.upper()} SCHEMA:\n")
            f.write("-" * 80 + "\n")
            for table_name, table_info in sorted(schema.items()):
                f.write(f"\nTable: {table_name}\n")
                f.write(f"  Columns:\n")
                for col_name, col_info in table_info["columns"].items():
                    f.write(f"    • {col_name}: {col_info['type']}")
                    if col_info['key']:
                        f.write(f" [{col_info['key']}]")
                    if col_info['extra']:
                        f.write(f" {col_info['extra']}")
                    f.write("\n")
                if table_info["indexes"]:
                    f.write(f"  Indexes: {', '.join(set(table_info['indexes']))}\n")
    
    print(f"✅ Detailed report saved to {report_file}\n")
