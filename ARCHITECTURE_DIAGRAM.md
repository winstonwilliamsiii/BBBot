# Architecture Diagram & Visual Reference

## 🏗️ Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     BENTLEY BUDGET BOT - MULTI-ENVIRONMENT              │
│                           ARCHITECTURE v1.0                             │
└─────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════
                          DEVELOPMENT ENVIRONMENT
                         (Moor Kingdom - Localhost)
═══════════════════════════════════════════════════════════════════════════

┌────────────────────────────────────────────────────────────────────────┐
│ DEVELOPER MACHINE (Moor Kingdom)                                       │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ Project Directory: C:\Users\winst\BentleyBudgetBot            │  │
│  │                                                                 │  │
│  │ .venv/                         ← Python Virtual Environment    │  │
│  │ .env.local ✓ (Gitignored)      ← LOCAL SECRETS               │  │
│  │ .env.development ✓             ← Dev Configuration           │  │
│  │ config_env.py ✓                ← Config Manager              │  │
│  │ streamlit_app.py               ← Main App                    │  │
│  │                                                                 │  │
│  │ uploads_dev/  ← Local upload directory                         │  │
│  │ logs_dev/     ← Local logs directory                           │  │
│  │ data_dev/     ← Local data directory                           │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                              │                                          │
│                              │                                          │
│  ┌───────────────────────────┴──────────────────────────────────────┐  │
│  │ LOCAL SERVICES                                                 │  │
│  │                                                                 │  │
│  │ MySQL 8.0 (Docker Container)                                  │  │
│  │ ├─ Database: bentley_bot_dev                                 │  │
│  │ ├─ Port: 3306                                                │  │
│  │ └─ Credentials from .env.local                              │  │
│  │                                                                 │  │
│  │ Streamlit App                                                 │  │
│  │ ├─ http://localhost:8501                                     │  │
│  │ ├─ Debug Mode: ON                                            │  │
│  │ ├─ Hot Reload: ON                                            │  │
│  │ └─ Console Logging: DEBUG                                    │  │
│  │                                                                 │  │
│  │ Local APIs (Configured)                                        │  │
│  │ ├─ Alpaca Paper Trading Account                              │  │
│  │ ├─ Plaid Sandbox                                             │  │
│  │ ├─ Google Generative AI (Dev Key)                            │  │
│  │ └─ Appwrite Local Instance                                   │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                              │                                          │
│                              ↓                                          │
│                        GIT WORKFLOW                                     │
│                   (Create feature branches)                            │
└────────────────────────────────────────────────────────────────────────┘
                              │
                              │ git push
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      GITHUB REPOSITORY                                 │
│                (winstonwilliamsiii/BBBot)                             │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ BRANCH STRUCTURE                                            │   │
│  │                                                             │   │
│  │ main/              Production Branch                        │   │
│  │ └─ Auto-deploys to Streamlit Cloud                         │   │
│  │                                                             │   │
│  │ dev/               Development Branch (YOUR WORK)           │   │
│  │ └─ Where features get integrated                           │   │
│  │                                                             │   │
│  │ feature/*          Feature Branches                         │   │
│  │ └─ Create PRs to dev when ready                            │   │
│  │                                                             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                         │                                            │
│                         ↓                                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ GITHUB ACTIONS WORKFLOWS                                   │   │
│  │                                                             │   │
│  │ 1. dev-test.yml                                           │   │
│  │    Trigger: Every push to dev                             │   │
│  │    Actions:                                                │   │
│  │    ├─ Test on Python 3.10 & 3.11                          │   │
│  │    ├─ Lint (flake8, black, isort)                         │   │
│  │    ├─ Security scan (Bandit, Safety)                      │   │
│  │    └─ Environment validation                              │   │
│  │    Result: ✅ PASS or ❌ FAIL shown in GitHub              │   │
│  │                                                             │   │
│  │ 2. dev-to-main.yml                                        │   │
│  │    Trigger: Pull Request to main                          │   │
│  │    Actions:                                                │   │
│  │    ├─ Full test suite                                     │   │
│  │    ├─ PR validation (title, description)                  │   │
│  │    ├─ Security audit                                      │   │
│  │    ├─ Production readiness check                          │   │
│  │    └─ Deployment simulation                               │   │
│  │    Result: Blocks merge if any gate fails                 │   │
│  │                                                             │   │
│  │ 3. prod-deploy.yml                                        │   │
│  │    Trigger: Push to main                                  │   │
│  │    Actions:                                                │   │
│  │    ├─ Final validation                                    │   │
│  │    ├─ Deploy to Streamlit Cloud                           │   │
│  │    ├─ Health checks                                       │   │
│  │    └─ Notifications                                       │   │
│  │    Result: App live at https://bbbot305.streamlit.app     │   │
│  │                                                             │   │
│  │ 4. feature-test.yml                                       │   │
│  │    Trigger: Pushes to feature/* branches                  │   │
│  │    Actions:                                                │   │
│  │    ├─ Linting & basic tests                               │   │
│  │    └─ Encourage PR to dev                                 │   │
│  │                                                             │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              │ Auto-deploy on main
                              ↓

═══════════════════════════════════════════════════════════════════════════
                       PRODUCTION ENVIRONMENT
                        (Streamlit Cloud)
═══════════════════════════════════════════════════════════════════════════

┌────────────────────────────────────────────────────────────────────────┐
│ STREAMLIT CLOUD DEPLOYMENT                                             │
│                                                                        │
│  Application: bbbot305.streamlit.app                                   │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ PRODUCTION ENVIRONMENT (.env.production)                       │  │
│  │                                                                 │  │
│  │ ENVIRONMENT=production                                         │  │
│  │ LOG_LEVEL=INFO                                                │  │
│  │ DEBUG_MODE=false                                              │  │
│  │ ENABLE_EXPERIMENTAL_FEATURES=false                            │  │
│  │ STREAMLIT_LOGGER_LEVEL=info                                   │  │
│  │ ALPACA_ENVIRONMENT=live                                       │  │
│  │ ALPACA_BATCH_SIZE=5 (conservative)                            │  │
│  │                                                                 │  │
│  │ [Secrets configured in Streamlit Cloud Web UI]                │  │
│  │ ├─ DB_PASSWORD                                                │  │
│  │ ├─ ALPACA_API_KEY (LIVE TRADING)                              │  │
│  │ ├─ ALPACA_SECRET_KEY (LIVE TRADING)                           │  │
│  │ ├─ GOOGLE_API_KEY                                             │  │
│  │ ├─ GEMINI_API_KEY                                             │  │
│  │ └─ PLAID_SECRET                                               │  │
│  │                                                                 │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                              │                                         │
│  ┌───────────────────────────┴──────────────────────────────────────┐  │
│  │ PRODUCTION SERVICES                                            │  │
│  │                                                                 │  │
│  │ Cloud MySQL Database                                           │  │
│  │ ├─ Database: bentley_bot_production                            │  │
│  │ ├─ Host: prod-db.aws.amazonaws.com                            │  │
│  │ ├─ Live financial data                                         │  │
│  │ └─ Portfolio tracking                                          │  │
│  │                                                                 │  │
│  │ Streamlit Cloud Runtime                                        │  │
│  │ ├─ Python 3.10                                                │  │
│  │ ├─ Auto-reload on main branch changes                         │  │
│  │ ├─ HTTPS enabled                                              │  │
│  │ ├─ Rate limiting on requests                                  │  │
│  │ └─ Monitoring & logging                                       │  │
│  │                                                                 │  │
│  │ Production APIs (Live Credentials)                             │  │
│  │ ├─ Alpaca LIVE Trading                                        │  │
│  │ ├─ Plaid Production                                           │  │
│  │ ├─ Google Production API                                      │  │
│  │ ├─ Yahoo Finance                                              │  │
│  │ └─ Appwrite Production Instance                               │  │
│  │                                                                 │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  Users Access: https://bbbot305.streamlit.app                        │
│  ├─ Portfolio management                                             │
│  ├─ Live trading integration                                         │
│  ├─ Budget dashboard                                                 │
│  ├─ Economic calendar                                                │
│  └─ AI-powered chatbot                                               │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data & Credential Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CREDENTIAL MANAGEMENT FLOW                          │
└─────────────────────────────────────────────────────────────────────────┘

DEVELOPMENT (Moor Kingdom - Safe)
═════════════════════════════════

  .env.local (GITIGNORED - 🔒 Secret File)
  ├─ DB_PASSWORD: your_local_password
  ├─ ALPACA_API_KEY: pk_test_xxx (PAPER TRADING)
  ├─ ALPACA_SECRET_KEY: sk_test_xxx
  ├─ PLAID_SECRET: dev_secret_xxx
  └─ UPLOAD_DIRECTORY: C:\Users\winst\BentleyBudgetBot\uploads_dev
       │
       ↓
  config_env.py (ENV MANAGER)
       │
       ├─ Load .env.local (highest priority)
       ├─ Overlay .env.development
       └─ Fallback to .env
       │
       ↓
  streamlit_app.py (APP)
       │
       ├─ LOCAL MySQL: bentley_bot_dev
       ├─ PAPER TRADING: Alpaca Demo Account
       ├─ SANDBOX: Plaid Sandbox
       └─ DEV KEYS: Google Generative AI
       │
       ↓
  ✅ SAFE - No real trading
     No production data
     Full debugging enabled


PRODUCTION (Streamlit Cloud - Protected)
═════════════════════════════════════════

  .env.production (COMMITTED to repo - ✅ Public Safe)
  ├─ Non-sensitive production settings
  ├─ ENVIRONMENT=production
  ├─ LOG_LEVEL=INFO
  └─ ALPACA_ENVIRONMENT=live
       │
       ↓
  Streamlit Cloud Web UI (🔒 Encrypted)
  ├─ DB_PASSWORD: ***encrypted***
  ├─ ALPACA_API_KEY: ***live key*** (REAL TRADING)
  ├─ ALPACA_SECRET_KEY: ***live secret***
  ├─ PLAID_SECRET: ***production secret***
  └─ GOOGLE_API_KEY: ***production key***
       │
       ↓
  config_env.py (ENV MANAGER)
       │
       └─ Load from Streamlit Cloud Secrets
       │
       ↓
  streamlit_app.py (APP)
       │
       ├─ CLOUD MySQL: bentley_bot_production
       ├─ LIVE TRADING: Real Alpaca Account
       ├─ PRODUCTION: Plaid Live Environment
       └─ PRODUCTION KEYS: Google Live API
       │
       ↓
  ✅ SECURE - Credentials never in code
     Encrypted in Streamlit Cloud
     Real trading on live account
```

---

## 📊 Configuration Precedence

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  ENVIRONMENT VARIABLE PRECEDENCE                       │
│                    (Highest → Lowest Priority)                         │
└─────────────────────────────────────────────────────────────────────────┘

TIER 1 - HIGHEST (Machine Specific)
┌──────────────────────────────────┐
│  .env.local                      │
│  ✓ Gitignored (not in repo)      │
│  ✓ Machine-specific secrets      │
│  ✓ Passwords, API keys           │
│  ✓ Local file paths              │
│                                  │
│  File: C:\...\BentleyBudgetBot\  │
│        .env.local (you create)   │
│                                  │
│  Content Example:                │
│  DB_PASSWORD=my_secret           │
│  ALPACA_API_KEY=pk_test_xxx      │
│  UPLOAD_DIRECTORY=C:\Users\...   │
└──────────────────────────────────┘
         ↓ OVERRIDES ↓


TIER 2 - MEDIUM (Environment Specific)
┌──────────────────────────────────┐
│  .env.{ENVIRONMENT}              │
│  ✓ Committed to repo             │
│  ✓ Dev or Production defaults    │
│  ✓ Non-sensitive config          │
│                                  │
│  Files:                          │
│  - .env.development              │
│  - .env.production               │
│                                  │
│  Content Example:                │
│  LOG_LEVEL=DEBUG (dev)           │
│  ALPACA_ENVIRONMENT=paper        │
│  DB_HOST=localhost               │
└──────────────────────────────────┘
         ↓ OVERRIDES ↓


TIER 3 - LOWEST (Default Fallback)
┌──────────────────────────────────┐
│  .env                            │
│  ✓ Committed to repo             │
│  ✓ Legacy support                │
│  ✓ Base defaults                 │
│                                  │
│  File: .env                      │
│                                  │
│  Content Example:                │
│  DEFAULT_TIMEOUT=30              │
│  CACHE_ENABLED=true              │
└──────────────────────────────────┘


LOADING ORDER (in config_env.py):
1. Load .env (defaults)
2. Load .env.{ENVIRONMENT} (environment overrides)
3. Load .env.local (machine overrides) ← FINAL VALUES USED
```

---

## 🚀 Deployment Workflow Timeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FEATURE TO PRODUCTION TIMELINE                      │
└─────────────────────────────────────────────────────────────────────────┘

DAY 1 - MORNING: Start Feature Development
═══════════════════════════════════════════

09:00 AM   ┌─ Checkout dev branch
           │  git checkout dev
           │  git pull origin dev
           │
10:00 AM   ├─ Create feature branch
           │  git checkout -b feature/new-widget
           │
11:00 AM   ├─ Develop & test locally
           │  - Edit code
           │  - Run: streamlit run streamlit_app.py
           │  - Test with local MySQL
           │  - Verify Alpaca paper trading
           │
02:00 PM   └─ Commit & push
              git add .
              git commit -m "feat(dashboard): add new widget"
              git push origin feature/new-widget

                    ↓

DAY 1 - AFTERNOON: Code Review
═══════════════════════════════

02:15 PM   ┌─ Create PR on GitHub
           │  - PR to dev branch
           │  - GitHub Actions STARTS: dev-test.yml
           │
02:30 PM   ├─ GitHub Actions Running:
           │  ├─ Linting (flake8) ...
           │  ├─ Tests (pytest) ...
           │  ├─ Security scan (Bandit, Safety) ...
           │  ├─ Python 3.10 tests ...
           │  ├─ Python 3.11 tests ...
           │  └─ Environment validation ...
           │
02:45 PM   ├─ GitHub Actions Complete ✅ PASS
           │  - All checks passed
           │  - PR shows green checkmarks
           │
03:00 PM   ├─ Code review & approval
           │  - Team reviews changes
           │  - Requests approved
           │
03:15 PM   └─ Merge to dev
              git checkout dev
              git merge feature/new-widget
              git push origin dev

                    ↓

DAY 2 - MORNING: Integration & Staging
═══════════════════════════════════════

09:00 AM   ┌─ Test on dev branch
           │  - Feature integrated with other code
           │  - Test end-to-end
           │  - Verify no conflicts
           │
10:00 AM   ├─ When ready for production...
           │
10:15 AM   ├─ Create PR: dev → main on GitHub
           │  - GitHub Actions STARTS: dev-to-main.yml
           │
10:30 AM   ├─ GitHub Actions VALIDATION GATES Run:
           │  ├─ Full test suite (3 min) ...
           │  ├─ Security audit (2 min) ...
           │  ├─ Production readiness check (1 min) ...
           │  ├─ Deployment simulation (2 min) ...
           │  ├─ Branch validation (1 min) ...
           │  └─ All gates complete ✅
           │
11:00 AM   ├─ GitHub PR shows:
           │  ✅ Pre-merge checks passed
           │  ✅ Branch validation passed
           │  ✅ Security audit passed
           │  ✅ Production readiness passed
           │  ✅ Deployment simulation passed
           │
11:15 AM   ├─ Final review & approval
           │
11:30 AM   └─ MERGE TO MAIN
              git checkout main
              git merge --no-ff dev
              git push origin main

                    ↓

DAY 2 - NOON: Production Deployment
════════════════════════════════════

11:35 AM   ┌─ GitHub Actions STARTS: prod-deploy.yml
           │
11:40 AM   ├─ Final production validation
           │  - Compiles app
           │  - Checks all imports
           │  - Validates production config
           │
11:45 AM   ├─ Deploy to Streamlit Cloud
           │  - Code cloned from main
           │  - Dependencies installed
           │  - App started
           │  - Health checks run
           │
12:00 PM   ├─ 🎉 LIVE IN PRODUCTION
           │  - https://bbbot305.streamlit.app
           │  - New feature available to users
           │  - Monitoring & alerts active
           │
12:15 PM   └─ Post-deployment verification
              - Check app loads
              - Test new feature on prod
              - Monitor logs for errors
```

---

## 📈 Environment Comparison Matrix

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT vs PRODUCTION                           │
└─────────────────────────────────────────────────────────────────────────┘

ASPECT                  │ DEVELOPMENT           │ PRODUCTION
────────────────────────┼───────────────────────┼──────────────────────
Location                │ Localhost             │ Streamlit Cloud
Machine                 │ Moor Kingdom Laptop   │ Cloud Server
URL                     │ localhost:8501        │ bbbot305.streamlit.app
────────────────────────┼───────────────────────┼──────────────────────
Python Version          │ Flexible (3.10+)      │ Fixed (3.10)
Database                │ Local MySQL           │ Cloud MySQL (AWS)
Database Name           │ bentley_bot_dev       │ bentley_bot_production
────────────────────────┼───────────────────────┼──────────────────────
Logging                 │ DEBUG                 │ INFO
Debug Mode              │ ENABLED               │ DISABLED
Profiling               │ ENABLED               │ DISABLED
Error Tracing           │ ENABLED               │ DISABLED
────────────────────────┼───────────────────────┼──────────────────────
Cache Control           │ DISABLED              │ ENABLED
Session Timeout         │ 60 minutes            │ 30 minutes
────────────────────────┼───────────────────────┼──────────────────────
Alpaca Trading          │ PAPER TRADING         │ LIVE TRADING
Alpaca Batch Size       │ 10 (permissive)       │ 5 (conservative)
Alpaca API              │ paper-api.alpaca...   │ api.alpaca.markets
────────────────────────┼───────────────────────┼──────────────────────
Plaid Environment       │ SANDBOX               │ PRODUCTION
Google API              │ Dev Key               │ Production Key
────────────────────────┼───────────────────────┼──────────────────────
Experimental Features   │ ENABLED               │ DISABLED
Budget Dashboard        │ ENABLED               │ ENABLED
Chatbot                 │ ENABLED               │ ENABLED
Economic Calendar       │ ENABLED               │ ENABLED
────────────────────────┼───────────────────────┼──────────────────────
CORS Origins            │ localhost:*           │ bbbot305.streamlit.app
CSRF Protection         │ DISABLED              │ ENABLED
Allowed Hosts           │ localhost, 127.0.0.1  │ bbbot305.streamlit.app
────────────────────────┼───────────────────────┼──────────────────────
Credentials             │ .env.local            │ Streamlit Cloud Secrets
Secrets in Code         │ ✓ SAFE (in .env.local)│ ✓ SAFE (encrypted)
Secrets in Repo         │ ✗ NEVER (gitignored) │ ✗ NEVER (cloud managed)
────────────────────────┼───────────────────────┼──────────────────────
Update Method           │ Manual restart        │ Auto on main push
Deployment Risk         │ NONE (local only)     │ PRODUCTION
Rollback Time           │ Immediate (local)     │ 5-10 minutes
────────────────────────┼───────────────────────┼──────────────────────
User Access             │ You only              │ Public (authenticated)
Data Exposure           │ None (localhost)      │ Production data
Trading Impact          │ NONE (paper)          │ REAL MONEY
```

---

## 🔐 Security Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      MULTI-LAYER SECURITY                              │
└─────────────────────────────────────────────────────────────────────────┘

LAYER 1: Repository Level (GitHub)
═══════════════════════════════════
  ├─ .gitignore protects sensitive files
  │  ├─ .env.local ← Machine secrets (NEVER committed)
  │  ├─ .env.*.local ← Environment-specific secrets
  │  ├─ *.pyc ← Compiled Python
  │  └─ __pycache__/ ← Cache files
  │
  ├─ Branch protection on main
  │  ├─ Requires PR review
  │  ├─ Requires passing checks
  │  └─ Prevents direct pushes
  │
  └─ GitHub Secrets scanning
     ├─ Detects exposed API keys
     ├─ Alerts on suspicious commits
     └─ Blocks commits with keys


LAYER 2: Build/CI Level (GitHub Actions)
═════════════════════════════════════════
  ├─ Pre-merge validation checks
  │  ├─ Bandit security scan
  │  ├─ Safety dependency check
  │  ├─ Secret exposure detection
  │  └─ Production config validation
  │
  ├─ Environment isolation
  │  ├─ Dev uses paper trading keys
  │  ├─ Prod uses live keys
  │  └─ Keys never logged in actions
  │
  └─ Test coverage
     ├─ Code quality checks
     ├─ Deployment simulation
     └─ Security audits


LAYER 3: Configuration Level (.env files)
══════════════════════════════════════════
  ├─ Development (.env.development)
  │  ├─ ✅ Committed to repo
  │  ├─ ✓ Non-sensitive defaults
  │  └─ Dev environment settings
  │
  ├─ Production (.env.production)
  │  ├─ ✅ Committed to repo
  │  ├─ ✓ Non-sensitive settings
  │  ├─ Placeholders for secrets
  │  └─ Uses Streamlit Cloud Secrets
  │
  └─ Local (.env.local) ⭐ MOST IMPORTANT
     ├─ ✗ GITIGNORED (never committed)
     ├─ 🔒 Contains all secrets
     ├─ 🔒 Machine-specific paths
     ├─ 🔒 API keys & passwords
     └─ 🔒 Only on your laptop


LAYER 4: Application Level (config_env.py)
═══════════════════════════════════════════
  ├─ Safe environment loading
  │  ├─ Three-tier precedence
  │  ├─ Proper override mechanism
  │  └─ Error handling for missing values
  │
  ├─ Type-safe getters
  │  ├─ config.get() → string
  │  ├─ config.get_bool() → boolean
  │  ├─ config.get_int() → integer
  │  └─ None returned if missing
  │
  └─ Environment checks
     ├─ config.is_production()
     ├─ config.is_development()
     └─ Safe conditional logic


LAYER 5: Streamlit Cloud Level
═══════════════════════════════
  ├─ Web UI Secrets Management
  │  ├─ 🔐 Encrypted storage
  │  ├─ Access controls
  │  ├─ No plain text viewing
  │  └─ Audit logging
  │
  ├─ Live API Key Management
  │  ├─ 🔐 Alpaca live keys
  │  ├─ 🔐 Plaid production keys
  │  ├─ 🔐 Database passwords
  │  └─ 🔐 API credentials
  │
  └─ Runtime Environment
     ├─ HTTPS only
     ├─ Rate limiting
     ├─ Request logging
     └─ Error reporting


SECURITY VALIDATION CHECKLIST
══════════════════════════════
  ✅ Secrets NEVER hardcoded in Python
  ✅ Secrets NEVER in public config files
  ✅ .env.local GITIGNORED (safe)
  ✅ .env.production uses placeholders
  ✅ Streamlit Cloud manages prod secrets
  ✅ Paper trading used in dev
  ✅ Live trading in prod only
  ✅ Credentials loaded via config_env.py
  ✅ No secrets in GitHub Actions logs
  ✅ Security scan on every PR
  ✅ Bandit checks for security issues
  ✅ Safety checks for vulnerable deps
```

---

**Legend:**
- ✅ = Complete/Safe
- ✓ = Good/Verified
- ✗ = Not committed/Gitignored
- 🔒 = Encrypted/Secure
- ⭐ = Critical/Important
- ℹ️ = Information
- ⚠️ = Warning

**Last Updated:** January 19, 2026
