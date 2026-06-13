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
    # Test bbbot1 (Demo_Bots schema)
    test_connection(
        host="127.0.0.1",
        port=3307,
        user="root",
        password="root",
        database="bbbot1"
    )
