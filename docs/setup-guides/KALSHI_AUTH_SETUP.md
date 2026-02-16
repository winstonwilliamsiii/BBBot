# Kalshi API Authentication Setup

**Branch:** `feature/prediction-analytics`

## 🔑 Kalshi Authentication Headers

Kalshi API requires three authentication headers for each request:

```
KALSHI-ACCESS-KEY      = Your API Key ID
KALSHI-ACCESS-TIMESTAMP = Request timestamp in milliseconds
KALSHI-ACCESS-SIGNATURE = HMAC-SHA256 signature of request
```

---

## 📋 What to Store vs. Generate

| Header | Storage | Generated At |
|--------|---------|--------------|
| `KALSHI-ACCESS-KEY` | ✅ Store in env | N/A |
| `KALSHI_PRIVATE_KEY` | ✅ Store in env (secret) | N/A |
| `KALSHI-ACCESS-TIMESTAMP` | ❌ No | Per request (milliseconds) |
| `KALSHI-ACCESS-SIGNATURE` | ❌ No | Per request (HMAC-SHA256) |

---

## 🛠️ Implementation Details

### Signature Generation (Python)

```python
import hashlib
import hmac
import time

def generate_signature(private_key, timestamp, method, path, body=""):
    message = f"{timestamp}{method}{path}{body}"
    signature = hmac.new(
        private_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

# Example: GET /markets at timestamp 1674123456789
timestamp = 1674123456789
signature = generate_signature(
    private_key="your_private_key",
    timestamp=timestamp,
    method="GET",
    path="/markets",
    body=""
)

headers = {
    "KALSHI-ACCESS-KEY": "your_key_id",
    "KALSHI-ACCESS-TIMESTAMP": str(timestamp),
    "KALSHI-ACCESS-SIGNATURE": signature
}
```

---

## 🔒 Environment Variables to Add

### Railway Dashboard
```env
KALSHI_API_KEY=pk_live_xxxxx          # Your Key ID
KALSHI_PRIVATE_KEY=sk_live_xxxxx      # Your Private Key
```

### Streamlit Cloud Secrets
Same as above - add in **Settings** → **Secrets**

### Appwrite Environment Variables
Same as above - add in **Appwrite Console** → **Settings** → **Env**

### .env.railway-prediction (Local)
```env
KALSHI_API_KEY=pk_live_xxxxx
KALSHI_PRIVATE_KEY=sk_live_xxxxx
```

---

## 📜 How to Get Kalshi API Credentials

1. Go to **https://kalshi.com/api**
2. Create an API application
3. Generate API credentials:
   - **Key ID** (public) → `KALSHI_API_KEY`
   - **Private Key** (secret) → `KALSHI_PRIVATE_KEY`
4. Store securely - never commit to git

---

## 🚀 Code Implementation

### Demo Version (Synchronous)
File: `prediction_analytics/services/demo_kalshi.py`

```python
def fetch_kalshi_contracts():
    api_key = os.getenv("KALSHI_API_KEY")
    private_key = os.getenv("KALSHI_PRIVATE_KEY")
    timestamp = int(time.time() * 1000)
    signature = _generate_kalshi_signature(private_key, timestamp, "GET", "/markets")
    
    headers = {
        "KALSHI-ACCESS-KEY": api_key,
        "KALSHI-ACCESS-TIMESTAMP": str(timestamp),
        "KALSHI-ACCESS-SIGNATURE": signature
    }
    response = requests.get(url, headers=headers, timeout=30)
```

### Production Version (Async)
File: `prediction_analytics/services/kalshi_client.py`

```python
class KalshiClient:
    def _get_auth_headers(self, method="GET", path=""):
        timestamp = int(time.time() * 1000)
        signature = self._generate_signature(timestamp, method, path)
        return {
            "KALSHI-ACCESS-KEY": self.api_key,
            "KALSHI-ACCESS-TIMESTAMP": str(timestamp),
            "KALSHI-ACCESS-SIGNATURE": signature,
            "Content-Type": "application/json"
        }
    
    async def fetch_markets(self):
        headers = self._get_auth_headers("GET", "/markets")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                return await resp.json()
```

---

## 🔍 Testing Kalshi Authentication

### Test Locally
```bash
export KALSHI_API_KEY="your_key_id"
export KALSHI_PRIVATE_KEY="your_private_key"
python prediction_analytics/demo_main.py
```

### Test with curl
```bash
timestamp=$(date +%s)000
signature=$(echo -n "${timestamp}GET/markets" | openssl dgst -sha256 -mac HMAC -macopt "key:${KALSHI_PRIVATE_KEY}" -hex | cut -d= -f2)

curl -X GET "https://api.kalshi.com/v1/markets" \
  -H "KALSHI-ACCESS-KEY: $KALSHI_API_KEY" \
  -H "KALSHI-ACCESS-TIMESTAMP: $timestamp" \
  -H "KALSHI-ACCESS-SIGNATURE: $signature"
```

---

## ✅ Deployment Checklist

- [ ] Get Kalshi API Key ID and Private Key from https://kalshi.com/api
- [ ] Add `KALSHI_API_KEY` to Railway Dashboard
- [ ] Add `KALSHI_PRIVATE_KEY` to Railway Dashboard (marked as secret)
- [ ] Add both to Streamlit Cloud Secrets
- [ ] Add both to Appwrite environment
- [ ] Create `.env.railway-prediction.local` with actual values (DO NOT COMMIT)
- [ ] Test locally: `python prediction_analytics/demo_main.py`
- [ ] Deploy to Railway: `git push origin feature/prediction-analytics`
- [ ] Monitor logs for signature errors

---

## 🐛 Troubleshooting

### Error: "Invalid signature"
- Verify `KALSHI_PRIVATE_KEY` is correct
- Check timestamp is in milliseconds (not seconds)
- Ensure no extra whitespace in keys

### Error: "Missing authentication header"
- Verify all three headers are present
- Check variable names match (case-sensitive)

### Error: "Invalid API key"
- Verify `KALSHI_API_KEY` is the Key ID (not private key)
- Check key hasn't been revoked

---

## 📚 References
- Kalshi API Docs: https://kalshi.com/api/docs
- HMAC-SHA256: https://en.wikipedia.org/wiki/HMAC
