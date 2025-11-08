"""
Bentley Budget Bot API - Lightweight Vercel Function
"""
import json
from datetime import datetime

def handler(request):
    """
    Simple API handler for Vercel
    """
    
    # Get the request path
    path = request.get('path', '/')
    
    if path == '/':
        # Main information page
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🤖 Bentley Budget Bot API</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 0; padding: 20px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; min-height: 100vh;
                }}
                .container {{ 
                    max-width: 800px; margin: 0 auto; 
                    background: rgba(255,255,255,0.1); 
                    padding: 40px; border-radius: 15px; 
                    backdrop-filter: blur(10px);
                }}
                .btn {{ 
                    background: #ff6b6b; color: white; 
                    padding: 12px 24px; text-decoration: none; 
                    border-radius: 25px; display: inline-block; 
                    margin: 10px 5px; transition: all 0.3s ease;
                }}
                .btn:hover {{ background: #ff5252; transform: translateY(-2px); }}
                .endpoint {{ 
                    background: rgba(255,255,255,0.1); 
                    padding: 15px; margin: 10px 0; 
                    border-radius: 8px; border-left: 4px solid #4ecdc4;
                }}
                h1 {{ font-size: 2.5em; margin-bottom: 20px; }}
                h2 {{ color: #4ecdc4; }}
                .status {{ 
                    display: inline-block; 
                    background: #4caf50; 
                    padding: 5px 15px; 
                    border-radius: 20px; 
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Bentley Budget Bot</h1>
                <div class="status">✅ API Online</div>
                
                <h2>📊 Portfolio Dashboard</h2>
                <p>A comprehensive financial portfolio management and analysis tool with real-time data integration.</p>
                
                <h2>🚀 Deployment Status</h2>
                <ul>
                    <li><strong>API Endpoint:</strong> ✅ Active (Vercel)</li>
                    <li><strong>Dashboard App:</strong> Deploy to Streamlit Cloud recommended</li>
                    <li><strong>Repository:</strong> GitHub synchronized</li>
                </ul>
                
                <h2>📋 API Endpoints</h2>
                <div class="endpoint">
                    <strong>GET /</strong> - This information page
                </div>
                <div class="endpoint">
                    <strong>GET /api/status</strong> - Service status check
                </div>
                <div class="endpoint">
                    <strong>GET /api/health</strong> - Health monitoring
                </div>
                
                <h2>🔗 Quick Links</h2>
                <a href="/api/status" class="btn">📊 API Status</a>
                <a href="/api/health" class="btn">🏥 Health Check</a>
                <a href="https://github.com/winstonwilliamsiii/BBBot" class="btn">📦 GitHub Repo</a>
                
                <p style="margin-top: 40px; text-align: center; opacity: 0.8;">
                    <small>Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</small>
                </p>
            </div>
        </body>
        </html>
        """
        
        return {{
            'statusCode': 200,
            'headers': {{'Content-Type': 'text/html'}},
            'body': html_content
        }}
    
    elif path == '/api/status':
        # API status endpoint
        response = {{
            "status": "online",
            "service": "Bentley Budget Bot API",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "endpoints": ["/", "/api/status", "/api/health"],
            "deployment": "vercel",
            "environment": "production"
        }}
        
        return {{
            'statusCode': 200,
            'headers': {{'Content-Type': 'application/json'}},
            'body': json.dumps(response)
        }}
    
    elif path == '/api/health':
        # Health check endpoint
        response = {{
            "health": "OK",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime": "running",
            "checks": {{
                "api": "✅ operational",
                "database": "N/A (stateless)",
                "external_apis": "⚡ ready"
            }}
        }}
        
        return {{
            'statusCode': 200,
            'headers': {{'Content-Type': 'application/json'}},
            'body': json.dumps(response)
        }}
    
    else:
        # 404 for other paths
        response = {{
            "error": "Not Found",
            "message": f"The requested path '{{path}}' was not found.",
            "timestamp": datetime.now().isoformat(),
            "available_endpoints": ["/", "/api/status", "/api/health"]
        }}
        
        return {{
            'statusCode': 404,
            'headers': {{'Content-Type': 'application/json'}},
            'body': json.dumps(response)
        }}