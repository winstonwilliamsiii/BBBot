# Git Flow Quick Reference

## Your New Workflow Structure

```
PRODUCTION (main)
    ↑
    | PR Review + Status Checks
    ↑
STAGING (dev) ← Current: f99fabc9 ✅
    ↑
    | PR + Testing
    ↑
FEATURES (Choose your path)
    ├─ feature/bot_dev ← MT5/Trading work
    └─ feature/Plaid ← Bank integration work
```

---

## Quick Commands

### Start Development

```bash
# Get latest code
git fetch origin
git checkout dev
git pull origin dev

# Create your work branch (e.g., Plaid feature)
git checkout -b feature/Plaid/link-integration

# Make changes, test with .env.development
# Then:
git add .
git commit -m "feat: add Plaid Link component"
git push origin feature/Plaid/link-integration

# Create PR on GitHub: your branch → feature/Plaid
```

### After Review & Approval

```bash
# Merge to feature branch (on GitHub or local)
# Then PR: feature/Plaid → dev

# After dev approval, PR: dev → main
# Auto-deploys to production ✅
```

---

## Key Branches NOW

| Branch | Purpose | Status |
|--------|---------|--------|
| `main` | **PRODUCTION** | fc4bb5f8 - Do NOT push directly |
| `dev` | **STAGING** | f99fabc9 - PR-only, must be current |
| `feature/bot_dev` | MT5/Alpaca trading | 2030d0c0 - Ready |
| `feature/Plaid` | Bank connection | f99fabc9 - Ready |

---

## Protection Rules (GitHub Settings)

### Main Branch
- ✅ Require pull request reviews (1+ reviewers)
- ✅ Require status checks to pass
- ✅ Restrict who can push (admin only)

### Dev Branch
- ✅ Require pull request reviews
- ✅ No direct pushes allowed

---

## DO's & DON'Ts

✅ **DO**
- Always `git pull origin dev` before starting
- Create feature sub-branches (e.g., `feature/Plaid/link-integration`)
- Write descriptive commit messages
- Test locally before pushing
- Use PRs for all changes

❌ **DON'T**
- Push directly to main (except emergencies)
- Force-push to main or dev
- Mix features in one branch
- Commit broken code
- Ignore failing status checks

---

## Environment Usage

```bash
# Local development
cp .env.development .env.local
# Edit .env.local with your local settings
streamlit run streamlit_app.py

# Production secrets are in Streamlit Cloud secrets (not committed)
# .env.production is template only
```

---

## Full Workflow Doc

See `GIT_FLOW_WORKFLOW.md` for comprehensive guide with:
- Detailed feature development steps
- Merge conflict resolution
- Emergency hotfixes
- Reverting changes
- Troubleshooting

---

## Current Status ✅

- ✅ Dev branch reset and current (f99fabc9)
- ✅ feature/bot_dev synced (2030d0c0)
- ✅ feature/Plaid created (f99fabc9)
- ✅ .env.development updated with MT5 settings
- ✅ .env.production enhanced with MT5/Railway config
- ✅ Git Flow documentation added

**You're ready to start feature development!**

---

## First Steps

1. **Switch to dev**: `git checkout dev && git pull origin dev`
2. **Pick your feature**: `feature/bot_dev` or `feature/Plaid`
3. **Create work branch**: `git checkout -b feature/Plaid/your-feature-name`
4. **Test locally**: `streamlit run streamlit_app.py`
5. **Commit & push**: `git push origin feature/Plaid/your-feature-name`
6. **Create PR** on GitHub

Questions? See `GIT_FLOW_WORKFLOW.md`

---

**Setup Date**: January 30, 2026  
**Status**: Production-Ready ✅
