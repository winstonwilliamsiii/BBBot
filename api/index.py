"""
Vercel Serverless API Handler for BentleyBudgetBot
Handles HTTP requests and provides status/health endpoints
"""

import json
import os
from datetime import datetime

def handler(request):
    """Main request handler for Vercel serverless functions"""
    
    path = request.path
    
    # Health check endpoint
    if path == '/' or path == '/health':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'status': 'healthy',
                'service': 'bentley-budget-bot-api',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            })
        }
    
    # Status endpoint
    elif path == '/status':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'service': 'BentleyBudgetBot API',
                'status': 'operational',
                'endpoints': {
                    'health': '/health',
                    'status': '/status',
                    'frontend': 'https://bentley-budget-bot.streamlit.app'
                },
                'timestamp': datetime.now().isoformat()
            })
        }
    
    # Portfolio endpoint (placeholder for future integration)
    elif path == '/api/portfolio':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Portfolio endpoint placeholder',
                'note': 'Connect to Streamlit frontend for portfolio data'
            })
        }
    
    # 404 for unknown routes
    else:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Endpoint not found',
                'path': path,
                'available_endpoints': [
                    '/health',
                    '/status',
                    '/api/portfolio'
                ]
            })
        }

# Export for Vercel
app = handler
