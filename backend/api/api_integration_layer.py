import requests
import mysql.connector

def fetch_plaid_transactions(api_key, account_id):
    url = f"https://api.plaid.com/transactions/{account_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def store_in_mysql(data, conn_params):
    conn = mysql.connector.connect(**conn_params)
    cursor = conn.cursor()
    for tx in data['transactions']:
        cursor.execute(
            "INSERT INTO transactions (id, amount, date) VALUES (%s, %s, %s)",
            (tx['transaction_id'], tx['amount'], tx['date'])
        )
    conn.commit()
    cursor.close()
    conn.close()