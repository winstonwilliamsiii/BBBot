# BentleyBudgetBot Environment Configuration

## 🌐 Deployment URLs

**Production (Streamlit Cloud):**
- URL: https://bbbot305.streamlit.app/
- Source: GitHub repository `winstonwilliamsiii/BBBot`
- Branch: `main`

**Local Development:**
- URL: http://localhost:8501
- Path: `C:\Users\winst\BentleyBudgetBot`
- Python: `C:\Users\winst\BentleyBudgetBot\.venv\Scripts\python.exe`
- Streamlit Command: `python -m streamlit run streamlit_app.py`

## 📂 Critical File Paths

### Main Application
```
C:\Users\winst\BentleyBudgetBot\streamlit_app.py    ← MAIN ENTRY POINT (run this)
```

### Pages (Auto-discovered by Streamlit)
```
C:\Users\winst\BentleyBudgetBot\pages\
├── 01_💰_Personal_Budget.py
├── 02_📈_Investment_Analysis.py
├── 03_🔴_Live_Crypto_Dashboard.py
├── 04_💼_Broker_Trading.py
└── 05_🤖_Trading_Bot.py
```

### Appwrite Functions (Serverless)
```
C:\Users\winst\BentleyBudgetBot\appwrite-functions\
├── _shared\appwriteClient.js
├── create_transaction\index.js
├── get_transactions\index.js
├── get_transactions_streamlit\index.js
├── add_to_watchlist_streamlit\index.js
├── get_watchlist_streamlit\index.js
├── get_user_profile_streamlit\index.js
├── create_audit_log\index.js
├── get_audit_logs\index.js
├── create_payment\index.js
├── get_payments\index.js
├── manage_roles\index.js
├── manage_permissions\index.js
├── create_bot_metric\index.js
├── get_bot_metrics\index.js
├── get_bot_metrics_stats\index.js
└── create_all_indexes\index.js
```

### Services (Appwrite Integration)
```
C:\Users\winst\BentleyBudgetBot\services\
├── __init__.py
├── transactions.py    ← HTTP client for transaction functions
└── watchlist.py       ← HTTP client for watchlist functions
```

### Frontend Components
```
C:\Users\winst\BentleyBudgetBot\frontend\
├── components\
│   ├── budget_dashboard.py
│   └── bentley_chatbot.py
├── utils\
│   ├── styling.py
│   ├── rbac.py
│   └── yahoo.py
└── styles\
    └── colors.py
```

## 🔧 Environment Variables

**Location:** `C:\Users\winst\BentleyBudgetBot\.env`

```env
# Appwrite Configuration
APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
APPWRITE_PROJECT_ID=your_project_id
APPWRITE_DATABASE_ID=your_database_id
APPWRITE_API_KEY=your_api_key

# Appwrite Function IDs (after deployment)
APPWRITE_FUNCTION_ID_CREATE_TRANSACTION=function_id
APPWRITE_FUNCTION_ID_GET_TRANSACTIONS=function_id
APPWRITE_FUNCTION_ID_ADD_WATCHLIST=function_id
APPWRITE_FUNCTION_ID_GET_WATCHLIST=function_id
```

## 🚀 Starting Local Server

### Method 1: Using Virtual Environment
```powershell
cd C:\Users\winst\BentleyBudgetBot
& C:/Users/winst/BentleyBudgetBot/.venv/Scripts/Activate.ps1
python -m streamlit run streamlit_app.py
```

### Method 2: Direct Python Path
```powershell
cd C:\Users\winst\BentleyBudgetBot
& C:/Users/winst/BentleyBudgetBot/.venv/Scripts/python.exe -m streamlit run streamlit_app.py
```

### Method 3: Full Command (No Virtual Env Activation)
```powershell
C:\Users\winst\BentleyBudgetBot\.venv\Scripts\python.exe -m streamlit run C:\Users\winst\BentleyBudgetBot\streamlit_app.py
```

## 🔄 Troubleshooting Local vs Production Differences

### Issue: localhost:8501 shows old version, but bbbot305.streamlit.app shows updates

**Cause:** Browser cache or Streamlit is running cached version

**Solution:**

1. **Clear Browser Cache:**
   - Press `Ctrl + Shift + Delete`
   - Select "Cached images and files"
   - Clear cache

2. **Hard Refresh:**
   - Press `Ctrl + F5` (Windows)
   - Or `Ctrl + Shift + R`

3. **Stop All Streamlit Processes:**
   ```powershell
   Get-Process python | Where-Object {$_.Path -like "*BentleyBudgetBot*"} | Stop-Process -Force
   ```

4. **Clear Streamlit Cache:**
   ```powershell
   Remove-Item -Path "$env:USERPROFILE\.streamlit\cache" -Recurse -Force -ErrorAction SilentlyContinue
   ```

5. **Restart Fresh:**
   ```powershell
   cd C:\Users\winst\BentleyBudgetBot
   & .venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.port 8501
   ```

## 📊 Verifying Correct File is Running

When you visit http://localhost:8501, you should see:

✅ **Main Page:**
- 🤖 Bentley Bot Dashboard header
- Bentley AI ChatBot section
- ⚡ Quick Actions (Transactions & Watchlist tabs)
- Portfolio Data Upload section

✅ **Sidebar:**
- 📄 Upload Portfolio CSV
- 5 pages listed:
  - 💰 Personal Budget
  - 📈 Investment Analysis
  - 🔴 Live Crypto Dashboard
  - 💼 Broker Trading
  - 🤖 Trading Bot

## 🌍 Python Environment Details

**Virtual Environment Path:**
```
C:\Users\winst\BentleyBudgetBot\.venv\
```

**Python Executable:**
```
C:\Users\winst\BentleyBudgetBot\.venv\Scripts\python.exe
```

**Streamlit Module:**
```
C:\Users\winst\BentleyBudgetBot\.venv\Lib\site-packages\streamlit\
```

**Activation Script:**
```
C:\Users\winst\BentleyBudgetBot\.venv\Scripts\Activate.ps1
```

## 📝 Requirements

**Core Dependencies:**
- streamlit >= 1.28.0
- python-dotenv >= 1.0.0
- requests >= 2.31.0
- pandas
- yfinance (optional)

**Install Command:**
```bash
pip install -r requirements.txt
```

## 🔐 Security Notes

1. **Never commit `.env` file** - Contains sensitive Appwrite credentials
2. **gitignore includes:**
   - `.env`
   - `__pycache__/`
   - `.streamlit/secrets.toml`
   - `.venv/`

## 🌐 Network URLs

When Streamlit starts, it provides:
- **Local URL:** http://localhost:8501 (same machine only)
- **Network URL:** http://192.168.1.53:8501 (accessible from other devices on your network)

## 📦 Deployment to Streamlit Cloud

Your Streamlit Cloud deployment (`bbbot305.streamlit.app`) automatically:
1. Pulls latest code from GitHub `main` branch
2. Runs `streamlit_app.py` as entry point
3. Discovers all pages in `pages/` folder
4. Uses secrets from Streamlit Cloud dashboard (not `.env` file)

**To update production:**
```bash
git add .
git commit -m "Update message"
git push origin main
```

Streamlit Cloud will auto-deploy within 1-2 minutes.
