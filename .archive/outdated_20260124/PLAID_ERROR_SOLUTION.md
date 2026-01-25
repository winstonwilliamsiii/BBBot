# Plaid Credentials Error - Solution Guide

## 🚨 Problem Summary

You're getting the error:
```
Failed to create link token: Status Code: 400 Reason: Bad Request
error_code: "INVALID_API_KEYS"
error_message: "invalid client_id or secret provided"
```

**Root Cause:** The Plaid credentials in your `.env` file are **invalid or expired**. Both the current credentials and the ones in templates are being rejected by Plaid's API.

---

## ✅ How to Fix

### Option 1: Get Real Credentials from Plaid Dashboard (Recommended)

**Step 1: Log into Plaid Dashboard**
- Open: https://dashboard.plaid.com/
- Sign in with your Plaid account credentials

**Step 2: Find Your API Keys**
1. Click on **Settings** (bottom left corner)
2. Select **API Keys**
3. You'll see your:
   - **Client ID** - Copy this exactly
   - **Secret** - Copy this exactly  
   - Environment selector (Sandbox/Development/Production)

**Step 3: Update `.env` File**

Edit `C:\Users\winst\BentleyBudgetBot\.env` and find this section:

```dotenv
# Before (INVALID - Remove)
PLAID_CLIENT_ID=677f5a06bfb57e001d2ca8e9
PLAID_SECRET=7ce1f012fdd48c25854e3ecc5d1a91
PLAID_ENV=sandbox
```

Replace with:

```dotenv
# After (From your Plaid dashboard)
PLAID_CLIENT_ID=your_actual_client_id_here
PLAID_SECRET=your_actual_secret_here
PLAID_ENV=sandbox
```

**Important:** 
- Copy the values **exactly** as shown in the dashboard
- Don't add quotes around the values
- Don't add extra spaces
- Keep PLAID_ENV as `sandbox` for testing

**Step 4: Verify the Fix**

Run this test command:
```bash
cd C:\Users\winst\BentleyBudgetBot
python test_plaid_credentials.py
```

You should see:
```
✅ SUCCESS! Link token created:
   Token: link-sandbox-...
   Expires: ...

✅ ALL TESTS PASSED!
```

---

## 📋 Valid Credential Format

Your credentials should look like this pattern:

| Field | Format | Example |
|-------|--------|---------|
| PLAID_CLIENT_ID | 24+ alphanumeric chars | `abc123def456ghi789jkl012` |
| PLAID_SECRET | 30+ alphanumeric chars | `abcdef123456789ghijklmnopqrstuvwxyz` |
| PLAID_ENV | sandbox/development/production | `sandbox` |

---

## 🆘 If You Don't Have Plaid Credentials

If you don't have a Plaid account or credentials:

1. **Create a Plaid Account:**
   - Go to https://plaid.com/
   - Click "Start For Free"
   - Sign up with your email
   - Complete the verification process

2. **Once Signed Up:**
   - You'll be given sandbox credentials automatically
   - Go to dashboard: https://dashboard.plaid.com/
   - Find your API Keys in Settings
   - Use those in your `.env` file

3. **Important Notes:**
   - Sandbox credentials are for **testing only**
   - They only work with test bank accounts
   - For production, you need separate production credentials (requires approval)

---

## 🔑 Where Each File Was Updated

I've already updated these files with the attempted fix:

1. **`.env`** (Primary configuration)
   - ✅ Updated: `PLAID_CLIENT_ID=677f5a06bfb57e001d2ca8e9`
   - ✅ Updated: `PLAID_SECRET=7ce1f012fdd48c25854e3ecc5d1a91`
   - ❌ These credentials are still invalid - need REAL ones from dashboard

2. **Created new diagnostic tools:**
   - `test_plaid_credentials.py` - Simple test
   - `diagnose_plaid.py` - Comprehensive diagnostic
   - `PLAID_CREDENTIALS_FIX.md` - This guide

---

## 📊 Configuration Files Affected

When you update `.env`, these components will use the new credentials:

### Frontend (Streamlit)
- `frontend/utils/plaid_link.py` → PlaidLinkManager class
- `frontend/components/plaid_link.py` → Plaid UI components

### Backend (Appwrite Functions)
- `functions/create_link_token/main.py` → Creates link tokens
- `functions/exchange_public_token/main.py` → Exchanges tokens
- `#Appwrite Function for Plaid Quickstart.js` → JS handlers

### Database
- Tables: `plaid_items`, `plaid_transactions`, `plaid_sync_status` in `mydb`

---

## 🔒 Security Best Practices

⚠️ **IMPORTANT:**

1. **Never commit `.env` to GitHub**
   - It contains secrets
   - `.env` is in `.gitignore` (already configured)
   - Only commit `.env.example` with placeholder values

2. **Rotate credentials if exposed**
   - Go to Plaid Dashboard
   - Regenerate API keys
   - Update all `.env` files immediately

3. **Use environment-specific credentials**
   - Sandbox for testing/development
   - Development for staging
   - Production for live (needs approval)

4. **Limit API key access**
   - Each key should have minimal required permissions
   - Create separate keys for different services if needed

---

## 🧪 Testing Checklist

After updating credentials:

- [ ] Update `.env` with real Plaid credentials from dashboard
- [ ] Run `python test_plaid_credentials.py`
- [ ] See "✅ ALL TESTS PASSED!" message
- [ ] Restart Streamlit app
- [ ] Navigate to Plaid Link section in app
- [ ] Click "Connect Bank Account"
- [ ] Complete Plaid Link flow successfully
- [ ] Verify bank account appears in app

---

## 📞 Need Help?

### Plaid Support
- **Documentation:** https://plaid.com/docs/
- **Support Portal:** https://support.plaid.com/
- **Status Page:** https://status.plaid.com/

### Common Issues

**Q: I updated the credentials but still getting the error**
- A: Verify you copied the values **exactly** from Plaid Dashboard
- A: Check for extra spaces before/after the values
- A: Ensure you're using Sandbox credentials for testing

**Q: My Plaid credentials aren't showing in the dashboard**
- A: Your account may not be fully activated
- A: Check your email for verification links
- A: Wait 5-10 minutes for account activation

**Q: Should I use Sandbox or Production?**
- A: For development/testing: Use **Sandbox**
- A: For production: Request Production credentials (requires approval)

---

## 📝 Next Steps

1. ✅ Get valid credentials from https://dashboard.plaid.com/
2. ✅ Update `.env` file with real credentials
3. ✅ Run diagnostic: `python diagnose_plaid.py`
4. ✅ See "ALL TESTS PASSED" message
5. ✅ Restart Streamlit app
6. ✅ Test Plaid Link integration in your app

---

**Last Updated:** January 15, 2026  
**Status:** Awaiting valid Plaid credentials
**Created By:** Automated diagnostic system
