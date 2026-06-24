# URGENT: Fix Streamlit Cloud Secrets Configuration

**Date:** January 15, 2026  
**Issue:** MySQL looking to localhost:3307, Alpaca not working, Plaid showing Docker errors  
**Cause:** Streamlit Cloud secrets not configured - falling back to localhost defaults  
**Status:** 🔴 ACTION REQUIRED

## What's Wrong

You reported:
1. **MySQL** looking to `localhost:3307` (should be `nozomi.proxy.rlwy.net:54537`)
2. **Alpaca** doesn't work (missing secrets)
3. **Plaid** showing Docker troubleshooting (wrong - should use Appwrite Function on cloud)

**Root Cause:** Streamlit Cloud secrets are **NOT configured** or **incomplete**. The code is falling back to localhost defaults:

```python
# Current behavior (WRONG on cloud):
'host': get_secret('BUDGET_MYSQL_HOST', '127.0.0.1')  # ← Falls back to localhost!
'port': int(get_secret('MYSQL_PORT', '3307'))         # ← Falls back to 3307!
```

## IMMEDIATE FIX - Step by Step

### Step 1: Open Streamlit Cloud Secrets

1. Go to https://share.streamlit.io/
2. Sign in to your Streamlit account
3. Find "bbbot305" app in your list
4. Click on "bbbot305"
5. Click **"Settings"** (gear icon) on the right side
6. Click **"Secrets"** tab

### Step 2: Copy Complete Secrets

Open the file: [STREAMLIT_SECRETS_TEMPLATE.toml](STREAMLIT_SECRETS_TEMPLATE.toml)

Copy **THE ENTIRE FILE** content (all 106 lines)

### Step 3: Paste into Streamlit Cloud

1. In Streamlit Cloud Secrets editor, **DELETE everything currently there**
2. **PASTE** the complete content from STREAMLIT_SECRETS_TEMPLATE.toml
3. Click **"Save"** button
4. Click **"Reboot app"** button

### Step 4: Wait for Reboot (2-3 minutes)

Watch the app status indicator:
- 🟡 **Rebooting** - Wait
- 🟢 **Running** - Ready to test

### Step 5: Verify Fixes

#### Test 1: Check Debug Messages
1. Go to https://bbbot305.streamlit.app/
2. Click on "💰 Personal Budget" page (left sidebar)
3. Look at the **sidebar debug messages**:
   - Should show: `🔍 BUDGET_MYSQL_HOST from secrets: nozomi.proxy.rlwy.net`
   - Should show: `🔍 BUDGET_MYSQL_PORT from secrets: 54537`
   - Should NOT show: `127.0.0.1` or `3307`

#### Test 2: MySQL Connection
1. On "💰 Personal Budget" page
2. Should NOT show error: `Can't connect to MySQL server on '127.0.0.1:3307'`
3. Should connect to Railway (or show different error if database doesn't have data)

#### Test 3: Alpaca API
1. Go to "💼 Broker Trading" page
2. Scroll to "🧪 Test Alpaca Connection"
3. Should show:
   - ✅ Alpaca Connected!
   - Portfolio Value: $100,000.00
   - Buying Power: $200,000.00
   - Status: ACTIVE

#### Test 4: Plaid
1. Go to "🏦 Plaid Test" page
2. Should show: `🌐 Running on Streamlit Cloud - Using Appwrite Function`
3. Backend URL should be: `https://fra.cloud.appwrite.io/v1/...`
4. Should NOT show Docker troubleshooting

## What Each Secret Does

### Railway MySQL Secrets (CRITICAL)
```toml
MYSQL_HOST = "nozomi.proxy.rlwy.net"          # Railway MySQL server
MYSQL_PORT = "54537"                          # Railway external port
MYSQL_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"
```
**Without these:** App tries to connect to localhost:3307 which doesn't exist on Streamlit Cloud

### Budget MySQL Secrets (Personal Budget page)
```toml
BUDGET_MYSQL_HOST = "nozomi.proxy.rlwy.net"   # Same Railway server
BUDGET_MYSQL_PORT = "54537"                   # Same Railway port
BUDGET_MYSQL_DATABASE = "mydb"                # Plaid transactions database
BUDGET_MYSQL_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"
```
**Without these:** Personal Budget page fails with "Can't connect to MySQL"

### Alpaca Secrets (Broker Trading page)
```toml
ALPACA_API_KEY = "***REDACTED***"
ALPACA_SECRET_KEY = "***REDACTED***"
ALPACA_PAPER = "true"
```
**Without these:** Alpaca connection fails, can't test paper trading account

### Plaid Secrets (Plaid Test page)
```toml
PLAID_CLIENT_ID = "677f5a06bfb57e001d2ca8e9"
PLAID_SECRET = "7ce1f012fdd48c25854e3ecc5d1a91"
PLAID_ENV = "sandbox"
```
**Without these:** Plaid Link won't initialize

### MLflow Secrets (Investment Analysis page)
```toml
MLFLOW_MYSQL_HOST = "nozomi.proxy.rlwy.net"
MLFLOW_MYSQL_PORT = "54537"
MLFLOW_MYSQL_DATABASE = "mlflow_db"
MLFLOW_MYSQL_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"
```
**Without these:** "🔬 MLflow Experiments" tab will fail

## Current vs Fixed Configuration

### ❌ CURRENT (Broken)
```
Streamlit Cloud Secrets: EMPTY or INCOMPLETE
↓
Code falls back to defaults:
  MYSQL_HOST → 127.0.0.1 (localhost)
  MYSQL_PORT → 3307 (local Docker)
↓
Result: Can't connect (localhost doesn't exist on cloud)
```

### ✅ AFTER FIX
```
Streamlit Cloud Secrets: COMPLETE (from template)
↓
Code uses secrets:
  MYSQL_HOST → nozomi.proxy.rlwy.net (Railway)
  MYSQL_PORT → 54537 (Railway external port)
↓
Result: Connects to Railway MySQL successfully
```

## Common Mistakes to Avoid

### Mistake 1: Partial Secrets
❌ Only adding MYSQL_HOST without MYSQL_PORT
✅ Add ALL secrets from template

### Mistake 2: Wrong Format
❌ Adding secrets without `=` signs or quotes where needed
✅ Copy exact format from template

### Mistake 3: Forgetting to Reboot
❌ Saving secrets but not rebooting app
✅ Always click "Reboot app" after changing secrets

### Mistake 4: Using Local Values
❌ Setting MYSQL_HOST = "127.0.0.1" in cloud
✅ Always use Railway: "nozomi.proxy.rlwy.net"

## Troubleshooting

### Problem: Still seeing localhost:3307
**Solution:**
1. Verify secrets were saved (go back to Settings → Secrets)
2. Verify you clicked "Reboot app"
3. Clear browser cache and reload page
4. Check debug messages in sidebar

### Problem: Alpaca still not working
**Check in Streamlit logs (Manage app → Logs):**
```python
# Should see:
api_key = st.secrets.get("ALPACA_API_KEY")  # Gets value from secrets
# Should NOT see:
api_key = os.getenv("ALPACA_API_KEY", "")   # Empty - secrets not found
```

### Problem: MySQL password wrong
**Verify Railway password hasn't changed:**
1. Go to https://railway.app/project/bb94b4b8-9905-44b4-bf52-83996d04ed97
2. Click MySQL service
3. Click "Variables" tab
4. Check MYSQL_PASSWORD or MYSQL_ROOT_PASSWORD
5. If different, update template and re-paste to Streamlit

### Problem: Secrets won't save
**Try:**
1. Make sure you have edit permissions on the app
2. Try deleting all secrets first, then pasting
3. Check for TOML syntax errors (extra quotes, missing =)

## Why This Wasn't Caught Earlier

1. **Local development works** - Uses .env file with correct values
2. **Import path fixes worked locally** - Could import modules
3. **Package additions worked** - Installed mlflow, appwrite
4. **BUT secrets were never configured on cloud** - Fell back to localhost

The error messages you saw:
- "MySQL looking to localhost:3307" → Secrets not found, using default
- "Plaid showing Docker troubleshooting" → Wrong backend URL for cloud
- "Alpaca doesn't work" → No API keys in secrets

## Verification Commands

After fixing secrets, check Streamlit logs for:

```
✅ GOOD:
BUDGET_MYSQL_HOST from secrets: nozomi.proxy.rlwy.net
MYSQL_PORT from secrets: 54537
Alpaca API Key: PKAYRIJUWUPO...
```

```
❌ BAD:
BUDGET_MYSQL_HOST NOT in secrets, trying env
MYSQL_PORT from env/default: 3307
Alpaca API Key: (empty)
```

## Summary

**What to do RIGHT NOW:**
1. Open Streamlit Cloud: https://share.streamlit.io/
2. Go to bbbot305 → Settings → Secrets
3. Delete everything in the editor
4. Copy ALL of [STREAMLIT_SECRETS_TEMPLATE.toml](STREAMLIT_SECRETS_TEMPLATE.toml)
5. Paste into Streamlit secrets editor
6. Click "Save"
7. Click "Reboot app"
8. Wait 2-3 minutes for reboot
9. Test: Should see Railway host in debug messages

**This WILL fix:**
- ✅ MySQL connecting to Railway instead of localhost
- ✅ Alpaca API working with paper trading account
- ✅ Plaid using Appwrite Function instead of Docker
- ✅ MLflow experiments tracking to Railway mlflow_db

---

**Created:** January 15, 2026  
**Priority:** 🔴 URGENT - Required for all APIs to work  
**Time to fix:** 5 minutes  
**Impact:** Complete app functionality restored
