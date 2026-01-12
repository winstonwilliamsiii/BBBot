# Streamlit Cloud Secrets Configuration

## 🚨 URGENT: Update Streamlit Cloud Secrets After MySQL Consolidation

After consolidating MySQL from port 3306 to 3307, you **MUST** update Streamlit Cloud secrets to prevent connection errors.

## Error You're Seeing
```
❌ Database connection error: 2003: Can't connect to MySQL server on '127.0.0.1:3306' (Errno 111: Connection refused)
```

## How to Fix

### Step 1: Go to Streamlit Cloud Dashboard
1. Visit https://share.streamlit.io/
2. Navigate to your app: **bbbot305**
3. Click the **⋮** menu (three dots) → **Settings**
4. Click the **Secrets** tab

### Step 2: Update Secrets
Replace your existing secrets with these values:

```toml
# === MySQL Configuration (Port 3307) ===
MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = "3307"
MYSQL_USER = "root"
MYSQL_PASSWORD = "root"
MYSQL_DATABASE = "mansa_bot"

# Budget Database (Port 3307)
BUDGET_MYSQL_HOST = "127.0.0.1"
BUDGET_MYSQL_PORT = "3307"
BUDGET_MYSQL_USER = "root"
BUDGET_MYSQL_PASSWORD = "root"
BUDGET_MYSQL_DATABASE = "mydb"

# Operational Database (Port 3307)
BBBOT1_MYSQL_HOST = "127.0.0.1"
BBBOT1_MYSQL_PORT = "3307"
BBBOT1_MYSQL_USER = "root"
BBBOT1_MYSQL_PASSWORD = "root"
BBBOT1_MYSQL_DATABASE = "bbbot1"

# === Railway MySQL (Production) ===
RAILWAY_MYSQL_HOST = "nozomi.proxy.rlwy.net"
RAILWAY_MYSQL_PORT = "54537"
RAILWAY_MYSQL_USER = "root"
RAILWAY_MYSQL_PASSWORD = "your_railway_password_here"
RAILWAY_MYSQL_DATABASE = "railway"

# === Appwrite Configuration ===
APPWRITE_ENDPOINT = "https://cloud.appwrite.io/v1"
APPWRITE_PROJECT_ID = "68869ef500017ca73772"
APPWRITE_API_KEY = "your_appwrite_api_key_here"
APPWRITE_DATABASE_ID = "694481eb003c0a14151d"
APPWRITE_BUCKET_ID = "your_bucket_id"

# === Broker API Keys ===
ALPACA_KEY_ID = "your_alpaca_key"
ALPACA_SECRET_KEY = "your_alpaca_secret"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

# === Banking APIs ===
PLAID_CLIENT_ID = "your_plaid_client_id"
PLAID_SECRET_SANDBOX = "your_plaid_secret"
PLAID_ENV = "sandbox"

CAPITAL_ONE_CLIENT_ID = "your_capital_one_client_id"
CAPITAL_ONE_CLIENT_SECRET = "your_capital_one_secret"

# === Market Data APIs ===
TIINGO_API_TOKEN = "your_tiingo_token"
ALPHA_VANTAGE_API_KEY = "your_alpha_vantage_key"
```

### Step 3: Save and Reboot
1. Click **Save** button
2. Click **Reboot app** to apply changes
3. Wait 30-60 seconds for the app to restart

### Step 4: Verify Connection
Visit https://bbbot305.streamlit.app and check:
- ✅ No "Connection refused" errors
- ✅ Budget dashboard loads successfully
- ✅ All MySQL databases accessible

---

## ⚠️ Important Notes

### Local vs Cloud Configuration
- **Local Development**: Uses `.env` file (port 3307) ✅
- **Streamlit Cloud**: Uses Streamlit Secrets (needs update to 3307) ⚠️

### Why This Happened
1. We consolidated MySQL from dual ports (3306 + 3307) to single port 3307
2. Updated local `.env` file successfully
3. Pushed code to GitHub
4. **Forgot to update Streamlit Cloud secrets** ← YOU ARE HERE

### Railway vs Local MySQL
Choose one connection strategy:

**Option A: Use Railway (Recommended for Cloud)**
```toml
MYSQL_HOST = "nozomi.proxy.rlwy.net"
MYSQL_PORT = "54537"
MYSQL_PASSWORD = "your_railway_password"
MYSQL_DATABASE = "railway"
```

**Option B: Use SSH Tunnel to Local (Advanced)**
```toml
MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = "3307"
# Requires SSH tunnel from Streamlit Cloud to your local machine
```

**Option C: Ngrok/Cloudflare Tunnel (Development Only)**
```toml
MYSQL_HOST = "your-tunnel-url.ngrok.io"
MYSQL_PORT = "3307"
# Temporary tunnel for testing
```

---

## 🔧 Troubleshooting

### Still Getting Port 3306 Error?
1. **Clear browser cache** (Ctrl+Shift+R)
2. **Hard reboot** the Streamlit app
3. **Check secrets were saved** in Streamlit Cloud UI
4. **Verify no typos** in MYSQL_PORT value

### Can't Connect to Railway?
1. Verify Railway MySQL is running: https://railway.app/project/your-project
2. Check Railway database password in Settings → Variables
3. Test connection with MySQL Workbench first

### Need to Rollback?
```toml
# Revert to old port 3306 (NOT RECOMMENDED)
MYSQL_PORT = "3306"
BUDGET_MYSQL_PORT = "3306"
BBBOT1_MYSQL_PORT = "3306"
```

---

## 📋 Quick Reference

| Secret Key | Old Value | New Value | Priority |
|------------|-----------|-----------|----------|
| `MYSQL_PORT` | 3306 | **3307** | 🔴 CRITICAL |
| `BUDGET_MYSQL_PORT` | 3306 | **3307** | 🔴 CRITICAL |
| `BBBOT1_MYSQL_PORT` | 3306 | **3307** | 🔴 CRITICAL |

---

## ✅ Completion Checklist

- [ ] Opened Streamlit Cloud settings
- [ ] Updated MYSQL_PORT to 3307
- [ ] Updated BUDGET_MYSQL_PORT to 3307
- [ ] Updated BBBOT1_MYSQL_PORT to 3307
- [ ] Saved secrets
- [ ] Rebooted app
- [ ] Tested app loads without errors
- [ ] Verified budget dashboard works

---

## 📞 Need Help?

If still seeing errors:
1. Check MySQL is running locally: `netstat -an | Select-String "3307"`
2. Test connection with MySQL Workbench
3. Review logs in Streamlit Cloud: **Manage app** → **Logs**
4. Create GitHub issue with error details

Last Updated: January 12, 2026
