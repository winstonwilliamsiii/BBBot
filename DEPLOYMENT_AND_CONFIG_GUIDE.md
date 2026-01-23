# Bentley Budget Bot - Complete Deployment & Configuration

## 🎯 Quick Start for Teams

This guide consolidates everything needed to work with the Bentley Budget Bot across development and production environments.

### For Developers (Local Development)
```bash
# 1. Clone and setup
git clone https://github.com/your-org/BentleyBudgetBot.git
cd BentleyBudgetBot
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate      # macOS/Linux
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env.local
# Edit .env.local with your MySQL credentials

# 3. Initialize database (one-time)
python scripts/setup/init_trading_bot_db.py

# 4. Verify setup
python verify_trading_bot_fix.py

# 5. Run app
streamlit run streamlit_app.py
```

### For DevOps (Production Deployment)
```bash
# 1. Ensure main branch is ready
git log --oneline -1  # Verify latest commit

# 2. Go to Streamlit Cloud
# https://share.streamlit.io → New App → Connect GitHub

# 3. Configure Secrets (App Settings → Secrets)
# Add all DB_* variables and API keys

# 4. Initialize production database
python scripts/setup/init_trading_bot_db.py
# (with production DB_* environment variables)

# 5. Verify deployment
# Visit https://your-app.streamlit.app
# Check for "Database Connection Not Available" error
```

---

## 📚 Documentation Structure

### Core Configuration
| Document | Purpose | Audience |
|----------|---------|----------|
| [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) | All env vars reference | Everyone |
| [.env.example](.env.example) | Configuration template | Developers |
| [.env.development](.env.development) | Dev configuration | Developers |

### Deployment & Operations
| Document | Purpose | Audience |
|----------|---------|----------|
| [DEPLOYMENT.md](DEPLOYMENT.md) | How to deploy | Developers, DevOps |
| [PRODUCTION_CONFIG.md](PRODUCTION_CONFIG.md) | Production setup | DevOps, Ops |
| [.github/workflows/test.yml](.github/workflows/test.yml) | CI/CD pipeline | DevOps |
| [.github/workflows/deploy.yml](.github/workflows/deploy.yml) | Auto-deployment | DevOps |

### Feature-Specific
| Document | Purpose | Audience |
|----------|---------|----------|
| [TRADING_BOT_CONNECTION_FIX.md](TRADING_BOT_CONNECTION_FIX.md) | Trading Bot DB fix | Developers, DevOps |
| [TRADING_BOT_FIX_SUMMARY.md](TRADING_BOT_FIX_SUMMARY.md) | Quick summary | Everyone |

---

## 🔄 Environment Overview

### Development (localhost)
```
┌─────────────────────────────────────────┐
│ Developer Machine                       │
├─────────────────────────────────────────┤
│ ✓ .env.development (version-controlled) │
│ ✓ .env.local (machine-specific, ignored)│
│ ✓ Local MySQL (localhost:3306)          │
│ ✓ Streamlit on :8501                    │
└─────────────────────────────────────────┘
```

**Configuration Loading**:
1. `.env.local` (highest priority - machine-specific secrets)
2. `.env.development` (version-controlled defaults)
3. `.env` (fallback)
4. Hardcoded defaults (last resort)

### Production (Streamlit Cloud)
```
┌─────────────────────────────────────────┐
│ Streamlit Cloud                         │
├─────────────────────────────────────────┤
│ ✓ Secrets dashboard (no version control)│
│ ✓ Railway MySQL (cloud-hosted)          │
│ ✓ App auto-redeployed on main push      │
│ ✓ HTTPS enabled by default              │
└─────────────────────────────────────────┘
```

**Configuration Loading**:
1. Streamlit Secrets (highest priority - dashboard configured)
2. System environment variables
3. Hardcoded defaults (last resort)

---

## 🔑 Critical Variables (All Environments)

### Database Configuration (Required)
```
DB_HOST = localhost or RDS endpoint
DB_PORT = 3306 (default)
DB_USER = root or production user
DB_PASSWORD = your secure password (NEVER hardcode)
DB_NAME = bentley_bot_dev or bentley_bot_prod
```

### Environment Identifier (Required)
```
ENVIRONMENT = development or production
DEPLOYMENT_TARGET = localhost, docker, or streamlit-cloud
```

### Legacy MySQL Variables (Optional, for backward compatibility)
```
MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
(Use same values as DB_* if setting)
```

---

## 🚀 Deployment Workflow

### Developer Workflow
```
1. git checkout -b feature/my-feature
2. Make changes locally
3. Test: streamlit run streamlit_app.py
4. Verify: python verify_trading_bot_fix.py
5. Lint: flake8 pages/ frontend/
6. git push origin feature/my-feature
7. Create Pull Request on GitHub
   → GitHub Actions runs tests automatically
8. Code review & approval
9. Merge to main → Auto-deploys to production!
```

### GitHub Actions Workflow
```
PR Open:
  ├─ test.yml runs (linting, DB schema, env vars, security)
  └─ Status shows on PR

Merge to main:
  ├─ Full test suite runs
  ├─ deploy.yml triggers
  └─ Streamlit Cloud auto-redeployed (2-3 min)
```

---

## ✅ Pre-Deployment Checklist

### Code Quality
- [ ] Passes `flake8 pages/ frontend/`
- [ ] No hardcoded credentials
- [ ] Docstrings on complex functions
- [ ] Type hints added where appropriate

### Database
- [ ] Schema changes in `scripts/setup/init_trading_bot_db.py`
- [ ] Backward compatible (no breaking changes)
- [ ] Tested locally with `python scripts/setup/init_trading_bot_db.py`
- [ ] Verified with `python verify_trading_bot_fix.py`

### Configuration
- [ ] New env vars documented in `.env.example`
- [ ] `.env.local` contains no secrets
- [ ] `.env.development` has proper defaults
- [ ] Secrets configured in Streamlit Cloud (production)

### Git & Versioning
- [ ] Feature branch created from main
- [ ] Descriptive commit messages
- [ ] No `.env` files committed
- [ ] `requirements.txt` updated if dependencies changed

---

## 🔐 Security Best Practices

### DO ✅
- ✅ Use `.env.local` for development secrets (ignored by Git)
- ✅ Use Streamlit Cloud Secrets for production
- ✅ Commit `.env.example` (template with placeholders)
- ✅ Commit `.env.development` (safe, no secrets)
- ✅ Use strong passwords (16+ characters)
- ✅ Rotate credentials regularly

### DON'T ❌
- ❌ Commit `.env` or `.env.local` files
- ❌ Commit `.env.production` files
- ❌ Put passwords in comments
- ❌ Use test credentials in production
- ❌ Share secrets in pull requests
- ❌ Hardcode API keys in code

---

## 🛠️ Common Tasks

### Task: Add a New API Key
```
1. Decide if it's dev-only or prod-only
2. Add to `.env.example` with placeholder
3. Add to `.env.development` (if dev)
4. For production, add to Streamlit Secrets via dashboard
5. Use: api_key = os.getenv('YOUR_API_KEY')
6. Test locally, then deploy
```

### Task: Change Database
```
Development:
1. Update `.env.local` with new credentials
2. Run: python scripts/setup/init_trading_bot_db.py
3. Verify: python verify_trading_bot_fix.py
4. Test locally

Production:
1. Backup existing database
2. Set up new database with schema
3. Update Secrets in Streamlit Cloud dashboard
4. Monitor logs after deployment
```

### Task: Deploy Hotfix to Production
```
1. git checkout -b hotfix/issue-name
2. Make minimal fix
3. Test thoroughly locally
4. git push origin hotfix/issue-name
5. Create Pull Request (mark as "DO NOT MERGE to main" if sensitive)
6. Code review
7. Merge to main
8. Monitor deployment logs
9. Verify fix is live
```

---

## 📊 Environment Matrix

| Aspect | Development | Production |
|--------|-------------|-----------|
| **MySQL Host** | localhost:3306 | Railway endpoint |
| **Database** | bentley_bot_dev | bentley_bot_prod |
| **User** | root | bentley_prod_user |
| **Password** | root | [strong random] |
| **Config File** | .env.development | Streamlit Secrets |
| **SSL** | Not required | Required |
| **Backups** | Manual | Automatic (RDS) |
| **Monitoring** | Log files | Streamlit Cloud logs |

---

## 🔗 Quick Links

### Documentation
- [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) - Complete variable reference
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment procedures  
- [PRODUCTION_CONFIG.md](PRODUCTION_CONFIG.md) - Production setup
- [TRADING_BOT_CONNECTION_FIX.md](TRADING_BOT_CONNECTION_FIX.md) - Technical details

### Configuration Files
- [.env.example](.env.example) - Template
- [.env.development](.env.development) - Development defaults
- [.streamlit/config.toml](.streamlit/config.toml) - Streamlit settings

### Automation
- [.github/workflows/test.yml](.github/workflows/test.yml) - CI/CD testing
- [.github/workflows/deploy.yml](.github/workflows/deploy.yml) - Auto-deployment

### Setup Scripts
- [scripts/setup/init_trading_bot_db.py](scripts/setup/init_trading_bot_db.py) - Database initialization
- [verify_trading_bot_fix.py](verify_trading_bot_fix.py) - Connection verification
- [test_trading_bot_db.py](test_trading_bot_db.py) - Connection test

---

## ❓ FAQ

### Q: How do I add a new collaborator?
A: 
1. Invite to GitHub repository (Settings → Collaborators)
2. Have them follow "Developer Setup" section above
3. For production access: Add to Streamlit Cloud app (Settings → Collaborators)

### Q: How do I test production settings locally?
A:
```bash
# Create .env.prod-test with production-like config
DB_HOST=your-rds-host.amazonaws.com
DB_PORT=3306
# etc.

# Use it: Load .env.prod-test instead of .env.local
# But NEVER commit actual passwords!
```

### Q: What if the database connection fails in production?
A:
1. Check Streamlit Cloud logs
2. Verify Secrets are set correctly
3. Test manually: `mysql -u user -p -h host`
4. Check RDS security groups allow connection
5. Redeploy to refresh secrets

### Q: How do I rollback a bad deployment?
A:
```bash
git log --oneline
git revert <commit-hash>
git push origin main
# Streamlit Cloud auto-redeploys within 2-3 min
```

### Q: Can I use a local MySQL instead of RDS?
A:
Yes, but:
- Must be accessible from Streamlit Cloud
- Requires SSH tunnel or public IP
- Less reliable than managed RDS
- Recommended: Use RDS for production

---

## 📞 Support & Resources

### GitHub Actions Issues
See: `.github/workflows/test.yml` and `.github/workflows/deploy.yml`

### Database Configuration
See: [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) → Database Variables

### Deployment Issues
See: [DEPLOYMENT.md](DEPLOYMENT.md) → Troubleshooting

### Production Setup
See: [PRODUCTION_CONFIG.md](PRODUCTION_CONFIG.md) → Troubleshooting

---

## 🎓 Learning Resources

### For Developers
1. Read [DEPLOYMENT.md](DEPLOYMENT.md) - Understand the workflow
2. Review [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) - Know all config options
3. Check [.env.example](.env.example) - See what variables are available
4. Set up development environment following Quick Start above

### For DevOps/Ops
1. Read [PRODUCTION_CONFIG.md](PRODUCTION_CONFIG.md) - Complete setup guide
2. Review [.github/workflows/deploy.yml](.github/workflows/deploy.yml) - Understand automation
3. Set up Streamlit Cloud following "Production Deployment" section
4. Configure Railway MySQL following database setup steps

### For All
1. Review [TRADING_BOT_FIX_SUMMARY.md](TRADING_BOT_FIX_SUMMARY.md) - Understand the fix
2. Keep `.env.example` and `.gitignore` in sync with actual variables
3. Document any new environment variables
4. Follow the pre-deployment checklist before merging

---

## 📝 Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-22 | 1.0 | Initial documentation package |
| | | - Trading Bot DB connection fixed |
| | | - GitHub Actions workflows created |
| | | - Environment variable system implemented |
| | | - Complete deployment guide provided |
| | | - Production configuration documented |

---

**Last Updated**: January 22, 2026  
**Status**: ✅ Ready for Production  
**Maintained By**: Development Team
