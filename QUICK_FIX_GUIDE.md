# 🚨 QUICK FIX GUIDE - Streamlit Cloud Production

## ⚡ 3-Minute Fix for Production Errors

### Error 1: Unknown database 'bbbot1'
```toml
# In Streamlit Cloud → Settings → Secrets, add:
[mysql]
MYSQL_HOST = "your-railway-host.railway.app"
MYSQL_DATABASE = "railway"  # ← Change to YOUR database name!
MYSQL_USER = "root"
MYSQL_PASSWORD = "your-password"
```

**How to find your database name:**
1. Log into Railway
2. Open MySQL service
3. Click "Query" tab
4. Run: `SHOW DATABASES;`
5. Use that name in secrets

---

### Error 2: Alpaca credentials not configured
```toml
# In Streamlit Cloud → Settings → Secrets, add:
[alpaca]
ALPACA_API_KEY = "PKXXXXXXXXXXXXX"
ALPACA_SECRET_KEY = "XXXXXXXXXXXXXXX"
ALPACA_PAPER = "true"
```

**If you see "unauthorized":**
1. Go to https://alpaca.markets/
2. Paper Trading → API Keys
3. **Delete old keys**
4. Generate new keys
5. Copy to secrets

---

### Error 3: Plaid Link not initializing
```toml
# In Streamlit Cloud → Settings → Secrets, add:
[plaid]
PLAID_CLIENT_ID = "your_client_id"
PLAID_SECRET = "your_sandbox_secret"
PLAID_ENV = "sandbox"
```

**Also required:**
1. Go to https://dashboard.plaid.com/
2. API → Redirect URIs
3. Add: `https://your-app-name.streamlit.app`
4. Save

---

## ✅ How to Apply Fixes

### Step 1: Copy Template
Open: `STREAMLIT_CLOUD_SECRETS_TEMPLATE.toml`

### Step 2: Update Streamlit Cloud
1. Visit https://share.streamlit.io/
2. Click your app
3. Settings (⚙️) → Secrets
4. Paste template
5. Replace placeholder values
6. Click "Save"

### Step 3: Restart App
App will auto-restart after saving secrets

### Step 4: Verify
Look for status banner:
```
✅ MySQL: railway    ✅ Alpaca API    ✅ Plaid API
```

---

## 🧪 Test Locally First

```bash
python test_production_integrations.py
```

Expected:
```
✅ MySQL Database:    ✅ PASS
✅ Alpaca Trading:    ✅ PASS
✅ Plaid Banking:     ✅ PASS
```

---

## 📋 Secrets Checklist

Copy this and fill in:

```
□ MYSQL_HOST (from Railway)
□ MYSQL_DATABASE (verify with SHOW DATABASES)
□ MYSQL_PASSWORD (from Railway)
□ ALPACA_API_KEY (regenerate if expired)
□ ALPACA_SECRET_KEY (regenerate if expired)
□ PLAID_CLIENT_ID (from Plaid dashboard)
□ PLAID_SECRET (from Plaid dashboard)
□ PLAID redirect URI configured
```

---

## 🆘 Still Not Working?

### MySQL Error
- ✅ Check database name is correct (most common issue)
- ✅ Verify Railway MySQL is running
- ✅ Test connection from Railway console

### Alpaca Error
- ✅ Keys expire after 90 days - regenerate
- ✅ Use Paper Trading keys (not live)
- ✅ Check https://alpaca.markets/status

### Plaid Error
- ✅ Redirect URI must match exactly
- ✅ Check PLAID_ENV matches key type
- ✅ Verify keys are for correct environment

---

## 📚 Full Documentation

- **Complete Guide**: `PRODUCTION_DEPLOYMENT_GUIDE.md`
- **Secrets Template**: `STREAMLIT_CLOUD_SECRETS_TEMPLATE.toml`
- **Test Script**: `test_production_integrations.py`
- **Summary**: `PRODUCTION_FIXES_SUMMARY.md`

---

**Most Common Mistake**: Database name mismatch!  
The hardcoded "bbbot1" doesn't exist in production.  
Check Railway for actual database name (usually "railway")
