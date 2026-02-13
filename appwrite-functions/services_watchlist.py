# services_watchlist

from services.appwrite_client import call_function

def add_to_watchlist(user_id, symbol):
    return call_function("add_to_watchlist_streamlit", {
        "user_id": user_id,
        "symbol": symbol
    })

def get_watchlist(user_id):
    return call_function("get_watchlist_streamlit", {
        "user_id": user_id
    })