import mysql.connector
import os

def ensure_database_exists(host, port, user, password, database):
    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        print(f"Database '{database}' ensured on {host}:{port}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"ERROR: Could not ensure database '{database}' on {host}:{port}")
        print(e)

if __name__ == "__main__":
    ensure_database_exists(
        os.getenv("MYSQL_HOST", "127.0.0.1"),
        int(os.getenv("MYSQL_PORT", 3307)),
        os.getenv("MYSQL_USER", "root"),
        os.getenv("MYSQL_PASSWORD", "root"),
        os.getenv("MYSQL_DATABASE", "mansa_bot")
    )
