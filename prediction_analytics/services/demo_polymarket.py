"""Simplified Polymarket client using requests for Demo_Bots testing."""
import requests
from prediction_analytics.config_dual import DemoConfig

def fetch_polymarket_contracts():
    """Fetch markets from Polymarket Gamma API."""
    url = f"{DemoConfig.POLYMARKET_API}/markets"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()
