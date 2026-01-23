# Deployment Guide

Complete step-by-step guide for deploying the Bentley Budget Bot to development and production environments.

## Table of Contents
1. [Initial Setup (Development)](#initial-setup-development)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Development Deployment](#development-deployment)
4. [Production Deployment](#production-deployment)
5. [GitHub Actions Workflow](#github-actions-workflow)
6. [Troubleshooting](#troubleshooting)
7. [Rollback Procedures](#rollback-procedures)

---

## Initial Setup (Development)

### Step 1: Clone Repository
```bash
# Clone the repository
git clone https://github.com/your-org/BentleyBudgetBot.git
cd BentleyBudgetBot

# Create feature branch
git checkout -b feature/your-feature-name
```

### Step 2: Set Up Python Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
```bash
# Copy template
cp .env.example .env.development  # Already exists

# Create machine-specific file
cp .env.example .env.local

# Edit .env.local with YOUR credentials
# Windows
notepad .env.local

# macOS/Linux
nano .env.local
```

**Minimal .env.local for development**:
```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=bentley_bot_dev
```

### Step 5: Initialize Database
```bash
# Run one-time database setup
python scripts/setup/init_trading_bot_db.py

# Verify
python verify_trading_bot_fix.py
```

Expected output:
```
✅ Trading Bot Database Ready!
   - bot_status: 0 records
   - trading_signals: 0 records
   - trades_history: 0 records
   - performance_metrics: 0 records
```

### Step 6: Test Local Setup
```bash
# Run linting
flake8 pages/ frontend/

# Run tests (if available)
pytest tests/ -v

# Start Streamlit
streamlit run streamlit_app.py
```

Open browser to: `http://localhost:8501`

---

## Pre-Deployment Checklist

### Code Quality
- [ ] Code follows PEP 8 style guide
- [ ] No hardcoded credentials
- [ ] All imports are used
- [ ] No console print statements (use logging)
- [ ] Type hints added to functions
- [ ] Docstrings written for complex functions

### Database Changes
- [ ] All schema changes are in `scripts/setup/init_trading_bot_db.py`
- [ ] Backward compatible (no breaking changes)
- [ ] Migration script tested locally
- [ ] New tables have appropriate indexes
- [ ] Foreign keys properly defined

### Configuration
- [ ] All new environment variables documented in `.env.example`
- [ ] `.env.local` contains no secrets
- [ ] Sensitive files in `.gitignore`
- [ ] Default values appropriate for environment

### Testing
- [ ] Unit tests pass: `pytest tests/ -v`
- [ ] Linting passes: `flake8 pages/ frontend/`
- [ ] Database initialization passes
- [ ] Feature tested locally in all related pages
- [ ] No database errors in logs

### Git & Version Control
- [ ] Feature branch created from `main` or `develop`
- [ ] Commit messages are descriptive
- [ ] No `.env` files committed
- [ ] No dependencies removed without updating `requirements.txt`
- [ ] Changelog updated if applicable

---

## Development Deployment

### Local Development Workflow

```bash
# 1. Create feature branch
git checkout -b fix/trading-bot-db-connection

# 2. Make changes
# ... edit files ...

# 3. Test locally
streamlit run streamlit_app.py

# 4. Verify database connection
python verify_trading_bot_fix.py

# 5. Run linting & tests
flake8 pages/ frontend/
pytest tests/ -v

# 6. Commit changes
git add pages/05_🤖_Trading_Bot.py .env.development scripts/
git commit -m "fix: use environment variables for Trading Bot DB connection

- Updated database configuration to use env variables
- Created database initialization script
- Fixed SQL reserved keyword issue (signal -> signal_type)
- Added connection pooling for reliability"

# 7. Push to remote
git push origin fix/trading-bot-db-connection

# 8. Create Pull Request on GitHub
# GitHub Actions automatically runs:
#   - Linting checks
#   - Database schema validation
#   - Environment variable verification
#   - Unit tests
```

### Monitor GitHub Actions
```
PR Check Results:
├── ✅ Lint & Code Quality
├── ✅ Validate Database Schema
├── ✅ Verify Environment Variables
├── ✅ Run Unit Tests
└── ✅ Security Check
```

### Code Review & Merge
```bash
# After approval, merge to main
git checkout main
git pull origin main
git merge --no-ff fix/trading-bot-db-connection
git push origin main

# GitHub Actions automatically:
# 1. Runs full test suite
# 2. Deploys to Streamlit Cloud (production)
# 3. Creates deployment summary
```

---

## Production Deployment

### Prerequisite: Streamlit Cloud Setup

#### Step 1: Connect GitHub Repository
1. Go to: https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New App"
4. Select repository: `BentleyBudgetBot`
5. Select branch: `main`
6. Set main file: `streamlit_app.py`

#### Step 2: Configure Secrets in Dashboard
1. Go to: **App Settings** → **Secrets**
2. Add production configuration:
```toml
# Database Configuration
DB_HOST = "your-rds-instance.us-east-1.rds.amazonaws.com"
DB_PORT = "3306"
DB_USER = "bentley_prod_user"
DB_PASSWORD = "your_super_secure_password"
DB_NAME = "bentley_bot_prod"

# API Keys
DEEPSEEK_API_KEY = "your-production-key"
ALPACA_API_KEY = "your-production-key"
ALPACA_SECRET_KEY = "your-production-secret"

# Environment
ENVIRONMENT = "production"
DEPLOYMENT_TARGET = "streamlit-cloud"
```

#### Step 3: Verify Production Database
```bash
# SSH into production MySQL (if applicable)
ssh your-db-server

# Create production database
mysql -u root -p
CREATE DATABASE bentley_bot_prod;
EXIT;

# Initialize schema
python scripts/setup/init_trading_bot_db.py
# (with production env vars set)

# Verify tables
mysql -u root -p bentley_bot_prod -e "SHOW TABLES;"
```

### Deployment Process

#### Automatic Deployment (via GitHub Actions)
```
Developer merges to main
        ↓
GitHub Actions triggered
        ↓
├─ Run tests
├─ Validate schema
└─ Deploy to Streamlit Cloud
        ↓
Streamlit rebuilds & restarts app
        ↓
✅ Live within 2-3 minutes
```

#### Manual Deployment (if needed)
```bash
# On your local machine
git checkout main
git pull origin main

# Run final verification
python verify_trading_bot_fix.py

# Streamlit Cloud auto-detects changes from GitHub
# No manual deployment needed!
```

### Verification Steps
```bash
# 1. Wait 2-3 minutes for deployment
# 2. Visit https://your-app-url.streamlit.app/
# 3. Navigate to Trading Bot tab
# 4. Verify no "Database Connection Not Available" message
# 5. Check logs for any errors:
#    App Settings → Manage Repo → View Logs
```

---

## GitHub Actions Workflow

### Trigger Events

```yaml
# Triggers:
# 1. Pull Requests to main/develop
# 2. Pushes to main/develop
# 3. Changes to specific files:
#    - pages/**
#    - frontend/**
#    - sites/**
#    - .env.development
#    - requirements.txt
#    - scripts/**
```

### Workflow Jobs (test.yml)

```
┌─────────────────────────────────────────┐
│ Lint & Code Quality                     │
├─────────────────────────────────────────┤
│ ✓ flake8 style check                    │
│ ✓ isort import sorting                  │
│ ✓ black code formatting                 │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Validate Database Schema                │
├─────────────────────────────────────────┤
│ ✓ Start MySQL service                   │
│ ✓ Run init script                       │
│ ✓ Verify all tables created             │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Verify Environment Variables            │
├─────────────────────────────────────────┤
│ ✓ Check .env.example exists             │
│ ✓ Verify required vars documented       │
│ ✓ Ensure .gitignore correct             │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Run Unit Tests                          │
├─────────────────────────────────────────┤
│ ✓ pytest tests/                         │
│ ✓ Generate coverage report              │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Security Check                          │
├─────────────────────────────────────────┤
│ ✓ No exposed secrets                    │
│ ✓ No hardcoded credentials              │
└─────────────────────────────────────────┘
```

### Deployment Workflow (deploy.yml)

Triggered only on merge to `main`:

```
Pre-Deployment Validation
        ↓
Validate schema syntax
        ↓
Check deployment requirements
        ↓
Deploy to Streamlit Cloud
        ↓
Post-Deployment Verification
        ↓
Create deployment summary
        ↓
✅ Deployment Complete
```

---

## Troubleshooting

### Issue: GitHub Actions Test Fails

**Problem**: Linting test fails
```
flake8: line 86 has trailing whitespace
```

**Solution**:
```bash
# Fix automatically
black pages/ frontend/
isort pages/ frontend/

# Commit and push
git add .
git commit -m "style: fix formatting"
git push
```

---

### Issue: Database Schema Test Fails

**Problem**: 
```
ERROR: test_bentley_bot database already exists
```

**Solution**:
```bash
# The test creates a clean database each run
# This is expected - GitHub Actions cleans up automatically
# If failing locally:
mysql -u root -p -e "DROP DATABASE IF EXISTS test_bentley_bot;"
python scripts/setup/init_trading_bot_db.py
```

---

### Issue: Streamlit Cloud App Crashes After Merge

**Problem**: 
```
App crashed with: ModuleNotFoundError: No module named 'sqlalchemy'
```

**Solution**:
1. Check `requirements.txt` has all dependencies
2. Run locally: `pip install -r requirements.txt`
3. If module still missing, add to `requirements.txt`:
   ```bash
   pip freeze | grep sqlalchemy >> requirements.txt
   git add requirements.txt
   git commit -m "fix: add missing dependency"
   git push
   ```

---

### Issue: Secrets Not Loading in Production

**Problem**: 
```
Database connection failed: (pymysql.err.OperationalError) (1045, "Access denied")
```

**Solution**:
1. Go to Streamlit Cloud dashboard
2. Check **App Settings** → **Secrets**
3. Verify `DB_PASSWORD` and other credentials
4. Test connection locally with same credentials
5. If still failing, rotate credentials and update Secrets

---

### Issue: Database Connection Timeout

**Problem**: 
```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")
```

**Solution** (Production):
1. Verify RDS instance is running
2. Check security groups allow connection
3. Verify `DB_HOST` is correct RDS endpoint
4. Test SSH tunnel if using one

**Solution** (Development):
1. Ensure MySQL running: `mysql --version`
2. Check port: `netstat -an | grep 3306`
3. Restart MySQL service
4. Verify `.env.development` has correct port

---

## Rollback Procedures

### Rollback in Production

#### Option 1: Revert Commit (Recommended)
```bash
# On your machine
git log --oneline  # Find commit to revert
git revert abc123  # Create new commit undoing changes
git push origin main

# Streamlit Cloud automatically redeployed within 2-3 minutes
```

#### Option 2: GitHub Revert Button
```
GitHub Dashboard → Pull Requests → Closed
→ Select merged PR → Revert → Confirm
```

#### Option 3: Manual Secrets Restoration
```
Streamlit Cloud → App Settings → Secrets
→ Restore from backup or revert values
```

### Rollback in Development

```bash
# Discard changes
git checkout HEAD -- .env.development pages/

# Hard reset to previous state
git reset --hard origin/main

# Restart app
# (Streamlit hot-reloads if you change files directly)
```

### Rollback Database Changes

```bash
# If schema change broke app:

# 1. Identify last working schema version
git log --oneline scripts/setup/init_trading_bot_db.py

# 2. Restore old version
git checkout <old-commit> -- scripts/setup/init_trading_bot_db.py

# 3. Re-initialize database
mysql -u root -p bentley_bot_dev < backup.sql
# OR
python scripts/setup/init_trading_bot_db.py  # with old schema
```

---

## Deployment Checklist

### Before Merging to Main
- [ ] All tests pass locally
- [ ] No linting errors
- [ ] Database changes tested
- [ ] No hardcoded credentials
- [ ] `.env.example` updated with new variables
- [ ] Feature branch is up to date with main

### Before Production Merge
- [ ] Code review approved
- [ ] All GitHub Actions checks passed
- [ ] Production database backups created
- [ ] Secrets configured in Streamlit Cloud
- [ ] Team notified of deployment

### After Deployment
- [ ] App loads without errors
- [ ] Database connection works
- [ ] All features functional
- [ ] No console errors in browser
- [ ] Performance acceptable

---

## Related Documentation
- [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) - All configuration options
- [PRODUCTION_CONFIG.md](PRODUCTION_CONFIG.md) - Production environment setup
- [.github/workflows/test.yml](.github/workflows/test.yml) - Test workflow
- [.github/workflows/deploy.yml](.github/workflows/deploy.yml) - Deploy workflow
