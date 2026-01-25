# 🚀 Production Deployment Fix Guide

## Issues Addressed

This guide fixes three critical production issues in Streamlit Cloud:

1. ❌ **ML Trading Signals Error**: `Unknown database 'bbbot1'`
2. ❌ **Alpaca Credentials Error**: `Alpaca credentials not configured`
3. ❌ **Plaid Link Error**: Plaid Link does not complete initializing

## 🔧 What Was Fixed

### 1. MySQL Database Connection
- **Problem**: Hardcoded database name `bbbot1` that doesn't exist in production
- **Solution**: Created `secrets_helper.py` utility that reads from Streamlit secrets
- **Files Updated**:
  - `frontend/utils/secrets_helper.py` (new file)
  - `sites/Mansa_Bentley_Platform/pages/04_💼_Broker_Trading.py` (updated)

### 2. Configuration Management
- **Problem**: Mixed use of environment variables and Streamlit secrets
- **Solution**: Unified secrets management with fallback priority:
  1. Streamlit Cloud secrets (production)
  2. Environment variables (local development)
  3. Default values (fallback)

### 3. Credential Validation
- **Added**: Real-time credential status checks in UI
- **Added**: Comprehensive integration test script
- **Files Created**:
  - `test_production_integrations.py` (test all integrations)
  - `STREAMLIT_CLOUD_SECRETS_TEMPLATE.toml` (deployment template)

## 📋 Deployment Checklist for Streamlit Cloud

### Step 1: Update Streamlit Cloud Secrets

1. Go to https://share.streamlit.io/
2. Click on your app → **Settings** (⚙️) → **Secrets**
3. Copy the content from `STREAMLIT_CLOUD_SECRETS_TEMPLATE.toml`
4. Update these **CRITICAL** values:

```toml
[mysql]
MYSQL_HOST = "YOUR_RAILWAY_HOST.railway.app"  # Get from Railway dashboard
MYSQL_PORT = "3306"
MYSQL_USER = "root"
MYSQL_PASSWORD = "YOUR_ACTUAL_PASSWORD"       # Get from Railway
MYSQL_DATABASE = "railway"                     # ⚠️ Verify actual database name

[alpaca]
ALPACA_API_KEY = "YOUR_ALPACA_KEY"            # Get from alpaca.markets
ALPACA_SECRET_KEY = "YOUR_ALPACA_SECRET"      # MUST regenerate if expired
ALPACA_PAPER = "true"

[plaid]
PLAID_CLIENT_ID = "YOUR_CLIENT_ID"            # Get from dashboard.plaid.com
PLAID_SECRET = "YOUR_SANDBOX_SECRET"          # Or development/production
PLAID_ENV = "sandbox"                          # sandbox, development, or production
```

### Step 2: Verify Database Name

**CRITICAL**: The database error happens because of name mismatch.

Check your actual database name:

```sql
-- Run this in your Railway MySQL console
SHOW DATABASES;
```

Common names:
- `railway` (Railway default)
- `mansa_bot` (legacy)
- `bbbot1` (Docker local)
- `mydb` (budget app)

Update `MYSQL_DATABASE` in secrets to match!

### Step 3: Regenerate Alpaca API Keys (If Needed)

If you see "unauthorized" error:

1. Go to https://alpaca.markets/
2. Login → Paper Trading → API Keys
3. **Delete old keys**
4. Generate new key pair
5. Update both `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` in secrets
6. Save and redeploy

### Step 4: Configure Plaid Redirect URI

1. Go to https://dashboard.plaid.com/
2. Navigate to **API** → **Webhook & Redirect URIs**
3. Add your Streamlit app URL:
   ```
   https://your-app-name.streamlit.app
   ```
4. Save changes

### Step 5: Test Locally First

Before deploying to cloud, test locally:

```bash
# Activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run integration test
python test_production_integrations.py
```

Expected output:
```
✅ MySQL Database:    ✅ PASS
✅ Alpaca Trading:    ✅ PASS (or ❌ if keys expired)
✅ Plaid Banking:     ✅ PASS
```

### Step 6: Deploy to Streamlit Cloud

After secrets are configured:

1. Push changes to GitHub:
   ```bash
   git add .
   git commit -m "fix: MySQL, Alpaca, Plaid configuration for production"
   git push origin main
   ```

2. Streamlit Cloud will auto-deploy (or manually trigger)

3. Check the app - you should see status indicators:
   ```
   ✅ MySQL: railway    ✅ Alpaca API    ✅ Plaid API
   ```

## 🧪 Testing in Production

### Test 1: MySQL Connection
- Navigate to **Broker Trading** page
- Check status banner: `✅ MySQL: railway`
- Scroll to **ML Trading Signals** section
- Should load without "Unknown database" error

### Test 2: Alpaca API
- Status banner should show: `✅ Alpaca API`
- If shows `❌`, expand "How to fix" and follow instructions
- Alpaca credentials expire after 90 days

### Test 3: Plaid Link
- Go to Plaid integration page
- Click "Link Bank Account"
- Should open Plaid Link modal
- Test with sandbox credentials (provided by Plaid)

## 🐛 Troubleshooting

### Issue: "Unknown database 'bbbot1'"
**Cause**: Database name in secrets doesn't match actual database
**Fix**:
1. Check actual database name in Railway
2. Update `MYSQL_DATABASE` in Streamlit secrets
3. Restart app

### Issue: "Alpaca credentials not configured"
**Cause**: Missing or invalid Alpaca keys
**Fix**:
1. Verify keys exist in Streamlit secrets under `[alpaca]`
2. Try regenerating keys at alpaca.markets
3. Ensure keys are for Paper Trading (not live)

### Issue: Plaid Link won't initialize
**Cause**: Usually redirect URI mismatch
**Fix**:
1. Check redirect URI in Plaid dashboard matches Streamlit URL
2. Verify `PLAID_CLIENT_ID` and `PLAID_SECRET` are correct
3. Check `PLAID_ENV` matches your key type (sandbox/dev/production)

### Issue: All secrets work locally but not in cloud
**Cause**: Streamlit secrets not properly saved
**Fix**:
1. Go to Streamlit Cloud → Settings → Secrets
2. Verify all sections exist: `[mysql]`, `[alpaca]`, `[plaid]`
3. Click "Save" explicitly (don't just close)
4. Force redeploy

## 📁 Files Modified

```
New Files:
✅ frontend/utils/secrets_helper.py
✅ test_production_integrations.py
✅ STREAMLIT_CLOUD_SECRETS_TEMPLATE.toml
✅ PRODUCTION_DEPLOYMENT_GUIDE.md

Modified Files:
✅ sites/Mansa_Bentley_Platform/pages/04_💼_Broker_Trading.py
✅ .streamlit/secrets.toml (local dev only)
```

## 🌿 Branch Strategy

We've fixed these issues on `main` since dev has too many issues.

For future development:
```bash
# Create stable feature branch from fixed main
git checkout main
git pull origin main
git checkout -b feature/stable-development

# Work on features
git add .
git commit -m "feat: new feature"

# Merge back when stable
git checkout main
git merge feature/stable-development
git push origin main
```

## 🎯 Next Steps

1. ✅ Fix MySQL connection string
2. ✅ Add Alpaca/Plaid to secrets helper
3. ✅ Create credential status UI
4. ✅ Write integration test script
5. ⏳ Deploy to Streamlit Cloud
6. ⏳ Test in production
7. ⏳ Create stable development branch

## 📞 Support

If issues persist:
1. Check Streamlit Cloud logs (Settings → Logs)
2. Run `test_production_integrations.py` locally
3. Verify all credentials are fresh and valid
4. Check service dashboards (Railway, Alpaca, Plaid)

---

Last Updated: 2026-01-24
