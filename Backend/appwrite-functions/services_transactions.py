#services/transactions

from services.appwrite_client import call_function

def create_transaction(user_id, amount, date):
    return call_function("create_transaction", {
        "user_id": user_id,
        "amount": amount,
        "date": date
    })

def get_transactions(user_id, limit=100):
    return call_function("get_transactions_streamlit", {
        "user_id": user_id,
        "limit": limit
    })