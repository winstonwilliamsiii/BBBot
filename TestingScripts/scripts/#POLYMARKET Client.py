#POLYMARKET Client
import requests
from config import Config

def fetch_polymarket_contracts():
    url = f"{Config.POLYMARKET_API}/markets"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()