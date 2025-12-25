# 🔍 Appwrite Function Deployment Troubleshooting Guide

## ✅ Diagnosis Results

### Package Contents: CORRECT ✅
- ✅ index.js present
- ✅ package.json present with correct dependencies
- ✅ _shared/appwriteClient.js present
- ✅ All required files are in the .tar.gz

**This means the package structure is correct!**

---

## 🚨 Common Deployment Failure Causes

### 1. **Environment Variables Not Set** ⚠️ MOST COMMON

**Symptom:** Function deploys but execution fails

**Solution:** For each function, add these in Appwrite Console:

```
APPWRITE_FUNCTION_ENDPOINT=https://fra.cloud.appwrite.io/v1
APPWRITE_FUNCTION_PROJECT_ID=68869ef500017ca73772
APPWRITE_API_KEY=your_appwrite_api_key_here
APPWRITE_DATABASE_ID=your_database_id_here
```

**⚠️ IMPORTANT:** 
- Replace `your_appwrite_api_key_here` with your actual API key from the Appwrite console
- Get your API key from: https://cloud.appwrite.io/console/project-68869ef500017ca73772/settings
- Never commit API keys to version control
- Store sensitive keys as environment variables

**Where to add:**
1. Go to Function → Settings → Variables
2. Click "Add Variable"
3. Add each variable (name and value)
4. Save

---

### 2. **Wrong Entry Point**

**Symptom:** Build fails with "Cannot find entry point"

**Current Setting Should Be:**
- Entry Point: `index.js` (NOT `src/index.js` or `./index.js`)

**How to Fix:**
1. Go to Function → Settings → Configuration
2. Entry Point: `index.js`
3. Save

---

### 3. **Wrong Runtime Version**

**Symptom:** Dependencies fail to install

**Current Setting Should Be:**
- Runtime: `Node.js 18.0` (or newer like 20.0)

**How to Fix:**
1. Go to Function → Settings → Configuration
2. Runtime: Select "Node.js 18.0" or "Node.js 20.0"
3. Save and redeploy

---

### 4. **Build Timeout**

**Symptom:** "Build timeout" error

**Solution:**
1. Go to Function → Settings → Configuration
2. Build Timeout: Increase to 300 seconds (5 minutes)
3. Execution Timeout: Set to 30 seconds
4. Save and redeploy

---

### 5. **Missing Database ID**

**Symptom:** Function executes but returns "Database not found"

**Solution:**
You need to get your Database ID from Appwrite:

1. Go to: https://cloud.appwrite.io/console/project-68869ef500017ca73772/databases
2. Click on your database
3. Copy the Database ID (looks like: `67a1b2c3d4e5f6...`)
4. Add it as environment variable: `APPWRITE_DATABASE_ID`

---

## 🔍 How to Check What Failed

### In Appwrite Console:

1. **Go to Function → Deployments**
   - Look for red X or failed status
   - Click on deployment to see details

2. **Check Build Logs:**
   - Click on failed deployment
   - View "Build Logs" tab
   - Look for error messages

3. **Check Execution Logs:**
   - Go to Function → Executions
   - Try to execute manually
   - View execution logs for errors

---

## 📋 Step-by-Step Fix Checklist

For EACH failed function, verify:

- [ ] Function Status: Shows "Active" (not "Disabled")
- [ ] Latest Deployment: Shows green checkmark ✅
- [ ] Runtime: Node.js 18.0 or 20.0
- [ ] Entry Point: `index.js` (exactly)
- [ ] Build Timeout: 300 seconds
- [ ] Execution Timeout: 30 seconds
- [ ] Environment Variables (4 required):
  - [ ] APPWRITE_FUNCTION_ENDPOINT
  - [ ] APPWRITE_FUNCTION_PROJECT_ID
  - [ ] APPWRITE_API_KEY
  - [ ] APPWRITE_DATABASE_ID
- [ ] Execute Access: "Any" (for testing)

---

## 🎯 Quick Test

After fixing, test one function:

1. Go to Function → Execute
2. Add test body:
```json
{
  "user_id": "test123",
  "limit": 10
}
```
3. Click "Execute Now"
4. Check response - should NOT be error

---

## 🆘 If Still Failing

### Get Error Details:

1. **Screenshot the error** from Appwrite Console
2. **Copy build logs** from failed deployment
3. **Copy execution logs** from test execution

### Most Likely Issues:

1. **Missing APPWRITE_DATABASE_ID** ← Check this first!
   - Go get your Database ID from Databases section
   - Add it to EVERY function's environment variables

2. **API Key Permissions**
   - API key might not have correct scopes
   - Needs: `databases.read`, `databases.write`, `users.read`

3. **Database Doesn't Exist**
   - You need to create collections in Appwrite first
   - Collections: transactions, watchlist, users, etc.

---

## ✅ What Works (Verified)

- ✅ Package structure is correct
- ✅ index.js is present
- ✅ package.json is correct
- ✅ Dependencies are specified
- ✅ _shared folder is included
- ✅ .tar.gz format is correct

**The packages are good! The issue is in Appwrite configuration.**

---

## 🚀 Alternative: Try Option 1 (CLI Deployment)

If manual upload keeps failing, try CLI:

```powershell
.\deploy-to-appwrite-cli.ps1
```

Choose Option 1, authenticate via browser, and let CLI handle everything.

**Pros:**
- Sets environment variables automatically
- Handles configuration correctly
- Deploys all functions at once

**Cons:**
- Requires browser authentication
- Slightly more complex setup

---

## 📞 What to Check Right Now

1. **Get your Database ID:**
   ```
   https://cloud.appwrite.io/console/project-68869ef500017ca73772/databases
   ```

2. **For ONE function (e.g., get_transactions_streamlit):**
   - Go to Settings → Variables
   - Verify all 4 environment variables are set
   - Verify APPWRITE_DATABASE_ID has your actual Database ID

3. **Try manual execution:**
   - Go to Execute tab
   - Run with test data
   - Check what error appears

**Send me the error message and I can help fix it!**
