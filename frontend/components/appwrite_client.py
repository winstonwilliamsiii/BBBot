"""
Appwrite Client Module for BentleyBudgetBot.

This is a standalone module that can be imported WITHOUT Streamlit dependencies.
Use this for backend scripts, tests, and Streamlit pages.

Usage:
    from frontend.utils.appwrite_client import AppwriteClient, get_transactions
    
    # Direct client usage
    client = AppwriteClient()
    result = client.call_function("get_transactions", {"user_id": "123"})
    
    # Or use helper functions
    transactions = get_transactions("user_123")
"""

import os
import requests
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

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
    "create_audit_log": os.getenv("APPWRITE_FUNCTION_ID_CREATE_AUDIT_LOG"),
    "get_audit_logs": os.getenv("APPWRITE_FUNCTION_ID_GET_AUDIT_LOGS"),
}

# Optional: Appwrite SDK availability flag
APPWRITE_SDK_AVAILABLE = False

try:
    from appwrite.client import Client
    from appwrite.services.databases import Databases
    from appwrite.services.account import Account
    from appwrite.services.functions import Functions
    APPWRITE_SDK_AVAILABLE = True
except ImportError:
    pass


# ==============================================
# APPWRITE REST API CLIENT
# ==============================================

class AppwriteClient:
    """
    Lightweight Appwrite client using REST API.
    Works without the Appwrite SDK installed.
    
    Usage:
        client = AppwriteClient()
        result = client.call_function("get_transactions", {"user_id": "123"})
    """
    
    def __init__(
        self,
        endpoint: str = None,
        project_id: str = None,
        api_key: str = None,
        database_id: str = None
    ):
        """
        Initialize Appwrite client.
        
        Args:
            endpoint: Appwrite endpoint (defaults to env var)
            project_id: Project ID (defaults to env var)
            api_key: API Key (defaults to env var)
            database_id: Database ID (defaults to env var)
        """
        self.endpoint = endpoint or APPWRITE_ENDPOINT
        self.project_id = project_id or APPWRITE_PROJECT_ID
        self.api_key = api_key or APPWRITE_API_KEY
        self.database_id = database_id or APPWRITE_DATABASE_ID
        
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
        async_execution: bool = False,
        timeout: int = 30
    ) -> Optional[Dict]:
        """
        Execute an Appwrite Cloud Function.
        
        Args:
            function_name: Key from FUNCTION_IDS or direct function ID
            payload: Data to pass to the function
            async_execution: If True, don't wait for response
            timeout: Request timeout in seconds
            
        Returns:
            Function execution result or None on error
        """
        # Resolve function ID from name or use directly
        function_id = FUNCTION_IDS.get(function_name) or function_name
        
        if not function_id:
            raise ValueError(f"Unknown function: {function_name}. "
                           f"Available: {list(FUNCTION_IDS.keys())}")
        
        url = f"{self.endpoint}/functions/{function_id}/executions"
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={"data": payload or {}, "async": async_execution},
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            print(f"Appwrite function timeout after {timeout}s")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Appwrite function error: {e}")
            return None
    
    def list_documents(
        self,
        collection_id: str,
        queries: List[str] = None,
        limit: int = 25,
        offset: int = 0
    ) -> Optional[Dict]:
        """
        List documents from an Appwrite collection.
        
        Args:
            collection_id: The collection ID
            queries: Optional list of query strings (e.g., ['equal("status", "active")'])
            limit: Maximum documents to return
            offset: Number of documents to skip
            
        Returns:
            Documents list or None on error
        """
        url = f"{self.endpoint}/databases/{self.database_id}/collections/{collection_id}/documents"
        
        params = {"limit": limit, "offset": offset}
        if queries:
            params["queries[]"] = queries
        
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
        data: Dict[str, Any],
        document_id: str = "unique()",
        permissions: List[str] = None
    ) -> Optional[Dict]:
        """
        Create a document in an Appwrite collection.
        
        Args:
            collection_id: The collection ID
            data: Document data
            document_id: Unique document ID (default: auto-generated)
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
    
    def update_document(
        self,
        collection_id: str,
        document_id: str,
        data: Dict[str, Any],
        permissions: List[str] = None
    ) -> Optional[Dict]:
        """Update an existing document."""
        url = f"{self.endpoint}/databases/{self.database_id}/collections/{collection_id}/documents/{document_id}"
        
        body = {"data": data}
        if permissions:
            body["permissions"] = permissions
        
        try:
            response = requests.patch(
                url,
                headers=self._get_headers(),
                json=body,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Appwrite update document error: {e}")
            return None
    
    def delete_document(
        self,
        collection_id: str,
        document_id: str
    ) -> bool:
        """Delete a document. Returns True if successful."""
        url = f"{self.endpoint}/databases/{self.database_id}/collections/{collection_id}/documents/{document_id}"
        
        try:
            response = requests.delete(
                url,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Appwrite delete document error: {e}")
            return False


# ==============================================
# SINGLETON CLIENT INSTANCE
# ==============================================

# Global client instance
_client: Optional[AppwriteClient] = None


def get_client() -> AppwriteClient:
    """Get the singleton AppwriteClient instance."""
    global _client
    if _client is None:
        _client = AppwriteClient()
    return _client


# ==============================================
# SERVICE HELPER FUNCTIONS
# ==============================================

def get_transactions(user_id: str, limit: int = 100) -> Optional[Dict]:
    """Get transactions for a user via Appwrite function."""
    return get_client().call_function("get_transactions", {
        "user_id": user_id,
        "limit": limit
    })


def create_transaction(
    user_id: str, 
    amount: float, 
    date: str,
    description: str = None,
    category: str = None,
    **kwargs
) -> Optional[Dict]:
    """Create a new transaction."""
    payload = {
        "user_id": user_id,
        "amount": amount,
        "date": date,
    }
    if description:
        payload["description"] = description
    if category:
        payload["category"] = category
    payload.update(kwargs)
    
    return get_client().call_function("create_transaction", payload)


def get_watchlist(user_id: str) -> Optional[Dict]:
    """Get watchlist for a user."""
    return get_client().call_function("get_watchlist", {
        "user_id": user_id
    })


def add_to_watchlist(user_id: str, symbol: str) -> Optional[Dict]:
    """Add a symbol to user's watchlist."""
    return get_client().call_function("add_watchlist", {
        "user_id": user_id,
        "symbol": symbol
    })


def get_user_profile(user_id: str) -> Optional[Dict]:
    """Get user profile data."""
    return get_client().call_function("get_user_profile", {
        "user_id": user_id
    })


def get_bot_metrics(bot_id: str = None) -> Optional[Dict]:
    """Get bot metrics and statistics."""
    return get_client().call_function("get_bot_metrics", {
        "bot_id": bot_id
    })


def get_payments(user_id: str, limit: int = 50) -> Optional[Dict]:
    """Get payments for a user."""
    return get_client().call_function("get_payments", {
        "user_id": user_id,
        "limit": limit
    })


def create_audit_log(
    user_id: str,
    action: str,
    resource: str,
    details: Dict = None
) -> Optional[Dict]:
    """Create an audit log entry."""
    return get_client().call_function("create_audit_log", {
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "details": details or {}
    })


# ==============================================
# CONNECTION TEST
# ==============================================

def test_connection() -> Dict[str, Any]:
    """
    Test Appwrite connectivity.
    
    Returns:
        Dict with connection status and details
    """
    client = get_client()
    
    result = {
        "configured": client.is_configured,
        "sdk_available": APPWRITE_SDK_AVAILABLE,
        "endpoint": APPWRITE_ENDPOINT,
        "project_id": APPWRITE_PROJECT_ID[:8] + "..." if APPWRITE_PROJECT_ID else None,
        "database_id": APPWRITE_DATABASE_ID[:8] + "..." if APPWRITE_DATABASE_ID else None,
        "functions_loaded": sum(1 for v in FUNCTION_IDS.values() if v),
        "api_reachable": False,
    }
    
    # Try a simple health check
    if client.is_configured:
        try:
            response = requests.get(
                f"{APPWRITE_ENDPOINT}/health",
                headers={"X-Appwrite-Project": APPWRITE_PROJECT_ID},
                timeout=5
            )
            result["api_reachable"] = response.status_code == 200
            result["health_status"] = response.json() if response.status_code == 200 else None
        except Exception as e:
            result["health_error"] = str(e)
    
    return result


# ==============================================
# CLI TEST
# ==============================================

if __name__ == "__main__":
    print("=" * 60)
    print("APPWRITE CLIENT CONNECTION TEST")
    print("=" * 60)
    
    result = test_connection()
    
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    print("")
    print("Function IDs:")
    for name, fid in FUNCTION_IDS.items():
        status = "✅" if fid else "❌"
        print(f"  {status} {name}: {fid[:12] + '...' if fid else 'NOT SET'}")
    
    print("=" * 60)
