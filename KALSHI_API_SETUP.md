# Kalshi API Key Setup Guide

## 🔴 Why This Changed

Your Kalshi account has **MFA/2FA enabled**, which blocks email/password authentication via API. This is a security feature by Kalshi.

**Solution**: Use RSA API keys that bypass MFA for programmatic access.

---

## 📋 Step-by-Step Setup

### Step 1: Generate API Keys on Kalshi

1. **Log into Kalshi**: Go to https://kalshi.com and log in with your account
   - Email: `wwilliams@mansacap.com`
   - Password: `Cartagena57!@`
   - Complete MFA if prompted

2. **Navigate to Profile Settings**: 
   - Click your profile picture/icon in the top-right corner
   - Or go directly to: https://kalshi.com/account/profile

3. **Find API Keys Section**:
   - Scroll down to the "API Keys" section
   - Click **"Create New API Key"** button

4. **Save Your Credentials** ⚠️ CRITICAL:
   
   Kalshi will show you **two pieces of information**:
   
   - **Key ID** (looks like: `a952bcbe-ec3b-4b5b-b8f9-11dae589608c`)
     - Copy this immediately
   
   - **Private Key** (RSA format, starts with `-----BEGIN RSA PRIVATE KEY-----`)
     - This will auto-download as a `.key` or `.txt` file
     - **SAVE THIS FILE** - You cannot retrieve it again!
   
   ⚠️ **WARNING**: Once you close this page, you **CANNOT** retrieve the private key again. Save it now!

5. **Optional**: Give your key a descriptive name like "BentleyBot-Development"

---

### Step 2: Save Private Key File

1. Download the private key file (should be named something like `kalshi-key-xxxxx.key`)

2. Move it to your BentleyBudgetBot project directory:
   ```
   C:\Users\winst\BentleyBudgetBot\kalshi-private-key.key
   ```

3. **Rename the file** to exactly: `kalshi-private-key.key`

4. **IMPORTANT**: The file should look like this when opened:
   ```
   -----BEGIN RSA PRIVATE KEY-----
   MIIEpAIBAAKCAQEA1234567890...
   (many lines of Base64 text)
   ...
   -----END RSA PRIVATE KEY-----
   ```

---

### Step 3: Update Environment Files

Now update your `.env.development` file with your credentials:

1. Open: `C:\Users\winst\BentleyBudgetBot\.env.development`

2. Find the Kalshi section (around line 108-115)

3. Replace the placeholder values:
   ```bash
   # ============================================
   # PREDICTION ANALYTICS - KALSHI (DEVELOPMENT)
   # ============================================
   # RSA API Key Authentication (bypasses MFA/2FA) 
   # Endpoint: https://trading-api.kalshi.com
   # Generate keys at: https://kalshi.com/account/profile
   KALSHI_API_KEY_ID=a952bcbe-ec3b-4b5b-b8f9-11dae589608c  # <- REPLACE WITH YOUR KEY ID
   KALSHI_PRIVATE_KEY_PATH=./kalshi-private-key.key
   ```

4. **Save the file**

5. **Repeat for production**: Update `.env.production` with the same values

---

### Step 4: Test the Connection

Run the debug script to verify authentication works:

```bash
python test_kalshi_debug.py
```

**Expected output**:
```
============================================================
🔍 KALSHI API DEBUG TEST
============================================================

🔑 API Key ID: a952bcbe-ec3b-4b5b-b...
📄 Private Key Path: ./kalshi-private-key.key

🔄 Initializing Kalshi client...
✅ Authenticated: True

============================================================
📊 TESTING API ENDPOINTS
============================================================

1️⃣ GET USER PROFILE
------------------------------------------------------------
✅ Profile Response Type: <class 'dict'>
📄 Profile Data:
   user_id: wwilliams
   email: wwilliams@mansacap.com
   ...
```

If you see `✅ Authenticated: True`, **it's working!** 🎉

---

## 🔧 Troubleshooting

### Error: "Private key file not found"
- Make sure the file is named exactly `kalshi-private-key.key`
- Place it in: `C:\Users\winst\BentleyBudgetBot\`
- Check the `KALSHI_PRIVATE_KEY_PATH` in `.env.development`

### Error: "Could not deserialize key data"
- The private key file is corrupted or incorrect format
- Re-download the key from Kalshi (if possible)
- Or generate a new API key

### Error: Still getting authentication failures
- Double-check the `KALSHI_API_KEY_ID` is correct
- Verify the private key file content starts with `-----BEGIN RSA PRIVATE KEY-----`
- Make sure `.env.development` is saved after editing
- Restart any running Streamlit applications

### Need to Generate New Keys?
If you lost your private key:
1. Go back to https://kalshi.com/account/profile
2. **Delete the old API key** (if it exists)
3. Create a new one
4. Update your `.env` files with the new credentials

---

## 🔒 Security Best Practices

### ✅ DO:
- **Keep private keys secure** - treat them like passwords
- **Store keys in `.env` files** (not in code)
- **Add `*.key` to `.gitignore`** (already done)
- **Use different keys for development/production**
- **Rotate keys periodically** (every 90 days)

### ❌ DON'T:
- **Never commit private keys to Git**
- **Never share private keys** in Slack/email/Discord
- **Don't store keys in public places**
- **Don't reuse production keys for testing**

---

## 📊 What Changed in the Code?

### Before (Email/Password - BLOCKED BY MFA):
```python
client = KalshiClient(
    email="wwilliams@mansacap.com",
    password="Cartagena57!@"
)
# ❌ Fails with: "invalid_credentials" due to MFA
```

### After (RSA API Keys - WORKS WITH MFA):
```python
client = KalshiClient(
    api_key_id="a952bcbe-ec3b-4b5b-b8f9-11dae589608c",
    private_key_path="./kalshi-private-key.key"
)
# ✅ Authenticates successfully, bypasses MFA
```

### How It Works:
1. Each API request is **signed with your RSA private key**
2. Kalshi verifies the signature with your public key
3. No password needed - cryptographic proof of identity
4. MFA doesn't apply to API key authentication

---

## 🎯 Next Steps After Setup

Once authentication works:

1. **Test the dashboard**:
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Navigate to Prediction Analytics page**

3. **Check if your $9.82 investment displays** in the portfolio

4. **Verify all tabs work**:
   - Active Markets
   - My Portfolio
   - Account balance
   - Trade history

5. **Remove debug code** (optional):
   - The `print()` statements in fetch functions
   - The debug panel expander

6. **Deploy to production**:
   - Update Streamlit Cloud secrets with your API key
   - Upload private key securely (use Streamlit secrets manager)

---

## 📞 Support

### Official Kalshi Documentation:
- API Docs: https://docs.kalshi.com/
- API Keys Guide: https://docs.kalshi.com/getting_started/api_keys
- Support: support@kalshi.com

### BentleyBot Issues:
- Check `PREDICTION_ANALYTICS_STATUS.md` for integration status
- Run `test_kalshi_debug.py` for detailed diagnostics
- Review logs in terminal output

---

## ✅ Verification Checklist

Before proceeding, confirm:

- [ ] Generated API keys on Kalshi website
- [ ] Saved private key file as `kalshi-private-key.key`
- [ ] Updated `KALSHI_API_KEY_ID` in `.env.development`
- [ ] Updated `KALSHI_PRIVATE_KEY_PATH` in `.env.development`
- [ ] Ran `test_kalshi_debug.py` successfully
- [ ] Saw `✅ Authenticated: True` in test output
- [ ] Ready to test the Streamlit dashboard

---

**Last Updated**: February 7, 2026  
**Status**: Ready for API key generation  
**Branch**: `feature/prediction-analytics`
