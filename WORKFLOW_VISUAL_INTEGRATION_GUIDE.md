# Visual Integration Guide: Backend + Frontend CI/CD Pipeline

## The Big Picture: Your Bentley Budget Bot Deployment Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    YOU: Developer with New Code                          │
│                                                                          │
│    Git Commit: "feat: add new dashboard widget"                         │
│    git push origin feature/dashboard-widget                             │
└────────────────────────────┬─────────────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────────┐
         │  GitHub Repository (BBBot)                 │
         │  branches:                                 │
         │    - main (production)                    │
         │    - staging (pre-prod)                   │
         │    - feature/* (development)              │
         └────────────────┬─────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌─────────────┐ ┌──────────────┐ ┌──────────────┐
    │ main branch │ │staging branch│ │feature branch│
    │ (merge PR)  │ │ (test here)  │ │(never deploy)│
    └──────┬──────┘ └───────┬──────┘ └──────────────┘
           │                │
    [TRIGGER]        [TRIGGER]
           │                │
           ▼                ▼
    ┌──────────────────────────────────────────────┐
    │   GITHUB ACTIONS WORKFLOW                     │
    │   streamlit-vercel-deploy.yml                │
    │                                              │
    │   Step 1: VALIDATION                         │
    │   ├─ Check out code                          │
    │   ├─ Setup Python 3.11                       │
    │   ├─ Install requirements.txt                │
    │   ├─ Lint with flake8                        │
    │   ├─ Validate imports                        │
    │   ├─ Check vercel.json                       │
    │   └─ Verify secrets exist                    │
    │                                              │
    │   Step 2: DEPLOYMENT                         │
    │   ├─ Setup Node.js                           │
    │   ├─ Install Vercel CLI                      │
    │   └─ Deploy to Vercel                        │
    │                                              │
    │   Step 3: VERIFICATION                       │
    │   ├─ Wait for Vercel propagation             │
    │   ├─ Check /api/health endpoint              │
    │   └─ Validate connectivity                   │
    │                                              │
    │   Step 4: NOTIFICATION                       │
    │   └─ Report success/failure                  │
    └──────────────────┬───────────────────────────┘
                       │
        [IF MAIN]      │      [IF STAGING]
           │           │           │
           ▼           ▼           ▼
    ┌──────────────────────────────────────────────┐
    │    VERCEL DEPLOYMENT ENVIRONMENT              │
    │                                              │
    │  ┌────────────────────────────────────────┐  │
    │  │  Production (main branch)              │  │
    │  │  Domain: bbbot305.streamlit.app        │  │
    │  │  Replicas: 1+ (scaled)                 │  │
    │  │                                        │  │
    │  │  ├─ API Server (api/index.py)          │  │
    │  │  │  └─ /api/health                    │  │
    │  │  │  └─ /api/status                    │  │
    │  │  │  └─ /api/status/migration          │  │
    │  │  │                                    │  │
    │  │  ├─ Streamlit App (streamlit_app.py)  │  │
    │  │  │  ├─ Portfolio Dashboard            │  │
    │  │  │  ├─ RBAC Management                │  │
    │  │  │  ├─ Chatbot Integration            │  │
    │  │  │  └─ Economic Calendar              │  │
    │  │  │                                    │  │
    │  │  └─ Frontend Modules (frontend/)       │  │
    │  │     ├─ utils/                         │  │
    │  │     │  ├─ api.py (NEW!)               │  │
    │  │     │  ├─ styling.py                  │  │
    │  │     │  ├─ yahoo.py                    │  │
    │  │     │  └─ rbac.py                     │  │
    │  │     ├─ components/                    │  │
    │  │     │  └─ budget_dashboard.py         │  │
    │  │     └─ styles/                        │  │
    │  │        └─ colors.py                   │  │
    │  │                                        │  │
    │  └────────────────────────────────────────┘  │
    │                                              │
    │  ┌────────────────────────────────────────┐  │
    │  │  Staging/Preview (staging branch)      │  │
    │  │  Domain: [random].vercel.app           │  │
    │  │  Replicas: 1                           │  │
    │  │  (same structure as production)        │  │
    │  └────────────────────────────────────────┘  │
    │                                              │
    └──────────────────────────────────────────────┘
                       │
    ┌──────────────────┴──────────────────┐
    ▼                                     ▼
┌──────────────────────┐      ┌─────────────────────┐
│  CONNECTED SERVICES  │      │  DATABASE LAYER    │
│                      │      │                    │
│ MySQL (RBAC DB)      │      │ ┌─────────────────┐│
│ Appwrite (Auth)      │      │ │ MySQL Databases:││
│ Supabase (Optional)  │      │ │ - main_bbbot    ││
│ Yahoo Finance API    │      │ │ - bbbot1        ││
│ Plaid (Banking)      │      │ │ - mlflow_db     ││
│                      │      │ │ - quant_models  ││
│                      │      │ │ - mansa_quant   ││
│ (Configured via      │      │ │                 ││
│  Vercel Env Vars)    │      │ │ (Accessed by API││
│                      │      │ │  & Streamlit)   ││
└──────────────────────┘      │ └─────────────────┘│
                               │                    │
                               │ Appwrite Auth     │
                               │ (Session Mgmt)    │
                               └────────────────────┘
```

---

## The New Frontend Integration: APIClient in Action

### Before (How It Was)
```python
# streamlit_app.py (OLD)
import streamlit as st

# Direct database connection - risky!
import mysql.connector
conn = mysql.connector.connect(
    host="db.host",
    user="user",
    password="password"  # ❌ Exposed in app code!
)

st.write("Connected") # ❌ No validation that connection works
```

**Problems:**
- ❌ Credentials in app code
- ❌ Direct DB access (RBAC not enforced)
- ❌ No error handling
- ❌ No API layer
- ❌ Frontend tightly coupled to backend

---

### After (With New APIClient)
```python
# streamlit_app.py (NEW)
import streamlit as st
from frontend.utils.api import get_api_client

# Initialize API client (environment-aware)
api = get_api_client()

# Method 1: Simple health check
if api.health_check():
    st.success("✅ Backend operational")
else:
    st.warning("⚠️ Backend unavailable")

# Method 2: Get status info
status = api.get_status()
st.write(f"Backend version: {status['version']}")

# Method 3: Verify migrations complete
migrations = api.get_migration_status()
if migrations['status'] == 'complete':
    st.success("✅ All migrations completed")
```

**Benefits:**
- ✅ Credentials in environment variables only
- ✅ All requests go through API layer (RBAC enforced)
- ✅ Proper error handling
- ✅ Environment-aware routing
- ✅ Frontend loosely coupled to backend
- ✅ Easy to test/mock

---

## How APIClient Routes Requests

```
┌────────────────────────────────────────────────────────┐
│ from frontend.utils.api import get_api_client           │
│ api = get_api_client()                                  │
└────────────────────────┬───────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  APIClient.__init__() │
              │                      │
              │  Checks: DEPLOYMENT  │
              │  _ENV env var        │
              └─────────┬────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
    ["local"]      ["staging"]     ["production"]
        │               │               │
        ▼               ▼               ▼
  localhost:    staging_api_url     bbbot305
   8501/api     (from env var)   .streamlit.app
                                      /api
        │               │               │
        └───────────────┴───────────────┘
                        │
                        ▼
        ┌────────────────────────────┐
        │  api.health_check()        │
        │  api.get_status()          │
        │  api.get_migration_status()│
        └────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
    [Success]                      [Failure]
    ✅ Response                    ❌ Logged
    ✅ Data returned               ❌ Graceful fallback
```

---

## Deployment Flow: From Code to Live

### When You Push to `main`:

```
Time  Action                          Status
────  ──────────────────────────────  ────────────────────
 0s   git push origin main            ▶ Pushing code
 
 1s   GitHub detects push             ✓ Workflow triggered
      Workflow: streamlit-vercel-deploy.yml runs
      
 3s   Setup phase                     ⏳ Python 3.11 installed
 5s   Dependencies                    ✓ requirements.txt installed
 8s   Validation                      
      ├─ Syntax check                 ✓ No errors
      ├─ Import check                 ✓ All modules found
      ├─ Config check                 ✓ vercel.json valid
      └─ Secrets check                ✓ All env vars present
      
12s   Linting                         ✓ flake8 passed
      
15s   Deployment phase                
      ├─ Install Vercel CLI           ✓ npm i vercel
      └─ Deploy to Vercel             ▶ Deploying...
      
20s   Vercel receives                 ✓ Build started
      ├─ Build Python (api/)          ⏳ Compiling...
      ├─ Build frontend               ⏳ Bundling...
      └─ Deploy instances             ⏳ Starting...
      
35s   Verification phase              
      ├─ Wait for propagation         ⏳ 10 second wait
      ├─ Hit /api/health              ▶ Checking...
      │  └─ Attempt 1: 503            ⏳ API not ready
      │  └─ Attempt 2: 200 ✓          ✓ API responding
      └─ Validate response body       ✓ Contains "healthy"
      
40s   Success notification            ✅ Deployment complete!
      
      URL: https://bbbot305.streamlit.app
      Commit: a7f3e1c
      Branch: main
      Environment: production
```

**Total Time:** ~40 seconds from push to live ⚡

---

### When You Push to `staging`:

Same workflow, but:
- Deploys to Vercel **Preview** environment (temporary URL)
- Different domain: `https://[random-hash].vercel.app`
- Doesn't replace production
- Great for testing before promoting to main

---

## The RBAC + API Gateway Flow

### Without Proper Integration (What Could Go Wrong)

```
Streamlit App              Database
    │                          │
    │─ SELECT * FROM users    │
    │─ (No RBAC check!)       │
    │  ❌ User sees other    │
    │     users' data!        │
    │◄─────────────────────────│
    │     All data             │
```

### With Proper Integration (How It Works Now)

```
┌─────────────────────────────────────┐
│  Streamlit App (streamlit_app.py)   │
│                                     │
│  from frontend.utils.api import ... │
│  api = get_api_client()             │
│                                     │
│  status = api.get_status()          │
│  migrations = api.get_migration...()│
└─────────────┬───────────────────────┘
              │ (HTTPS + Auth Header)
              ▼
┌──────────────────────────────────────┐
│  API Gateway (api/index.py)          │
│  Running on Vercel                   │
│                                      │
│  1. Check API Key ✓                  │
│  2. Verify request signature         │
│  3. Enforce RBAC rules ✓             │
│  4. Log access attempt               │
│  5. Return filtered data only        │
└─────────────┬──────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│  MySQL Database                      │
│                                      │
│  ✓ Returns only data this user       │
│    is authorized to see              │
│  ✓ Audit log records the access     │
│                                      │
│  SELECT * FROM users WHERE           │
│    user_id IN (get_authorized_..);   │
└──────────────────────────────────────┘
```

**Key Difference:**
- ✅ All requests go through the API (enforces RBAC)
- ✅ Credentials never exposed to frontend
- ✅ Audit trail of all access
- ✅ Easy to add new security rules

---

## Environment Variables Flow: Where They Live

```
┌────────────────────────────────────────────────────────────────┐
│ GITHUB ORGANIZATION SECRETS                                    │
│ (Settings → Secrets → Actions)                                 │
│                                                                │
│ ✓ VERCEL_TOKEN       (Vercel account authentication)           │
│ ✓ VERCEL_ORG_ID      (Vercel org identifier)                  │
│ ✓ VERCEL_PROJECT_ID  (Vercel project identifier)              │
│ ✓ VERCEL_SCOPE       (Team/org for deployment)                │
│                                                                │
│ (Used by: GitHub Actions Workflow only)                        │
└────────────────────────────────────────────────────────────────┘
              │
              ▼ (Passed during deployment)
┌────────────────────────────────────────────────────────────────┐
│ VERCEL ENVIRONMENT VARIABLES                                   │
│ (Vercel Dashboard → Project → Settings)                        │
│                                                                │
│ ✓ DEPLOYMENT_ENV        = "production" or "staging"           │
│ ✓ FRONTEND_ORIGIN       = "https://bbbot305.streamlit.app"   │
│ ✓ API_GATEWAY_KEY       = "your-secret-api-key"              │
│ ✓ MYSQL_HOST            = "your-db.host"                      │
│ ✓ MYSQL_USER            = "db_user"                           │
│ ✓ MYSQL_PASSWORD        = "db_password"                       │
│ ✓ APPWRITE_ENDPOINT     = "https://appwrite.example.com"     │
│ ✓ APPWRITE_API_KEY      = "appwrite-key"                      │
│                                                                │
│ (Used by: Vercel runtime, api/index.py)                        │
└────────────────────────────────────────────────────────────────┘
              │
              ▼ (Available to running processes)
┌────────────────────────────────────────────────────────────────┐
│ STREAMLIT CLOUD SECRETS                                        │
│ (Streamlit Cloud → App → Settings → Secrets)                  │
│                                                                │
│ ✓ deployment_env  = "production"                              │
│ ✓ frontend_origin = "https://bbbot305.streamlit.app"         │
│ ✓ mysql_host      = "your-db.host"                           │
│ ✓ mysql_user      = "db_user"                                │
│ ✓ mysql_password  = "db_password"                            │
│ ✓ appwrite_*      = (all appwrite credentials)               │
│ ✓ plaid_*         = (all plaid credentials)                  │
│                                                                │
│ (Used by: streamlit_app.py at runtime)                         │
└────────────────────────────────────────────────────────────────┘
              │
              ▼ (Read by application code)
┌────────────────────────────────────────────────────────────────┐
│ RUNTIME APPLICATION                                             │
│                                                                │
│ API Client:                                                    │
│   from frontend.utils.api import get_api_client               │
│   api = get_api_client()  # Uses DEPLOYMENT_ENV               │
│                                                                │
│ Database:                                                      │
│   mysql.connect(                                              │
│     host=st.secrets["mysql_host"],                            │
│     user=st.secrets["mysql_user"],                            │
│     password=st.secrets["mysql_password"]                     │
│   )                                                           │
│                                                                │
│ Backend API:                                                  │
│   headers = {"X-API-Key": st.secrets["api_gateway_key"]}     │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Your Deployment Checklist (Visual)

```
┌─ SETUP PHASE (15 minutes)
│
├─ [ ] Step 1: Get Vercel Credentials (3 min)
│       From: https://vercel.com
│       Copy: Token, Org ID, Project ID, Scope name
│
├─ [ ] Step 2: Add GitHub Secrets (3 min)
│       Go: Settings → Secrets → Actions → New org secret
│       Add: VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID, VERCEL_SCOPE
│
├─ [ ] Step 3: Create GitHub Environments (2 min)
│       Go: Settings → Environments
│       Create: "production" (main), "staging" (staging)
│
├─ [ ] Step 4: Configure Vercel Env Vars (2 min)
│       Go: Vercel Dashboard → Project → Settings
│       Add: DEPLOYMENT_ENV, FRONTEND_ORIGIN, API_GATEWAY_KEY
│
├─ [ ] Step 5: Update Local Secrets (2 min)
│       Copy: .streamlit/secrets.example.toml → .streamlit/secrets.toml
│       Fill: All your actual values
│
└─ [ ] Step 6: Test Workflow (3 min)
        Push to staging branch
        Watch GitHub Actions
        Verify: All ✓ steps pass

Result: ✅ You're ready to deploy!
```

---

## Success Looks Like This

### In GitHub Actions (after your push):

```
✅ Checkout repository
✅ Set up Python
✅ Cache pip dependencies
✅ Install dependencies
✅ Validate Streamlit config
✅ Lint Python code
✅ Run import validation
✅ Validate environment requirements
✅ Set up Node.js for Vercel
✅ Install Vercel CLI
✅ Deploy to Vercel
✅ Wait for deployment to be ready
✅ Verify API health endpoint
✅ Run basic connectivity test
✅ Success notification

Deployment successful! ✨
Environment: Production
URL: https://bbbot305.streamlit.app
```

### In Your Streamlit App (on startup):

```
From streamlit_app.py with new API client:

>>> from frontend.utils.api import get_api_client
>>> api = get_api_client()
>>> api.health_check()
True

>>> api.get_status()
{
  'status': 'healthy',
  'service': 'bentley-budget-bot-api',
  'version': '1.0.0',
  'timestamp': '2026-01-27T...'
}

✅ Everything working!
```

---

## What Could Still Go Wrong? (Troubleshooting)

```
Issue                         Fix
────────────────────────────  ──────────────────────────────
❌ "HTTP 401" during deploy  → VERCEL_TOKEN expired/wrong
❌ Health check fails         → API_GATEWAY_KEY missing
❌ Wrong app deployed         → App path still `./streamlit_app`
❌ DB connection fails        → MYSQL_HOST/USER/PASSWORD in Vercel
❌ Imports not found          → requirements.txt out of sync
❌ Workflow doesn't trigger   → Push to main or staging?
```

See `WORKFLOW_QUICK_START_SETUP.md` for full troubleshooting guide.

---

## Timeline: Realistic Deployment

```
Day 1:
  ├─ 9:00 AM: Read this guide (30 min)
  ├─ 9:30 AM: Gather Vercel credentials (10 min)
  ├─ 9:40 AM: Configure GitHub secrets (10 min)
  ├─ 9:50 AM: Test on staging branch (15 min)
  └─ 10:05 AM: ✅ Workflow working!

Day 2-3:
  ├─ Test new features on staging branch
  ├─ Monitor for any deployment issues
  └─ ✅ Ready to use main branch for production

Ongoing:
  ├─ Every push to main → Auto-deploys
  ├─ Every push to staging → Tests before production
  └─ Easy rollback if needed
```

---

**You're all set!** Start with `WORKFLOW_QUICK_START_SETUP.md` to activate everything. 🚀
