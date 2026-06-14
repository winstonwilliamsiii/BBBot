import os, socket, dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.connection import allowed_gai_family

dotenv.load_dotenv()
key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
print("AV key loaded:", (key[:4] + "****") if key else "MISSING")


class _IPv4Adapter(HTTPAdapter):
    def send(self, request, *args, **kwargs):
        _orig = allowed_gai_family
        try:
            import urllib3.util.connection as _c
            _c.allowed_gai_family = lambda: socket.AF_INET
            return super().send(request, *args, **kwargs)
        finally:
            import urllib3.util.connection as _c
            _c.allowed_gai_family = _orig


session = requests.Session()
session.mount("https://", _IPv4Adapter())

url = "https://www.alphavantage.co/query"
params = {"function": "GLOBAL_QUOTE", "symbol": "IYT", "apikey": key}
r = session.get(url, params=params, timeout=10)
data = r.json()

if "Global Quote" in data and data["Global Quote"]:
    q = data["Global Quote"]
    price = q.get("05. price", "N/A")
    volume = q.get("06. volume", "N/A")
    print(f"AV live quote IYT: ${price} (volume: {volume})")
elif "Note" in data:
    print("AV rate limit note:", data["Note"][:120])
elif "Information" in data:
    print("AV info:", data["Information"][:120])
else:
    print("Unexpected response:", str(data)[:200])
