# Git Flow Workflow - Bentley Budget Bot

## Overview

This project uses **Git Flow** for branch management with three primary branches:

```
main (PRODUCTION)
├─ dev (STAGING/INTEGRATION)
│   ├─ feature/bot_dev (MT5 & Trading Features)
│   └─ feature/Plaid (Bank Integration)
└─ [hotfixes branch if needed]
```

---

## Branch Responsibilities

### 📌 `main` (PRODUCTION)
- **Purpose**: Production-ready code only
- **Status**: Stable, tested, deployed to Streamlit Cloud + Railway
- **Protection**: 
  - Requires PR review (1 reviewer minimum)
  - Requires status checks to pass
  - Only admins can push directly (emergency hotfixes only)
- **Deployment**: Automatic to Streamlit Cloud on merge
- **Current**: 73 commits ahead of old `dev` branch (with MT5 REST API + Docker + Railway)

### 🔄 `dev` (STAGING/INTEGRATION)
- **Purpose**: Integration branch for feature testing before production
- **Status**: Latest development code; **must be ≤2 commits behind main**
- **Protection**:
  - No direct pushes; PR-only
  - Must pass all tests
- **Workflow**: Feature branches → PRs to `dev` → Tested → Merged
- **Reset**: Jan 30, 2025 - Reset to match `main` (commit fc4bb5f8)
- **Deployment**: Deployed to staging server (optional) or tested locally

### ✨ Feature Branches

#### `feature/bot_dev` (MT5 & Trading Bot Features)
- **Purpose**: Develop and test MT5/Alpaca/trading functionality
- **Base**: `dev` branch
- **Workflow**:
  1. Create feature branches OFF `feature/bot_dev` for specific features
  2. Test locally with `.env.development`
  3. Create PR to `feature/bot_dev`
  4. Review + test
  5. Merge to `feature/bot_dev`
  6. When ready: PR from `feature/bot_dev` → `dev`
  7. Final: PR from `dev` → `main` for production release
- **Current**: Synced with dev (commit 2030d0c0)
- **Status**: Ready for MT5 REST API enhancements

#### `feature/Plaid` (Bank Integration)
- **Purpose**: Develop Plaid bank connection features
- **Base**: `dev` branch
- **Workflow**: Same as `feature/bot_dev` (see above)
- **Created**: Jan 30, 2025
- **Status**: Ready for Plaid work
- **Note**: Works independently from bot_dev; combine later if both ready

---

## Workflow: Developing a Feature

### 1️⃣ Get Latest Dev Code

```bash
git fetch origin
git checkout dev
git pull origin dev
```

### 2️⃣ Create Feature Sub-Branch (Off Feature/Plaid or feature/bot_dev)

For Plaid work:
```bash
git checkout feature/Plaid
git checkout -b feature/Plaid/link-integration    # e.g., specific Plaid feature
```

For MT5 work:
```bash
git checkout feature/bot_dev
git checkout -b feature/bot_dev/rest-api-health-checks  # specific MT5 feature
```

### 3️⃣ Develop & Test Locally

```bash
# Update .env.development with your local settings
# Run Streamlit locally
streamlit run streamlit_app.py

# Verify no regressions
# Test the specific feature thoroughly
```

### 4️⃣ Commit & Push

```bash
git add .
git commit -m "feat: [descriptive message about what was added/fixed]"
git push origin feature/Plaid/link-integration
```

### 5️⃣ Create Pull Request

**On GitHub**:
1. Go to Pull Requests tab
2. Click "New Pull Request"
3. Compare: `feature/Plaid/link-integration` → `feature/Plaid` (or `feature/bot_dev`)
4. Write clear description of changes
5. Request review
6. Wait for status checks + review

### 6️⃣ Merge to Main Feature Branch

```bash
# After approval, GitHub UI handles merge OR local:
git checkout feature/Plaid
git merge feature/Plaid/link-integration
git push origin feature/Plaid
```

### 7️⃣ PR to Dev (When Feature Complete)

```bash
# On GitHub: PR from feature/Plaid → dev
# After review and testing: MERGE
```

### 8️⃣ PR to Main (Release Ready)

```bash
# On GitHub: PR from dev → main
# After final review and validation: MERGE
# Automatically deploys to production
```

---

## Environment Variables

### Local Development (`.env.development`)
```env
ENVIRONMENT=development
DEPLOYMENT_TARGET=localhost
DB_HOST=localhost
MT5_USER=dev_mt5_account
MT5_PASSWORD=dev_mt5_password
ALPACA_ENVIRONMENT=paper
PLAID_ENVIRONMENT=sandbox
RAILWAY_PROJECT_NAME=bentley_mt5_bridge
RAILWAY_PROJECT_ID=c061b9e1-f140-472f-9f00-ffb6478cdc8d
```

### Production (`.env.production`)
```env
ENVIRONMENT=production
DEPLOYMENT_TARGET=streamlit_cloud
DB_HOST=*** SET IN STREAMLIT CLOUD SECRETS ***
MT5_REST_API_URL=https://bentley-mt5-api.up.railway.app
ALPACA_ENVIRONMENT=live
PLAID_ENVIRONMENT=production
RAILWAY_PROJECT_NAME=bentley_mt5_bridge
RAILWAY_PROJECT_ID=c061b9e1-f140-472f-9f00-ffb6478cdc8d
```

---

## Commit Message Convention

```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

### Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation update
- `config`: Configuration change
- `refactor`: Code refactoring (no new features)
- `test`: Test additions/updates
- `chore`: Build, dependencies, cleanup

### Examples:
```
feat: add MT5 REST health check endpoint
fix: resolve Plaid token refresh timeout
config: add Railway MT5 bridge settings
docs: update Git Flow workflow
```

---

## Status Checks

Before merging to `dev` or `main`, these checks must pass:

- ✅ **Pre-commit validation** (syntax, linting)
- ✅ **GitHub Actions CI** (Python tests, if configured)
- ✅ **Code review** (1 reviewer for dev, 1+ for main)

---

## Handling Merge Conflicts

### If `dev` has advanced during your feature work:

```bash
git checkout feature/Plaid
git fetch origin
git rebase origin/dev

# If conflicts appear:
# 1. Open files, resolve conflicts manually
# 2. git add <resolved-files>
# 3. git rebase --continue
# 4. git push origin feature/Plaid --force-with-lease
```

### If merging feature → dev has conflicts:

```bash
git checkout dev
git pull origin dev
git merge feature/Plaid

# Resolve conflicts in editor
git add <resolved-files>
git commit -m "merge: resolve conflicts from feature/Plaid"
git push origin dev
```

---

## Reverting Changes

### Undo Last Commit (Not Pushed)
```bash
git reset --soft HEAD~1  # Keep changes
git reset --hard HEAD~1  # Discard changes
```

### Undo Pushed Commit (Create Revert Commit)
```bash
git revert <commit-hash>
git push origin <branch>
```

### Emergency Revert on Main
```bash
git checkout main
git pull origin main
git revert <bad-commit-hash>
git push origin main
```

---

## Branch Status & Commands

### View All Branches
```bash
git branch -a                    # Local + remote
git branch -v                    # With last commit
git branch -vv                   # With upstream tracking
```

### Delete Local Branch
```bash
git branch -d feature/old-work   # Safe (only if merged)
git branch -D feature/old-work   # Force delete
```

### Delete Remote Branch
```bash
git push origin --delete feature/old-work
```

### Sync Local with Remote
```bash
git fetch origin
git branch -u origin/dev dev     # Track origin/dev
git pull                         # Now pulls from origin/dev
```

---

## Emergency Hotfixes

If production needs an urgent fix:

```bash
git checkout main
git checkout -b hotfix/critical-issue
# Make fix...
git add .
git commit -m "hotfix: [description]"
git push origin hotfix/critical-issue

# On GitHub: PR hotfix/critical-issue → main
# After merge to main, also merge back to dev:
git checkout dev
git pull origin dev
git merge hotfix/critical-issue
git push origin dev
```

---

## Current Repository State

| Branch | Latest Commit | Status | Purpose |
|--------|--------------|--------|---------|
| **main** | fc4bb5f8 (Jan 30) | ✅ Production | Stable production code |
| **dev** | 916cd85c (Jan 30) | ✅ Current | Integration point |
| **feature/bot_dev** | 2030d0c0 (Jan 30) | ✅ Current | MT5 trading features |
| **feature/Plaid** | 916cd85c (Jan 30) | ✅ New | Plaid bank integration |

---

## Key Principles

1. ✅ **Always pull before starting work** - `git pull origin dev`
2. ✅ **Small, focused commits** - One feature per commit
3. ✅ **Descriptive messages** - Reviewers understand what changed
4. ✅ **Test locally first** - Don't push broken code
5. ✅ **Never force-push to main** - Only main needs protection
6. ✅ **Keep dev fresh** - dev should track main closely
7. ✅ **Feature isolation** - feature/Plaid and feature/bot_dev are independent

---

## Troubleshooting

### "Your branch is behind origin/main by 73 commits"
```bash
git fetch origin
git pull origin main  # Or your current branch
```

### "error: refused to merge unrelated histories"
```bash
git merge --allow-unrelated-histories origin/main
```

### "fatal: not a git repository"
```bash
cd /correct/directory  # Ensure you're in the repo root
```

### Need to update your fork?
```bash
git remote add upstream https://github.com/winstonwilliamsiii/BBBot.git
git fetch upstream
git checkout main
git merge upstream/main
```

---

## Resources

- [GitHub Flow Guide](https://guides.github.com/introduction/flow/)
- [Git Rebase Guide](https://git-scm.com/book/en/v2/Git-Branching-Rebasing)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Last Updated**: January 30, 2026  
**Git Flow Setup Complete**: ✅  
**Status**: Production-Ready with Staging Integration
