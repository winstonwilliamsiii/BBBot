# Railway Deployment Guide for MT5 REST API

## Overview

The MT5 REST API is containerized and ready for deployment on Railway. However, MT5's Python connector is **Windows-only**, so Railway (Linux) runs the API service for routing/health checks, while actual MT5 trading executes on a Windows VPS.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Railway (Linux Container)                              │
│ - Runs mt5_rest.py (Flask)                             │
│ - Serves REST endpoints at public URL                  │
│ - Acts as API gateway/proxy                            │
│ - Health checks & monitoring                           │
└───────────────────┬─────────────────────────────────────┘
                    │
            HTTP requests (REST API calls)
                    │
┌───────────────────▼─────────────────────────────────────┐
│ Windows VPS (Production MT5)                           │
│ - Runs mt5_rest.py + MT5 Python connector              │
│ - Executes actual trades                               │
│ - Stores account credentials                           │
│ - 24/7 uptime for trading                              │
└─────────────────────────────────────────────────────────┘
```

## Railway Setup (5 minutes)

### 1. Create Railway Project

1. Go to **https://railway.app**
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select: **winstonwilliamsiii/BBBot**
4. Branch: **main**
5. Railway auto-detects `Dockerfile`

### 2. Set Environment Variables

In Railway → Settings → Variables:

```
HOST=0.0.0.0
PORT=8080
MT5_USER=demo_user
MT5_PASSWORD=demo_password
MT5_HOST=mt5-broker.example.com
```

**Note**: MT5 credentials won't authenticate on Railway (Linux), so these can be placeholder values. The real service runs on Windows VPS.

### 3. Deploy

1. Click **"Deploy"**
2. Railway builds Docker image (~2 min)
3. Container starts
4. Public URL assigned: `https://bentley-mt5-api.up.railway.app`

### 4. Verify

```bash
curl https://bentley-mt5-api.up.railway.app/health
# Response: {"status": "ok", "service": "mt5-bridge"}
```

**Expected behavior on Railway**:
- ✅ `/health` endpoint works
- ✅ Container healthy
- ❌ `/connect` and trading endpoints fail (MT5 unavailable on Linux)
- ✅ Windows VPS calls work normally

---

## Windows VPS Deployment (Production)

For live trading, deploy the same container on a Windows VPS:

### 1. Windows VPS Setup

**Requirements**:
- Windows Server 2019/2022
- MetaTrader 5 installed
- Python 3.11+
- Docker Desktop (optional) or native Python

### 2. Deploy via Script

See [deploy-windows-vps.ps1](../../scripts/deploy_windows_vps.ps1) for automated setup:

```powershell
# Download and run
$uri = "https://raw.githubusercontent.com/winstonwilliamsiii/BBBot/main/scripts/deploy_windows_vps.ps1"
Invoke-WebRequest -Uri $uri -OutFile deploy_windows_vps.ps1
.\deploy_windows_vps.ps1 -MTUser "your_account" -MTPassword "your_password" -MTHost "broker.example.com"
```

Or manually:

```powershell
# 1. Clone repo
git clone https://github.com/winstonwilliamsiii/BBBot
cd BBBot

# 2. Create venv
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run with MT5 (Windows-specific)
$env:MT5_USER = "your_account"
$env:MT5_PASSWORD = "your_password"
$env:MT5_HOST = "broker.example.com"
$env:PORT = 8080
$env:HOST = "0.0.0.0"

python mt5_rest.py
# Server runs at http://localhost:8080
```

---

## Architecture Decision: Why Two Deployments?

| Aspect | Railway (Linux) | Windows VPS (Production) |
|--------|-----------------|--------------------------|
| **MT5 Connector** | ❌ Fails (Windows-only) | ✅ Works |
| **Trading Execution** | ❌ N/A | ✅ Full support |
| **Public URL** | ✅ Yes | ⚠️ Requires reverse proxy |
| **Cost** | $5-20/mo | $20-100/mo |
| **Use Case** | Health checks, proxy | **Live trading** |

**Recommendation**: 
- Use **Railway** for public API gateway (optional, for monitoring)
- Deploy **production on Windows VPS** for actual trading

Alternatively, skip Railway and run everything on Windows VPS directly.

---

## API Endpoints

All endpoints available on both Railway and Windows VPS:

### Health Check
```bash
GET /health
```

### Connection
```bash
POST /connect
Content-Type: application/json

{
  "user": "account_number",
  "password": "password",
  "host": "broker.example.com"
}
```

### Trading
```bash
POST /trade
Content-Type: application/json

{
  "symbol": "GBPJPY",
  "action": "buy",
  "volume": 1.0,
  "stop_loss": 100.50,
  "take_profit": 101.00,
  "comment": "Trend following"
}
```

### Get Positions
```bash
GET /positions
```

### Close Position
```bash
POST /close
Content-Type: application/json

{
  "symbol": "GBPJPY",
  "volume": 1.0
}
```

See [mt5_rest.py](../../mt5_rest.py) for full endpoint documentation.

---

## Monitoring & Logs

### Railway Logs
- In Railway dashboard: **Deployments** → **Logs**
- Real-time log streaming
- Error tracking

### Windows VPS Logs
```powershell
# Terminal output shows:
# - Connection status
# - Trade execution
# - Errors and warnings

# Or use application logging:
Get-Content -Path "C:\BentleyBot\logs\mt5_rest.log" -Tail 50
```

---

## Environment Variables

### Railway Variables
```
PORT=8080
HOST=0.0.0.0
MT5_USER=placeholder
MT5_PASSWORD=placeholder
MT5_HOST=placeholder
```

### Windows VPS Variables
```powershell
$env:PORT = 8080
$env:HOST = 0.0.0.0
$env:MT5_USER = "your_real_account"
$env:MT5_PASSWORD = "your_real_password"
$env:MT5_HOST = "real-broker.example.com"
```

---

## Troubleshooting

### Railway Deployment Fails
- Check logs: Railway dashboard → Deployments → Logs
- Verify `Dockerfile` and `requirements.txt` are in repo root
- Ensure Docker image builds (may take 2-3 min)

### MT5 Connection Fails on Railway (Expected)
- MT5 connector requires Windows
- This is by design—use Windows VPS for trading

### MT5 Connection Fails on Windows VPS
- Verify MT5 installed and running
- Check credentials: user, password, host
- Ensure broker connection active
- Review MT5 logs: `%APPDATA%\MetaQuotes\Terminal\<ID>\logs\`

### Port Already in Use
```powershell
# Find process using port 8080
netstat -ano | findstr :8080

# Kill process
taskkill /PID <PID> /F

# Use different port
$env:PORT = 8081
```

---

## Next Steps

1. **Deploy on Railway**:
   - Create project at https://railway.app
   - Link to GitHub repo
   - Set environment variables
   - Deploy (automatic on push)

2. **Deploy on Windows VPS**:
   - Follow [deploy-windows-vps.ps1](../../scripts/deploy_windows_vps.ps1)
   - Or run manually with credentials
   - Test `/connect` endpoint

3. **Monitor**:
   - Railway logs for API health
   - Windows VPS for trade execution
   - Set up Discord/email alerts

4. **Scale**:
   - Add multiple MT5 accounts
   - Load balance across VPS instances
   - Use Railway for HA proxy

---

**Ready to deploy?** Start with Railway for testing, then move to Windows VPS for production.
