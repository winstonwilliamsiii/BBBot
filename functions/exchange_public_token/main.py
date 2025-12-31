"""
Appwrite Function: Exchange Public Token for Access Token
Runs on Appwrite backend - exchanges tokens and stores in MySQL
Deploy to Appwrite with: appwrite deploy function exchange_public_token
"""

import os
import json
import mysql.connector
from plaid.api import plaid_api
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.configuration import Configuration
from plaid.api_client import ApiClient


def initialize_plaid_client():
    """Initialize Plaid API client"""
    client_id = os.getenv('PLAID_CLIENT_ID')
    secret = os.getenv('PLAID_SECRET')
    env = os.getenv('PLAID_ENV', 'sandbox')
    
    if not client_id or not secret:
        raise ValueError("PLAID_CLIENT_ID and PLAID_SECRET must be set")
    
    env_hosts = {
        'sandbox': 'https://sandbox.plaid.com',
        'development': 'https://development.plaid.com',
        'production': 'https://production.plaid.com'
    }
    
    configuration = Configuration(
        host=env_hosts.get(env, 'https://sandbox.plaid.com'),
        api_key={
            'clientId': client_id,
            'secret': secret,
        }
    )
    
    api_client = ApiClient(configuration)
    return plaid_api.PlaidApi(api_client)


def save_to_database(user_id: str, item_id: str, access_token: str, institution_name: str, tenant_id: str = None):
    """Save Plaid token to MySQL database with RBAC tenant support"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE')
        )
        
        cursor = conn.cursor()
        
        # Create table with RBAC fields if not exists
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS plaid_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                
                -- RBAC / Multi-tenant fields
                tenant_id VARCHAR(64) NOT NULL,
                user_id VARCHAR(64) NOT NULL,
                
                -- Plaid identifiers
                item_id VARCHAR(128) NOT NULL,
                access_token VARCHAR(512) NOT NULL,
                institution_id VARCHAR(64),
                institution_name VARCHAR(255),
                
                -- State management
                is_active TINYINT(1) DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                -- Audit / raw JSON
                raw_json JSON,
                
                -- Indexes for fast RBAC queries
                INDEX idx_plaid_items_tenant_user (tenant_id, user_id),
                INDEX idx_plaid_items_item (item_id),
                INDEX idx_plaid_items_active (tenant_id, is_active),
                UNIQUE KEY unique_tenant_user_item (tenant_id, user_id, item_id)
            )
        """
        cursor.execute(create_table_sql)
        
        # Use tenant from context or environment
        if not tenant_id:
            tenant_id = os.getenv('APPWRITE_FUNCTION_DEPLOYMENT', 'default_tenant')
        
        sql = """
            INSERT INTO plaid_items (
                tenant_id, user_id, item_id, access_token, 
                institution_name, is_active, created_at, updated_at, raw_json
            )
            VALUES (%s, %s, %s, %s, %s, 1, NOW(), NOW(), %s)
            ON DUPLICATE KEY UPDATE 
                access_token = VALUES(access_token),
                institution_name = VALUES(institution_name),
                is_active = 1,
                updated_at = NOW(),
                raw_json = VALUES(raw_json)
        """
        
        raw_json = json.dumps({
            'item_id': item_id,
            'institution_name': institution_name,
            'synced_at': None,
            'status': 'connected'
        })
        
        cursor.execute(sql, (tenant_id, user_id, item_id, access_token, institution_name, raw_json))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        raise Exception(f"Database error: {str(e)}")


def main(context):
    """
    Main Appwrite Function handler
    
    Expected payload:
    {
        "public_token": "public-sandbox-...",
        "user_id": "user123",
        "tenant_id": "tenant123",  -- Optional, derives from context if not provided
        "institution_name": "Chase"
    }
    """
    try:
        # Parse request body
        body = context.req.body_text if hasattr(context.req, 'body_text') else ''
        payload = json.loads(body) if body else {}
        
        public_token = payload.get('public_token')
        user_id = payload.get('user_id')
        tenant_id = payload.get('tenant_id') or os.getenv('APPWRITE_FUNCTION_DEPLOYMENT', 'default_tenant')
        institution_name = payload.get('institution_name', 'Bank')
        
        if not public_token or not user_id:
            return context.res.json({
                'success': False,
                'error': 'public_token and user_id are required'
            }, 400)
        
        # Initialize Plaid client
        plaid_client = initialize_plaid_client()
        
        # Exchange public token for access token
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = plaid_client.item_public_token_exchange(exchange_request)
        
        access_token = exchange_response['access_token']
        item_id = exchange_response['item_id']
        
        # Save to database (tenant-scoped by user_id)
        save_to_database(user_id, item_id, access_token, institution_name, tenant_id)
        
        return context.res.json({
            'success': True,
            'access_token': access_token,
            'item_id': item_id,
            'message': f'Successfully connected {institution_name}'
        })
        
    except Exception as e:
        return context.res.json({
            'success': False,
            'error': str(e)
        }, 500)
