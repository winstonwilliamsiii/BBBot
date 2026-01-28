# Active: 1737943595894@@127.0.0.1@3306@mydb
import mysql.connector
import os

def migrate_data(source_config, target_config, table_name):
    try:
        src_conn = mysql.connector.connect(**source_config)
        tgt_conn = mysql.connector.connect(**target_config)
        src_cursor = src_conn.cursor(dictionary=True)
        tgt_cursor = tgt_conn.cursor()

        src_cursor.execute(f"SELECT * FROM {table_name}")
        rows = src_cursor.fetchall()
        if not rows:
            print(f"No data found in {table_name}.")
            return
        columns = rows[0].keys()
        placeholders = ','.join(['%s'] * len(columns))
        insert_sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
        for row in rows:
            tgt_cursor.execute(insert_sql, tuple(row.values()))
        tgt_conn.commit()
        print(f"Migrated {len(rows)} rows from {table_name}.")
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        src_cursor.close()
        tgt_cursor.close()
        src_conn.close()
        tgt_conn.close()

if __name__ == "__main__":
    # Example: migrate 'transactions' table from mydb (budget) to mansa_bot
    source = {
        'host': os.getenv("BUDGET_MYSQL_HOST", "127.0.0.1"),
        'port': int(os.getenv("BUDGET_MYSQL_PORT", 3306)),
        'user': os.getenv("BUDGET_MYSQL_USER", "root"),
        'password': os.getenv("BUDGET_MYSQL_PASSWORD", "root"),
        'database': os.getenv("BUDGET_MYSQL_DATABASE", "mydb")
    }
    target = {
        'host': os.getenv("MYSQL_HOST", "127.0.0.1"),
        'port': int(os.getenv("MYSQL_PORT", 3306)),
        'user': os.getenv("MYSQL_USER", "root"),
        'password': os.getenv("MYSQL_PASSWORD", "root"),
        'database': os.getenv("MYSQL_DATABASE", "mansa_bot")
    }
    migrate_data(source, target, 'transactions')
