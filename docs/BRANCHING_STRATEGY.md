# Bentley Budget Bot - Branching Strategy & Development Workflow

## Overview

This document describes the multi-environment development strategy for Bentley Budget Bot with separated development and production deployments.

---

## 🏗️ Architecture

### Branch Structure

```
main/               → Production Branch (Streamlit Cloud)
  ↑
  │ (PR with automated tests)
  │
dev/                → Development Branch (localhost - Moor Kingdom)
  ↑
  │ (PR with feature development)
  │
feature/*           → Experimental Features (isolated work)
```

### Environment Separation

| Aspect | **Development** | **Production** |
|--------|-----------------|----------------|
| **Location** | Localhost (127.0.0.1) | Streamlit Cloud |
| **Machine** | Moor Kingdom Laptop | Cloud Environment |
| **Python Version** | Flexible (3.10+) | Fixed (3.10) |
| **Database** | Local MySQL (dev_*) | Cloud MySQL (production_*) |
| **API Keys** | Paper Trading / Dev | Live Trading / Prod |
| **Logging** | DEBUG | INFO |
| **Cache** | Disabled | Enabled |
| **Features** | All (experimental enabled) | Stable only |

---

## 🚀 Getting Started

### 1. Setup Development Environment (Moor Kingdom)

```bash
# Clone repository
git clone https://github.com/winstonwilliamsiii/BBBot.git
cd BentleyBudgetBot

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1  # PowerShell on Windows
# or
source .venv/bin/activate     # bash on Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Local Environment

```bash
# Copy template to local config
cp .env.local.template .env.local

# Edit with your machine-specific settings
# Windows: notepad .env.local
# Mac/Linux: nano .env.local
```

**Required settings in `.env.local`:**
```env
ENVIRONMENT=development
DB_PASSWORD=your_local_mysql_password
ALPACA_API_KEY=your_paper_trading_key
ALPACA_SECRET_KEY=your_paper_trading_secret
UPLOAD_DIRECTORY=C:\Users\winst\BentleyBudgetBot\uploads_dev
```

### 3. Create Local Directories

```bash
# Create development directories
mkdir -p uploads_dev logs_dev data_dev
```

### 4. Run Local Development

```bash
# Load development environment
$env:ENVIRONMENT = "development"

# Run Streamlit app
streamlit run streamlit_app.py
```

---

## 📋 Workflow: Feature Development

### Scenario: Adding a New Dashboard Widget

#### Step 1: Create Feature Branch

```bash
# Update dev branch
git checkout dev
git pull origin dev

# Create feature branch from dev
git checkout -b feature/new-dashboard-widget
```

**Branch naming convention:**
- `feature/user-dashboard` - New feature
- `fix/portfolio-loading-bug` - Bug fix
- `docs/api-documentation` - Documentation
- `perf/optimize-queries` - Performance improvement

#### Step 2: Develop on Localhost

```bash
# Ensure development environment
echo "ENVIRONMENT=development" >> .env.local

# Start developing
streamlit run streamlit_app.py

# Test with local data
# - Upload portfolio CSV
# - Verify features work
# - Check console for errors
```

#### Step 3: Commit Changes

```bash
# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat(dashboard): add new portfolio summary widget"
```

**Conventional commit format:**
```
type(scope): description

[optional body]
[optional footer]
```

Types: `feat`, `fix`, `docs`, `perf`, `refactor`, `test`, `ci`, `chore`

#### Step 4: Push & Create Pull Request

```bash
# Push feature branch
git push origin feature/new-dashboard-widget
```

Then create PR to `dev` branch on GitHub:
- **Title:** Follow conventional commits
- **Description:** What changed and why
- **Testing:** How to verify the changes

#### Step 5: Merge to Dev

Once PR is approved and tests pass:

```bash
# Merge via GitHub UI or command line
git checkout dev
git pull origin dev
git merge feature/new-dashboard-widget
git push origin dev
```

---

## 🔄 Workflow: Dev → Production Promotion

### When Ready for Production

#### Step 1: Create Release PR (dev → main)

```bash
# Ensure dev is up to date
git checkout dev
git pull origin dev

# Create PR to main
# GitHub will automatically run validation checks:
# ✓ Full test suite
# ✓ Security audit
# ✓ Production environment validation
# ✓ Deployment simulation
```

#### Step 2: Automated Checks Run

The `.github/workflows/dev-to-main.yml` workflow validates:

- **Pre-merge Checks**
  - Full pytest suite passes
  - Flake8 linting passes
  - Environment configuration valid

- **Branch Validation**
  - PR title follows conventional commits
  - PR description is detailed
  - Changelog is updated

- **Security Audit**
  - Bandit security scan
  - No exposed API keys
  - Safety check for vulnerable dependencies

- **Production Readiness**
  - `.env.production` properly configured
  - All critical files present
  - Deployment simulation successful

#### Step 3: Review & Merge

```bash
# GitHub shows ✓ or ❌ for each check
# Review changes in PR
# Request approvals if needed
# Merge to main
```

#### Step 4: Production Deployment

Automatically triggered when merged to `main`:
- ✓ Tests run on `main` branch
- ✓ Code deploys to Streamlit Cloud
- ✓ Health checks verify deployment
- ✓ Monitoring alerts configured

---

## 🔧 Environment Configuration Files

### `.env.development` (Committed to Repo)

Contains **non-sensitive** development defaults:

```env
ENVIRONMENT=development
DEPLOYMENT_TARGET=localhost
DB_HOST=localhost
DB_PORT=3306
YFINANCE_BATCH_SIZE=10
ALPACA_ENVIRONMENT=paper
LOG_LEVEL=DEBUG
DEBUG_MODE=true
```

### `.env.production` (Committed to Repo)

Contains **non-sensitive** production settings:

```env
ENVIRONMENT=production
DEPLOYMENT_TARGET=streamlit_cloud
STREAMLIT_LOGGER_LEVEL=info
LOG_LEVEL=INFO
DEBUG_MODE=false
ENABLE_EXPERIMENTAL_FEATURES=false
```

### `.env.local` (Gitignored - Machine Specific)

Contains **sensitive** credentials and machine paths:

```env
# Database
DB_PASSWORD=your_local_password

# API Keys (Paper trading)
ALPACA_API_KEY=pk_test_...
ALPACA_SECRET_KEY=sk_test_...

# Paths
UPLOAD_DIRECTORY=C:\Users\winst\uploads_dev
```

### Configuration Precedence

```
Priority (Highest to Lowest):
1. .env.local          ← Machine-specific overrides (gitignored)
2. .env.{ENVIRONMENT}  ← Environment-specific config
3. .env                ← Base defaults
```

---

## 🐛 Development Tips

### Running Tests Locally

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_portfolio.py -v
```

### Checking Environment

```python
# In your Python code
from config_env import config

print(f"Environment: {config.get('ENVIRONMENT')}")
print(f"Is Development: {config.is_development()}")
print(f"Is Production: {config.is_production()}")
print(f"Database Host: {config.get('DB_HOST')}")
```

### Reloading Configuration

In Streamlit app:

```python
from config_env import reload_env

if st.button("🔄 Reload Config"):
    reload_env()
    st.rerun()
```

### Local MySQL Setup

```bash
# Start MySQL (Docker recommended)
docker run -d \
  --name bentley-bot-dev-mysql \
  -e MYSQL_ROOT_PASSWORD=dev_password \
  -e MYSQL_DATABASE=bentley_bot_dev \
  -p 3306:3306 \
  mysql:8.0

# Connect
mysql -h localhost -u root -p bentley_bot_dev
```

---

## 📊 GitHub Actions Workflows

### Workflow Files

1. **`dev-test.yml`** - Runs on every `dev` push
   - Tests on Python 3.10 & 3.11
   - Linting (flake8, black, isort)
   - Dependency security checks
   - Environment validation

2. **`dev-to-main.yml`** - Runs on PR to `main`
   - Pre-merge comprehensive tests
   - Branch & PR validation
   - Security audit
   - Production readiness check
   - Deployment simulation

3. **`prod-deploy.yml`** - Runs on `main` push
   - Final production validation
   - Deploys to Streamlit Cloud
   - Post-deployment health check

4. **`feature-test.yml`** - Runs on `feature/*` branches
   - Basic linting & testing
   - Encourages PR to `dev`

### Monitoring Workflow Status

Visit: **GitHub → Actions → [Workflow Name]**

View logs for each step to diagnose failures.

---

## 🚨 Common Issues & Solutions

### Issue: "Connection refused" on localhost

**Solution:** Ensure MySQL is running locally
```bash
# Docker check
docker ps | grep mysql

# Local MySQL check
mysql -u root -p
```

### Issue: Import errors for development-only modules

**Solution:** Install all dependencies
```bash
pip install -r requirements.txt
```

### Issue: Environment variables not loading

**Solution:** Check precedence and file location
```bash
# Verify .env.local exists and has correct content
cat .env.local

# Reload in Python
from config_env import reload_env
reload_env()
```

### Issue: Tests fail locally but pass on GitHub

**Solution:** Ensure same Python version
```bash
python --version  # Should be 3.10+

# Or use pyenv
pyenv install 3.10.0
pyenv local 3.10.0
```

---

## 🔐 Security Best Practices

1. **Never commit `.env.local`** - Already in `.gitignore`
2. **Never hardcode API keys** in Python files
3. **Use `.env.local.template`** to show required variables
4. **Rotate credentials regularly** - Especially Alpaca keys
5. **Keep secrets in Streamlit Cloud** - Use Secrets UI
6. **Review PR changes** before merging to main

---

## 📞 Support & Troubleshooting

### Quick Debug Checklist

- [ ] Python version 3.10+: `python --version`
- [ ] Virtual environment activated: `.venv\Scripts\Activate.ps1`
- [ ] Dependencies installed: `pip list | grep streamlit`
- [ ] `.env.local` configured: `cat .env.local | head -5`
- [ ] MySQL running: `docker ps`
- [ ] Ports available: `netstat -ano | findstr :8501`

### Contact

For issues or questions about the branching strategy, create an issue in GitHub with the `documentation` or `infrastructure` label.

---

## 📝 Changelog

### v1.0 - Initial Setup
- Created dev/main/feature branching strategy
- Implemented environment-specific configuration
- Set up GitHub Actions CI/CD workflows
- Added comprehensive documentation
