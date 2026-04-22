# Railway MT5 Bridge Deployment Guide

## Overview

The `bentley-mt5-bridge` service on Railway runs a lightweight FastAPI server that acts as a proxy to MetaTrader 5.

## Why It Was Failing

**Previous Dockerfile Issues:**
1. ❌ Required `mt5/terminal/` directory with MT5 desktop binaries
2. ❌ Required Wine + Xvfb for headless MT5 execution
3. ❌ Binaries not committed to git (in `.gitignore`)
4. ❌ Railway builds failed: `terminal64.exe not found`

**New Solution:**
✅ Lightweight FastAPI-only Docker image
✅ Connects to external MT5 server (local machine or cloud)
✅ No Wine/Xvfb dependencies
✅ Faster builds and deployments

## Deployment Steps

### 1. Update Railway Service Configuration

Railway now uses the new `Dockerfile.mt5-bridge` which:
- Installs only Python + FastAPI/Uvicorn
- Exposes port 8080 for MT5 API bridge
- Includes health checks
- No build failures due to missing MT5 terminal files

### 2. Configure Environment Variables in Railway

In your Railway dashboard, set these for the `bentley-mt5-bridge` service:

```
PORT=8080
HOST=0.0.0.0
MT5_REQUEST_TIMEOUT=20
MT5_CONNECT_RETRIES=3
MT5_CONNECT_RETRY_DELAY=1.0
```

### 3. Configure External MT5 Server (Important!)

You have two options:

#### Option A: Use Local MT5 (Development)
- Run MT5 bridge locally on your machine: `python scripts/mt5_rest.py`
- Set in Streamlit secrets:
  ```toml
  MT5_API_URL = "http://localhost:8080"
  ```

#### Option B: Use Remote MT5 Server (Production)
- Set up a VPS/cloud server with MT5 running
- Set in Railway environment or `.streamlit/secrets.toml`:
  ```toml
  MT5_API_URL = "https://your-mt5-server.railway.app"
  MT5_USER = "your_account"
  MT5_PASSWORD = "your_password"
  MT5_HOST = "broker.server.com"
  MT5_PORT = 443
  ```

### 4. Deploy to Railway

```bash
# Using Railway CLI
railway up

# Or push to GitHub (if connected to Railway)
git push origin main
```

Monitor deployment:
```bash
railway status
railway logs --follow
```

## Troubleshooting

### Build Succeeds but Connection Fails

**Error:** `Network error reaching MT5 bridge: ConnectionError`

**Causes & Fixes:**
1. **MT5 bridge not running:**
   - Check Railway logs: `railway logs bentley-mt5-bridge`
   - Verify environment variables are set correctly

2. **Wrong MT5_API_URL in Streamlit:**
   - Streamlit is pointing to `localhost:8080` instead of Railway URL
   - Update `.streamlit/secrets.toml` with correct Railway MT5 bridge URL:
     ```toml
     MT5_API_URL = "https://bentley-mt5-bridge-<random>.railway.app"
     ```

3. **External MT5 server not reachable:**
   - Verify external server URL is correct and accessible
   - Check firewall/security group rules

### Build Fails

**Error:** `ERROR: Build failed`

1. Check logs: `railway logs bentley-mt5-bridge --follow`
2. Common issues:
   - Python package conflicts (run `pip check` locally)
   - Missing dependencies (check `requirements.txt`)
   - Network timeout downloading packages

### Health Check Fails

**Error:** `Health check failed`

1. MT5 bridge service isn't responding to `/health` endpoint
2. Check service logs: `railway logs bentley-mt5-bridge`
3. Verify port 8080 is correctly exposed

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Streamlit App (Bentley Dashboard)              │
│  Deployed on Railway or Streamlit Cloud         │
└────────────┬────────────────────────────────────┘
             │ HTTP Requests (REST API)
             │ Connection to: MT5_API_URL
             ↓
┌─────────────────────────────────────────────────┐
│  bentley-mt5-bridge Service (Railway)           │
│  URL: https://bentley-mt5-bridge-*.railway.app  │
│  Image: python:3.11-slim + FastAPI              │
│  Port: 8080 (internal → 443/external if HTTPS)  │
└────────────┬────────────────────────────────────┘
             │ Routes to external MT5 server
             │ via scripts/mt5_rest.py
             ↓
┌─────────────────────────────────────────────────┐
│  External MT5 Server                            │
│  - Local: http://localhost:8080                 │
│  - Remote: Your VPS/cloud server                │
│  - AXI/FTMO: mt5-demo07.axi.com                 │
└─────────────────────────────────────────────────┘
```

## Monitoring

### Check Service Status

```bash
railway status
```

### View Real-time Logs

```bash
# MT5 bridge logs
railway logs bentley-mt5-bridge --follow

# Entire Railway app logs
railway logs --follow
```

### Manual Health Check

```bash
# Test from command line
curl https://bentley-mt5-bridge-<random>.railway.app/health

# Expected response
{
  "status": "ok",
  "service": "mt5-bridge"
}
```

## Rollback

If deployment issues occur:

```bash
# Revert to previous version
railway rollback

# Or rebuild from scratch
railway down
railway up
```

## Related Documentation

- [MT5 Bridge Fix Guide](./MT5_BRIDGE_FIX.md)
- [MT5 Connection Troubleshooting](./MT5_CONNECTION_TROUBLESHOOTING.md)
- [Multi-Broker README](./MULTI_BROKER_README.md)

## Support

For issues:
1. Check Railway logs first
2. Verify environment variables
3. Test external MT5 server connectivity
4. Review error messages in logs
