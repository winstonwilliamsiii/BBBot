# 🚨 CORRECT Streamlit Cloud Secrets

## The REAL Problem
Your Streamlit Cloud app is trying to connect to `127.0.0.1:3306` which **doesn't exist** in the cloud. You need to use **Railway MySQL** instead!

## ✅ COPY THIS EXACTLY into Streamlit Cloud Secrets

Go to https://share.streamlit.io/ → bbbot305 → Settings → Secrets and paste:

```toml
# === Railway MySQL (REQUIRED for Streamlit Cloud) ===
MYSQL_HOST = "nozomi.proxy.rlwy.net"
MYSQL_PORT = "54537"
MYSQL_USER = "root"
MYSQL_PASSWORD = "YOUR_RAILWAY_PASSWORD_HERE"
MYSQL_DATABASE = "railway"

# Budget Database (same Railway instance)
BUDGET_MYSQL_HOST = "nozomi.proxy.rlwy.net"
BUDGET_MYSQL_PORT = "54537"
BUDGET_MYSQL_USER = "root"
BUDGET_MYSQL_PASSWORD = "YOUR_RAILWAY_PASSWORD_HERE"
BUDGET_MYSQL_DATABASE = "railway"

# Operational Database (same Railway instance)
BBBOT1_MYSQL_HOST = "nozomi.proxy.rlwy.net"
BBBOT1_MYSQL_PORT = "54537"
BBBOT1_MYSQL_USER = "root"
BBBOT1_MYSQL_PASSWORD = "YOUR_RAILWAY_PASSWORD_HERE"
BBBOT1_MYSQL_DATABASE = "railway"

# === Get Railway Password ===
# 1. Go to https://railway.app/
# 2. Open your project: mansa_bentley
# 3. Click on MySQL service
# 4. Go to Variables tab
# 5. Copy the MYSQL_ROOT_PASSWORD value
# 6. Paste it in all PASSWORD fields above

# === Appwrite ===
APPWRITE_ENDPOINT = "https://cloud.appwrite.io/v1"
APPWRITE_PROJECT_ID = "68869ef500017ca73772"
APPWRITE_API_KEY = "YOUR_APPWRITE_KEY"
APPWRITE_DATABASE_ID = "694481eb003c0a14151d"

# === Broker APIs ===
ALPACA_KEY_ID = "YOUR_ALPACA_KEY"
ALPACA_SECRET_KEY = "YOUR_ALPACA_SECRET"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

# === Banking APIs ===
PLAID_CLIENT_ID = "YOUR_PLAID_ID"
PLAID_SECRET_SANDBOX = "YOUR_PLAID_SECRET"
PLAID_ENV = "sandbox"

# === Market Data ===
TIINGO_API_TOKEN = "YOUR_TIINGO_TOKEN"
ALPHA_VANTAGE_API_KEY = "YOUR_ALPHA_VANTAGE_KEY"
```

## Why This Fixes It

| Wrong (What You Had) | Right (What You Need) |
|---------------------|---------------------|
| `MYSQL_HOST = "127.0.0.1"` | `MYSQL_HOST = "nozomi.proxy.rlwy.net"` |
| `MYSQL_PORT = "3306"` or `"3307"` | `MYSQL_PORT = "54537"` |
| `MYSQL_DATABASE = "mydb"` | `MYSQL_DATABASE = "railway"` |

## After Saving Secrets:
1. Click **Save**
2. Click **Reboot app**
3. Wait 2-3 minutes for app to redeploy
4. Check sidebar for debug messages showing port 54537

## 🔍 Debug Messages
The app will now show in the sidebar:
- `🔍 BUDGET_MYSQL_PORT from secrets: 54537` ← Should say 54537!
- `🔍 DEBUG: Connecting to MySQL Port 54537` ← Should say 54537!

If you still see 3306, the secrets didn't save correctly.
