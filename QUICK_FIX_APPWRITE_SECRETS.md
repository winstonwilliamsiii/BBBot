# 🚨 URGENT FIX: Quick Actions Watchlist Error

**Date:** January 22, 2026  
**Issue:** Missing Appwrite configuration on Production  
**Error:** `Missing Appwrite configuration. Set APPWRITE_PROJECT_ID and APPWRITE_FUNCTION_ID_ADD_WATCHLIST`  
**Location:** https://bbbot305.streamlit.app/ → Home page → Quick Actions → Watchlist

---

## 🎯 Root Cause

The Streamlit Cloud secrets are **missing Appwrite Function IDs** that are required for the Quick Actions watchlist feature. The code expects:

```python
APPWRITE_PROJECT_ID = "68869ef500017ca73772"  # ✅ Already set
APPWRITE_FUNCTION_ID_ADD_WATCHLIST_STREAMLIT = "???"  # ❌ MISSING!
```

---

## ⚡ 5-Minute Fix (Step-by-Step)

### Step 1: Open Streamlit Cloud Secrets (1 minute)

1. Go to **https://share.streamlit.io/**
2. Sign in to your account
3. Click on **bbbot305** app
4. Click **⚙️ Settings** (top right)
5. Click **🔐 Secrets** tab

### Step 2: Add Missing Appwrite Function IDs (2 minutes)

**IMPORTANT:** Do NOT delete existing secrets. Just **ADD** these lines at the bottom:

```toml
# =============================================================================
# APPWRITE FUNCTION IDs (Required for Quick Actions and Watchlist)
# =============================================================================

# Streamlit-specific functions (CRITICAL for homepage Quick Actions)
APPWRITE_FUNCTION_ID_GET_TRANSACTIONS_STREAMLIT = "694daffaae8121bb7837"
APPWRITE_FUNCTION_ID_ADD_WATCHLIST_STREAMLIT = "694da7003804de8bb29a"
APPWRITE_FUNCTION_ID_GET_WATCHLIST_STREAMLIT = "694da75bd55dc6d65fb9"
APPWRITE_FUNCTION_ID_GET_USER_PROFILE_STREAMLIT = "694da7aedf6018cc8266"

# Core transaction functions
APPWRITE_FUNCTION_ID_CREATE_TRANSACTION = "694db02c58495b52f6e6"
APPWRITE_FUNCTION_ID_GET_TRANSACTIONS = "694daffaae8121bb7837"

# Payment functions
APPWRITE_FUNCTION_ID_CREATE_PAYMENT = "694dab48338627afc96a"
APPWRITE_FUNCTION_ID_GET_PAYMENTS = "694daddc3fed56721c52"

# Audit log functions
APPWRITE_FUNCTION_ID_CREATE_AUDIT_LOG = "694dab48338627afc96a"
APPWRITE_FUNCTION_ID_GET_AUDIT_LOGS = "694daaad91f3b1b6d68c"

# Role and permission functions
APPWRITE_FUNCTION_ID_MANAGE_ROLES = "694dadd46101f81438ab"
APPWRITE_FUNCTION_ID_MANAGE_PERMISSIONS = "694dadcc6bf877c015de"

# Bot metrics functions
APPWRITE_FUNCTION_ID_CREATE_BOT_METRIC = "694dadc18bd08f7a3895"
APPWRITE_FUNCTION_ID_GET_BOT_METRICS = "694dadba22d1eeada62d"
APPWRITE_FUNCTION_ID_GET_BOT_METRICS_STATS = "694dada2b9c2ddef7c56"
```

### Step 3: Save and Reboot (1 minute)

1. Click **💾 Save** button
2. Click **🔄 Reboot app** button
3. Wait 30-60 seconds for restart

### Step 4: Verify Fix (1 minute)

1. Go to **https://bbbot305.streamlit.app/**
2. On Home page, find **Quick Actions** section
3. Try **Add to Watchlist** feature
4. Error should be **GONE** ✅

---

## 📋 What Each Function ID Does

| Function ID | Purpose | Used By |
|-------------|---------|---------|
| `APPWRITE_FUNCTION_ID_ADD_WATCHLIST_STREAMLIT` | Adds symbols to user watchlist | Quick Actions, Watchlist page |
| `APPWRITE_FUNCTION_ID_GET_WATCHLIST_STREAMLIT` | Retrieves user's watchlist | Home page, Watchlist page |
| `APPWRITE_FUNCTION_ID_GET_TRANSACTIONS_STREAMLIT` | Gets user transactions | Transaction history |
| `APPWRITE_FUNCTION_ID_GET_USER_PROFILE_STREAMLIT` | Gets user profile data | Profile page |

---

## 🔍 Where Was This Configured?

These Function IDs were deployed on **December 25, 2025** and stored in:
- ✅ Local `.env` file (working locally)
- ✅ `.env.backup_20260112_094253` (backup)
- ❌ Streamlit Cloud Secrets (MISSING - causing production error)

---

## 🆘 Still Not Working?

### Symptom 1: Still seeing "Missing Appwrite configuration"
**Solution:**
1. Double-check you saved the secrets in Streamlit Cloud
2. Make sure you clicked "Reboot app"
3. Wait 60 seconds for full restart
4. Clear browser cache (Ctrl+Shift+R)

### Symptom 2: New error "Function execution failed"
**Solution:**
1. Check Appwrite Console: https://cloud.appwrite.io/console/project-68869ef500017ca73772
2. Navigate to **Functions** section
3. Verify function `694da7003804de8bb29a` exists and is deployed
4. Check function logs for execution errors

### Symptom 3: "APPWRITE_PROJECT_ID not found"
**Solution:**
Add this to Streamlit Cloud Secrets:
```toml
APPWRITE_PROJECT_ID = "68869ef500017ca73772"
```

---

## 📝 Full Secrets Template

For a **complete** Streamlit Cloud secrets configuration (including ALL settings), see:
**[STREAMLIT_SECRETS_TEMPLATE.toml](STREAMLIT_SECRETS_TEMPLATE.toml)**

This template includes:
- ✅ All MySQL connections (Railway)
- ✅ Alpaca trading API keys
- ✅ Plaid banking API keys
- ✅ Appwrite backend configuration
- ✅ Appwrite Function IDs (NOW INCLUDED!)
- ✅ Capital One, Tiingo, Alpha Vantage APIs

---

## ✅ Verification Checklist

After applying the fix:

- [ ] Opened Streamlit Cloud Secrets
- [ ] Added all Appwrite Function IDs
- [ ] Saved secrets
- [ ] Rebooted app
- [ ] Waited 60 seconds
- [ ] Visited https://bbbot305.streamlit.app/
- [ ] Checked Quick Actions section
- [ ] Confirmed error is gone
- [ ] Tested "Add to Watchlist" feature

---

## 🎉 Success Indicators

You'll know it's working when:
1. ✅ No error message in Quick Actions section
2. ✅ "Add to Watchlist" button works
3. ✅ Watchlist displays user's saved symbols
4. ✅ No console errors related to Appwrite

---

**Last Updated:** January 22, 2026  
**Time to Fix:** 5 minutes  
**Impact:** High - Enables core Quick Actions functionality on production
