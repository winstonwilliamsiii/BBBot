# 🔧 Appwrite Functions - Issues & Fixes History

**Last Updated:** December 25, 2025

This document tracks all major issues encountered with Appwrite Functions deployment and their resolutions with timestamps.

---

## 📅 December 25, 2025 - Module Resolution Error (CRITICAL FIX)

### Issue: Cannot find module '../_shared/appwriteClient'

**Error Message:**
```
Error: Cannot find module '../_shared/appwriteClient'
Require stack:
- /usr/local/server/src/function/index.js
- /usr/local/server/src/server.js
```

**Status:** ✅ RESOLVED

### Root Causes Identified

1. **Double-nested `_shared` folders** 
   - Every function had `function/_shared/_shared/appwriteClient.js`
   - Created by accidentally copying shared folder into each function directory

2. **Incorrect require paths**
   - Mix of `./_shared` and `../_shared` across different functions
   - 7 functions using `./_shared`, 9 using `../_shared`

3. **Packaging structure mismatch**
   - Functions using `../_shared` but tar.gz had flat structure
   - Appwrite extracts to `/usr/local/server/src/function/` with flat layout

### Solution Applied

**Step 1: Removed All Nested `_shared` Folders** ✅
```powershell
Get-ChildItem -Path ".\appwrite-functions\*\_shared" -Directory | Remove-Item -Recurse -Force
```

Affected all 16 functions:
- add_to_watchlist_streamlit
- create_all_indexes
- create_audit_log
- create_bot_metric
- create_payment
- create_transaction
- get_audit_logs
- get_bot_metrics
- get_bot_metrics_stats
- get_payments
- get_transactions
- get_transactions_streamlit
- get_user_profile_streamlit
- get_watchlist_streamlit
- manage_permissions
- manage_roles

**Step 2: Standardized All Require Paths** ✅

Changed ALL 16 functions from:
```javascript
const { createClient } = require('../_shared/appwriteClient');
```

To:
```javascript
const { createClient } = require('./_shared/appwriteClient');
```

**Step 3: Repackaged Functions** ✅
```powershell
.\package-appwrite-functions-targz.ps1
```

Result: 16 functions packaged (21.3 KB total) in `appwrite-deployments-targz/`

### Correct Structure

**Repository (Source):**
```
appwrite-functions/
├── _shared/                    ← Single shared folder at parent level
│   └── appwriteClient.js
├── get_transactions_streamlit/
│   ├── index.js               ← require('./_shared/appwriteClient')
│   └── package.json
└── ... (15 more functions)
```

**TAR.GZ Package (Deployed):**
```
get_transactions_streamlit.tar.gz
├── index.js                   ← require('./_shared/appwriteClient')
├── package.json
└── _shared/                   ← Same level as index.js
    └── appwriteClient.js
```

**Appwrite Runtime:**
```
/usr/local/server/src/function/
├── index.js                   ← require('./_shared/appwriteClient')
├── package.json
└── _shared/                   ← Resolves correctly!
    └── appwriteClient.js
```

---

## 📅 December 25, 2025 - CLI Command Update

### Issue: Outdated Appwrite CLI Command

**Status:** ✅ RESOLVED

### Problem
Documentation and scripts used old command:
```bash
appwrite deploy function
```

This was deprecated in favor of:
```bash
appwrite push function
```

### Solution Applied

Updated all references in:
- **Documentation (8 files):**
  - APPWRITE_FUNCTIONS_FIX_COMPLETE.md
  - APPWRITE_DEPLOYMENT_GUIDE.md
  - ISSUES_SUMMARY.md
  - MIGRATION_STATUS_EXPLAINED.md
  - appwrite-functions/README.md
  - sites/Mansa_Bentley_Platform/APPWRITE_DEPLOYMENT_GUIDE.md
  - sites/Mansa_Bentley_Platform/ISSUES_SUMMARY.md
  - sites/Mansa_Bentley_Platform/appwrite-functions/README.md

- **PowerShell scripts (4 files):**
  - package-appwrite-functions-targz.ps1
  - deploy-to-appwrite-cli.ps1
  - sites/Mansa_Bentley_Platform/package-appwrite-functions-targz.ps1
  - sites/Mansa_Bentley_Platform/deploy-to-appwrite-cli.ps1

---

## 🎯 Appwrite Console Navigation Issues

### Issue: Confusion Between Global vs Function Variables

**Status:** ✅ DOCUMENTED

### Problem
Users accessing **Project Settings** (bottom left gear icon) instead of **Function Settings** (per-function configuration).

**Wrong Path:**
```
Appwrite Console
└── Settings (bottom left) ❌
    └── Environment Variables
        └── Global Variables ← Wrong location for function-specific config
```

**Correct Path:**
```
Appwrite Console
└── Functions (left sidebar) ✅
    └── [Specific Function Name]
        └── Settings (top navigation)
            └── Variables ← Correct location
```

### Key Differences

| Aspect | Global Variables | Function Variables |
|--------|-----------------|-------------------|
| **Location** | Settings (bottom left) → Environment Variables | Functions → [Function] → Settings → Variables |
| **Scope** | Entire Appwrite project | Only that specific function |
| **Use Case** | Values ALL services need (rare) | Function-specific configuration |
| **Functions can read** | Maybe (version dependent) | YES, always |
| **Recommended** | NO for function config | YES for function config |

### Environment Variables Required

Each function needs these 4 variables:

```bash
APPWRITE_FUNCTION_ENDPOINT=https://fra.cloud.appwrite.io/v1
APPWRITE_FUNCTION_PROJECT_ID=68869ef500017ca73772
APPWRITE_API_KEY=<your-api-key>
APPWRITE_DATABASE_ID=<your-database-id>
```

**Option A:** Global Variables (all functions access)
- Settings → Environment Variables → Global Variables

**Option B:** Function Variables (per function - recommended)
- Functions → [Function Name] → Settings → Variables
- 4 variables × 16 functions = 64 entries

---

## 📊 All 16 Functions Status

| # | Function Name | Status | Package Size |
|---|---------------|--------|--------------|
| 1 | create_transaction | ✅ Fixed | 1.75 KB |
| 2 | get_transactions | ✅ Fixed | 1.49 KB |
| 3 | get_transactions_streamlit | ✅ Fixed | 1.21 KB |
| 4 | add_to_watchlist_streamlit | ✅ Fixed | 1.20 KB |
| 5 | get_watchlist_streamlit | ✅ Fixed | 1.19 KB |
| 6 | get_user_profile_streamlit | ✅ Fixed | 0.96 KB |
| 7 | create_audit_log | ✅ Fixed | 1.26 KB |
| 8 | get_audit_logs | ✅ Fixed | 1.23 KB |
| 9 | create_payment | ✅ Fixed | 1.22 KB |
| 10 | get_payments | ✅ Fixed | 1.21 KB |
| 11 | manage_roles | ✅ Fixed | 1.27 KB |
| 12 | manage_permissions | ✅ Fixed | 1.34 KB |
| 13 | create_bot_metric | ✅ Fixed | 1.40 KB |
| 14 | get_bot_metrics | ✅ Fixed | 1.43 KB |
| 15 | get_bot_metrics_stats | ✅ Fixed | 1.60 KB |
| 16 | create_all_indexes | ✅ Fixed | 1.54 KB |

---

## 🚀 Quick Reference Commands

### Repackage Functions
```powershell
.\package-appwrite-functions-targz.ps1
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

### Check Appwrite CLI Status
```powershell
appwrite --version
appwrite login
appwrite list functions
```

### Verify Package Structure
```powershell
mkdir test-verify
cd test-verify
tar -xzf ..\appwrite-deployments-targz\get_transactions_streamlit.tar.gz
Get-ChildItem -Recurse
```

### Test Function Execution
1. Go to Appwrite Console → Functions → [Function Name]
2. Click "Execute" tab
3. Add test payload:
   ```json
   {
     "user_id": "test123"
   }
   ```
4. Click "Execute"
5. Check for errors

---

## 📝 Lessons Learned

### 1. Appwrite Tar.gz Structure
- Appwrite extracts tar.gz files to `/usr/local/server/src/function/`
- All files in tar.gz are placed at same level (flat structure)
- Shared code must be included IN each tar.gz package
- Use `./_shared` for same-level requires, not `../_shared`

### 2. Packaging Best Practices
- Keep ONE `_shared` folder at parent level in repository
- Never nest `_shared` inside function directories
- Packaging script copies `_shared` into each tar.gz
- Always verify extracted structure before deploying

### 3. Environment Variables
- Function Variables > Global Variables for function config
- Test with Global Variables first (easier setup)
- Use Function Variables for production (better isolation)
- Always set all 4 required environment variables

### 4. CLI Commands
- Use `appwrite push` not `appwrite deploy`
- `--all` flag deploys all functions at once
- `--functionId` flag deploys specific function
- Always login before pushing: `appwrite login`

---

## 🔍 Troubleshooting Checklist

If functions fail to execute:

- [ ] Check function names are set (not just IDs)
- [ ] Verify all 4 environment variables are set
- [ ] Confirm package has flat structure with `_shared/` at root
- [ ] Check `index.js` uses `require('./_shared/appwriteClient')`
- [ ] Verify `package.json` exists in tar.gz
- [ ] Confirm `node-appwrite` version is `^11.0.0`
- [ ] Test with simple execution payload first
- [ ] Check Appwrite function logs for detailed errors
- [ ] Verify API key has correct permissions
- [ ] Confirm database ID matches your project

---

**Date Fixed:** December 25, 2025  
**Files Modified:** 16 index.js files, 12 documentation files, 4 PowerShell scripts  
**Folders Removed:** 16 nested `_shared` directories  
**Packages Created:** 16 tar.gz files (21.3 KB total)  
**Status:** All functions ready for deployment ✅
