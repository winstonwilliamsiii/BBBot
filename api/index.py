"""
Vercel Serverless API Handler for BentleyBudgetBot
Adds CORS and simple API key auth for /api/* endpoints.
"""

import json
import os
from datetime import datetime


ALLOWED_ORIGIN = os.getenv("FRONTEND_ORIGIN", "https://bbbot305.streamlit.app")
API_KEY = os.getenv("API_GATEWAY_KEY")


def _cors_headers(origin: str = ALLOWED_ORIGIN):
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, x-api-key",
    }


def _response(status: int, body: dict, origin: str = ALLOWED_ORIGIN):
    return {
        "statusCode": status,
        "headers": _cors_headers(origin),
        "body": json.dumps(body),
    }


def handler(request):
    """Main request handler for Vercel serverless functions"""

    path = getattr(request, "path", "/")
    method = getattr(request, "method", "GET").upper()

    # Preflight
    if method == "OPTIONS":
        return {
            "statusCode": 204,
            "headers": _cors_headers(),
            "body": "",
        }

    # Public: Health
    if path in ("/", "/health"):
        return _response(
            200,
            {
                "status": "healthy",
                "service": "bentley-budget-bot-api",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
            },
        )

    # Public: Status
    if path == "/status":
        return _response(
            200,
            {
                "service": "BentleyBudgetBot API",
                "status": "operational",
                "endpoints": {
                    "health": "/health",
                    "status": "/status",
                    "portfolio": "/api/portfolio",
                },
                "timestamp": datetime.now().isoformat(),
            },
        )

    # Protect all /api/* endpoints with x-api-key if configured
    if path.startswith("/api/") and API_KEY:
        provided = None
        # Vercel Python request headers are likely dict-like
        try:
            provided = request.headers.get("x-api-key")
        except Exception:
            pass
        if provided != API_KEY:
            return _response(401, {"error": "Unauthorized"})

    # Example API: Portfolio placeholder
    if path == "/api/portfolio":
        return _response(
            200,
            {
                "message": "Portfolio endpoint placeholder",
                "note": "Connect to Streamlit frontend for portfolio data",
            },
        )

    # Plaid Link Token endpoint
    if path == "/api/plaid/link_token":
        try:
            # Get link_token from Streamlit session via environment
            # In production, this would call Plaid API
            link_token = os.getenv("PLAID_LINK_TOKEN")
            if not link_token:
                return _response(
                    500,
                    {"error": "Link token not available. Create one in Streamlit first."},
                )
            return _response(200, {"link_token": link_token})
        except Exception as e:
            return _response(500, {"error": str(e)})

    # 404
    return _response(
        404,
        {
            "error": "Endpoint not found",
            "path": path,
            "available_endpoints": ["/health", "/status", "/api/portfolio", "/api/plaid/link_token"],
        },
    )


# Export for Vercel
app = handler
