# Environment Setup & Configuration Guide

## Quick Start

### 1. First-Time Setup on Moor Kingdom

```powershell
# Navigate to project
cd C:\Users\winst\BentleyBudgetBot

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create local config (GITIGNORED)
cp .env.local.template .env.local
# Edit .env.local with your credentials
```

### 2. Environment Configuration

**Three-tier configuration system:**

```
┌─────────────────────────────────────┐
│ 1. .env.local (Highest Priority)    │ ← Machine-specific secrets
│    - API keys, passwords            │
│    - Local paths                    │
│    - GITIGNORED (safe to commit)   │
├─────────────────────────────────────┤
│ 2. .env.{ENVIRONMENT}              │ ← Environment presets
│    - .env.development              │
│    - .env.production               │
│    - Committed to repo             │
├─────────────────────────────────────┤
│ 3. .env (Fallback)                 │ ← Legacy support
│    - Base defaults                 │
│    - Used if others missing        │
└─────────────────────────────────────┘
```

---

## 🏠 Development Environment (Moor Kingdom Laptop)

### Configuration

**`.env.local` for Moor Kingdom:**

```env
# ============================================
# ENVIRONMENT IDENTIFIER
# ============================================
ENVIRONMENT=development

# ============================================
# DATABASE - LOCAL MYSQL
# ============================================
DB_HOST=localhost
DB_PORT=3306
DB_USER=dev_user
DB_PASSWORD=your_mysql_password_here
DB_NAME=bentley_bot_dev

# ============================================
# ALPACA - PAPER TRADING (DEVELOPMENT ONLY)
# ============================================
ALPACA_API_KEY=PK_YOUR_PAPER_KEY_HERE
ALPACA_SECRET_KEY=SK_YOUR_PAPER_SECRET_HERE
ALPACA_ENVIRONMENT=paper

# ============================================
# PLAID - SANDBOX (DEVELOPMENT ONLY)
# ============================================
PLAID_CLIENT_ID=your_dev_client_id
PLAID_SECRET=your_dev_secret

# ============================================
# GOOGLE & GENERATIVE AI
# ============================================
GOOGLE_API_KEY=your_dev_google_key
GEMINI_API_KEY=your_dev_gemini_key

# ============================================
# APPWRITE - LOCAL/DEV INSTANCE
# ============================================
APPWRITE_ENDPOINT=http://localhost:80
APPWRITE_PROJECT_ID=dev_project
APPWRITE_API_KEY=dev_api_key

# ============================================
# FILE PATHS - MOOR KINGDOM LAPTOP
# ============================================
UPLOAD_DIRECTORY=C:\Users\winst\BentleyBudgetBot\uploads_dev
LOG_DIRECTORY=C:\Users\winst\BentleyBudgetBot\logs_dev
DATA_DIRECTORY=C:\Users\winst\BentleyBudgetBot\data_dev
```

### Setup Steps

#### Step 1: Create Required Directories

```powershell
$dirs = @(
    "C:\Users\winst\BentleyBudgetBot\uploads_dev",
    "C:\Users\winst\BentleyBudgetBot\logs_dev",
    "C:\Users\winst\BentleyBudgetBot\data_dev"
)

foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir
        Write-Host "✓ Created $dir"
    }
}
```

#### Step 2: Setup Local MySQL (Docker)

```bash
# Pull MySQL image
docker pull mysql:8.0

# Run MySQL container
docker run -d \
  --name bentley-bot-dev-mysql \
  -e MYSQL_ROOT_PASSWORD=dev_password \
  -e MYSQL_DATABASE=bentley_bot_dev \
  -e MYSQL_USER=dev_user \
  -e MYSQL_PASSWORD=your_mysql_password_here \
  -p 3306:3306 \
  -v bentley_bot_dev_data:/var/lib/mysql \
  mysql:8.0

# Verify connection
mysql -h localhost -u dev_user -p bentley_bot_dev
```

#### Step 3: Get Credentials

**Alpaca Paper Trading:**
1. Go to https://alpaca.markets
2. Sign up or login
3. Create Paper Trading account
4. Copy API Key and Secret Key
5. Verify endpoint: `https://paper-api.alpaca.markets`

**Plaid (Sandbox):**
1. Go to https://dashboard.plaid.com
2. Create account
3. Switch to Sandbox environment
4. Copy Client ID and Secret
5. Create test institution link

**Google Gemini API:**
1. Go to https://ai.google.dev
2. Create API key
3. Copy to `.env.local`

#### Step 4: Verify Setup

```python
# test_env.py
from config_env import config

print("Environment Configuration Check")
print("=" * 50)
print(f"ENVIRONMENT: {config.get('ENVIRONMENT')}")
print(f"Is Development: {config.is_development()}")
print(f"DB_HOST: {config.get('DB_HOST')}")
print(f"ALPACA_ENVIRONMENT: {config.get('ALPACA_ENVIRONMENT')}")
print(f"LOG_LEVEL: {config.get('LOG_LEVEL')}")
print("\n✓ Configuration loaded successfully")

# Test database connection
import mysql.connector
try:
    conn = mysql.connector.connect(
        host=config.get('DB_HOST'),
        user=config.get('DB_USER'),
        password=config.get('DB_PASSWORD'),
        database=config.get('DB_NAME')
    )
    print("✓ Database connection successful")
    conn.close()
except Exception as e:
    print(f"✗ Database connection failed: {e}")
```

Run it:
```bash
python test_env.py
```

---

## ☁️ Production Environment (Streamlit Cloud)

### Configuration

**Streamlit Cloud Secrets (Web UI):**

1. Go to https://share.streamlit.io/settings/secrets/
2. Add each secret as key=value
3. Streamlit automatically loads into app

**Secrets to configure:**

```
ENVIRONMENT=production
DB_HOST=prod-db-host.aws.amazonaws.com
DB_PORT=3306
DB_USER=prod_app_user
DB_PASSWORD=your_production_password
DB_NAME=bentley_bot_production
ALPACA_API_KEY=your_live_trading_key
ALPACA_SECRET_KEY=your_live_trading_secret
PLAID_CLIENT_ID=your_prod_plaid_id
PLAID_SECRET=your_prod_plaid_secret
GOOGLE_API_KEY=your_prod_google_key
GEMINI_API_KEY=your_prod_gemini_key
APPWRITE_PROJECT_ID=prod_project_id
APPWRITE_API_KEY=prod_api_key
```

### Deployment Process

1. **Push to `main` branch**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Streamlit Cloud auto-detects changes**
   - Pulls latest code
   - Installs requirements
   - Runs `streamlit_app.py`

3. **Application available at**
   - https://bbbot305.streamlit.app

4. **Monitor deployment**
   - Check Streamlit Cloud console
   - View logs in real-time
   - Check status dashboard

---

## 🔧 Configuration in Code

### Using Environment Configuration

```python
from config_env import config

# Get string value
db_host = config.get('DB_HOST')
db_password = config.get('DB_PASSWORD', 'default_password')

# Get boolean value
debug_mode = config.get_bool('DEBUG_MODE', False)
enable_features = config.get_bool('ENABLE_EXPERIMENTAL_FEATURES')

# Get integer value
timeout = config.get_int('YFINANCE_TIMEOUT', 30)
batch_size = config.get_int('YFINANCE_BATCH_SIZE', 8)

# Check environment
if config.is_development():
    print("Running in development mode")
    
if config.is_production():
    print("Running in production mode")

# Reload configuration (for Streamlit)
from config_env import reload_env
reload_env()
```

### Streamlit Configuration Integration

```python
import streamlit as st
from config_env import config

# Set Streamlit page config based on environment
st.set_page_config(
    page_title="Bentley Budget Bot",
    layout="wide",
    initial_sidebar_state="expanded" if config.is_development() else "collapsed"
)

# Debug mode toggle
if config.get_bool('DEBUG_MODE'):
    with st.sidebar:
        st.warning("🔧 Debug Mode Enabled")
        if st.button("Reload Config"):
            from config_env import reload_env
            reload_env()
            st.rerun()
```

---

## 📋 Checklist: Environment Setup

### Development (First Time)

- [ ] Virtual environment created and activated
- [ ] Requirements installed: `pip install -r requirements.txt`
- [ ] `.env.local` created with credentials
- [ ] MySQL running locally (Docker or native)
- [ ] Database connection verified
- [ ] Alpaca credentials configured (paper trading)
- [ ] Google API credentials configured
- [ ] Local directories created (`uploads_dev`, `logs_dev`, `data_dev`)
- [ ] App runs without errors: `streamlit run streamlit_app.py`
- [ ] Portfolio upload works
- [ ] Financial data loads
- [ ] No API key warnings in logs

### Production (Deployment)

- [ ] `.env.production` configured correctly
- [ ] Secrets configured in Streamlit Cloud
- [ ] Database migrated and verified
- [ ] Alpaca credentials use LIVE trading account
- [ ] Production Google API keys configured
- [ ] Tests pass in GitHub Actions
- [ ] Code pushed to `main` branch
- [ ] Deployment triggered and successful
- [ ] Application accessible at URL
- [ ] Health checks passed
- [ ] Monitoring alerts active

---

## 🚨 Troubleshooting

### "Module not found" error

```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Clear cache
rm -r .streamlit/__pycache__
```

### "Connection refused" for database

```bash
# Check MySQL running
docker ps | grep mysql

# Check credentials in .env.local
cat .env.local | grep DB_

# Verify port
netstat -ano | findstr :3306
```

### Environment variables not loading

```python
# In Python console
import os
from config_env import reload_env

# Reload configuration
reload_env()

# Check specific variable
print(os.getenv('ENVIRONMENT'))
print(os.getenv('DB_HOST'))
```

### Alpaca API errors

1. Verify environment: `ALPACA_ENVIRONMENT=paper` (dev) vs `live` (prod)
2. Check credentials are correct
3. Ensure paper trading account is active
4. Test connection: `alpaca_trade_client.get_account()`

---

## 📞 Support

Create an issue in GitHub with:
- Environment type (development/production)
- Error message
- Steps to reproduce
- `.env.local` snippet (redacted credentials)

---

**Last Updated:** January 19, 2026
