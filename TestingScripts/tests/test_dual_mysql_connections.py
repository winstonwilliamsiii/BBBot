import mysql.connector
import os

def test_connection(host, port, user, password, database):
    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        print(f"SUCCESS: Connected to {database} on {host}:{port}")
        conn.close()
    except Exception as e:
        print(f"ERROR: Could not connect to {database} on {host}:{port}")
        print(e)

if __name__ == "__main__":
    # Test mansa_bot (main)
    test_connection(
        os.getenv("MYSQL_HOST", "127.0.0.1"),
        int(os.getenv("MYSQL_PORT", 3306)),
        os.getenv("MYSQL_USER", "root"),
        os.getenv("MYSQL_PASSWORD", "root"),
        os.getenv("MYSQL_DATABASE", "mansa_bot")
    )
    # Test mydb (budget/plaid)
    test_connection(
        os.getenv("BUDGET_MYSQL_HOST", "127.0.0.1"),
        int(os.getenv("BUDGET_MYSQL_PORT", 3306)),
        os.getenv("BUDGET_MYSQL_USER", "root"),
        os.getenv("BUDGET_MYSQL_PASSWORD", "root"),
        os.getenv("BUDGET_MYSQL_DATABASE", "mydb")
    )
