from airflow.operators.python import PythonOperator
from plaid_client import PlaidClient

def plaid_ingest(**context):
    client = PlaidClient(client_id="YOUR_ID", secret="YOUR_SECRET")
    txs = client.fetch_transactions("ACCESS_TOKEN", "2025-11-01", "2025-11-23")
    client.store_transactions(txs, {
        "host": "localhost",
        "user": "root",
        "password": "password",
        "database": "finance_db"
    })

plaid_task = PythonOperator(
    task_id="plaid_ingest",
    python_callable=plaid_ingest
)