#KALSHI CLIENT
import requests
from config import Config

def fetch_kalshi_contracts():
    url = f"{Config.KALSHI_API}/markets"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()