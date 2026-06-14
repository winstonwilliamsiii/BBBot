# 🚀 Appwrite Functions - Deployment Guide

**Last Updated:** December 25, 2025

Complete guide for deploying all 16 serverless functions to Appwrite Cloud.

---

## 📋 Available Functions (16 Total)

### Transaction Functions (3)
1. ✅ `create_transaction` - Create transaction with RBAC
2. ✅ `get_transactions` - Get transactions with RBAC  
3. ✅ `get_transactions_streamlit` - Get transactions (simplified for Streamlit)

### Watchlist Functions (3)
4. ✅ `add_to_watchlist_streamlit` - Add to watchlist
5. ✅ `get_watchlist_streamlit` - Get watchlist
6. ✅ `get_user_profile_streamlit` - Get user profile

### Audit & Payment Functions (4)
7. ✅ `create_audit_log` - Create audit log entry
8. ✅ `get_audit_logs` - Retrieve audit logs
9. ✅ `create_payment` - Create payment record
10. ✅ `get_payments` - Get payment history

### RBAC Functions (2)
11. ✅ `manage_roles` - Create/list roles
12. ✅ `manage_permissions` - Create/list permissions

### Bot Metrics Functions (3)
13. ✅ `create_bot_metric` - Record bot performance metric
14. ✅ `get_bot_metrics` - Query bot metrics
15. ✅ `get_bot_metrics_stats` - Get statistical analysis

### Utility Functions (1)
16. ✅ `create_all_indexes` - Create all database indexes (run once)

---

## 🎯 Quick Start - Deploy All Functions

### Step 1: Package Functions
```powershell
cd C:\Users\winst\OneDrive\Documentos\GitHub\BBBot
.\package-appwrite-functions-targz.ps1
```

This creates 16 tar.gz files in `appwrite-deployments-targz/` directory.

### Step 2: Deploy via Appwrite CLI
```powershell
cd appwrite-deployments-targz
appwrite login
appwrite push function --all
```

**That's it!** All functions will be deployed to Appwrite Cloud.

---

## 📦 Method 1: Appwrite CLI (Recommended)

### Prerequisites
```powershell
# Install Appwrite CLI (if not installed)
npm install -g appwrite-cli

# Check version
appwrite --version

# Login to Appwrite Cloud
appwrite login
```

### Package Functions
```powershell
# From project root
.\package-appwrite-functions-targz.ps1

# Output: 16 tar.gz files in appwrite-deployments-targz/
```

### Deploy All Functions
```powershell
cd appwrite-deployments-targz
appwrite push function --all
```

### Deploy Specific Function
```powershell
appwrite push function --functionId <function-id>
```

### Verify Deployment
```powershell
# List all functions
appwrite list functions

# Get function details
appwrite get function --functionId <function-id>
```

---

## 🖱️ Method 2: Manual Upload via Console

### Step 1: Login to Appwrite Cloud
1. Go to https://cloud.appwrite.io/console/project-68869ef500017ca73772/functions
2. Sign in to your account

### Step 2: Create Function (For Each Function)

**Example: `get_transactions_streamlit`**

1. Click **"Create Function"** button

2. **Configuration:**
   - **Name:** `get_transactions_streamlit`
   - **Runtime:** **Node.js 18.0** or latest
   - **Execute Access:** Set to "Any" for testing, or configure permissions

3. **Deployment:**
   - Click **"Create Deployment"** 
   - **Manual:** Upload tar.gz file from `appwrite-deployments-targz/get_transactions_streamlit.tar.gz`
   - **Entrypoint:** `index.js`
   - **Commands:** Leave default (Build: `npm install`, Start: `node index.js`)

4. **Environment Variables:**
   - Go to **Settings** → **Variables**
   - Add these 4 variables:
   
   ```bash
   APPWRITE_FUNCTION_ENDPOINT=https://fra.cloud.appwrite.io/v1
   APPWRITE_FUNCTION_PROJECT_ID=68869ef500017ca73772
   APPWRITE_API_KEY=<your-api-key>
   APPWRITE_DATABASE_ID=<your-database-id>
   ```

5. **Wait for Build:**
   - Deployment will show "Building..."
   - Wait for green checkmark (✅ Active)
   - Check logs if errors occur

6. **Test Execution:**
   - Click **"Execute"** tab
   - Add test payload:
   ```json
   {
     "user_id": "test123",
     "limit": 10
   }
   ```
   - Click **"Execute Now"**
   - Verify response

7. **Copy Function ID:**
   - Go to **Settings** tab
   - Copy the **Function ID** (e.g., `67a1234bcdef...`)
   - Save for your application configuration

### Step 3: Repeat for All 16 Functions

Follow steps above for each function. Use corresponding tar.gz file from `appwrite-deployments-targz/` directory.

---

## 🔐 Environment Variables Setup

Each function requires these 4 environment variables:

```bash
APPWRITE_FUNCTION_ENDPOINT=https://fra.cloud.appwrite.io/v1
APPWRITE_FUNCTION_PROJECT_ID=68869ef500017ca73772
APPWRITE_API_KEY=<your-server-api-key>
APPWRITE_DATABASE_ID=<your-database-id>
```

### Option A: Global Variables (All Functions)
1. Go to **Settings** (bottom left, gear icon)
2. Click **Environment Variables**
3. Add to **Global Variables**
4. All functions can access these

**Pros:** Set once for all functions  
**Cons:** Less secure, affects entire project

### Option B: Function Variables (Per Function - Recommended)
1. Go to **Functions** → Select function
2. Click **Settings** (top navigation)
3. Scroll to **Variables** section
4. Add 4 variables for this function
5. Repeat for each function

**Pros:** Better isolation and security  
**Cons:** More setup (4 variables × 16 functions = 64 entries)

---

## 📝 Package Structure

Each tar.gz file contains:

```
get_transactions_streamlit.tar.gz
├── index.js                   # Main function code
├── package.json               # Dependencies
└── _shared/                   # Shared utilities
    └── appwriteClient.js      # Appwrite SDK client
```

### Key Points:
- `_shared/` folder is included in EACH package
- All requires use `./_shared/appwriteClient` (same level)
- `package.json` includes `node-appwrite: ^11.0.0`
- Entry point is always `index.js`

---

## ✅ Post-Deployment Checklist

After deploying all functions:

- [ ] Verify all 16 functions appear in Appwrite Console
- [ ] Check each function has meaningful name (not just ID)
- [ ] Confirm all functions show "Active" status (green checkmark)
- [ ] Test execution of at least 3 critical functions
- [ ] Verify environment variables are set (Global or Function-level)
- [ ] Copy all Function IDs for application configuration
- [ ] Update your `.env` file with Function IDs
- [ ] Test functions from your Streamlit app
- [ ] Check Appwrite logs for any errors
- [ ] Configure execute permissions as needed

---

## 🧪 Testing Functions

### Test via Appwrite Console

1. Navigate to **Functions** → Select function
2. Click **"Execute"** tab
3. Add test payload:

**Example for `get_transactions_streamlit`:**
```json
{
  "user_id": "test123",
  "limit": 10
}
```

4. Click **"Execute Now"**
5. Check response and logs

### Test via cURL

```bash
curl -X POST \
  https://fra.cloud.appwrite.io/v1/functions/[FUNCTION_ID]/executions \
  -H 'Content-Type: application/json' \
  -H 'X-Appwrite-Project: 68869ef500017ca73772' \
  -H 'X-Appwrite-Key: [YOUR_API_KEY]' \
  -d '{"user_id": "test123", "limit": 10}'
```

### Test from Streamlit App

Once deployed, update your Streamlit app configuration:

```python
# Update .env with Function IDs
APPWRITE_FUNCTION_GET_TRANSACTIONS=67a1234...
APPWRITE_FUNCTION_ADD_WATCHLIST=67a5678...
# ... etc
```

---

## 🔧 Troubleshooting

### Function Build Fails

**Check:**
- Verify tar.gz structure: `tar -tzf function.tar.gz`
- Ensure `package.json` exists in package
- Check `index.js` is at root of tar.gz
- Verify `_shared/` folder is included

**Common Issues:**
- Missing `package.json` → Add it to function directory
- Wrong entry point → Set to `index.js`
- Missing dependencies → Check `node-appwrite` in package.json

### Module Not Found Error

**Error:** `Cannot find module './_shared/appwriteClient'`

**Fix:**
1. Verify `_shared/` folder is in tar.gz
2. Check require path: `require('./_shared/appwriteClient')` not `require('../_shared/appwriteClient')`
3. Repackage function: `.\package-appwrite-functions-targz.ps1`

### Environment Variables Not Working

**Check:**
- Variables are set in correct location (Function Settings, not Project Settings)
- Variable names match exactly (case-sensitive)
- No extra spaces in values
- API key has correct permissions

**Test:**
```javascript
// Add to function for debugging
console.log('Endpoint:', process.env.APPWRITE_FUNCTION_ENDPOINT);
console.log('Project:', process.env.APPWRITE_FUNCTION_PROJECT_ID);
```

### Function Execution Timeout

**Increase timeout:**
1. Go to function **Settings**
2. Find **Timeout** field
3. Increase from default (15s) to 30s or 60s
4. Save changes

---

## 📊 Monitoring & Logs

### View Function Logs

1. Go to **Functions** → Select function
2. Click **"Logs"** tab
3. View real-time execution logs
4. Filter by success/error

### Monitor Executions

1. Go to **Functions** → Select function
2. Click **"Executions"** tab  
3. See all execution history
4. Check success rate and duration

---

## 🔄 Updating Functions

### Option 1: Redeploy via CLI
```powershell
# Repackage
.\package-appwrite-functions-targz.ps1

# Redeploy
cd appwrite-deployments-targz
appwrite push function --functionId <function-id>
```

### Option 2: Manual Upload
1. Package function
2. Go to function → **Deployments** tab
3. Click **"Create Deployment"**
4. Upload new tar.gz
5. Wait for build

---

## 📚 Additional Resources

- **Appwrite Cloud Console:** https://cloud.appwrite.io/console/project-68869ef500017ca73772/functions
- **Appwrite Functions Docs:** https://appwrite.io/docs/products/functions
- **Appwrite CLI Docs:** https://appwrite.io/docs/tooling/command-line/installation
- **Node.js SDK Docs:** https://appwrite.io/docs/sdks#server

---

## 🆘 Need Help?

If functions still fail after following this guide:

1. Check [ISSUES_AND_FIXES.md](./ISSUES_AND_FIXES.md) for known issues
2. Review function logs in Appwrite Console
3. Verify all environment variables are set correctly
4. Test with simple execution payload first
5. Check API key permissions in Appwrite Console

---

**Last Updated:** December 25, 2025  
**Status:** All 16 functions packaged and ready for deployment ✅
