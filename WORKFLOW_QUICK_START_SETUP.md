# Quick Start: Enable the New Deployment Workflow

**Time Required:** 10-15 minutes  
**Difficulty:** Easy

## Checklist

### ☐ Step 1: Verify Files Are in Place (2 min)

These new files should now exist:
```bash
✓ .github/workflows/streamlit-vercel-deploy.yml
✓ .github/workflows/frontend-validation.yml
✓ frontend/utils/api.py
✓ .streamlit/secrets.example.toml
✓ WORKFLOW_REVIEW_AND_RECOMMENDATIONS.md
✓ WORKFLOW_IMPLEMENTATION_SUMMARY.md
```

### ☐ Step 2: Get Vercel Credentials (3 min)

You need 4 values from Vercel:

**VERCEL_TOKEN:**
1. Go to: https://vercel.com/account/tokens
2. Click "Create Token"
3. Name it: `github-actions-bentley`
4. Copy the token value

**VERCEL_ORG_ID, VERCEL_PROJECT_ID, VERCEL_SCOPE:**
1. Go to your Vercel project: https://vercel.com/dashboard
2. Click on your project
3. Settings → General
4. Find and copy:
   - `Organization ID` → This is `VERCEL_ORG_ID`
   - `Project ID` → This is `VERCEL_PROJECT_ID`
5. Find your team/org name → This is `VERCEL_SCOPE`

### ☐ Step 3: Add GitHub Secrets (3 min)

1. Go to: GitHub → Your Repo Settings → Secrets and variables → Actions → Secrets
2. Click "New organization secret" (for shared access across repos)
3. Add these 4 secrets:

| Name | Value | From Where |
|------|-------|-----------|
| `VERCEL_TOKEN` | (paste from Step 2) | Vercel account tokens |
| `VERCEL_ORG_ID` | (paste from Step 2) | Vercel project settings |
| `VERCEL_PROJECT_ID` | (paste from Step 2) | Vercel project settings |
| `VERCEL_SCOPE` | (paste from Step 2) | Your Vercel org name |

### ☐ Step 4: Create GitHub Environments (2 min)

**For Production:**
1. Settings → Environments → New environment
2. Name: `production`
3. Deployment branches: `main`
4. Save

**For Staging:**
1. Settings → Environments → New environment
2. Name: `staging`
3. Deployment branches: `staging`
4. Save

### ☐ Step 5: Configure Vercel Environment Variables (3 min)

Go to https://vercel.com → Your Project → Settings → Environment Variables

Add these variables (for both Preview and Production):

| Name | Value | Example |
|------|-------|---------|
| `DEPLOYMENT_ENV` | production (or staging) | production |
| `FRONTEND_ORIGIN` | Your Streamlit app URL | https://bbbot305.streamlit.app |
| `API_GATEWAY_KEY` | Your API security key | (from your config) |

### ☐ Step 6: Update Local Streamlit Secrets (2 min)

Copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml`:

```bash
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` with your actual values:
```toml
deployment_env = "production"
frontend_origin = "https://bbbot305.streamlit.app"
mysql_host = "your.mysql.host"
mysql_user = "your_user"
mysql_password = "your_password"
mysql_database = "your_database"
appwrite_endpoint = "https://your-appwrite.example.com"
appwrite_project = "your_project_id"
appwrite_api_key = "your_api_key"
plaid_client_id = "your_client_id"
plaid_secret = "your_secret"
api_gateway_key = "your_gateway_key"
```

### ☐ Step 7: Test the Workflow (3 min)

**Option A: Safe Test (Recommended)**
```bash
# Push to staging branch to test without affecting production
git checkout staging
echo "# Deployment test" >> .DEPLOY_TEST
git add .DEPLOY_TEST
git commit -m "test: trigger workflow"
git push origin staging
```

Then watch the workflow:
- GitHub → Actions → Streamlit to Vercel Deployment → (latest run)

It should show:
- ✅ Checkout repository
- ✅ Set up Python
- ✅ Install dependencies
- ✅ Validate Streamlit config
- ✅ Lint Python code
- ✅ Run import validation
- ✅ Validate environment requirements
- ✅ Set up Node.js
- ✅ Install Vercel CLI
- ✅ Deploy to Vercel
- ✅ Wait for deployment
- ✅ Verify API health endpoint
- ✅ Run basic connectivity test
- ✅ Success notification

**Option B: Dry-Run Test**
```bash
# Test without actually pushing
gh workflow run streamlit-vercel-deploy.yml --ref staging --dry-run
```

---

## What Happens When You Push

### Pushes to `staging` Branch:
1. Workflow validates your code
2. Deploys to Vercel **Preview** environment
3. Creates temporary staging URL
4. Runs health checks
5. Shows results in GitHub Actions

### Pushes to `main` Branch:
1. Workflow validates your code
2. Deploys to Vercel **Production** environment  
3. Updates your live URL: https://bbbot305.streamlit.app
4. Runs health checks
5. Shows results in GitHub Actions

### What Gets Validated:
- ✅ Python syntax errors
- ✅ All imports are available
- ✅ vercel.json is valid JSON
- ✅ All required environment variables exist
- ✅ Code style (flake8)
- ✅ API health endpoint responds

---

## Troubleshooting

### ❌ "Deployment failed: HTTP 401"
**Fix:** Your `VERCEL_TOKEN` is invalid or expired
- Generate new token from https://vercel.com/account/tokens
- Update GitHub secret

### ❌ "missing required secrets"
**Fix:** GitHub secrets not set properly
- Verify all 4 secrets are in Settings → Secrets
- Secrets are case-sensitive: `VERCEL_TOKEN`, not `vercel_token`

### ❌ "health check failed after 5 attempts"
**Fix:** API endpoint not responding
- Check that `api/index.py` has `/health` route
- Verify environment variables in Vercel are correct
- Check Vercel deployment logs for errors

### ❌ "Permission denied" on streamlit-vercel-deploy.yml
**Fix:** File permissions issue
- Run: `git update-index --chmod=+x .github/workflows/streamlit-vercel-deploy.yml`
- Then: `git commit -m "fix: workflow file permissions"` and push

### ❌ Workflow doesn't trigger on push
**Fix:** Check your default branch
- GitHub → Settings → Branches → Default branch should be `main`
- Workflow only runs on `main` and `staging`

---

## Verify It's Working

After first successful deployment, you should see:

1. **In GitHub Actions:**
   - Green checkmarks on all steps
   - "Success notification" at the end
   - Deployment URL displayed

2. **In Vercel Dashboard:**
   - New deployment listed
   - Status: "Ready"
   - Domains pointing to new deployment

3. **In Streamlit Cloud:**
   - App should load normally
   - No error messages in logs

4. **API Health:**
   - Visit: `https://bbbot305.streamlit.app/api/health`
   - Should see: `{"status": "healthy", ...}`

---

## Next: Integrate API Client in App

Once the workflow is running, use the API client in your Streamlit app:

**Add to `streamlit_app.py`:**
```python
from frontend.utils.api import get_api_client
import streamlit as st

# Check backend connectivity
api = get_api_client()
if not api.health_check():
    st.warning("⚠️ Backend API temporarily unavailable")
else:
    # Get status info
    status = api.get_status()
    st.success(f"✅ Connected to backend")
```

---

## Undo / Rollback

If something goes wrong, you can disable the workflow:

1. GitHub → Actions → Workflows
2. Click the three dots on `streamlit-vercel-deploy.yml`
3. Select "Disable workflow"

Or manually rollback in Vercel:
```bash
vercel rollback --token $VERCEL_TOKEN
```

---

## Support

**Detailed info in:**
- `WORKFLOW_REVIEW_AND_RECOMMENDATIONS.md` - Full technical analysis
- `WORKFLOW_IMPLEMENTATION_SUMMARY.md` - Implementation overview
- `.github/workflows/streamlit-vercel-deploy.yml` - Code comments

**Need help?**
- Check workflow logs: GitHub → Actions → (click run) → (click job) → See logs
- Check Vercel logs: Vercel Dashboard → Project → Deployments → (click deployment) → Logs
- Check Streamlit logs: Streamlit Cloud → App → Logs tab

---

**You're all set!** 🚀

The next time you push to `staging` or `main`, your app will automatically deploy through GitHub Actions to Vercel.
