# API Issues - Self-Service Fix Guide

## 🎯 Summary of Issues Found

After running comprehensive diagnostics, here's what I found:

### ✅ Working APIs
- **Yahoo Finance** - ✅ Free tier working perfectly
- **Plaid** - ✅ Credentials configured correctly (may need browser refresh)
- **MySQL Database** - ✅ Connected successfully on port 3306

### ❌ Broken APIs  
- **Tiingo API** - ❌ **INVALID API KEY** (NOT a subscription issue)

## 🔴 Critical Issue: Tiingo API Key is Invalid

Your current API key returns: `{"detail":"Invalid token."}`

This means the key itself is not valid, regardless of subscription status.

### How to Fix Tiingo API

**Step 1: Log into Your Tiingo Account**
- Go to: https://www.tiingo.com/account/api
- Sign in with your credentials

**Step 2: Check Your API Key**
- You should see an "API Token" section
- If the key shown does NOT match `E6c794cd1e5e48519194065a2a43b2396298288b`, copy the correct one
- If there is NO key shown, click "Create New Token"

**Step 3: Verify Subscription Status**
- Check if your account shows as "Free" or "Paid"
- If you paid 48 hours ago but still shows "Free", contact support
- Even free tier should give a VALID token (with limited data access)

**Step 4: Update Your .env File**
```bash
# Open .env file and update this line:
TIINGO_API_KEY=YOUR_ACTUAL_KEY_FROM_DASHBOARD
```

**Step 5: Test the New Key**
```bash
# Test directly with curl (replace YOUR_KEY):
curl -H "Authorization: Token YOUR_KEY" "https://api.tiingo.com/tiingo/daily/AAPL/prices?startDate=2024-12-01"

# If valid, you'll get JSON data back
# If invalid, you'll get: {"detail":"Invalid token."}
```

**Step 6: Run Python Test**
```bash
python test_tiingo.py
```

## 🟢 Plaid API - Already Fixed!

Plaid is working correctly. If you still see errors in the Streamlit app:

### Browser Cache Issue
1. **Hard refresh your browser:**
   - Chrome/Edge: `Ctrl + Shift + R` or `Ctrl + F5`
   - Firefox: `Ctrl + Shift + R`
   - Safari: `Cmd + Shift + R`

2. **Or clear Streamlit cache:**
   ```bash
   # In Streamlit app, press 'C' or click menu → "Clear cache"
   ```

3. **Restart Streamlit:**
   ```bash
   # Stop current server (Ctrl+C)
   streamlit run streamlit_app.py
   ```

## 📋 API Setup Checklist

Use this checklist to verify your API setup:

### Tiingo API
- [ ] Have account at https://www.tiingo.com/
- [ ] Logged into account dashboard
- [ ] Can see API token in account settings
- [ ] Copied EXACT token (no extra spaces)
- [ ] Updated .env file with token
- [ ] Tested with curl command
- [ ] Tested with `python test_tiingo.py`
- [ ] If paid: Verified subscription is active

### Plaid API  
- [x] Credentials in .env file ✅
- [x] PlaidLinkManager working ✅
- [ ] Browser hard refreshed
- [ ] Streamlit app restarted

### Database
- [x] MySQL running on port 3306 ✅
- [x] Can connect successfully ✅
- [x] Database 'mansa_bot' exists ✅

## 🆘 Still Having Issues?

### If Tiingo Still Fails After New Key:

**Check Account Status:**
```
1. Login to https://www.tiingo.com/account
2. Look for "Subscription" or "Plan" section
3. Take screenshot of your account page
```

**Contact Tiingo Support:**
- Email: support@tiingo.com
- Include:
  - Your account email
  - Payment confirmation (if you paid)
  - Error message: "Invalid token"
  - Request new API key generation

### If Plaid Still Shows Error:

**Debug Steps:**
```bash
# 1. Test credentials
python test_plaid_simple.py

# 2. If test passes but UI fails, clear ALL caches:
# - Browser cache (Ctrl+Shift+Delete)
# - Streamlit cache (press 'C' in app)
# - Restart computer (nuclear option)
```

## 💡 Alternative: Use Free APIs Only

If you don't want to deal with paid APIs, you can use free alternatives:

### Yahoo Finance (Already Working)
- Free stock prices
- Company info  
- Historical data
- No API key needed

### Alpha Vantage (Free Tier)
```bash
# Get free key at: https://www.alphavantage.co/support/#api-key
# Add to .env:
ALPHA_VANTAGE_API_KEY=your_key_here
```

### IEX Cloud (Free Tier)
```bash
# Get free key at: https://iexcloud.io/
# Add to .env:
IEX_CLOUD_API_KEY=your_key_here
```

## 🔧 Quick Test Commands

```bash
# Test all APIs at once
python diagnostic_api_test.py

# Test individual APIs
python test_tiingo.py        # Tiingo test
python test_plaid_simple.py  # Plaid test
python quick_test_budget.py  # Budget page test

# Restart Streamlit fresh
streamlit run streamlit_app.py --server.headless true
```

## 📞 Getting Help

**Free Resources:**
- Tiingo Documentation: https://api.tiingo.com/documentation/general/overview
- Plaid Quickstart: https://plaid.com/docs/quickstart/
- Project Issues: https://github.com/winstonwilliamsiii/BBBot/issues

**Community Support:**
- Stack Overflow: [tiingo] or [plaid-api] tags
- Reddit: r/algotrading, r/personalfinance

---

**Next Steps:**
1. Focus on getting a valid Tiingo API key first
2. Test with curl before testing with Python
3. Once Tiingo works, verify Plaid in browser
4. Run full app and celebrate! 🎉

**Last Updated:** December 11, 2025
