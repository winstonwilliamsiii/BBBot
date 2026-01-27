"""Simplified Kalshi client using requests for Demo_Bots testing."""
import hashlib
import hmac
import time
import requests
import os
from prediction_analytics.config_dual import DemoConfig

def _generate_kalshi_signature(private_key: str, timestamp: int, method: str, path: str, body: str = ""):
    """Generate KALSHI-ACCESS-SIGNATURE using HMAC-SHA256."""
    message = f"{timestamp}{method}{path}{body}"
    signature = hmac.new(
        private_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

def fetch_kalshi_contracts():
    """Fetch markets from Kalshi API with authentication headers."""
    api_key = os.getenv("KALSHI_API_KEY", "")
    private_key = os.getenv("KALSHI_PRIVATE_KEY", "")
    
    if not api_key or not private_key:
        raise ValueError("KALSHI_API_KEY and KALSHI_PRIVATE_KEY required")
    
    url = f"{DemoConfig.KALSHI_API}/markets"
    timestamp = int(time.time() * 1000)  # milliseconds
    signature = _generate_kalshi_signature(private_key, timestamp, "GET", "/markets")
    
    headers = {
        "KALSHI-ACCESS-KEY": api_key,
        "KALSHI-ACCESS-TIMESTAMP": str(timestamp),
        "KALSHI-ACCESS-SIGNATURE": signature,
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()
