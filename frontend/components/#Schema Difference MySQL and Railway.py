#Schema Difference MySQL and Railway

import pymysql
from pprint import pprint

# -----------------------------
# CONFIGURE YOUR CONNECTIONS
# -----------------------------

LOCAL_DB = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "root",
    "database": "mydb"
}

RAILWAY_DB = {
    "host": "YOUR_RAILWAY_HOST",
    "port": 3306,  # Standard MySQL port
    "user": "YOUR_RAILWAY_USER",
    "password": "YOUR_RAILWAY_PASSWORD",
    "database": "YOUR_RAILWAY_DATABASE",
    "ssl": {"ssl": True}
}

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def get_schema(conn_params):
    conn = pymysql.connect(**conn_params)
    cursor = conn.cursor()

    cursor.execute("SHOW TABLES;")
    tables = [row[0] for row in cursor.fetchall()]

    schema = {}

    for table in tables:
        cursor.execute(f"DESCRIBE {table};")
        columns = cursor.fetchall()
        schema[table] = {
            col[0]: {
                "type": col[1],
                "null": col[2],
                "key": col[3],
                "default": col[4],
                "extra": col[5],
            }
            for col in columns
        }

    cursor.close()
    conn.close()
    return schema

def diff_schemas(local, remote):
    diff = {
        "missing_tables_in_remote": [],
        "missing_tables_in_local": [],
        "column_differences": {},
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
            local_cols = local[table]
            remote_cols = remote[table]

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

    return diff

# -----------------------------
# MAIN EXECUTION
# -----------------------------

if __name__ == "__main__":
    print("Fetching local schema...")
    local_schema = get_schema(LOCAL_DB)

    print("Fetching Railway schema...")
    remote_schema = get_schema(RAILWAY_DB)

    print("\nComparing schemas...\n")
    differences = diff_schemas(local_schema, remote_schema)

    pprint(differences)