"""
MySQL Schema Comparison Tool - Local vs Railway
================================================
Compares database schemas between local MySQL and Railway MySQL to identify:
- Missing tables in either database
- Missing columns in tables
- Column type mismatches
- Index differences

Usage:
    python compare_mysql_railway_schemas.py
"""

import pymysql
import os
from pprint import pprint
from dotenv import load_dotenv
from typing import Dict, List, Any

load_dotenv()

# -----------------------------
# CONFIGURE YOUR CONNECTIONS
# -----------------------------

LOCAL_DB = {
    "host": os.getenv("BUDGET_MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("BUDGET_MYSQL_PORT", "3306")),
    "user": os.getenv("BUDGET_MYSQL_USER", "root"),
    "password": os.getenv("BUDGET_MYSQL_PASSWORD", "root"),
    "database": os.getenv("BUDGET_MYSQL_DATABASE", "mydb")
}

# Railway connection (from Streamlit Cloud secrets)
# If you have Railway credentials in .env, they'll be used
# Otherwise, script will note that Railway connection is not configured
RAILWAY_DB = {
    "host": os.getenv("RAILWAY_MYSQL_HOST", "nozomi.proxy.rlwy.net"),
    "port": int(os.getenv("RAILWAY_MYSQL_PORT", "54537")),
    "user": os.getenv("RAILWAY_MYSQL_USER", "root"),
    "password": os.getenv("RAILWAY_MYSQL_PASSWORD", ""),  # Empty if not set
    "database": os.getenv("RAILWAY_MYSQL_DATABASE", "railway")
}

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def get_schema(conn_params: Dict, db_name: str = "Unknown") -> Dict:
    """
    Fetch complete schema from database including tables, columns, and indexes
    
    Args:
        conn_params: Database connection parameters
        db_name: Name for logging purposes
    
    Returns:
        Dict with table schemas
    """
    try:
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
            # Get column information
            cursor.execute(f"DESCRIBE {table};")
            columns = cursor.fetchall()
            
            # Get index information
            cursor.execute(f"SHOW INDEX FROM {table};")
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
                "indexes": {}
            }
            
            # Parse indexes
            for idx in indexes:
                idx_name = idx[2]  # Key_name
                if idx_name not in schema[table]["indexes"]:
                    schema[table]["indexes"][idx_name] = {
                        "columns": [],
                        "unique": idx[1] == 0,  # Non_unique (0 = unique)
                        "type": idx[10]  # Index_type
                    }
                schema[table]["indexes"][idx_name]["columns"].append(idx[4])  # Column_name

        cursor.close()
        conn.close()
        return schema
        
    except pymysql.err.OperationalError as e:
        print(f"   ❌ Connection failed: {e}")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def diff_schemas(local: Dict, remote: Dict) -> Dict:
    """
    Compare two database schemas and identify differences
    
    Args:
        local: Local database schema
        remote: Remote database schema
    
    Returns:
        Dict with all differences found
    """
    diff = {
        "missing_tables_in_remote": [],
        "missing_tables_in_local": [],
        "column_differences": {},
        "index_differences": {}
    }

    # Tables missing in Railway
    for table in local:
        if table not in remote:
            diff["missing_tables_in_remote"].append(table)

    # Tables missing locally
    for table in remote:
        if table not in local:
            diff["missing_tables_in_local"].append(table)

    # Column differences
    for table in local:
        if table in remote:
            local_cols = local[table]["columns"]
            remote_cols = remote[table]["columns"]

            col_diff = {
                "missing_in_remote": [],
                "missing_in_local": [],
                "type_mismatch": []
            }

            for col in local_cols:
                if col not in remote_cols:
                    col_diff["missing_in_remote"].append(col)
                else:
                    if local_cols[col]["type"] != remote_cols[col]["type"]:
                        col_diff["type_mismatch"].append({
                            "column": col,
                            "local_type": local_cols[col]["type"],
                            "remote_type": remote_cols[col]["type"]
                        })

            for col in remote_cols:
                if col not in local_cols:
                    col_diff["missing_in_local"].append(col)

            if any(col_diff.values()):
                diff["column_differences"][table] = col_diff
            
            # Index differences
            local_indexes = local[table]["indexes"]
            remote_indexes = remote[table]["indexes"]
            
            idx_diff = {
                "missing_in_remote": [],
                "missing_in_local": []
            }
            
            for idx in local_indexes:
                if idx not in remote_indexes:
                    idx_diff["missing_in_remote"].append(idx)
            
            for idx in remote_indexes:
                if idx not in local_indexes:
                    idx_diff["missing_in_local"].append(idx)
            
            if any(idx_diff.values()):
                diff["index_differences"][table] = idx_diff

    return diff


def print_report(differences: Dict, local_schema: Dict, remote_schema: Dict):
    """Print a formatted comparison report"""
    print("\n" + "=" * 80)
    print("DATABASE SCHEMA COMPARISON REPORT")
    print("=" * 80)
    
    print(f"\n📊 Summary:")
    print(f"   Local tables: {len(local_schema)}")
    print(f"   Railway tables: {len(remote_schema)}")
    
    # Missing tables
    if differences["missing_tables_in_remote"]:
        print(f"\n⚠️  Tables in LOCAL but missing in RAILWAY ({len(differences['missing_tables_in_remote'])}):")
        for table in differences["missing_tables_in_remote"]:
            print(f"   • {table}")
    
    if differences["missing_tables_in_local"]:
        print(f"\n⚠️  Tables in RAILWAY but missing in LOCAL ({len(differences['missing_tables_in_local'])}):")
        for table in differences["missing_tables_in_local"]:
            print(f"   • {table}")
    
    # Column differences
    if differences["column_differences"]:
        print(f"\n🔧 Column Differences ({len(differences['column_differences'])} tables):")
        for table, col_diff in differences["column_differences"].items():
            print(f"\n   📋 Table: {table}")
            
            if col_diff["missing_in_remote"]:
                print(f"      Missing in Railway: {', '.join(col_diff['missing_in_remote'])}")
            
            if col_diff["missing_in_local"]:
                print(f"      Missing in Local: {', '.join(col_diff['missing_in_local'])}")
            
            if col_diff["type_mismatch"]:
                print(f"      Type Mismatches:")
                for mismatch in col_diff["type_mismatch"]:
                    print(f"         • {mismatch['column']}: {mismatch['local_type']} (local) vs {mismatch['remote_type']} (remote)")
    
    # Index differences
    if differences["index_differences"]:
        print(f"\n🔑 Index Differences ({len(differences['index_differences'])} tables):")
        for table, idx_diff in differences["index_differences"].items():
            print(f"\n   📋 Table: {table}")
            
            if idx_diff["missing_in_remote"]:
                print(f"      Missing in Railway: {', '.join(idx_diff['missing_in_remote'])}")
            
            if idx_diff["missing_in_local"]:
                print(f"      Missing in Local: {', '.join(idx_diff['missing_in_local'])}")
    
    # Summary
    total_issues = (
        len(differences["missing_tables_in_remote"]) +
        len(differences["missing_tables_in_local"]) +
        len(differences["column_differences"]) +
        len(differences["index_differences"])
    )
    
    print("\n" + "=" * 80)
    if total_issues == 0:
        print("✅ SCHEMAS ARE IDENTICAL - No differences found!")
    else:
        print(f"⚠️  FOUND {total_issues} DIFFERENCE CATEGORIES")
        print("\n📌 Recommended Actions:")
        if differences["missing_tables_in_remote"]:
            print("   1. Create missing tables in Railway database")
        if differences["column_differences"]:
            print("   2. Run ALTER TABLE to sync column definitions")
        if differences["index_differences"]:
            print("   3. Create missing indexes for performance")
    print("=" * 80 + "\n")


# -----------------------------
# MAIN EXECUTION
# -----------------------------

if __name__ == "__main__":
    print("=" * 80)
    print("MySQL Schema Comparison: Local vs Railway")
    print("=" * 80)
    
    # Fetch schemas
    local_schema = get_schema(LOCAL_DB, "Local MySQL")
    
    if not RAILWAY_DB.get("password"):
        print("\n⚠️  Railway credentials not found in .env")
        print("   Set RAILWAY_MYSQL_* variables to compare with Railway")
        print("\n📌 Available in Streamlit Cloud secrets only")
        exit(0)
    
    remote_schema = get_schema(RAILWAY_DB, "Railway MySQL")
    
    if not local_schema:
        print("\n❌ Failed to fetch local schema")
        exit(1)
    
    if not remote_schema:
        print("\n❌ Failed to fetch Railway schema")
        print("   Check your Railway credentials in .env or Streamlit secrets")
        exit(1)
    
    # Compare schemas
    print("\n🔄 Comparing schemas...")
    differences = diff_schemas(local_schema, remote_schema)
    
    # Print formatted report
    print_report(differences, local_schema, remote_schema)
    
    # Also save raw diff to file for detailed analysis
    print("💾 Saving detailed diff to schema_diff.txt...")
    with open("schema_diff.txt", "w") as f:
        f.write("RAW SCHEMA DIFFERENCES\n")
        f.write("=" * 80 + "\n\n")
        pprint(differences, stream=f)
    
    print("✅ Detailed diff saved to schema_diff.txt\n")
