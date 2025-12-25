"""
Transaction Service - Connects to Appwrite Serverless Functions
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID")
FUNCTION_ID_CREATE_TX = os.getenv("APPWRITE_FUNCTION_ID_CREATE_TRANSACTION")
FUNCTION_ID_GET_TX = os.getenv("APPWRITE_FUNCTION_ID_GET_TRANSACTIONS_STREAMLIT")


def create_transaction(user_id: str, amount: float, date: str = None):
    """
    Create a new transaction via Appwrite Function
    
    Args:
        user_id: User identifier
        amount: Transaction amount
        date: Optional transaction date (ISO format)
    
    Returns:
        dict: Response from Appwrite Function
    """
    if not PROJECT_ID or not FUNCTION_ID_CREATE_TX:
        return {"error": "Missing Appwrite configuration. Set APPWRITE_PROJECT_ID and APPWRITE_FUNCTION_ID_CREATE_TRANSACTION"}
    
    url = f"{APPWRITE_ENDPOINT}/functions/{FUNCTION_ID_CREATE_TX}/executions"
    headers = {
        "Content-Type": "application/json",
        "X-Appwrite-Project": PROJECT_ID
    }
    
    body = {
        "user_id": user_id,
        "amount": float(amount),
        "date": date
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
        return {"error": f"Failed to create transaction: {str(e)}"}


def get_transactions(user_id: str, limit: int = 100):
    """
    Get transactions for a user via Appwrite Function
    
    Args:
        user_id: User identifier
        limit: Maximum number of transactions to retrieve
    
    Returns:
        dict: Response with transactions list
    """
    if not PROJECT_ID or not FUNCTION_ID_GET_TX:
        return {"error": "Missing Appwrite configuration. Set APPWRITE_PROJECT_ID and APPWRITE_FUNCTION_ID_GET_TRANSACTIONS"}
    
    url = f"{APPWRITE_ENDPOINT}/functions/{FUNCTION_ID_GET_TX}/executions"
    headers = {
        "Content-Type": "application/json",
        "X-Appwrite-Project": PROJECT_ID
    }
    
    body = {
        "user_id": user_id,
        "limit": limit
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
        return {"error": f"Failed to get transactions: {str(e)}"}
