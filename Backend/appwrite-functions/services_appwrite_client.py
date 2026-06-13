# services/appwrites_client.copy()

import os
import requests

APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT")
APPWRITE_PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID")
APPWRITE_API_KEY = os.getenv("APPWRITE_API_KEY")

def call_function(function_id, payload):
    url = f"{APPWRITE_ENDPOINT}/functions/{function_id}/executions"
    headers = {
        "X-Appwrite-Project": APPWRITE_PROJECT_ID,
        "X-Appwrite-Key": APPWRITE_API_KEY,
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()