# Quick Reference: Development Workflow Cheat Sheet

## 🚀 Quick Commands

### Initial Setup (Moor Kingdom)
```bash
# Clone & setup
git clone https://github.com/winstonwilliamsiii/BBBot.git
cd BentleyBudgetBot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configure local environment
cp .env.local.template .env.local
# Edit .env.local with your credentials
notepad .env.local

# Create directories
mkdir uploads_dev, logs_dev, data_dev

# Start MySQL (Docker)
docker run -d --name bentley-bot-dev-mysql -e MYSQL_ROOT_PASSWORD=dev_password -e MYSQL_DATABASE=bentley_bot_dev -p 3306:3306 mysql:8.0

# Run app
streamlit run streamlit_app.py
```

---

## 🌳 Branch Commands

### Working with Branches
```bash
# View all branches
git branch -a

# Switch to dev (development)
git checkout dev
git pull origin dev

# Create feature branch
git checkout -b feature/your-feature-name

# Commit with conventional message
git commit -m "feat(scope): description"
# Types: feat, fix, docs, perf, refactor, test, ci, chore

# Push to GitHub
git push origin feature/your-feature-name

# Create PR via GitHub UI
# Then merge after approval
```

---

## 📋 Branch Strategy Quick Reference

```
┌─ FEATURE BRANCH ──────────────────────┐
│ feature/dashboard-widget              │
│ → Tests run automatically             │
│ → Create PR to dev                    │
└─────────────────────────────────────┬─┘
                                       │
┌───────────────────────────────────────┘
│ ↓
│ DEV BRANCH (Development)
├─ Localhost/Moor Kingdom
├─ Paper trading (Alpaca)
├─ MySQL: bentley_bot_dev
├─ Tests run on every push
│ ↓ (When ready for production)
│ Create PR to main
│
└──────────────────────────────────────┬─
                                       │
┌───────────────────────────────────────┘
│ ↓
│ VALIDATION GATES (Auto-checks)
├─ Full test suite
├─ Security audit
├─ Production config check
├─ Deployment simulation
│ ↓ (All pass?)
│ Merge to main
│
└──────────────────────────────────────┬─
                                       │
┌───────────────────────────────────────┘
│ ↓
│ MAIN BRANCH (Production)
├─ Streamlit Cloud
├─ Live trading (Alpaca)
├─ MySQL: bentley_bot_production
├─ Auto-deploys to https://bbbot305.streamlit.app
└─────────────────────────────────────────
```

---

## 🔧 Environment Variables Quick Lookup

### Development (.env.local on Moor Kingdom)
```env
ENVIRONMENT=development
DB_HOST=localhost
DB_PASSWORD=your_mysql_password
ALPACA_API_KEY=your_paper_key
ALPACA_SECRET_KEY=your_paper_secret
ALPACA_ENVIRONMENT=paper
LOG_LEVEL=DEBUG
```

### Production (Streamlit Cloud Secrets)
```
ENVIRONMENT=production
ALPACA_ENVIRONMENT=live
LOG_LEVEL=INFO
(All credentials set in Streamlit UI)
```

---

## 📊 GitHub Actions Workflows

| Workflow | Trigger | What It Does |
|----------|---------|-------------|
| **dev-test.yml** | Push to `dev` | Lint, test on Python 3.10/3.11, security checks |
| **dev-to-main.yml** | PR to `main` | Pre-merge validation: tests, security, production check |
| **prod-deploy.yml** | Push to `main` | Deploy to Streamlit Cloud, health checks |
| **feature-test.yml** | Push to `feature/*` | Basic linting and testing |

**Check Status:** GitHub → Actions → [Workflow] → See ✅ or ❌

---

## 🐛 Troubleshooting Checklist

```
❓ Error running app?
□ Virtual environment activated: .\.venv\Scripts\Activate.ps1
□ Requirements installed: pip install -r requirements.txt
□ .env.local configured: cat .env.local | head

❓ Database connection error?
□ MySQL running: docker ps | grep mysql
□ Credentials correct: DB_USER, DB_PASSWORD in .env.local
□ Port available: netstat -ano | findstr :3306

❓ Config not loading?
□ .env.local exists
□ ENVIRONMENT=development set
□ Python code: from config_env import config; print(config.get('ENVIRONMENT'))

❓ Tests failing on GitHub?
□ Local tests pass: pytest
□ Python 3.10+: python --version
□ All dependencies: pip list | grep streamlit

❓ API errors?
□ Paper trading enabled (dev): ALPACA_ENVIRONMENT=paper
□ Correct credentials in .env.local
□ API keys not expired
```

---

## 🚀 Common Workflows

### Adding a Feature

```bash
# 1. Get latest dev code
git checkout dev
git pull origin dev

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Make changes & test locally
# (Edit code, run app: streamlit run streamlit_app.py)

# 4. Commit with conventional message
git add .
git commit -m "feat(scope): description of change"

# 5. Push & create PR
git push origin feature/my-feature
# → Create PR on GitHub to dev branch

# 6. Merge after review
# (Automated tests run on GitHub)
```

### Promoting to Production

```bash
# 1. Ensure dev is updated
git checkout dev
git pull origin dev

# 2. Create PR to main on GitHub
# (GitHub shows validation gates)

# 3. Review & merge
# (Automatically deploys to Streamlit Cloud)

# 4. Verify deployment
# https://bbbot305.streamlit.app
```

### Reloading Configuration in Development

```python
from config_env import reload_env
reload_env()
# Now all new env variables are loaded
```

---

## 📞 Quick Links

- **Branching Guide:** [BRANCHING_STRATEGY.md](BRANCHING_STRATEGY.md)
- **Environment Setup:** [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md)
- **Implementation Details:** [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)
- **GitHub Repository:** https://github.com/winstonwilliamsiii/BBBot
- **Production App:** https://bbbot305.streamlit.app

---

## 🎯 Key Points to Remember

✅ **Always work on features in feature branches**
✅ **Dev branch = localhost, main branch = production**
✅ **Use conventional commit messages** (feat, fix, etc.)
✅ **GitHub Actions validates automatically**
✅ **Paper trading on dev, live trading on main**
✅ **Never commit .env.local** (it's gitignored)
✅ **Check GitHub Actions logs** if tests fail
✅ **Ask questions in repo issues** with environment details

---

**Last Updated:** January 19, 2026
