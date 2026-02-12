# GitHub Actions Secrets Verification

## 🔐 Two Different Secret Locations!

### ⚠️ **Critical Understanding:**

You need secrets in **TWO DIFFERENT PLACES**:

## 1. **GitHub Actions Secrets** (For CI/CD Workflow)
   
   **Location:** https://github.com/winstonwilliamsiii/BBBot/settings/secrets/actions
   
   **Purpose:** Used by `.github/workflows/streamlit-vercel-deploy.yml` to deploy to Vercel
   
   **Required Secrets:**
   ```
   VERCEL_TOKEN          = <your-vercel-token>
   VERCEL_ORG_ID         = <your-vercel-org-id>
   VERCEL_PROJECT_ID     = <your-vercel-project-id>  
   VERCEL_SCOPE          = <your-vercel-scope>
   ```
   
   **How to Add:**
   1. Go to: https://github.com/winstonwilliamsiii/BBBot/settings/secrets/actions
   2. Click "New repository secret"
   3. Add each secret one by one

## 2. **Streamlit Cloud Secrets** (For Runtime App)
   
   **Location:** https://share.streamlit.io/ → Your App → Settings → Secrets
   
   **Purpose:** Used by your running Streamlit app at runtime
   
   **Required Secrets:**
   ```toml
   MYSQL_HOST = "nozomi.proxy.rlwy.net"
   MYSQL_PORT = "54537"
   MYSQL_USER = "root"
   MYSQL_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"
   MYSQL_DATABASE = "mansa_bot"
   
   ALPACA_API_KEY = "PKVZTQAQR47MD4O7F65TSDDMJW"
   ALPACA_SECRET_KEY = "6agcTrRaX3nsbgL1mctxmMSRpZUCsynshs5MS6MiPX9h"
   # ... etc
   ```

---

## 🎯 Current Workflow Behavior

### If GitHub Actions Secrets ARE configured:
✅ Workflow validates code  
✅ Deploys Python API to Vercel  
✅ Streamlit Cloud auto-deploys frontend  
✅ Both systems work together

### If GitHub Actions Secrets are NOT configured:
✅ Workflow validates code  
⏭️  Skips Vercel deployment  
✅ Streamlit Cloud still auto-deploys  
⚠️  API endpoints won't work (no backend)

---

## 🔍 Checking Your Current Setup

### Run this command to check GitHub Actions secrets:

```bash
# List configured secrets (won't show values, just names)
gh secret list
```

Or manually check at:
https://github.com/winston williamsiii/BBBot/settings/secrets/actions

You should see:
- ✅ VERCEL_TOKEN
- ✅ VERCEL_ORG_ID  
- ✅ VERCEL_PROJECT_ID
- ✅ VERCEL_SCOPE

---

## 🚀 To Fix the Failed Workflow

### Option 1: Add GitHub Actions Secrets (Recommended if you use API endpoints)

1. Get your Vercel credentials:
   - Go to: https://vercel.com/account/tokens
   - Create new token
   - Get org ID and project ID from your Vercel project settings

2. Add to GitHub:
   - https://github.com/winstonwilliamsiii/BBBot/settings/secrets/actions
   - Add all 4 VERCEL_* secrets

### Option 2: Skip Vercel Deployment (If you don't use api/index.py)

If you're NOT using the `/api/*` endpoints, Vercel isn't needed. The workflow will:
- ✅ Still validate your code
- ✅ Still let Streamlit Cloud deploy
- ⏭️  Just skip the Vercel API deployment

---

## 📊 Architecture Summary

```
┌─────────────────────────────────────────┐
│  Developer Pushes to GitHub             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  GitHub Actions Workflow Runs           │
│  (Uses GitHub Actions Secrets)          │
│  - Validates Python code                │
│  - Checks dependencies                  │
│  - IF Vercel secrets: Deploy API        │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
       ▼               ▼
┌──────────────┐  ┌───────────────┐
│   Vercel     │  │ Streamlit     │
│   (API)      │  │ Cloud (App)   │
│              │  │               │
│ api/index.py │  │ streamlit     │
│   /api/*     │  │ _app.py       │
│   /health    │  │               │
│   /status    │  │ Uses Streamlit│
│              │  │ Cloud Secrets │
└──────────────┘  └───────────────┘
       │                  │
       └─────────┬────────┘
                 │
                 ▼
        ┌────────────────┐
        │ Railway MySQL  │
        │ nozomi:54537   │
        └────────────────┘
```

---

## ✅ Quick Fix Checklist

- [ ] Check GitHub Actions secrets at: https://github.com/winstonwilliamsiii/BBBot/settings/secrets/actions
- [ ] Verify VERCEL_TOKEN is set (not empty)
- [ ] Verify VERCEL_PROJECT_ID is set  
- [ ] Check Streamlit Cloud secrets at: https://share.streamlit.io/
- [ ] Verify MYSQL_HOST = "nozomi.proxy.rlwy.net"
- [ ] Verify MYSQL_PORT = "54537"
- [ ] Push a commit to trigger workflow again
- [ ] Check workflow at: https://github.com/winstonwilliamsiii/BBBot/actions

---

## 💡 Node.js Explanation

**Q: What is Node.js used for?**

**A:** Node.js is ONLY used during deployment to run the Vercel CLI tool:

- `vercel deploy` command requires Node.js
- Your actual app is 100% Python
- Node.js is NOT used at runtime
- It's just a build tool (like calling `git` or `docker`)

**Analogy:** Like using a screwdriver (Node.js/Vercel CLI) to install a door (Python API) - you need the tool to install it, but the tool isn't part of the final product.
