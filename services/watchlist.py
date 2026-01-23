"""
Watchlist Service - Connects to Appwrite Serverless Functions
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT", "https://fra.cloud.appwrite.io/v1")
PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID")
# Function IDs are the configuration IDs from appwrite.json, not the runtime execution IDs
FUNCTION_ID_ADD_WATCHLIST = os.getenv("APPWRITE_FUNCTION_ID_ADD_WATCHLIST", "add_to_watchlist_streamlit")
FUNCTION_ID_GET_WATCHLIST = os.getenv("APPWRITE_FUNCTION_ID_GET_WATCHLIST", "get_watchlist_streamlit")


def add_to_watchlist(user_id: str, symbol: str):
    """
    Add a symbol to user's watchlist via Appwrite Function
    
    Args:
        user_id: User identifier
        symbol: Stock/crypto symbol
    
    Returns:
        dict: Response from Appwrite Function
    """
    if not PROJECT_ID or not FUNCTION_ID_ADD_WATCHLIST:
        return {"error": "Missing Appwrite configuration. Ensure APPWRITE_PROJECT_ID and APPWRITE_FUNCTION_ID_ADD_WATCHLIST are set in environment or use defaults."}
    
    url = f"{APPWRITE_ENDPOINT}/functions/{FUNCTION_ID_ADD_WATCHLIST}/executions"
    headers = {
        "Content-Type": "application/json",
        "X-Appwrite-Project": PROJECT_ID
    }
    
    body = {
        "user_id": user_id,
        "symbol": symbol.upper()
    }
    
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        
        result = response.json()
        # Appwrite Functions return results in responseBody
        if 'responseBody' in result:
            return json.loads(result['responseBody'])
        return result
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to add to watchlist: {str(e)}"}


def get_watchlist(user_id: str):
    """
    Get user's watchlist via Appwrite Function
    
    Args:
        user_id: User identifier
    
    Returns:
        dict: Response with watchlist items
    """
    if not PROJECT_ID or not FUNCTION_ID_GET_WATCHLIST:
        return {"error": "Missing Appwrite configuration. Set APPWRITE_PROJECT_ID and APPWRITE_FUNCTION_ID_GET_WATCHLIST"}
    
    url = f"{APPWRITE_ENDPOINT}/functions/{FUNCTION_ID_GET_WATCHLIST}/executions"
    headers = {
        "Content-Type": "application/json",
        "X-Appwrite-Project": PROJECT_ID
    }
    
    body = {
        "user_id": user_id
    }
    
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        
        result = response.json()
        # Appwrite Functions return results in responseBody
        if 'responseBody' in result:
            return json.loads(result['responseBody'])
        return result
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to get watchlist: {str(e)}"}
