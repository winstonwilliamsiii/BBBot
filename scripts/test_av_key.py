import os, dotenv, requests

dotenv.load_dotenv()
key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
print("AV key loaded:", (key[:4] + "****") if key else "MISSING")

url = "https://www.alphavantage.co/query"
params = {"function": "GLOBAL_QUOTE", "symbol": "IYT", "apikey": key}
r = requests.get(url, params=params, timeout=10)
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
