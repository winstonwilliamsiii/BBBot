"""Simplified Kalshi client using requests for Demo_Bots testing."""
import requests
from prediction_analytics.config_dual import DemoConfig

def fetch_kalshi_contracts():
    """Fetch markets from Kalshi API."""
    url = f"{DemoConfig.KALSHI_API}/markets"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()
