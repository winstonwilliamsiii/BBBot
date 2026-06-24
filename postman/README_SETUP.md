# Postman Validation Suite — Complete Setup Guide

## What Was Fixed

Your Postman collection (`MansaCapital.postman_collection.json`) was **corrupted with missing sections** and **lacked auth validation workflows**. It's now rebuilt with:

✅ **6 validation folders** (Appwrite, Docker, Plaid, CashPro, JWT, **Airbyte Cloud**)  
✅ **JWT pre-request + test scripts** for token decode & expiry checks  
✅ **Airbyte Cloud API test suite** mirroring what `Airbyt_sync_DAG_3.py` needs  
✅ **Auto-setting collection variables** (workspaceId, connectionId, jobId)  
✅ **Clear error messaging** for 401/403/500 failures  

---

## Files You Got

| File | Purpose |
|------|---------|
| `postman/MansaCapital.postman_collection.json` | **Updated Postman collection** — import this into Postman |
| `postman/AIRBYTE_JWT_AUTH_RESOLUTION.md` | **Step-by-step resolution guide** for Airbyte auth failures |
| `postman/JWT_TOKEN_GENERATION_GUIDE.md` | **How to add `/token` endpoint** to Main.py if not present |

---

## 3-Minute Setup

### 1. Import into Postman

1. Open **Postman** (app or web)
2. Click **File** → **Import**
3. Select `postman/MansaCapital.postman_collection.json`
4. Click **Import**

### 2. Set Collection Variables

In Postman, click the collection name → **Variables** tab → set these:

```
airbyte_api_key          = YOUR_AIRBYTE_API_KEY (get from cloud.airbyte.com)
jwt_token                = YOUR_JWT_TOKEN (get from Control Center /token endpoint)
```

(Other variables auto-populate after first requests run.)

### 3. Validate Each Folder

**Folder 5 (JWT):**
- Run: `Control Center - Health (No Auth)` → should 200
- Run: `Decode JWT + Assert Not Expired` → should pass all tests

**Folder 6 (Airbyte):**
- Run: `Health Check (No Auth Required)` → should 200
- Run: `List Workspaces (Validates API Key)` → should 200 and auto-set `airbyte_workspace_id`
- Run: `List Connections` → should 200 and auto-set `airbyte_connection_id`
- Run: `Trigger Sync (Manual Job)` → should 200 and create job
- Run: `Get Job Status` → should show `pending`, `running`, or `succeeded`

If all pass ✅ → your auth is healthy.

---

## Troubleshooting

### JWT Issues

**Problem**: `"401 Unauthorized"` or `"No Authorization header"`  
**Fix**: 
1. Check if Main.py has `/token` endpoint (if not, use JWT_TOKEN_GENERATION_GUIDE.md)
2. Get a valid token and set `jwt_token` variable
3. Run Postman folder 5 tests again

**Problem**: `"JWT token is EXPIRED"` in test output  
**Fix**:
1. Re-run `/token` endpoint to refresh
2. Update `jwt_token` variable
3. Re-run test

### Airbyte Issues

**Problem**: `"401 Unauthorized"` on List Workspaces  
**Fix**:
1. Go to https://cloud.airbyte.com/workspaces/{WS_ID}/settings/api-keys
2. Delete old key, create new one
3. Copy immediately (won't be shown again)
4. Update `airbyte_api_key` in Postman
5. Re-run test

**Problem**: `"404 Not Found"` on List Connections  
**Fix**:
1. Confirm `airbyte_workspace_id` is set (should auto-populate after List Workspaces)
2. If empty, manually set it from cloud.airbyte.com URL
3. Re-run List Connections

**Problem**: Job creation succeeds but status is `"cancelled"` or `"failed"`  
**Fix**:
1. Go to cloud.airbyte.com → your connection → Last Sync
2. Check error logs (usually schema mismatch or source connectivity)
3. Fix the issue in Airbyte
4. Manually trigger again in Postman

---

## Integration Checklist

Before any bot starts, confirm:

- [ ] **Airbyte Cloud account** created at https://cloud.airbyte.com
- [ ] **Connection created** (source → destination)
- [ ] **API key generated** and set as `airbyte_api_key`
- [ ] **Postman folder 6 tests all pass** (health, list workspaces, list connections, trigger, job status)
- [ ] **Main.py has `/token` endpoint** (or you're using pre-generated JWT)
- [ ] **JWT token set** as `jwt_token` in Postman
- [ ] **Postman folder 5 tests all pass** (health, JWT decode, expiry check)
- [ ] **Environment variables set** in `.env` / Streamlit secrets / Railway:
  ```bash
  AIRBYTE_API_URL=https://api.airbyte.com/v1
  AIRBYTE_API_KEY=<your_key>
  AIRBYTE_CONNECTION_ID=<your_connection_id>
  JWT_SECRET_KEY=<your_secret>
  BOT_USERNAME=bentley_bots
  BOT_PASSWORD=<your_password>
  ```
- [ ] **Airflow DAG enabled** and tested manually in UI
- [ ] **Bot services running** (Titan, Vega, Rigel, Dogon, Orion, etc.)

---

## Deep Dives

For detailed info, see:

1. **AIRBYTE_JWT_AUTH_RESOLUTION.md** — Full Airbyte Cloud setup + DAG mapping
2. **JWT_TOKEN_GENERATION_GUIDE.md** — Token endpoint options (service account, OAuth2, pre-generated)

---

## Next Steps

1. ✅ **Import collection** into Postman
2. ✅ **Run folder 5 & 6 tests** to validate auth
3. 📝 **Follow AIRBYTE_JWT_AUTH_RESOLUTION.md** for full Airbyte setup
4. 🔐 **Follow JWT_TOKEN_GENERATION_GUIDE.md** to add `/token` endpoint to Main.py
5. 🤖 **Start your bots** with confidence!

---

## Questions?

Check the FAQ sections in each guide, or re-run Postman tests with **Console** open (View → Show Postman Console) to see detailed pre-request/test script output.

Good luck! 🚀
