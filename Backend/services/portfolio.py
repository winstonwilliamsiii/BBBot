"""
Portfolio Service - Fetches portfolio data via Appwrite Function (MySQL bridge)
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID")
FUNCTION_ID_GET_PORTFOLIO = os.getenv("APPWRITE_FUNCTION_ID_GET_PORTFOLIO_MYSQL")


def get_user_portfolio(user_id: str, action: str = "get_holdings"):
    """
    Get user's portfolio via Appwrite Function → MySQL
    
    Args:
        user_id: User identifier
        action: Query action (get_holdings, get_summary, get_transactions)
    
    Returns:
        dict: Portfolio data from MySQL
    """
    if not PROJECT_ID or not FUNCTION_ID_GET_PORTFOLIO:
        return {"error": "Missing Appwrite configuration. Set APPWRITE_PROJECT_ID and APPWRITE_FUNCTION_ID_GET_PORTFOLIO_MYSQL"}
    
    url = f"{APPWRITE_ENDPOINT}/functions/{FUNCTION_ID_GET_PORTFOLIO}/executions"
    headers = {
        "Content-Type": "application/json",
        "X-Appwrite-Project": PROJECT_ID
    }
    
    body = {
        "user_id": user_id,
        "action": action
    }
    
    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        # Appwrite Functions return results in responseBody
        if 'responseBody' in result:
            return json.loads(result['responseBody'])
        return result
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to get portfolio: {str(e)}"}


def get_portfolio_holdings(user_id: str):
    """Get portfolio holdings"""
    return get_user_portfolio(user_id, action="get_holdings")


def get_portfolio_summary(user_id: str):
    """Get portfolio summary statistics"""
    return get_user_portfolio(user_id, action="get_summary")


def get_portfolio_transactions(user_id: str, limit: int = 100):
    """Get transaction history"""
    body_data = {"user_id": user_id, "action": "get_transactions", "limit": limit}
    
    if not PROJECT_ID or not FUNCTION_ID_GET_PORTFOLIO:
        return {"error": "Missing configuration"}
    
    url = f"{APPWRITE_ENDPOINT}/functions/{FUNCTION_ID_GET_PORTFOLIO}/executions"
    headers = {
        "Content-Type": "application/json",
        "X-Appwrite-Project": PROJECT_ID
    }
    
    try:
        response = requests.post(url, headers=headers, json=body_data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if 'responseBody' in result:
            return json.loads(result['responseBody'])
        return result
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to get transactions: {str(e)}"}
