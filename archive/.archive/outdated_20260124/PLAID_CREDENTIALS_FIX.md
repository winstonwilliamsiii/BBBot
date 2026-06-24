# Plaid Credentials Fix Guide

## 🚨 Current Issue
Your Plaid API keys are **invalid** - Plaid is rejecting them with:
```
error_code: "INVALID_API_KEYS"
error_message: "invalid client_id or secret provided"
```

## ✅ How to Fix

### Step 1: Get Your Real Plaid Credentials
1. Go to https://dashboard.plaid.com/
2. Log in with your Plaid account
3. Navigate to **Settings** → **API Keys**
4. You'll see:
   - **Client ID** (starts with a letter, typically 24+ characters)
   - **Secret** (long alphanumeric string)
   - Environment: **Sandbox**, **Development**, or **Production**

### Step 2: Update Your .env File
Replace the invalid credentials in `C:\Users\winst\BentleyBudgetBot\.env`:

```dotenv
# OLD (Invalid - REMOVE)
PLAID_CLIENT_ID=677f5a06bfb57e001d2ca8e9
PLAID_SECRET=7ce1f012fdd48c25854e3ecc5d1a91

# NEW (From your Plaid dashboard - ADD)
PLAID_CLIENT_ID=your_actual_client_id_from_dashboard
PLAID_SECRET=your_actual_secret_from_dashboard
PLAID_ENV=sandbox
```

### Step 3: Verify the Fix
Run the test script:
```bash
cd C:\Users\winst\BentleyBudgetBot
python test_plaid_credentials.py
```

If you see **✅ ALL TESTS PASSED!** then your credentials are valid.

## 🔍 Where to Find Your Credentials

### Plaid Dashboard:
- URL: https://dashboard.plaid.com/
- Section: **Settings → API Keys**
- Copy the exact values (no quotes, no spaces)

### Environment Options:
- **sandbox** - For testing (use this for development)
- **development** - For pre-production testing
- **production** - For live use (requires approval)

## 📝 Example Format
Your credentials should look like:
```dotenv
PLAID_CLIENT_ID=abc123def456ghi789jkl012mno345pqr
PLAID_SECRET=abcdef123456789ghijklmnopqrstuvwxyz1234567890
PLAID_ENV=sandbox
```

## ⚠️ Important Notes
1. **Do not commit real credentials to GitHub** - keep them in `.env` only
2. **Never share your secret** - it has full access to your Plaid data
3. **Use sandbox environment first** - for development and testing
4. **Rotate credentials regularly** - if they're ever exposed

## 🆘 Troubleshooting

### Still getting "invalid client_id or secret"?
1. Copy the values **exactly** from your Plaid dashboard
2. Check for extra spaces before/after the values
3. Ensure you're using the correct environment (sandbox/dev/prod)
4. If credentials are new, wait 2-3 minutes for them to activate

### Credentials don't appear in Plaid dashboard?
1. Your account may not be fully activated
2. Check your Plaid signup email for verification links
3. Contact Plaid support: https://support.plaid.com/

## 📊 Once Fixed
After adding valid credentials:
1. Save `.env`
2. Restart your Streamlit app
3. Test the Plaid Link integration
4. You should be able to "Connect Bank Account" successfully

---
**Last Updated:** January 15, 2026  
**Status:** Ready for credential update
