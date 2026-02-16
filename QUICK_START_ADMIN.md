# 🚀 Quick Start - Admin Control Center

**Created:** February 15, 2026  
**Status:** ✅ Ready to Use

---

## 🔑 Login Credentials

**URL:** http://localhost:8501 (Streamlit app)  
**Navigate to:** Sidebar → "🔧 Admin Control Center"

```
Username: admin
Password: admin
```

⚠️ **IMPORTANT:** These are DEVELOPMENT credentials only. Change before production!

---

## 🎯 What's Running

### ✅ Flask API (Backend)
- **Status:** ✅ RUNNING in background terminal
- **URL:** http://localhost:5000
- **Health Check:** http://localhost:5000/health
- **Test Endpoint:** http://localhost:5000/admin/test

### ⏳ Streamlit App (Frontend)
- **Status:** Need to start
- **Command:** `streamlit run streamlit_app.py`
- **URL:** http://localhost:8501

---

## 📋 Start Everything

### Step 1: Flask API is Already Running! ✅
The backend API is running in the background. You should see it in your terminal.

### Step 2: Start Streamlit

Open a **NEW** PowerShell terminal and run:
```powershell
cd C:\Users\winst\BentleyBudgetBot
streamlit run streamlit_app.py
```

### Step 3: Open Admin Dashboard

1. Browser will open to http://localhost:8501
2. Look in the **left sidebar**
3. Scroll down to find: **"🔧 Admin Control Center"**
4. Click it
5. Enter credentials:
   - Username: `admin`
   - Password: `admin`

---

## 🎨 What You'll See

### 6 Tabs Available:

1. **📊 Overview** - System health, metrics, Docker services
2. **🤖 Bot Manager** - Deploy and manage 13 AI bots
3. **🔌 Broker Health** - Monitor Alpaca, Schwab, IBKR, Binance, Coinbase
4. **🏢 Prop Firms** - FTMO, Axi, Zenit management
5. **🛡️ Risk Engine** - Drawdown limits, position sizing
6. **📈 System Logs** - Real-time monitoring

---

## 🔧 If Something's Not Working

### Flask API Not Responding?

Check if it's running:
```powershell
# Test the health endpoint
curl http://localhost:5000/health
```

Should return:
```json
{"status":"healthy","service":"Bentley Bot Control Center API"}
```

If not responding, restart Flask:
```powershell
cd backend/api
C:/Users/winst/BentleyBudgetBot/.venv/Scripts/python.exe app.py
```

### Streamlit Not Loading?

```powershell
# Kill any existing Streamlit processes
Get-Process *streamlit* | Stop-Process -Force

# Restart Streamlit
streamlit run streamlit_app.py
```

### Can't Login to Admin?

Make sure you're using:
- Username: `admin` (all lowercase)
- Password: `admin` (all lowercase)

### APIs Showing Errors?

The Control Center has **fallback mode**! If Flask API isn't available, it will show sample data instead. Everything will still work visually, just won't connect to real systems.

---

## 📊 Current System Status

### What's Working ✅
- Flask API (running on port 5000)
- Admin UI with 6 tabs
- Authentication system
- Sample data fallback
- Docker service monitoring (if Docker is running)

### What Needs Backend Endpoints 🔨
These will show "API not available" until Week 1-2 endpoints are built:
- Bot deployment actions
- Broker health checks (real data)
- Risk settings updates
- Log streaming

---

## 🚀 Next Steps

### Immediate (Today)
1. ✅ Start Streamlit: `streamlit run streamlit_app.py`
2. ✅ Login to Admin Control Center
3. ✅ Explore all 6 tabs
4. ✅ Familiarize yourself with the UI

### Week 1-2 (Building Out Backend)
1. Create Flask Blueprints in `backend/api/admin/`
2. Connect real bot data
3. Integrate broker APIs
4. Add risk engine logic

See: [CONTROL_CENTER_QUICK_START.md](docs/CONTROL_CENTER_QUICK_START.md)

---

## 🔗 Important Links

- **Flask API:** http://localhost:5000
- **Streamlit App:** http://localhost:8501
- **MLflow:** http://localhost:5000 (if Docker running)
- **Airflow:** http://localhost:8080 (if Docker running)
- **Airbyte:** http://localhost:8000 (if Docker running)

---

## 📞 Getting Help

### Documentation
- [CONTROL_CENTER_ADMIN_UI_GUIDE.md](docs/CONTROL_CENTER_ADMIN_UI_GUIDE.md) - Full UI guide
- [CONTROL_CENTER_QUICK_START.md](docs/CONTROL_CENTER_QUICK_START.md) - Week-by-week plan
- [FLASK_STREAMLIT_UPDATE.md](docs/FLASK_STREAMLIT_UPDATE.md) - Tech stack info

### Quick Commands

```powershell
# Check Flask API status
curl http://localhost:5000/health

# Check Streamlit status
Get-Process *streamlit*

# View Docker services
docker ps

# Restart everything
# 1. Ctrl+C in Flask terminal
# 2. Ctrl+C in Streamlit terminal
# 3. Re-run commands above
```

---

## 🎉 You're All Set!

The Control Center is ready to explore. Remember:
- **Login:** admin / admin
- **Flask API:** Already running in background
- **Streamlit:** Run `streamlit run streamlit_app.py`

Happy exploring! 🚀
