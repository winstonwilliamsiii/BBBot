# 🚨 Production Issues - Diagnosis & Fixes

## Critical Finding: Alpaca API Key is INVALID (401 Unauthorized)

Your current Alpaca credentials returned a **401 Unauthorized** error, which means:

- ❌ The API key `PKAYRIJUWUPO5VVWVTIWDXPRJ3` is **NOT VALID** or **EXPIRED**
- ❌ The Secret key `HDegV257ex4j1Wc7C3714mVBLoyircYYMTxTozZKWeaA` may also be invalid
- ❌ This is why you're seeing "Failed to retrieve account information" in production

---

## ✅ FIX: Generate New Alpaca API Keys

### Step 1: Log into Alpaca Dashboard
1. Go to https://app.alpaca.markets/
2. Sign in with your Alpaca account

### Step 2: Generate New API Keys
1. Click **Settings** → **API Keys**
2. Click **+ Create API Key**
3. Choose:
   - **Key Name**: "BentleyBot Production"
   - **Permissions**: Check "FULL CONTROL" or at minimum "Read & Trade"
   - **Paper Trading**: YES (for testing) / NO (for live trading)

### Step 3: Copy Your New Keys
You'll see:
- **Client ID** (this is your API Key)
- **Client Secret** (this is your Secret Key)

⚠️ **IMPORTANT**: Copy them IMMEDIATELY - you won't see the Secret Key again!

### Step 4: Update Streamlit Cloud Secrets

Go to https://share.streamlit.io/ → Your App Settings → Secrets

Update these keys:
```toml
ALPACA_API_KEY = "YOUR_NEW_CLIENT_ID_HERE"
ALPACA_SECRET_KEY = "YOUR_NEW_CLIENT_SECRET_HERE"
ALPACA_PAPER = "true"
```

### Step 5: Verify Connection
Run the test script locally:
```bash
python test_alpaca_production.py
```

You should see:
```
✅ SUCCESS: Connected to Alpaca API!
```

---

## 🐛 Additional Issue: Duplicate Keys in Secrets.toml

Fixed! Removed:
- Duplicate `APPWRITE_DATABASE_ID` entries
- Duplicate `[alpaca]` section with root-level Alpaca keys

Now secrets.toml uses only root-level keys (as required by Streamlit).

---

## 📊 Database Connection Fix (Already Applied)

Your trading signals query now:
1. ✅ Explicitly uses `bbbot1` database (maps `mansa_bot` → `bbbot1` on Railway)
2. ✅ Better error messages for "Unknown database" errors
3. ✅ Automatic database routing for production vs local environments

---

## 🔍 Improved Error Handling

Your broker trading pages now show:
1. ✅ Detailed Alpaca troubleshooting steps if connection fails
2. ✅ Diagnostic information (API key format, environment)
3. ✅ Specific error for "Unknown database" with auto-correction explanation

---

## 🚀 Next Steps

### Immediate Actions
1. **Generate new Alpaca API keys** (most critical)
2. Update Streamlit Cloud secrets with new keys
3. Monitor for "Alpaca Connected" confirmation

### Verification
- [ ] Test locally: `python test_alpaca_production.py` → Should show ✅ SUCCESS
- [ ] Check Streamlit Cloud app - should show "✅ Alpaca Connected!"
- [ ] Verify trading signals load without "Unknown database" error

### If Still Getting 401 Error
- [ ] Check Alpaca account is NOT suspended
- [ ] Verify paper trading is ENABLED (if using paper keys)
- [ ] Check that the account has $0.01+ buying power (paper trading requirement)
- [ ] Contact Alpaca support: support@alpaca.markets

---

## 📝 What Was Fixed in This Commit

**Production Fixes Applied:**
```
- Update get_mysql_url() to accept database parameter for flexible routing
- Explicitly use bbbot1 database for trading signals (maps mansa_bot -> bbbot1 on Railway)
- Improve Alpaca error messages to show troubleshooting steps
- Add specific handling for 'Unknown database' errors (1049) with auto-correction explanation
- Better error diagnostics showing API key format and connection details
- Remove duplicate keys in .streamlit/secrets.toml
```

**Code Changes:**
- `frontend/utils/secrets_helper.py` - Updated `get_mysql_url()` parameter handling
- `pages/05_💼_Broker_Trading.py` - Explicit bbbot1 database + improved error messages
- `.streamlit/secrets.toml` - Removed duplicate keys

---

## 🎯 Success Criteria

When you've completed the fixes:
1. ✅ Local test shows "Connected to Alpaca API"
2. ✅ Streamlit Cloud shows "Alpaca Connected!"
3. ✅ Trading signals load from bbbot1 database
4. ✅ No more "Unknown database" errors
5. ✅ App shows specific error messages (not generic failures)

---

## 📞 Support Resources

- **Alpaca API Docs**: https://docs.alpaca.markets/
- **Alpaca Support**: https://support.alpaca.markets/
- **Streamlit Secrets**: https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management
- **GitHub Commit**: `18fe41da`
