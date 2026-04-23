# 🔧 Fixing Plaid and Alpaca Issues

## Issue Summary
1. **Plaid Error**: `"client_id must be a properly formatted, non-empty string"`
2. **Alpaca Production**: Failed to retrieve account information on production

---

## 🔍 Root Causes Identified

### Plaid Issue
Your `PLAID_CLIENT_ID` in `.env` may be:
- Truncated or incomplete
- Has trailing/leading spaces
- Is the sandbox ID instead of production ID

**Current value in .env:**
```
PLAID_CLIENT_ID=68b8718ec2f428002456a84c
```

**Valid Plaid Client IDs should be:**
- Exactly **24 characters** for production
- Format: lowercase alphanumeric (e.g., `68b8718ec2f428002456a84c`)

### Alpaca Production Issue
Your `.env` is configured for **paper trading**:
```
ALPACA_API_KEY=PKAYRIJUWUPO5VVWVTIWDXPRJ3  ← Paper trading key (starts with PK)
ALPACA_SECRET_KEY=HDegV257ex4j1Wc7C3714mVBLoyircYYMTxTozZKWeaA
ALPACA_PAPER=true  ← Force paper mode
```

**Production keys should:**
- Start with `AK` (not `PK`)
- Use `ALPACA_PAPER=false`

---

## ✅ Fix Instructions

### Fix 1: Update Plaid Credentials

1. **Get your actual Plaid Client ID:**
   - Go to https://dashboard.plaid.com/
   - Log in
   - Navigate to **Team Settings** → **Keys**
   - Copy your **client_id** (should be 24 characters)
   - Copy your **secret** (development or production)

2. **Update .env file:**
   ```bash
   PLAID_CLIENT_ID=your_24_character_client_id_here
   PLAID_SECRET=your_actual_secret_here
   PLAID_ENV=sandbox  # or 'production' if using live keys
   ```

3. **Verify the fix:**
   ```bash
   python update_plaid_credentials.py
   ```

### Fix 2: Get Alpaca Production Keys

1. **Get production API keys:**
   - Go to https://alpaca.markets/
   - Log in to your account
   - Navigate to **Your API Keys** (Paper/Live toggle)
   - Switch to **Live Trading**
   - Generate new API keys (starts with `AK`)

2. **Update .env file:**
   ```bash
   # Production Keys
   ALPACA_API_KEY=AK... (your live key starting with AK)
   ALPACA_SECRET_KEY=... (your live secret)
   ALPACA_PAPER=false  # USE PRODUCTION

   # Keep paper keys separately
   ALPACA_PAPER_API_KEY=PK...
   ALPACA_PAPER_SECRET_KEY=...
   ```

3. **Test production connection:**
   ```bash
   python tests/test_alpaca_connection.py
   ```

---

## 🚀 Quick Fix Script

I've created an automated fix script for you:

```bash
# Run this to update credentials interactively
python fix_credentials.py
```

---

## ⚠️ Important Notes

### Plaid
- **Sandbox** keys work only with test banks (Chase, Wells Fargo, etc.)
- **Development** keys allow up to 100 live Items for free
- **Production** requires approval and has costs per Item

### Alpaca
- **Paper trading** = unlimited virtual money, no real trades
- **Live trading** = real money, requires funded account
- Never commit production keys to Git!

---

## 🧪 Testing Checklist

- [ ] Plaid Client ID is 24 characters
- [ ] Plaid Secret matches your environment (sandbox/production)
- [ ] Alpaca API key starts with `AK` for production
- [ ] `ALPACA_PAPER=false` for production
- [ ] Test with `python tests/test_alpaca_connection.py`
- [ ] Test Plaid with `streamlit run test_plaid_streamlit.py`

---

## 📞 Still Having Issues?

### Plaid Troubleshooting
```python
# Test Plaid credentials directly
from plaid.configuration import Configuration
from plaid.api_client import ApiClient

config = Configuration(
    host='https://sandbox.plaid.com',
    api_key={
        'clientId': 'YOUR_CLIENT_ID',
        'secret': 'YOUR_SECRET'
    }
)
client = ApiClient(config)
print("✅ Plaid client initialized successfully!")
```

### Alpaca Troubleshooting
```python
# Test Alpaca credentials directly
import requests

headers = {
    'APCA-API-KEY-ID': 'YOUR_API_KEY',
    'APCA-API-SECRET-KEY': 'YOUR_SECRET'
}
response = requests.get('https://api.alpaca.markets/v2/account', headers=headers)
print(response.json())
```

---

## Next Steps

1. Update your `.env` file with correct credentials
2. Restart your application
3. Test integrations
4. Verify no errors in console

**Need help?** Check the official docs:
- Plaid: https://plaid.com/docs/
- Alpaca: https://alpaca.markets/docs/
