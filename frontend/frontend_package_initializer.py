"""
Frontend package initializer for BentleyBudgetBot Investment Analysis.

This file ensures the `frontend` directory is treated as a Python package.
It centralizes common imports, configuration, and helper functions
for Streamlit pages and Appwrite API integration.
"""

import os
import requests
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv(override=True)

# Expose key modules for easy import
from . import components
from . import utils
from . import styles

# ==============================================
# APPWRITE CONFIGURATION
# ==============================================

APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
APPWRITE_PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID")
APPWRITE_API_KEY = os.getenv("APPWRITE_API_KEY")
APPWRITE_DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID")

# Function IDs from .env
FUNCTION_IDS = {
    "get_transactions": os.getenv("APPWRITE_FUNCTION_ID_GET_TRANSACTIONS_STREAMLIT"),
    "create_transaction": os.getenv("APPWRITE_FUNCTION_ID_CREATE_TRANSACTION"),
    "add_watchlist": os.getenv("APPWRITE_FUNCTION_ID_ADD_WATCHLIST_STREAMLIT"),
    "get_watchlist": os.getenv("APPWRITE_FUNCTION_ID_GET_WATCHLIST_STREAMLIT"),
    "get_user_profile": os.getenv("APPWRITE_FUNCTION_ID_GET_USER_PROFILE_STREAMLIT"),
    "create_payment": os.getenv("APPWRITE_FUNCTION_ID_CREATE_PAYMENT"),
    "get_payments": os.getenv("APPWRITE_FUNCTION_ID_GET_PAYMENTS"),
    "get_bot_metrics": os.getenv("APPWRITE_FUNCTION_ID_GET_BOT_METRICS"),
}

# Optional: Appwrite SDK client setup (if SDK is installed)
client = None
account = None
database = None

try:
    from appwrite.client import Client
    from appwrite.services.databases import Databases
    from appwrite.services.account import Account
    from appwrite.services.functions import Functions
    
    # Initialize the Appwrite client
    client = Client()
    client.set_endpoint(APPWRITE_ENDPOINT)
    client.set_project(APPWRITE_PROJECT_ID)
    client.set_key(APPWRITE_API_KEY)
    
    # Initialize services
    account = Account(client)
    database = Databases(client)
    functions = Functions(client)
    
    APPWRITE_SDK_AVAILABLE = True

except ImportError:
    # Appwrite SDK not installed - use REST API fallback
    APPWRITE_SDK_AVAILABLE = False
    functions = None


# ==============================================
# APPWRITE REST API CLIENT (SDK-free fallback)
# ==============================================

class AppwriteClient:
    """
    Lightweight Appwrite client using REST API.
    Works without the Appwrite SDK installed.
    
    Usage:
        from frontend import appwrite_client
        result = appwrite_client.call_function("get_transactions", {"user_id": "123"})
    """
    
    def __init__(self):
        self.endpoint = APPWRITE_ENDPOINT
        self.project_id = APPWRITE_PROJECT_ID
        self.api_key = APPWRITE_API_KEY
        self.database_id = APPWRITE_DATABASE_ID
        
    @property
    def is_configured(self) -> bool:
        """Check if Appwrite credentials are configured."""
        return all([self.endpoint, self.project_id, self.api_key])
    
    def _get_headers(self) -> Dict[str, str]:
        """Get standard Appwrite API headers."""
        return {
            "X-Appwrite-Project": self.project_id,
            "X-Appwrite-Key": self.api_key,
            "Content-Type": "application/json",
        }
    
    def call_function(
        self, 
        function_name: str, 
        payload: Dict[str, Any] = None,
        async_execution: bool = False
    ) -> Optional[Dict]:
        """
        Execute an Appwrite Cloud Function.
        
        Args:
            function_name: Key from FUNCTION_IDS or direct function ID
            payload: Data to pass to the function
            async_execution: If True, don't wait for response
            
        Returns:
            Function execution result or None on error
        """
        # Resolve function ID
        function_id = FUNCTION_IDS.get(function_name) or function_name
        
        if not function_id:
            raise ValueError(f"Unknown function: {function_name}")
        
        url = f"{self.endpoint}/functions/{function_id}/executions"
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={"data": payload or {}, "async": async_execution},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Appwrite function error: {e}")
            return None
    
    def list_documents(
        self,
        collection_id: str,
        queries: List[str] = None,
        limit: int = 25
    ) -> Optional[Dict]:
        """
        List documents from an Appwrite collection.
        
        Args:
            collection_id: The collection ID
            queries: Optional list of query strings
            limit: Maximum documents to return
            
        Returns:
            Documents list or None on error
        """
        url = f"{self.endpoint}/databases/{self.database_id}/collections/{collection_id}/documents"
        
        params = {"limit": limit}
        if queries:
            params["queries"] = queries
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Appwrite list documents error: {e}")
            return None
    
    def create_document(
        self,
        collection_id: str,
        document_id: str,
        data: Dict[str, Any],
        permissions: List[str] = None
    ) -> Optional[Dict]:
        """
        Create a document in an Appwrite collection.
        
        Args:
            collection_id: The collection ID
            document_id: Unique document ID (use "unique()" for auto-generated)
            data: Document data
            permissions: Optional permissions array
            
        Returns:
            Created document or None on error
        """
        url = f"{self.endpoint}/databases/{self.database_id}/collections/{collection_id}/documents"
        
        body = {
            "documentId": document_id,
            "data": data,
        }
        if permissions:
            body["permissions"] = permissions
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=body,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Appwrite create document error: {e}")
            return None
    
    def get_document(
        self,
        collection_id: str,
        document_id: str
    ) -> Optional[Dict]:
        """Get a single document by ID."""
        url = f"{self.endpoint}/databases/{self.database_id}/collections/{collection_id}/documents/{document_id}"
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Appwrite get document error: {e}")
            return None


# ==============================================
# SERVICE WRAPPER FUNCTIONS
# ==============================================

# Initialize the REST client
appwrite_client = AppwriteClient()


def get_transactions(user_id: str, limit: int = 100) -> Optional[Dict]:
    """Get transactions for a user via Appwrite function."""
    return appwrite_client.call_function("get_transactions", {
        "user_id": user_id,
        "limit": limit
    })


def create_transaction(user_id: str, amount: float, date: str, **kwargs) -> Optional[Dict]:
    """Create a new transaction."""
    return appwrite_client.call_function("create_transaction", {
        "user_id": user_id,
        "amount": amount,
        "date": date,
        **kwargs
    })


def get_watchlist(user_id: str) -> Optional[Dict]:
    """Get watchlist for a user."""
    return appwrite_client.call_function("get_watchlist", {
        "user_id": user_id
    })


def add_to_watchlist(user_id: str, symbol: str) -> Optional[Dict]:
    """Add a symbol to user's watchlist."""
    return appwrite_client.call_function("add_watchlist", {
        "user_id": user_id,
        "symbol": symbol
    })


def get_user_profile(user_id: str) -> Optional[Dict]:
    """Get user profile data."""
    return appwrite_client.call_function("get_user_profile", {
        "user_id": user_id
    })


def get_bot_metrics(bot_id: str = None) -> Optional[Dict]:
    """Get bot metrics and statistics."""
    return appwrite_client.call_function("get_bot_metrics", {
        "bot_id": bot_id
    })


# ==============================================
# UTILITY FUNCTIONS
# ==============================================

PACKAGE_NAME = "frontend"
VERSION = "0.2.0"


def get_version() -> str:
    """Return the current frontend package version."""
    return VERSION


def is_appwrite_connected() -> bool:
    """Check if Appwrite client is properly configured."""
    return appwrite_client.is_configured


def test_appwrite_connection() -> Dict[str, Any]:
    """
    Test Appwrite connectivity.
    
    Returns:
        Dict with connection status and details
    """
    result = {
        "configured": appwrite_client.is_configured,
        "sdk_available": APPWRITE_SDK_AVAILABLE,
        "endpoint": APPWRITE_ENDPOINT,
        "project_id": APPWRITE_PROJECT_ID[:8] + "..." if APPWRITE_PROJECT_ID else None,
        "functions_loaded": sum(1 for v in FUNCTION_IDS.values() if v),
    }
    
    # Try a simple API call
    if appwrite_client.is_configured:
        try:
            response = requests.get(
                f"{APPWRITE_ENDPOINT}/health",
                headers={"X-Appwrite-Project": APPWRITE_PROJECT_ID},
                timeout=5
            )
            result["api_reachable"] = response.status_code == 200
        except:
            result["api_reachable"] = False
    
    return result