# MT5 Bridge Deployment & Connectivity Fix

## Problem Summary
- ❌ Railway `bentley_MT5_bridge` container deployment failing
- ❌ Multi-Broker Trading Hub MT5 button shows: "Network error reaching MT5 bridge: ConnectionError"
- ❌ FastAPI dependencies missing from main requirements.txt

## Root Causes

### 1. Dockerfile Build Failure (Railway)
The Dockerfile expects `mt5/terminal/` directory (containing terminal64.exe) but:
- `mt5/terminal/` is in `.gitignore` (local files only)
- Railway build context doesn't include it
- Build fails at: `RUN test -f "/root/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe"`

### 2. Missing FastAPI Dependencies
- `scripts/mt5_rest.py` requires FastAPI/Uvicorn
- These aren't in `requirements.txt`
- Local MT5 bridge server can't start

### 3. Incorrect API URL Routing
- Frontend defaults to `http://localhost:8002` (local)
- Railway needs external MT5 server URL
- Production environment variables not configured

---

## Solutions

### Solution 1: Fix Local Development (Immediate)

#### Step 1: Add FastAPI to requirements

```bash
pip install fastapi[standard] uvicorn>=0.30.0
```

Or add to `requirements.txt`:

```
# MT5 REST bridge (FastAPI)
fastapi[standard]>=0.115.0
uvicorn[standard]>=0.30.0
```

#### Step 2: Start MT5 desktop application
- Open MetaTrader 5 on your local machine
- Ensure you're logged into your trading account
- Keep it running in background

#### Step 3: Start the MT5 REST bridge server

```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Start the bridge server on port 8080
$env:PORT = 8080
python scripts/mt5_rest.py
```

Expected output:
```
[entrypoint] Starting MT5 REST bridge
INFO:     Uvicorn running on http://0.0.0.0:8080
```

#### Step 4: Verify connectivity

```bash
# Test bridge health in another terminal
curl http://localhost:8080/health

# Response should be:
# {"status":"ok","service":"mt5-bridge"}
```

#### Step 5: Connect via Multi-Broker Dashboard

1. Open Streamlit: `streamlit run streamlit_app.py`
2. Navigate to **🌐 Multi-Broker Trading Hub**
3. Click **"🏥 Test MT5 Bridge"** button - should show ✅
4. Enter credentials and click **"Connect AXI"** or **"Connect MT5"**

---

### Solution 2: Fix Railway Deployment

Create a **conditional Dockerfile** that handles missing MT5 terminal files:

#### Option A: Skip Docker MT5, Use External Server (Recommended)

**File: `railway.json` (NEW)**

```json
{
  "services": [
    {
      "name": "bentley-mt5-bridge",
      "dockerfile": "Dockerfile.mt5-lightweight",
      "environmentVariables": {
        "PORT": "8080",
        "MT5_API_MODE": "client",
        "MT5_SERVER_URL": "${{ secrets.EXTERNAL_MT5_SERVER }}"
      }
    }
  ]
}
```

**File: `Dockerfile.mt5-lightweight` (NEW)**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install only Python dependencies (no Wine/MT5 desktop)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir fastapi[standard]>=0.115.0 uvicorn[standard]>=0.30.0

COPY scripts/mt5_rest.py .
COPY pages/api/mt5_bridge.py ./pages/api/

EXPOSE 8080

# Run REST bridge (connects to external MT5 server)
CMD ["python", "scripts/mt5_rest.py"]
```

#### Option B: Conditional Dockerfile (Fallback)

**File: `Dockerfile` (REPLACE)**

```dockerfile
FROM python:3.11-slim as base

# ── Check if MT5 terminal files exist in build context ──────────────────────
# If not available, skip Wine/MT5 setup and run in client mode
FROM base as check-mt5
COPY mt5 /tmp/mt5 2>/dev/null || true
RUN if [ -f "/tmp/mt5/terminal/terminal64.exe" ]; then echo "mt5" > /tmp/mt5_mode; else echo "client" > /tmp/mt5_mode; fi

# ── Stage 1: MT5 Server (if terminal files exist) ──────────────────────────
FROM base as mt5-server
# ... existing Wine/MT5 setup code ...

# ── Stage 2: MT5 Client (if terminal files missing) ──────────────────────────
FROM base as mt5-client

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir fastapi[standard]>=0.115.0 uvicorn[standard]>=0.30.0

COPY scripts/mt5_rest.py .
COPY pages/api/mt5_bridge.py ./pages/api/

EXPOSE 8080
CMD ["python", "scripts/mt5_rest.py"]

# ── Final: Route to correct stage ──────────────────────────────────────────
FROM mt5-client
```

---

### Solution 3: Configure Environment Variables

#### For Production (Railway)

Create `.streamlit/secrets-production.toml`:

```toml
# Production MT5 configuration
[production]
MT5_API_URL = "https://bentley-mt5-bridge.railway.app"  # Your Railway app URL
MT5_MODE = "external"  # Use external MT5 server
```

Set Railway environment variables:
```
STREAMLIT_CLIENT_THEME_MODE=dark
MT5_API_URL=https://bentley-mt5-bridge.railway.app
MT5_MODE=external
```

#### For Local Development

`.streamlit/secrets.toml`:

```toml
# Local MT5 configuration
[local]
MT5_API_URL = "http://localhost:8080"  # Local REST bridge
MT5_USER = "your_account_number"
MT5_PASSWORD = "your_password"
MT5_HOST = "your_broker_server"  # e.g., "mt5-demo07.axi.com"
MT5_PORT = 443
```

---

## Implementation Checklist

### For Immediate Local Fix ✅

- [ ] Install FastAPI: `pip install fastapi[standard] uvicorn`
- [ ] Start MT5 desktop application (log in)
- [ ] Start MT5 bridge: `python scripts/mt5_rest.py`
- [ ] Test health endpoint: `curl http://localhost:8080/health`
- [ ] Refresh Streamlit and test MT5 button

### For Railway Deployment ✅

- [ ] Choose Option A (lightweight) or Option B (conditional)
- [ ] Create appropriate Dockerfile variant
- [ ] Update `railway.json` with service config
- [ ] Set environment variables in Railway dashboard
- [ ] Configure external MT5 server URL
- [ ] Deploy and test

### For Code Cleanup ✅

- [ ] Add FastAPI to `requirements-local.txt` (if not present)
- [ ] Update `scripts/mt5_rest.py` shebang if needed
- [ ] Add FastAPI to dependency documentation
- [ ] Document MT5 bridge deployment architecture

---

## Testing Commands

```bash
# Test MT5 bridge health
curl -X GET http://localhost:8080/health

# Test connection (if credentials configured)
curl -X POST http://localhost:8080/connect \
  -H "Content-Type: application/json" \
  -d '{"user":"YOUR_ACCOUNT","password":"YOUR_PASSWORD","host":"YOUR_BROKER"}'

# View bridge logs
Get-Content logs/mt5_bridge.log -Wait
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│  Streamlit (Multi-Broker Dashboard)    │
│  http://localhost:8501                 │
└────────────┬────────────────────────────┘
             │ HTTP Requests
             ↓
┌─────────────────────────────────────────┐
│  MT5 REST Bridge                        │
│  LOCAL: http://localhost:8080           │
│  RAILWAY: https://...railway.app        │
└────────────┬────────────────────────────┘
             │ 
    ┌────────┴──────────┐
    ↓                   ↓
LOCAL: MT5 Terminal  EXTERNAL: MT5 Server
(Wine/Desktop)       (VPS/Cloud)
```

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: fastapi` | FastAPI not installed | `pip install fastapi[standard]` |
| `ConnectionError: localhost:8080` | MT5 bridge not running | Start with `python scripts/mt5_rest.py` |
| `MT5 terminal exited early` | MT5 not running locally | Start MetaTrader 5 desktop app |
| Railway build fails | `mt5/terminal/` missing | Use lightweight Dockerfile (Option A) |
| Connection timeout | Firewall blocking | Check firewall/antivirus settings |

---

## Next Steps

1. **Immediately**: Apply Solution 1 (local development fix)
2. **This week**: Choose and implement Railway solution (Option A or B)
3. **Ongoing**: Monitor bridge connectivity and add health checks
