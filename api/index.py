"""
Vercel Serverless API Handler for BentleyBudgetBot
Handles HTTP requests and provides status/health endpoints
"""

import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    """Main request handler for Vercel serverless functions"""
    
    def do_GET(self):
        """Handle GET requests"""
        path = self.path
        
        # Health check endpoint
        if path == '/' or path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'service': 'bentley-budget-bot-api',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Status endpoint
        elif path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'service': 'BentleyBudgetBot API',
                'status': 'operational',
                'endpoints': {
                    'health': '/health',
                    'status': '/status',
                    'frontend': 'https://bentley-budget-bot.streamlit.app'
                },
                'timestamp': datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Portfolio endpoint (placeholder for future integration)
        elif path == '/api/portfolio':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'message': 'Portfolio endpoint placeholder',
                'note': 'Connect to Streamlit frontend for portfolio data'
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        # 404 for unknown routes
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'error': 'Endpoint not found',
                'path': path,
                'available_endpoints': [
                    '/health',
                    '/status',
                    '/api/portfolio'
                ]
            }
            self.wfile.write(json.dumps(response).encode())
            return
