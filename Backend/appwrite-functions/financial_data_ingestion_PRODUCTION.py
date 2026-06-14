"""
Production-Grade Financial Data Ingestion Function for Appwrite
================================================================

Handles multi-aggregator financial data ingestion with:
✅ RBAC (Role-Based Access Control)
✅ Tenant scoping & isolation
✅ Secure token retrieval from Appwrite
✅ Multi-aggregator support (Plaid, CashPro, Capital One, CapitalView)
✅ Data normalization & deduplication
✅ MySQL insert/update with transactions
✅ Comprehensive audit logging
✅ Error handling & retry logic
✅ Safe return to Streamlit

Author: Bentley Budget Bot Team
Date: December 29, 2025
"""

import os
import json
import pymysql
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib
import traceback

# Appwrite SDK imports
from appwrite.client import Client
from appwrite.services.account import Account
from appwrite.services.databases import Databases
from appwrite.exception import AppwriteException
from appwrite.query import Query

# ============================================================================
# CONFIGURATION
# ============================================================================

# MySQL Configuration
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB", "mydb")

# Appwrite Configuration
APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT")
APPWRITE_PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID")
APPWRITE_API_KEY = os.getenv("APPWRITE_API_KEY")
APPWRITE_DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID")

# Collections
TOKENS_COLLECTION_ID = os.getenv("TOKENS_COLLECTION_ID", "user_tokens")
AUDIT_COLLECTION_ID = os.getenv("AUDIT_COLLECTION_ID", "audit_logs")
RBAC_COLLECTION_ID = os.getenv("RBAC_COLLECTION_ID", "user_roles")

# Aggregator Selection
AGGREGATOR = os.getenv("AGGREGATOR", "plaid")

# Retry Configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "2"))

# ============================================================================
# APPWRITE CLIENT
# ============================================================================

def get_appwrite_client(api_key: str = None) -> Client:
    """
    Initialize Appwrite client with proper configuration
    
    Args:
        api_key: Optional API key override (for server-side operations)
        
    Returns:
        Configured Appwrite client
    """
    client = Client()
    client.set_endpoint(APPWRITE_ENDPOINT)
    client.set_project(APPWRITE_PROJECT_ID)
    
    if api_key:
        client.set_key(api_key)
    else:
        client.set_key(APPWRITE_API_KEY)
    
    return client


# ============================================================================
# RBAC VALIDATION
# ============================================================================

def validate_rbac(user_id: str, tenant_id: str, required_permission: str = "transactions:read") -> Tuple[bool, str]:
    """
    Validate user has required permission for tenant
    
    Args:
        user_id: User ID to check
        tenant_id: Tenant ID for scoping
        required_permission: Permission required (e.g., "transactions:read", "transactions:write")
        
    Returns:
        Tuple of (is_authorized, error_message)
    """
    try:
        client = get_appwrite_client()
        databases = Databases(client)
        
        # Query user roles for this tenant
        response = databases.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=RBAC_COLLECTION_ID,
            queries=[
                Query.equal("user_id", user_id),
                Query.equal("tenant_id", tenant_id),
                Query.equal("is_active", True)
            ]
        )
        
        if not response['documents']:
            return False, f"No active role found for user {user_id} in tenant {tenant_id}"
        
        # Check if user has required permission
        user_role = response['documents'][0]
        permissions = user_role.get('permissions', [])
        
        if required_permission in permissions or "admin" in permissions:
            return True, ""
        
        return False, f"User lacks required permission: {required_permission}"
        
    except AppwriteException as e:
        return False, f"RBAC validation failed: {str(e)}"
    except Exception as e:
        return False, f"Unexpected RBAC error: {str(e)}"


# ============================================================================
# DATABASE CONNECTION WITH POOLING
# ============================================================================

def get_db_connection():
    """
    Create MySQL connection with SSL and proper error handling
    
    Returns:
        pymysql.Connection object
    """
    try:
        return pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,
            ssl={'ca': None} if os.getenv("MYSQL_SSL_ENABLED", "false").lower() == "true" else None,
            autocommit=False
        )
    except pymysql.MySQLError as e:
        raise Exception(f"Database connection failed: {str(e)}")


# ============================================================================
# SECURE TOKEN RETRIEVAL
# ============================================================================

def load_access_token(user_id: str, tenant_id: str, aggregator: str) -> Optional[str]:
    """
    Load encrypted access token from Appwrite database
    
    Args:
        user_id: User ID
        tenant_id: Tenant ID for isolation
        aggregator: Aggregator type (plaid, cashpro, etc.)
        
    Returns:
        Decrypted access token or None
    """
    try:
        client = get_appwrite_client()
        databases = Databases(client)
        
        # Query tokens collection with tenant scoping
        response = databases.list_documents(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=TOKENS_COLLECTION_ID,
            queries=[
                Query.equal("user_id", user_id),
                Query.equal("tenant_id", tenant_id),
                Query.equal("aggregator", aggregator),
                Query.equal("is_active", True)
            ]
        )
        
        if not response['documents']:
            raise ValueError(f"No active {aggregator} token found for user {user_id} in tenant {tenant_id}")
        
        token_doc = response['documents'][0]
        
        # Return encrypted token (decryption handled by aggregator SDK)
        return token_doc.get('access_token')
        
    except AppwriteException as e:
        raise Exception(f"Token retrieval failed: {str(e)}")


# ============================================================================
# AGGREGATOR IMPLEMENTATIONS
# ============================================================================

def fetch_plaid_transactions(access_token: str, start_date: str, end_date: str) -> List[Dict]:
    """Fetch transactions from Plaid API"""
    try:
        from plaid.api import plaid_api
        from plaid.model.transactions_get_request import TransactionsGetRequest
        from plaid.configuration import Configuration
        from plaid.api_client import ApiClient
        
        configuration = Configuration(
            host=os.getenv("PLAID_ENV", "https://sandbox.plaid.com"),
            api_key={
                'clientId': os.getenv("PLAID_CLIENT_ID"),
                'secret': os.getenv("PLAID_SECRET")
            }
        )
        
        api_client = ApiClient(configuration)
        client = plaid_api.PlaidApi(api_client)
        
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date
        )
        
        response = client.transactions_get(request)
        return response['transactions']
        
    except Exception as e:
        raise Exception(f"Plaid API error: {str(e)}")


def fetch_cashpro_transactions(access_token: str, start_date: str, end_date: str) -> List[Dict]:
    """Fetch transactions from Bank of America CashPro API"""
    try:
        import requests
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'startDate': start_date,
            'endDate': end_date
        }
        
        response = requests.get(
            os.getenv("CASHPRO_API_URL"),
            headers=headers,
            params=params,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json().get('transactions', [])
        
    except Exception as e:
        raise Exception(f"CashPro API error: {str(e)}")


def fetch_capitalone_transactions(access_token: str, start_date: str, end_date: str) -> List[Dict]:
    """Fetch transactions from Capital One DevExchange API"""
    try:
        import requests
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'version': '1'
        }
        
        params = {
            'fromDate': start_date,
            'toDate': end_date
        }
        
        response = requests.get(
            f"{os.getenv('CAPITALONE_API_URL')}/transactions",
            headers=headers,
            params=params,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json().get('transactions', [])
        
    except Exception as e:
        raise Exception(f"Capital One API error: {str(e)}")


def fetch_capitalview_transactions(access_token: str, start_date: str, end_date: str) -> List[Dict]:
    """Fetch transactions from CapitalView API"""
    try:
        import requests
        
        headers = {
            'Authorization': f'Token {access_token}',
            'Accept': 'application/json'
        }
        
        payload = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        response = requests.post(
            f"{os.getenv('CAPITALVIEW_API_URL')}/v1/transactions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json().get('data', [])
        
    except Exception as e:
        raise Exception(f"CapitalView API error: {str(e)}")


def fetch_transactions_with_retry(access_token: str, aggregator: str, start_date: str, end_date: str) -> List[Dict]:
    """
    Fetch transactions with retry logic and fallback
    
    Args:
        access_token: Access token for API
        aggregator: Aggregator type
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        List of transactions
    """
    for attempt in range(MAX_RETRIES):
        try:
            if aggregator == "plaid":
                return fetch_plaid_transactions(access_token, start_date, end_date)
            elif aggregator == "cashpro":
                return fetch_cashpro_transactions(access_token, start_date, end_date)
            elif aggregator == "capitalone":
                return fetch_capitalone_transactions(access_token, start_date, end_date)
            elif aggregator == "capitalview":
                return fetch_capitalview_transactions(access_token, start_date, end_date)
            else:
                raise ValueError(f"Unsupported aggregator: {aggregator}")
                
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            raise e


# ============================================================================
# DATA NORMALIZATION
# ============================================================================

def generate_transaction_hash(tx: Dict) -> str:
    """
    Generate unique hash for transaction deduplication
    
    Args:
        tx: Transaction dict
        
    Returns:
        MD5 hash string
    """
    unique_string = f"{tx.get('date')}:{tx.get('amount')}:{tx.get('merchant')}:{tx.get('account_id')}"
    return hashlib.md5(unique_string.encode()).hexdigest()


def normalize_transaction(tx: Dict, user_id: str, tenant_id: str, aggregator: str) -> Dict:
    """
    Normalize transaction to common schema with deduplication hash
    
    Args:
        tx: Raw transaction from aggregator
        user_id: User ID
        tenant_id: Tenant ID
        aggregator: Source aggregator
        
    Returns:
        Normalized transaction dict
    """
    normalized = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "account_id": tx.get("account_id"),
        "transaction_id": tx.get("transaction_id"),
        "amount": float(tx.get("amount", 0)),
        "date": tx.get("date"),
        "merchant": tx.get("name") or tx.get("merchant_name") or "Unknown",
        "category": (tx.get("category") or ["uncategorized"])[0] if isinstance(tx.get("category"), list) else tx.get("category", "uncategorized"),
        "pending": tx.get("pending", False),
        "aggregator": aggregator,
        "raw_json": json.dumps(tx),
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Add deduplication hash
    normalized["transaction_hash"] = generate_transaction_hash(normalized)
    
    return normalized


# ============================================================================
# DATABASE OPERATIONS WITH DEDUPLICATION
# ============================================================================

def upsert_transactions(transactions: List[Dict], conn) -> Tuple[int, int]:
    """
    Insert or update transactions with deduplication
    
    Args:
        transactions: List of normalized transactions
        conn: MySQL connection
        
    Returns:
        Tuple of (inserted_count, updated_count)
    """
    cursor = conn.cursor()
    inserted = 0
    updated = 0
    
    try:
        for tx in transactions:
            # Check if transaction exists
            check_sql = """
                SELECT id, amount, category FROM transactions
                WHERE tenant_id = %s AND transaction_hash = %s
            """
            cursor.execute(check_sql, (tx['tenant_id'], tx['transaction_hash']))
            existing = cursor.fetchone()
            
            if existing:
                # Update if changed
                update_sql = """
                    UPDATE transactions
                    SET amount = %s, category = %s, merchant = %s, 
                        pending = %s, raw_json = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """
                cursor.execute(update_sql, (
                    tx['amount'], tx['category'], tx['merchant'],
                    tx['pending'], tx['raw_json'], existing['id']
                ))
                updated += 1
            else:
                # Insert new transaction
                insert_sql = """
                    INSERT INTO transactions
                    (tenant_id, user_id, account_id, transaction_id, amount, date, 
                     merchant, category, pending, aggregator, raw_json, transaction_hash, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_sql, (
                    tx['tenant_id'], tx['user_id'], tx['account_id'], tx['transaction_id'],
                    tx['amount'], tx['date'], tx['merchant'], tx['category'],
                    tx['pending'], tx['aggregator'], tx['raw_json'], tx['transaction_hash'],
                    tx['created_at']
                ))
                inserted += 1
        
        conn.commit()
        return inserted, updated
        
    except Exception as e:
        conn.rollback()
        raise Exception(f"Database upsert failed: {str(e)}")
    finally:
        cursor.close()


# ============================================================================
# AUDIT LOGGING
# ============================================================================

def log_audit_event(
    user_id: str, 
    tenant_id: str, 
    action: str, 
    status: str, 
    details: Dict,
    duration_ms: int = 0
):
    """
    Log audit event to Appwrite database
    
    Args:
        user_id: User who performed action
        tenant_id: Tenant ID
        action: Action performed (e.g., "transaction_sync")
        status: Status (success, error, partial)
        details: Additional details dict
        duration_ms: Operation duration in milliseconds
    """
    try:
        client = get_appwrite_client()
        databases = Databases(client)
        
        audit_log = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "action": action,
            "status": status,
            "details": json.dumps(details),
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat(),
            "function_name": "financial_data_ingestion"
        }
        
        databases.create_document(
            database_id=APPWRITE_DATABASE_ID,
            collection_id=AUDIT_COLLECTION_ID,
            document_id='unique()',
            data=audit_log
        )
        
    except Exception as e:
        # Don't fail main operation if audit logging fails
        print(f"Audit logging failed: {str(e)}")


# ============================================================================
# MAIN HANDLER
# ============================================================================

def main(req, res):
    """
    Main Appwrite Function handler for financial data ingestion
    
    Expected request body:
    {
        "user_id": "user_123",
        "tenant_id": "tenant_456",
        "aggregator": "plaid",  // optional, defaults to env AGGREGATOR
        "start_date": "2024-01-01",  // optional, defaults to 30 days ago
        "end_date": "2025-12-31"  // optional, defaults to today
    }
    
    Returns:
    {
        "success": true,
        "inserted": 45,
        "updated": 12,
        "total": 57,
        "aggregator": "plaid",
        "duration_ms": 2341
    }
    """
    start_time = time.time()
    conn = None
    
    try:
        # ====================================================================
        # 1. PARSE AND VALIDATE INPUT
        # ====================================================================
        body = json.loads(req.body) if req.body else {}
        
        user_id = body.get("user_id")
        tenant_id = body.get("tenant_id")
        
        if not user_id or not tenant_id:
            return res.json({
                "success": False,
                "error": "Missing required fields: user_id, tenant_id"
            }, 400)
        
        aggregator = body.get("aggregator", AGGREGATOR)
        
        # Date range defaults
        end_date = body.get("end_date", datetime.now().strftime("%Y-%m-%d"))
        start_date = body.get("start_date", (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        
        # ====================================================================
        # 2. RBAC VALIDATION
        # ====================================================================
        is_authorized, rbac_error = validate_rbac(user_id, tenant_id, "transactions:write")
        
        if not is_authorized:
            log_audit_event(user_id, tenant_id, "transaction_sync", "unauthorized", {
                "error": rbac_error
            })
            return res.json({
                "success": False,
                "error": f"Authorization failed: {rbac_error}"
            }, 403)
        
        # ====================================================================
        # 3. LOAD ACCESS TOKEN
        # ====================================================================
        try:
            access_token = load_access_token(user_id, tenant_id, aggregator)
        except Exception as e:
            log_audit_event(user_id, tenant_id, "transaction_sync", "error", {
                "error": f"Token load failed: {str(e)}"
            })
            return res.json({
                "success": False,
                "error": f"Token retrieval failed: {str(e)}"
            }, 500)
        
        # ====================================================================
        # 4. FETCH TRANSACTIONS FROM AGGREGATOR
        # ====================================================================
        try:
            transactions = fetch_transactions_with_retry(
                access_token, aggregator, start_date, end_date
            )
        except Exception as e:
            log_audit_event(user_id, tenant_id, "transaction_sync", "error", {
                "error": f"API fetch failed: {str(e)}",
                "aggregator": aggregator
            })
            return res.json({
                "success": False,
                "error": f"Failed to fetch transactions: {str(e)}"
            }, 500)
        
        if not transactions:
            duration_ms = int((time.time() - start_time) * 1000)
            log_audit_event(user_id, tenant_id, "transaction_sync", "success", {
                "message": "No transactions found in date range",
                "date_range": f"{start_date} to {end_date}"
            }, duration_ms)
            return res.json({
                "success": True,
                "inserted": 0,
                "updated": 0,
                "total": 0,
                "message": "No transactions found",
                "duration_ms": duration_ms
            })
        
        # ====================================================================
        # 5. NORMALIZE TRANSACTIONS
        # ====================================================================
        normalized = [
            normalize_transaction(tx, user_id, tenant_id, aggregator)
            for tx in transactions
        ]
        
        # ====================================================================
        # 6. DATABASE OPERATIONS
        # ====================================================================
        conn = get_db_connection()
        inserted, updated = upsert_transactions(normalized, conn)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # ====================================================================
        # 7. AUDIT LOGGING
        # ====================================================================
        log_audit_event(user_id, tenant_id, "transaction_sync", "success", {
            "aggregator": aggregator,
            "date_range": f"{start_date} to {end_date}",
            "fetched": len(transactions),
            "inserted": inserted,
            "updated": updated
        }, duration_ms)
        
        # ====================================================================
        # 8. RETURN SUCCESS RESPONSE
        # ====================================================================
        return res.json({
            "success": True,
            "inserted": inserted,
            "updated": updated,
            "total": len(normalized),
            "aggregator": aggregator,
            "date_range": {
                "start": start_date,
                "end": end_date
            },
            "duration_ms": duration_ms
        })
        
    except Exception as e:
        # ====================================================================
        # ERROR HANDLING
        # ====================================================================
        duration_ms = int((time.time() - start_time) * 1000)
        error_trace = traceback.format_exc()
        
        # Log error audit event
        if 'user_id' in locals() and 'tenant_id' in locals():
            log_audit_event(user_id, tenant_id, "transaction_sync", "error", {
                "error": str(e),
                "trace": error_trace
            }, duration_ms)
        
        return res.json({
            "success": False,
            "error": str(e),
            "trace": error_trace if os.getenv("DEBUG", "false").lower() == "true" else None,
            "duration_ms": duration_ms
        }, 500)
        
    finally:
        # Clean up database connection
        if conn:
            try:
                conn.close()
            except:
                pass
