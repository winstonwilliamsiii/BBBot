# 🎯 Getting Started - First Time Setup (5-10 Minutes)

**Goal:** Get your development environment running on Moor Kingdom laptop in under 10 minutes

---

## ✅ Prerequisites

- [ ] Git installed: `git --version`
- [ ] Python 3.10+: `python --version`
- [ ] Docker installed: `docker --version`
- [ ] Repository cloned: `C:\Users\winst\BentleyBudgetBot`

---

## 🚀 Step 1: Setup Python Environment (2 min)

```powershell
# Navigate to project
cd C:\Users\winst\BentleyBudgetBot

# Create virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Verify
python -c "import streamlit; print('✓ Streamlit ready')"
```

**Expected Output:** `✓ Streamlit ready`

---

## 🔑 Step 2: Configure Secrets (1 min)

```powershell
# Copy template
cp config/env-templates/.env.local.template .env.local

# Open for editing
notepad .env.local
```

**Required entries in `.env.local`:**

```env
# Development identifier
ENVIRONMENT=development

# Local database
DB_HOST=localhost
DB_PORT=3306
DB_USER=dev_user
DB_PASSWORD=change_this_to_mysql_password

# Alpaca paper trading (use test keys)
ALPACA_API_KEY=PK_YOUR_PAPER_KEY_HERE
ALPACA_SECRET_KEY=SK_YOUR_PAPER_SECRET_HERE

# Paths (Windows format)
UPLOAD_DIRECTORY=C:\Users\winst\BentleyBudgetBot\uploads_dev
LOG_DIRECTORY=C:\Users\winst\BentleyBudgetBot\logs_dev
DATA_DIRECTORY=C:\Users\winst\BentleyBudgetBot\data_dev
```

**Save the file** (Ctrl+S)

---

## 📁 Step 3: Create Local Directories (1 min)

```powershell
# Create data directories
mkdir -Force uploads_dev, logs_dev, data_dev

# Verify they exist
ls | grep _dev
```

---

## 🐳 Step 4: Start MySQL (3 min)

```powershell
# Pull MySQL image (if first time, takes ~1-2 min)
docker pull mysql:8.0

# Start MySQL container
docker run -d `
  --name bentley-bot-dev-mysql `
  -e MYSQL_ROOT_PASSWORD=rootpass123 `
  -e MYSQL_DATABASE=bentley_bot_dev `
  -e MYSQL_USER=dev_user `
  -e MYSQL_PASSWORD=your_mysql_password `
  -p 3306:3306 `
  mysql:8.0

# Wait for MySQL to start (takes ~20-30 seconds)
Start-Sleep -Seconds 30

# Verify it's running
docker ps | Select-String mysql
```

**Expected Output:** Container ID and `bentley-bot-dev-mysql` shown

---

## ✨ Step 5: Run the Application (1 min)

```powershell
# Make sure you're still in .venv
# (Should see (.venv) in your prompt)

# Run Streamlit
streamlit run streamlit_app.py
```

**Expected Output:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

✅ **Open in browser:** http://localhost:8501

---

## 🧪 Step 6: Test It Works (1 min)

In the Streamlit app, try:
- [ ] Load page successfully
- [ ] No red error boxes
- [ ] Can see portfolio section
- [ ] Check console for `✓ Config loaded`

---

## ✅ You're Done!

Your development environment is ready. Now:

```bash
# When you want to work on features:
git checkout -b feature/my-feature-name

# Make changes & commit
git add .
git commit -m "feat(scope): description"

# Push & create PR to dev
git push origin feature/my-feature-name
```

---

## 🔧 Troubleshooting Quick Fixes

### "Port 3306 already in use"
```powershell
# Stop existing MySQL
docker stop bentley-bot-dev-mysql

# Remove it
docker rm bentley-bot-dev-mysql

# Restart (from Step 4)
```

### "ModuleNotFoundError: No module named..."
```powershell
# Reinstall dependencies
pip install -r requirements.txt

# Clear Python cache
rm -r .streamlit/__pycache__
```

### "Connection refused" when running app
```powershell
# Check MySQL is running
docker ps | Select-String mysql

# If not running, restart it (Step 4)
```

### Environment variables not loading
```python
# In Python terminal
from config_env import reload_env
reload_env()

# Check it worked
from config_env import config
print(config.get('ENVIRONMENT'))  # Should print "development"
```

---

## 📚 Next Steps

1. **Read the guides:**
   - [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command cheat sheet
   - [BRANCHING_STRATEGY.md](BRANCHING_STRATEGY.md) - Workflow guide
   - [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) - Detailed setup

2. **Create a test feature:**
   - `git checkout -b feature/test-branch`
   - Make a small change
   - Push and see GitHub Actions run tests

3. **Get API credentials:**
   - Alpaca: https://alpaca.markets
   - Plaid: https://dashboard.plaid.com
   - Google: https://ai.google.dev

---

## ❓ Need Help?

**Quick reference:**
- **App won't start?** → Check MySQL is running
- **Import errors?** → Reinstall requirements.txt
- **Config not loading?** → Check .env.local exists
- **GitHub Actions failing?** → Check python version and dependencies
- **Database error?** → Verify credentials in .env.local

**For more help**, see [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md#-troubleshooting)

---

**You're all set! Happy coding! 🎉**

---

## One Last Thing

**Important:** Never commit `.env.local` (it's gitignored for safety):
```bash
# ✅ SAFE - won't be committed
- .env.local

# ✗ DON'T DO - would expose secrets
- committing .env.local
- hardcoding API keys
- sharing passwords
```

Questions? Check the [documentation](BRANCHING_STRATEGY.md) or [quick reference](QUICK_REFERENCE.md).
