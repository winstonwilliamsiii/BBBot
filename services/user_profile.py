"""
User Profile Service - Connects to Appwrite Serverless Functions
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT", "https://fra.cloud.appwrite.io/v1")
PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID")
# Function IDs are the configuration IDs from appwrite.json, not the runtime execution IDs
FUNCTION_ID_GET_USER_PROFILE = os.getenv("APPWRITE_FUNCTION_ID_GET_USER_PROFILE_STREAMLIT", "get_user_profile_streamlit")


def get_user_profile(user_id: str):
    """
    Get user profile via Appwrite Function
    
    Args:
        user_id: User identifier
    
    Returns:
        dict: User profile data
    """
    if not PROJECT_ID or not FUNCTION_ID_GET_USER_PROFILE:
        return {"error": "Missing Appwrite configuration. Set APPWRITE_PROJECT_ID and APPWRITE_FUNCTION_ID_GET_USER_PROFILE_STREAMLIT"}
    
    url = f"{APPWRITE_ENDPOINT}/functions/{FUNCTION_ID_GET_USER_PROFILE}/executions"
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
        return {"error": f"Failed to get user profile: {str(e)}"}
