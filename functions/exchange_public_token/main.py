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


def save_to_database(user_id: str, item_id: str, access_token: str, institution_name: str):
    """Save Plaid token to MySQL database"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE')
        )
        
        cursor = conn.cursor()
        
        # Create table if not exists
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS plaid_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL UNIQUE,
                item_id VARCHAR(255) NOT NULL,
                access_token VARCHAR(500) NOT NULL,
                institution_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id)
            )
        """
        cursor.execute(create_table_sql)
        
        sql = """
            INSERT INTO plaid_items (user_id, item_id, access_token, institution_name, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE 
                access_token = VALUES(access_token),
                institution_name = VALUES(institution_name),
                item_id = VALUES(item_id),
                updated_at = NOW()
        """
        
        cursor.execute(sql, (user_id, item_id, access_token, institution_name))
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
        "institution_name": "Chase"
    }
    """
    try:
        # Parse request body
        body = context.req.body_text if hasattr(context.req, 'body_text') else ''
        payload = json.loads(body) if body else {}
        
        public_token = payload.get('public_token')
        user_id = payload.get('user_id')
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
        save_to_database(user_id, item_id, access_token, institution_name)
        
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
