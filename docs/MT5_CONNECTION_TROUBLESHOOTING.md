# MT5 Connection Troubleshooting Guide

## Issue: "❌ MT5 API server is not responding"

This error occurs when the Streamlit app cannot connect to the MT5 REST API bridge server.

### Root Cause
The MT5 REST API server is not running on port **8002** (or the configured port).

**Note:** Port 8000 is occupied by Airbyte, so we use port 8002 for MT5.

---

## Quick Fix (3 Steps)

### 1. Start MetaTrader 5 Desktop
- Launch the **MetaTrader 5** desktop application
- **Log in** to your trading account
- Keep it running in the background

### 2. Start MT5 REST API Server
Run the provided batch script:
```cmd
START_MT5_SERVER.bat
```

Or manually start it:
```cmd
.venv\Scripts\activate
set PORT=8002
python src\mt5_rest_api_server.py
```

### 3. Connect in Streamlit
- Go to: **🌐 Multi-Broker Trading Hub** page
- Click **"Connect MT5"** button
- The connection should now succeed ✅

---

## Detailed Diagnostics

### Check if MT5 Desktop is Running
```powershell
Get-Process | Where-Object { $_.ProcessName -like "*terminal64*" }
```

Expected output: MT5 terminal process

### Check if MT5 API Server is Running
```powershell
Test-NetConnection -ComputerName localhost -Port 8002
```

Expected: `TcpTestSucceeded : True`

### Test MT5 API Health Endpoint
```powershell
Invoke-WebRequest -Uri "http://localhost:8002/Health" -Method GET
```

Expected response:
```json
{
  "status": "healthy",
  "mt5_initialized": true,
  "timestamp": "2026-01-31T..."
}
```

### Check Environment Variables
Verify these are set in `.env.development`:
```dotenv
MT5_API_URL=http://localhost:8002
MT5_USER=your_account_number
MT5_PASSWORD=your_password
MT5_HOST=your_broker_server
MT5_PORT=443
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│  Streamlit App (Multi-Broker Dashboard)        │
│  Port: 8501                                     │
│  File: pages/06_🌐_Multi_Broker_Trading.py     │
└────────────┬────────────────────────────────────┘
             │ HTTP Requests
             ↓
┌─────────────────────────────────────────────────┐
│  MT5 REST API Bridge                            │
│  Port: 8002 (configurable via PORT env var)     │
│  File: src/mt5_rest_api_server.py               │
└────────────┬────────────────────────────────────┘
             │ Python MetaTrader5 package
             ↓
┌─────────────────────────────────────────────────┐
│  MetaTrader 5 Desktop Terminal                  │
│  Process: terminal64.exe                        │
│  Status: Must be logged in                      │
└─────────────────────────────────────────────────┘
```

---

## Common Issues & Solutions

### Issue 1: "Port 8000 already in use"
**Cause:** Airbyte is using port 8000

**Solution:** Use port 8002 instead (already configured)

### Issue 2: "MT5 initialization failed"
**Cause:** MT5 desktop terminal is not running

**Solution:**
1. Open MetaTrader 5 desktop app
2. Log in to your account
3. Restart the MT5 REST API server

### Issue 3: "Login failed: Invalid credentials"
**Cause:** MT5 credentials in .env file are incorrect or outdated

**Solution:**
1. Verify your MT5 account credentials
2. Update `.env.development`:
   ```dotenv
   MT5_USER=your_actual_account_number
   MT5_PASSWORD=your_actual_password
   MT5_HOST=your_actual_broker_server
   ```
3. Restart the MT5 API server

### Issue 4: Connection timeout
**Cause:** Firewall or network issue

**Solution:**
1. Check Windows Firewall
2. Add exception for Python and MT5
3. Try disabling antivirus temporarily

---

## Testing the Connection

### Step-by-step Test

1. **Test MT5 Desktop**
   - Open MT5 terminal
   - Check connection status (bottom right - should be green with ping time)

2. **Test MT5 API Server**
   ```powershell
   # Start the server
   .\START_MT5_SERVER.bat
   
   # In another terminal, test health
   Invoke-RestMethod -Uri "http://localhost:8002/Health"
   ```

3. **Test Connection from Streamlit**
   ```powershell
   # Make sure correct env is loaded
   $env:ENV_FILE='.env.development'
   streamlit run streamlit_app.py
   
   # Navigate to Multi-Broker Trading page
   # Click "Connect MT5"
   ```

---

## Production Deployment Notes

### Railway/Cloud Deployment
For production deployment, the MT5 REST server needs to run on a VPS/server where:
- MetaTrader 5 terminal can run (Windows/Linux with Wine)
- The server has stable internet connection
- Firewall allows incoming connections on the configured port

### Configuration for Production
```dotenv
# .env.production
MT5_API_URL=https://your-mt5-server.railway.app
MT5_USER=your_prod_account
MT5_PASSWORD=your_prod_password
MT5_HOST=live.broker.com
MT5_PORT=443
```

---

## Additional Resources

- **MT5 Python Package:** https://www.mql5.com/en/docs/integration/python_metatrader5
- **MT5 REST Server Code:** `src/mt5_rest_api_server.py`
- **MT5 Connector Code:** `frontend/components/mt5_connector.py`
- **Multi-Broker Dashboard:** `pages/06_🌐_Multi_Broker_Trading.py`
- **Startup Script:** `START_MT5_SERVER.bat`

---

## Summary Checklist

Before connecting to MT5, ensure:
- [ ] MetaTrader 5 desktop is running and logged in
- [ ] MT5 REST API server is running on port 8002
- [ ] `.env.development` has correct MT5 credentials
- [ ] No firewall blocking port 8002
- [ ] Virtual environment is activated when running the server

**Quick Command:**
```cmd
START_MT5_SERVER.bat
```

Then connect via the Multi-Broker Trading Hub page! 🚀
