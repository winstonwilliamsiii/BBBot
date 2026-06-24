# BBBot Auth Validation — Quick Reference Card

## TL;DR: 5-Minute Bot Startup Checklist

Before running **any bot** (Titan, Vega, Rigel, Dogon, Orion, Draco, Altair, Procryon, Hydra, Triton, Dione, Cephei, Rhea, Jupicita):

### Step 1: Airbyte Cloud ✅
```bash
# Get API key from https://cloud.airbyte.com/workspaces/{WS_ID}/settings/api-keys
export AIRBYTE_API_KEY=<your_key>
export AIRBYTE_CONNECTION_ID=<your_connection_id>
export AIRBYTE_API_URL=https://api.airbyte.com/v1

# Test in Postman folder 6: List Workspaces (Validates API Key)
# Expected: 200 OK
```

### Step 2: JWT Token ✅
```bash
# Option A: Get token from Control Center /token endpoint
curl -X POST http://localhost:5001/token \
  -H "Content-Type: application/json" \
  -d '{"username":"bentley_bots","password":"<password>"}'

# Option B: Use pre-generated token from .env
export JWT_TOKEN=$(cat .env | grep JWT_TOKEN | cut -d= -f2)

# Test in Postman folder 5: Decode JWT + Assert Not Expired
# Expected: All tests pass
```

### Step 3: Environment Variables ✅
```bash
# .env should have:
AIRBYTE_API_KEY=...
AIRBYTE_CONNECTION_ID=...
AIRBYTE_API_URL=https://api.airbyte.com/v1
JWT_SECRET_KEY=...
BOT_USERNAME=bentley_bots
BOT_PASSWORD=...
```

### Step 4: Control Center Running ✅
```bash
# Confirm Main.py is running on port 5001
curl -s http://localhost:5001/health | jq .
# Expected: {"status":"ok"} or similar
```

### Step 5: Start Bot ✅
```powershell
# Run your bot (example: Titan)
& "C:\Users\winst\BentleyBudgetBot\start_bot_mode.ps1" -Bot Titan -Mode ON

# Check logs for "Authorization: Bearer" in request headers
# Expected: No 401 Unauthorized errors
```

---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | JWT token is invalid/expired | Refresh token via `/token` endpoint |
| `403 Forbidden` | JWT valid but bot lacks permissions | Check user role in JWT payload |
| `Airbyte API key invalid` | `AIRBYTE_API_KEY` is wrong/expired | Regenerate at cloud.airbyte.com |
| `Connection not found` | `AIRBYTE_CONNECTION_ID` doesn't match workspace | Run Postman folder 6 → List Connections |
| `Control Center timeout` | Main.py not running on port 5001 | `python -m uvicorn Main:app --port 5001` |
| `JWT token is expired` | Token's `exp` claim is in the past | Refresh token |

---

## Postman Folders at a Glance

| Folder | Purpose | Run Before Bot? | All Tests Pass? |
|--------|---------|---|---|
| 1. Appwrite Function | Plaid integration (optional) | No | N/A |
| 2. Docker Quickstart | Local backend testing | No | N/A |
| 3. Plaid Direct API | Plaid sandbox testing (optional) | No | N/A |
| 4. CashPro | Future banking integration | No | N/A |
| **5. JWT Token Validation** | **Control Center auth** | **YES ✅** | **YES ✅** |
| **6. Airbyte Cloud API** | **Data sync auth** | **YES ✅** | **YES ✅** |

---

## Variable Reference

### Must Set (Before Running Bots)
- `airbyte_api_key` = Your Airbyte Cloud API key
- `jwt_token` = Your JWT Bearer token

### Auto-Populated (After Running Postman Tests)
- `airbyte_workspace_id` ← Folder 6, "List Workspaces"
- `airbyte_connection_id` ← Folder 6, "List Connections"
- `airbyte_job_id` ← Folder 6, "Trigger Sync (Manual Job)"

### Diagnostic Variables
- `jwt_decoded_sub` ← JWT subject (user/bot ID)
- `jwt_decoded_exp` ← JWT expiry (Unix epoch)

---

## One-Liner Health Checks

```bash
# JWT token valid?
curl -s -H "Authorization: Bearer $(echo $JWT_TOKEN)" http://localhost:5001/health

# Airbyte API reachable?
curl -s https://api.airbyte.com/v1/health

# Airbyte API key valid?
curl -s -H "Authorization: Bearer $AIRBYTE_API_KEY" https://api.airbyte.com/v1/workspaces

# Control Center reachable?
curl -s http://localhost:5001/health

# All checks passing?
curl -s http://localhost:5001/health && echo " ✅" || echo " ❌"
```

---

## Import Postman Collection

1. Download: `postman/MansaCapital.postman_collection.json`
2. Open Postman
3. **File** → **Import** → Select file
4. Collection imported! ✅

---

## Run Full Validation Workflow

1. Set `airbyte_api_key` variable in Postman
2. Run Folder 6: **Health Check (No Auth Required)** ✅
3. Run Folder 6: **List Workspaces (Validates API Key)** ✅
4. Run Folder 6: **List Connections** ✅
5. Set `jwt_token` variable in Postman
6. Run Folder 5: **Control Center - Health (No Auth)** ✅
7. Run Folder 5: **Decode JWT + Assert Not Expired** ✅

All green? **Bots are ready to go!** 🚀

---

## Airbyte Job Status Reference

After triggering a sync in Postman folder 6, run **Get Job Status** repeatedly:

| Status | Meaning | Next? |
|--------|---------|-------|
| `pending` | Job queued, waiting to start | Wait 30 seconds, recheck |
| `running` | Sync in progress | Wait, monitor logs in Airbyte UI |
| `succeeded` | Sync complete! Data in warehouse | ✅ Ready for downstream tasks |
| `failed` | Sync failed | Check Airbyte UI for error logs, fix issue, retry |
| `cancelled` | Sync was cancelled | Rare; usually means resource exhaustion |

---

## Environment Variables Cheat Sheet

```bash
# Airbyte Cloud
export AIRBYTE_API_URL=https://api.airbyte.com/v1
export AIRBYTE_API_KEY=<your_key_from_cloud.airbyte.com>
export AIRBYTE_CONNECTION_ID=<your_connection_id>
export AIRBYTE_WORKSPACE_ID=<your_workspace_id>

# JWT / Control Center
export JWT_SECRET_KEY=<min_32_char_secret>
export BOT_USERNAME=bentley_bots
export BOT_PASSWORD=<secure_password>
export JWT_TOKEN=<generated_or_fetched_token>

# Optional
export CONTROL_CENTER_URL=http://localhost:5001
export AIRBYTE_LOCAL_API_URL=http://localhost:8001/api/v1  # If self-hosted
```

---

## Document Files

Save these in `postman/` for team reference:

- **README_SETUP.md** ← Start here (3-minute setup)
- **AIRBYTE_JWT_AUTH_RESOLUTION.md** ← Full Airbyte guide
- **JWT_TOKEN_GENERATION_GUIDE.md** ← Token endpoint setup
- **QUICK_REFERENCE_CARD.md** ← This file

---

## Still Having Issues?

1. **Open Postman Console** (View → Show Postman Console)
2. **Run failing test** (pre-request + test scripts print to console)
3. **Check 3 things**:
   - HTTP status code (401 = auth issue, 404 = not found, 500 = server error)
   - Response body (error message)
   - Pre-request script output (variable decoding, token validation)
4. **Compare with guides** above or in the docs

Good luck! 🚀
