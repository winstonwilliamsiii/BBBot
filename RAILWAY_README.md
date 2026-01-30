# Railway Deployment Guide for MT5 REST API

This guide covers deploying the MT5 REST API to [Railway.app](https://railway.app) for a public-facing API gateway.

> **Architecture Note**: Railway runs on Linux (cannot execute Windows MT5 connector). Use Railway as an **HTTP proxy/gateway** and point it to a Windows VPS for actual MT5 trading.

---

## 1. Quick Start (5 minutes)

### Prerequisites
- GitHub account connected to [railway.app](https://railway.app)
- Windows VPS with MT5 installed (for production trading)
- MT5 credentials (account number, password, broker host)

### Step-by-Step Setup

#### 1. Create Railway Project
```bash
# At railway.app dashboard, click "New Project"
# Select "Deploy from GitHub"
# Search and select: winstonwilliamsiii/BBBot
```

#### 2. Configure Environment Variables
In Railway dashboard → Settings → Variables, add:

```
HOST=0.0.0.0
PORT=8080
MT5_USER=YOUR_MT5_ACCOUNT_NUMBER
MT5_PASSWORD=YOUR_MT5_PASSWORD
MT5_HOST=YOUR_BROKER_HOST
WINDOWS_VPS_URL=http://YOUR_WINDOWS_VPS_IP:8080
```

#### 3. Deploy
Railway automatically detects `Dockerfile` and builds/deploys. Watch the Deployments tab for status.

#### 4. Test Deployment
```bash
# Get your Railway URL from the dashboard
curl https://bentley-mt5-api.up.railway.app/health

# Expected response:
# {"status": "ok", "service": "mt5-bridge"}
```

---

## 2. Railway Project Structure

### Key Files
| File | Purpose |
|------|---------|
| `Dockerfile` | Containerization recipe (Python 3.11 + Gunicorn) |
| `mt5_rest.py` | Flask REST API server |
| `requirements.txt` | Python dependencies |
| `pages/api/mt5_bridge.py` | MT5 bridge CLI (not executable on Linux) |

### Build Process
1. Railway detects repository
2. Reads `Dockerfile`
3. Builds Docker image with Python 3.11-slim
4. Installs dependencies from `requirements.txt`
5. Starts Gunicorn WSGI server on port 8080
6. Assigns `https://bentley-mt5-api.up.railway.app` URL

---

## 3. Environment Variables Reference

### Required Variables
```env
# API Configuration
HOST=0.0.0.0                      # Listen on all interfaces
PORT=8080                          # API port (Railway exposes as HTTPS)

# MT5 Connection (for direct use, not applicable on Railway Linux)
MT5_USER=12345                     # MT5 account number
MT5_PASSWORD=your_secure_password  # MT5 password
MT5_HOST=mt5.broker.com            # Broker MT5 host
```

### Optional Variables
```env
# Proxy Configuration (if using Railway as gateway to Windows VPS)
WINDOWS_VPS_URL=http://192.168.1.100:8080  # Windows production URL
ENABLE_PROXY=true                           # Enable gateway mode

# Logging
LOG_LEVEL=INFO                     # DEBUG, INFO, WARNING, ERROR
DEBUG=false                         # Flask debug mode (false in production)

# Performance
WORKERS=2                          # Gunicorn workers (Railway: 2-4)
THREADS_PER_WORKER=4              # Thread pool size
```

---

## 4. Deployment Architecture

```
                    ┌─────────────────────┐
                    │  Your Client/Bot    │
                    └──────────┬──────────┘
                               │ HTTPS
                    ┌──────────▼──────────┐
                    │  Railway.app        │  ← Public API Gateway
                    │  (Linux Container)  │     (bentley-mt5-api.up.railway.app)
                    │  mt5_rest.py        │
                    │  (Flask + Gunicorn) │
                    └──────────┬──────────┘
                               │ HTTP/Internal
            ┌──────────────────▼──────────────────┐
            │                                     │
            │  Option A: Railway Proxy            │
            │  (MT5 calls forwarded to Windows)   │
            │                                     │
            └─────────┬──────────────────────────┘
                      │ Reverse Proxy to Windows VPS
        ┌─────────────▼──────────────┐
        │  Windows VPS               │
        │  (Production MT5 Trading)  │
        │  mt5_rest.py               │
        │  (Direct MT5 Connector)    │
        └────────────────────────────┘
                 ↓
        ┌────────────────┐
        │ MetaTrader 5   │
        │ Terminal       │
        └────────────────┘
```

---

## 5. API Endpoints (via Railway URL)

### Health Check
```bash
GET https://bentley-mt5-api.up.railway.app/health

Response:
{
  "status": "ok",
  "service": "mt5-bridge"
}
```

### Account Info
```bash
GET https://bentley-mt5-api.up.railway.app/account

Response:
{
  "success": true,
  "data": {
    "login": 12345,
    "company": "MetaQuotes",
    "server": "MetaQuotes-Demo",
    "balance": 10000.00,
    "equity": 10050.00,
    "credit": 0.00,
    "leverage": 100,
    "margin_used": 50.00,
    "margin_free": 9950.00,
    "margin_level": 20100.00
  }
}
```

### Get Positions
```bash
GET https://bentley-mt5-api.up.railway.app/positions

Response:
{
  "success": true,
  "data": [
    {
      "ticket": 1001,
      "symbol": "EURUSD",
      "type": 0,
      "volume": 1.0,
      "open_price": 1.0850,
      "current_price": 1.0860,
      "profit": 10.00
    }
  ]
}
```

### Place Trade
```bash
POST https://bentley-mt5-api.up.railway.app/trade

Body:
{
  "symbol": "EURUSD",
  "action": "buy",
  "volume": 0.1,
  "price": 1.0850,
  "tp": 1.0900,
  "sl": 1.0800
}

Response:
{
  "success": true,
  "ticket": 1002,
  "message": "Trade executed successfully"
}
```

---

## 6. Monitoring & Logs

### Railway Logs
1. Go to Railway Dashboard → Bentley MT5 API project
2. Click "Logs" tab
3. View real-time application output

### View Logs Command
```bash
# Railway CLI (if installed)
railway logs -f
```

### Common Log Patterns

| Pattern | Meaning |
|---------|---------|
| `Starting Gunicorn` | Server starting successfully |
| `Connection refused` | Windows VPS unreachable |
| `MT5Connector not found` | Module import issue |
| `Port already in use` | Deployment conflict |

---

## 7. Troubleshooting

### Issue: Docker Build Fails
**Solution**: Check `requirements.txt` for platform-specific packages. Remove `mt5-connector` if present (Windows-only).

```bash
# In Railway Logs, look for:
# "error: Microsoft Visual C++ 14.0 is required"
```

### Issue: /health Returns 503 Error
**Solution**: 
1. Verify `MT5_USER`, `MT5_PASSWORD`, `MT5_HOST` variables set
2. Windows VPS must be running and accessible
3. Check Firewall rules on Windows VPS

### Issue: Timeout on Trade Requests
**Solution**:
1. Railway has 120-second timeout limit (standard tier)
2. Upgrade to Railway Pro tier for longer timeouts, or
3. Implement async job queue for long-running operations

```bash
# Test from Railway container
railway run curl http://localhost:8080/health
```

### Issue: Connection to Windows VPS Fails
**Possible causes**:
- Firewall blocking port 8080 on Windows VPS
- Windows VPS IP changed (update Railway variables)
- Network connectivity issue

**Test from Railway**:
```bash
# Via Railway CLI
railway run ping YOUR_WINDOWS_VPS_IP
railway run curl http://YOUR_WINDOWS_VPS_IP:8080/health
```

---

## 8. Advanced Configuration

### Enable Custom Domain
1. Railway Dashboard → Project Settings → Custom Domain
2. Add your domain (e.g., `api.bentleybot.com`)
3. Update DNS CNAME to Railway domain
4. Update client code to use custom domain

### Scale Replicas
1. Railway Dashboard → Deployment Settings
2. Set number of replicas (for load balancing)
3. Railway automatically distributes traffic

### Environment Secrets
For sensitive credentials:
```bash
# Use Railway Secrets (encrypted at rest)
# Dashboard → Environment → Add Service Variable
# Then reference in mt5_rest.py:
import os
mt5_password = os.getenv("MT5_PASSWORD")  # Retrieved securely
```

---

## 9. Production Checklist

- [ ] Railway project created and named `bentley-mt5-api`
- [ ] All environment variables configured
- [ ] Dockerfile builds successfully
- [ ] `/health` endpoint responds with 200 status
- [ ] Connected to Windows VPS with MT5
- [ ] Windows Firewall allows port 8080
- [ ] Tested `/account` endpoint (returns balance data)
- [ ] Tested `/trade` endpoint (executes sample order)
- [ ] Monitoring/logging configured
- [ ] Custom domain set up (optional)
- [ ] Backup/disaster recovery plan documented

---

## 10. Windows VPS Production Setup

For live trading, use [deploy_windows_vps.ps1](./scripts/deploy_windows_vps.ps1):

```powershell
# Run as Administrator on Windows VPS
.\scripts\deploy_windows_vps.ps1 -MTUser "12345" -MTPassword "pass" -MTHost "broker.com"
```

This script:
1. Clones repository
2. Sets up Python virtual environment
3. Installs dependencies
4. Configures MT5 credentials
5. Creates startup scripts
6. Configures Windows Firewall
7. (Optional) Creates Windows Service

**Then point Railway to the Windows VPS URL** in environment variables.

---

## 11. Migration from Development

### From Local Testing
```bash
# Before: Local Flask development
python mt5_rest.py

# After: Railway containerized deployment
# (No local server needed, Railway hosts it)
```

### From Docker Desktop
```bash
# Before: Docker Desktop local testing
docker run -p 8080:8080 bentley-mt5-api

# After: Railway manages containers
# (Update CI/CD to use Railway CLI or GitHub integration)
```

---

## 12. Support & Resources

- **Railway Documentation**: https://docs.railway.app
- **Docker Best Practices**: https://docs.docker.com/develop/dev-best-practices/
- **Flask Deployment**: https://flask.palletsprojects.com/en/2.3.x/deployment/
- **MT5 Python Connector**: https://www.mql5.com/en/docs/integration/python_metatrader5

---

## 13. Next Steps

1. **Create Railway Project** (bentley-mt5-api at railway.app)
2. **Set Environment Variables** (MT5 credentials)
3. **Verify Deployment** (`curl /health`)
4. **Set Up Windows VPS** (run deploy_windows_vps.ps1)
5. **Configure API Gateway** (Railway → Windows VPS connection)
6. **Begin Live Trading** (test small orders first)

---

**Last Updated**: 2025-01-28  
**Status**: Production Ready  
**Deployment Model**: Railway Linux Gateway + Windows VPS Production
