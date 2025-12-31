"""
Appwrite Function: Create Plaid Link Token
Runs on Appwrite backend - generates short-lived link tokens
Deploy to Appwrite with: appwrite deploy function create_link_token
"""

import os
import json
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.configuration import Configuration
from plaid.api_client import ApiClient


def initialize_plaid_client():
    """Initialize Plaid API client with environment variables"""
    client_id = os.getenv('PLAID_CLIENT_ID')
    secret = os.getenv('PLAID_SECRET')
    env = os.getenv('PLAID_ENV', 'sandbox')
    
    if not client_id or not secret:
        raise ValueError("PLAID_CLIENT_ID and PLAID_SECRET must be set in Appwrite environment")
    
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


def main(context):
    """
    Main Appwrite Function handler
    
    Expected payload:
    {
        "user_id": "user123",
        "client_name": "Bentley Budget Bot"
    }
    """
    try:
        # Parse request body
        body = context.req.body_text if hasattr(context.req, 'body_text') else ''
        payload = json.loads(body) if body else {}
        
        user_id = payload.get('user_id')
        client_name = payload.get('client_name', 'Bentley Budget Bot')
        
        if not user_id:
            return context.res.json({
                'success': False,
                'error': 'user_id is required'
            }, 400)
        
        # Initialize Plaid client
        plaid_client = initialize_plaid_client()
        
        # Create link token request
        request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id=str(user_id)),
            client_name=client_name,
            products=[Products("transactions")],
            country_codes=[CountryCode("US")],
            language='en',
        )
        
        # Call Plaid API
        response = plaid_client.link_token_create(request)
        
        return context.res.json({
            'success': True,
            'link_token': response['link_token'],
            'expiration': str(response['expiration']),
            'request_id': response['request_id']
        })
        
    except Exception as e:
        return context.res.json({
            'success': False,
            'error': str(e)
        }, 500)
