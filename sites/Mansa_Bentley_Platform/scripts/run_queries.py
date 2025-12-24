import mysql.connector
from mysql.connector import Error

def execute_query(connection, query):
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"Error: {e}")
        return None

def compare_schemas():
    try:
        # Connect to both databases
        connection_3306 = mysql.connector.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='root',
            database='mlflow_db'
        )

        connection_3307 = mysql.connector.connect(
            host='127.0.0.1',
            port=3307,
            user='root',
            password='root',
            database='mlflow_db'
        )

        if connection_3306.is_connected() and connection_3307.is_connected():
            print("Connected to both databases")

            # Compare tables
            query = "SHOW TABLES;"
            tables_3306 = execute_query(connection_3306, query)
            tables_3307 = execute_query(connection_3307, query)

            print("Tables in 3306:", tables_3306)
            print("Tables in 3307:", tables_3307)

            if tables_3306 == tables_3307:
                print("Table structures are identical")
            else:
                print("Differences in table structures detected")

            # Compare data for each table
            for table in tables_3306:
                table_name = table[0]
                print(f"Comparing data for table: {table_name}")

                query = f"SELECT * FROM {table_name} LIMIT 10;"
                data_3306 = execute_query(connection_3306, query)
                data_3307 = execute_query(connection_3307, query)

                if data_3306 == data_3307:
                    print(f"Data in table {table_name} is identical")
                else:
                    print(f"Differences in data detected for table {table_name}")

    except Error as e:
        print(f"Error while connecting to MySQL: {e}")

    finally:
        if connection_3306.is_connected():
            connection_3306.close()
            print("Connection to 3306 closed")
        if connection_3307.is_connected():
            connection_3307.close()
            print("Connection to 3307 closed")

def drop_and_restore_schemas():
    try:
        # Connect to port 3306 to drop mlflow_db
        connection_3306 = mysql.connector.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='root'
        )

        # Connect to port 3307 to restore bbbot1
        connection_3307 = mysql.connector.connect(
            host='127.0.0.1',
            port=3307,
            user='root',
            password='root'
        )

        if connection_3306.is_connected():
            print("Connected to port 3306")
            cursor = connection_3306.cursor()

            # Drop mlflow_db schema
            cursor.execute("DROP DATABASE IF EXISTS mlflow_db;")
            print("Dropped mlflow_db on port 3306")

        if connection_3307.is_connected():
            print("Connected to port 3307")
            cursor = connection_3307.cursor()

            # Restore bbbot1 schema
            cursor.execute("CREATE DATABASE IF NOT EXISTS bbbot1;")
            print("Restored bbbot1 on port 3307")

    except Error as e:
        print(f"Error while modifying schemas: {e}")

    finally:
        if connection_3306.is_connected():
            connection_3306.close()
            print("Connection to 3306 closed")
        if connection_3307.is_connected():
            connection_3307.close()
            print("Connection to 3307 closed")

if __name__ == "__main__":
    drop_and_restore_schemas()