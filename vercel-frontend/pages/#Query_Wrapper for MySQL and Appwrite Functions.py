#Query_Wrapper for MySQL and Appwrite Functions

import mysql.connector

def get_portfolio(user_id):
    conn = mysql.connector.connect(
        host="your_host",
        user="your_user",
        password="your_password",
        database="mydb"
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM portfolios WHERE user_id = %s", (user_id,))
    return cursor.fetchall()

