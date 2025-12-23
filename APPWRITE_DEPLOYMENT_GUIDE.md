# 🚀 Appwrite Functions Deployment Guide

## ❌ WHY APPWRITE CLOUD SHOWS NO FUNCTIONS

**The functions I created are LOCAL files only!** They exist in:
```
C:\Users\winst\BentleyBudgetBot\appwrite-functions\
```

**These files need to be DEPLOYED to Appwrite Cloud manually.**

---

## 📋 Functions Ready for Deployment (17 Total)

### Transaction Functions (3)
1. ✅ `create_transaction` - Create transaction with RBAC
2. ✅ `get_transactions` - Get transactions with RBAC
3. ✅ `get_transactions_streamlit` - Get transactions (simplified for StreamLit)

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

### Utility Functions (2)
16. ✅ `create_all_indexes` - Create all database indexes (run once)
17. ✅ `_shared/appwriteClient.js` - Shared SDK client

---

## 🎯 STEP-BY-STEP DEPLOYMENT TO APPWRITE CLOUD

### Method 1: Manual Upload via Appwrite Console (Recommended)

#### Step 1: Login to Appwrite Cloud
1. Go to https://cloud.appwrite.io
2. Sign in to your account
3. Select your project

#### Step 2: Navigate to Functions
1. Click **"Functions"** in the left sidebar
2. Click **"Create Function"** button

#### Step 3: Create Each Function

**For EACH function (e.g., `get_transactions_streamlit`):**

1. **Basic Configuration:**
   - **Name:** `get_transactions_streamlit`
   - **Runtime:** Select **"Node.js 18.0"** or latest
   - **Execute Access:** Set to appropriate permission (e.g., "Any" for testing)

2. **Upload Code:**
   - Click **"Settings"** tab
   - Scroll to **"Deployment"**
   - Choose **"Manual"** deployment
   - Click **"Upload"**
   
3. **Prepare Upload:**
   ```powershell
   # Create a deployment package
   cd C:\Users\winst\BentleyBudgetBot\appwrite-functions
   
   # For each function, create a zip with _shared folder
   # Example for get_transactions_streamlit:
   Compress-Archive -Path "get_transactions_streamlit\*", "_shared" -DestinationPath "get_transactions_streamlit.zip"
   ```

4. **Upload ZIP:**
   - Upload the created `.zip` file
   - Set **Entry Point:** `index.js`

5. **Environment Variables:**
   Add these in the **Variables** section:
   ```
   APPWRITE_FUNCTION_ENDPOINT=https://cloud.appwrite.io/v1
   APPWRITE_FUNCTION_PROJECT_ID=your_project_id
   APPWRITE_API_KEY=your_server_api_key
   APPWRITE_DATABASE_ID=your_database_id
   ```

6. **Deploy:**
   - Click **"Create Deployment"**
   - Wait for build to complete (green checkmark)

7. **Test:**
   - Click **"Execute"** tab
   - Add test body JSON:
   ```json
   {
     "user_id": "test123",
     "limit": 10
   }
   ```
   - Click **"Execute Now"**
   - Check response

#### Step 4: Copy Function IDs

After each function is deployed:
1. Click on the function name
2. Copy the **Function ID** (looks like: `6abc123def456...`)
3. Save it for your `.env` file

---

### Method 2: Appwrite CLI (Faster for Bulk Deployment)

#### Step 1: Install Appwrite CLI
```powershell
npm install -g appwrite-cli
```

#### Step 2: Login
```powershell
appwrite login
```
- Enter your Appwrite Cloud credentials
- Select your project

#### Step 3: Initialize Functions
```powershell
cd C:\Users\winst\BentleyBudgetBot\appwrite-functions
appwrite init function
```

#### Step 4: Deploy All Functions
```powershell
# Deploy each function
appwrite deploy function --functionId get_transactions_streamlit
appwrite deploy function --functionId add_to_watchlist_streamlit
# ... repeat for each function
```

---

## 📦 Quick Deployment Package Creator

Run this PowerShell script to create deployment packages for all functions:

```powershell
# Save as: deploy_packages.ps1
$functionsPath = "C:\Users\winst\BentleyBudgetBot\appwrite-functions"
$outputPath = "C:\Users\winst\BentleyBudgetBot\deployments"

# Create output directory
New-Item -ItemType Directory -Force -Path $outputPath

# List of functions to package
$functions = @(
    "create_transaction",
    "get_transactions",
    "get_transactions_streamlit",
    "add_to_watchlist_streamlit",
    "get_watchlist_streamlit",
    "get_user_profile_streamlit",
    "create_audit_log",
    "get_audit_logs",
    "create_payment",
    "get_payments",
    "manage_roles",
    "manage_permissions",
    "create_bot_metric",
    "get_bot_metrics",
    "get_bot_metrics_stats",
    "create_all_indexes"
)

foreach ($func in $functions) {
    Write-Host "Packaging $func..." -ForegroundColor Cyan
    
    # Create temp directory
    $tempDir = "$outputPath\temp_$func"
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
    
    # Copy function files
    Copy-Item -Path "$functionsPath\$func\*" -Destination $tempDir -Recurse
    
    # Copy shared folder
    Copy-Item -Path "$functionsPath\_shared" -Destination "$tempDir\_shared" -Recurse
    
    # Create package.json
    $packageJson = @{
        name = $func
        version = "1.0.0"
        main = "index.js"
        dependencies = @{
            "node-appwrite" = "^11.0.0"
        }
    } | ConvertTo-Json -Depth 10
    
    Set-Content -Path "$tempDir\package.json" -Value $packageJson
    
    # Create zip
    $zipPath = "$outputPath\$func.zip"
    Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -Force
    
    # Clean up temp
    Remove-Item -Path $tempDir -Recurse -Force
    
    Write-Host "✅ Created: $zipPath" -ForegroundColor Green
}

Write-Host "`n🎉 All packages created in: $outputPath" -ForegroundColor Green
Write-Host "Now upload these to Appwrite Cloud Console" -ForegroundColor Yellow
```

**Run the script:**
```powershell
cd C:\Users\winst\BentleyBudgetBot
.\deploy_packages.ps1
```

This creates ready-to-upload `.zip` files in the `deployments\` folder!

---

## 🔑 After Deployment: Update Your .env File

Once all functions are deployed, update your `.env`:

```env
# Appwrite Configuration
APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
APPWRITE_PROJECT_ID=your_actual_project_id
APPWRITE_DATABASE_ID=your_actual_database_id
APPWRITE_API_KEY=your_actual_server_api_key

# Function IDs (get these from Appwrite Console after deployment)
APPWRITE_FUNCTION_ID_CREATE_TRANSACTION=6abc123...
APPWRITE_FUNCTION_ID_GET_TRANSACTIONS=6def456...
APPWRITE_FUNCTION_ID_ADD_WATCHLIST=6ghi789...
APPWRITE_FUNCTION_ID_GET_WATCHLIST=6jkl012...
```

---

## ✅ Verification Checklist

After deployment, verify each function:

- [ ] Function appears in Appwrite Console → Functions list
- [ ] Function status shows "Active" (green)
- [ ] Latest deployment shows "Ready" with green checkmark
- [ ] Test execution returns expected response
- [ ] Environment variables are set correctly
- [ ] Function ID is copied to `.env` file

---

## 🐛 Troubleshooting

### "Module not found: node-appwrite"
**Solution:** Add `package.json` to your deployment package:
```json
{
  "dependencies": {
    "node-appwrite": "^11.0.0"
  }
}
```

### "Cannot find module '../_shared/appwriteClient'"
**Solution:** Include `_shared` folder in your deployment ZIP

### "Execution timeout"
**Solution:** Increase timeout in Function Settings (default 15s, max 900s)

### "Invalid credentials"
**Solution:** Verify API key has correct scopes:
- `databases.read`
- `databases.write`
- `users.read`

---

## 📊 Expected Deployment Time

- **Per Function:** ~2-3 minutes (upload + build)
- **All 17 Functions:** ~30-45 minutes total
- **Using CLI:** ~15-20 minutes (bulk deployment)

---

## 🎯 Priority Deployment Order

Deploy in this order to get core functionality working first:

1. **Core Functions (for StreamLit):**
   - `get_transactions_streamlit`
   - `add_to_watchlist_streamlit`
   - `get_watchlist_streamlit`

2. **RBAC Functions (for security):**
   - `create_transaction` (with RBAC)
   - `get_transactions` (with RBAC)

3. **Utility Functions:**
   - `create_all_indexes` (run once to optimize database)

4. **Remaining Functions:**
   - Deploy as needed for additional features

---

## 📞 Need Help?

- **Appwrite Docs:** https://appwrite.io/docs/functions
- **Discord:** https://appwrite.io/discord
- **GitHub:** https://github.com/appwrite/appwrite

---

**Remember:** Until you deploy to Appwrite Cloud, the functions only exist as local files. They need to be uploaded to work with your StreamLit app!
