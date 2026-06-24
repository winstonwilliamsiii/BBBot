# BBBot JWT + Airbyte Auth Resolution Guide

## Problem Summary

Your bots are failing auth because:
1. **Airbyte is not configured** — `AIRBYTE_API_KEY`, `AIRBYTE_CONNECTION_ID`, and `AIRBYTE_API_URL` are missing or placeholder values in `.env` / environment.
2. **JWT tokens are stale or not being validated** — The Control Center API (Main.py on port 5001) requires a valid JWT Bearer token, but there's no pre-flight validation before bots attempt to use it.
3. **No token inspection workflow** — Developers have no way to quickly check if a JWT is valid before running bots.

---

## Solution: Use the Updated Postman Collection

The refreshed **MansaCapital.postman_collection.json** now includes:

### Folder 5: JWT Token Validation
- **Decode JWT + Assert Not Expired**: Decodes your JWT in the pre-request script, asserts it hasn't expired, and hits `/health` to verify the Control Center accepts it.
- **Control Center - Health (No Auth)**: Tests unauthenticated access to confirm the FastAPI server is reachable.

### Folder 6: Airbyte Cloud API
- **Health Check (No Auth Required)**: Confirms you can reach `api.airbyte.com/v1`.
- **List Workspaces (Validates API Key)**: 200 = API key is valid; 401 = key is wrong or expired. Test script auto-sets `airbyte_workspace_id`.
- **List Connections**: Lists connections in your workspace and auto-sets `airbyte_connection_id`.
- **Trigger Sync (Manual Job)**: Calls the same endpoint as `Airbyt_sync_DAG_3.py` — tests job creation.
- **Get Job Status**: Polls the job to monitor progress (pending → running → succeeded).

---

## Step-by-Step Resolution

### 1. Get Your Airbyte Cloud Credentials

1. Go to **https://cloud.airbyte.com**
2. Sign in or create a free account
3. Create a **Source** (e.g., Postgres, MySQL, Snowflake) with your data
4. Create a **Destination** (e.g., Snowflake, BigQuery) for data to land
5. Create a **Connection** between them
6. Go to **Settings** → **API Keys** → **Create New Key**
7. Copy the key (this is `AIRBYTE_API_KEY`)
8. Find your **Workspace ID** in the URL: `https://cloud.airbyte.com/workspaces/{WORKSPACE_ID}/dashboard`
9. Find your **Connection ID** in the Connections list URL: `https://cloud.airbyte.com/workspaces/{WS_ID}/connections/{CONNECTION_ID}`

### 2. Update Your Environment Variables

Add to your `.env` file (or Streamlit secrets / Railway environment):

```bash
# Airbyte Cloud
AIRBYTE_API_URL=https://api.airbyte.com/v1
AIRBYTE_API_KEY=<your_api_key_from_step_7>
AIRBYTE_CONNECTION_ID=<your_connection_id_from_step_9>
AIRBYTE_WORKSPACE_ID=<your_workspace_id_from_step_8>
```

### 3. Validate in Postman (Folder 6)

1. Open the **MansaCapital.postman_collection.json** in Postman
2. Go to the **6. Airbyte Cloud API** folder
3. Set collection variables:
   - `airbyte_api_key` = the key from step 7
   - `airbyte_api_url` = `https://api.airbyte.com/v1` (default, no change)
4. Run **Health Check (No Auth Required)** → should return 200
5. Run **List Workspaces (Validates API Key)** → should return 200 and auto-set `airbyte_workspace_id`
6. Run **List Connections** → should find your connection and auto-set `airbyte_connection_id`
7. Run **Trigger Sync (Manual Job)** → should return 200 and create a job
8. Run **Get Job Status** → should show job status (pending, running, or succeeded)

**If any test fails:**
- 401 = API key is wrong or expired → regenerate at cloud.airbyte.com
- 404 = workspace or connection ID doesn't exist → double-check values
- 500 = Airbyte service issue → wait a few minutes and retry

### 4. Get Your JWT Token

Your bots need a JWT to call the Control Center API (Main.py on port 5001).

**If Main.py has a `/login` or `/token` endpoint:**
```bash
curl -X POST http://localhost:5001/token \
  -H "Content-Type: application/json" \
  -d '{"username":"your_bot_user","password":"your_password"}'
```
Copy the returned `access_token`.

**If you're generating JWTs manually in the codebase:**
Look for code patterns like:
```python
from jose import jwt
token = jwt.encode(
    {"sub": "bot_user", "exp": datetime.utcnow() + timedelta(hours=1)},
    "SECRET_KEY",
    algorithm="HS256"
)
```

### 5. Validate JWT in Postman (Folder 5)

1. Set collection variable `jwt_token` = your token from step 4
2. Run **Decode JWT + Assert Not Expired**:
   - Pre-request script decodes the JWT
   - Tests check expiry and hit `/health`
   - If all pass: ✅ JWT is valid and Control Center accepts it
   - If test fails: ❌ Token is expired or invalid → refresh in step 4

3. Run **Control Center - Health (No Auth)** → confirms server is running on port 5001

---

## Mapping to DAG Code

The Postman folder 6 mirrors what `airflow/dags/Airbyt_sync_DAG_3.py` does:

| Postman Request | DAG Code | Env Variable |
|---|---|---|
| List Workspaces | (metadata lookup) | `AIRBYTE_API_URL` |
| List Connections | (metadata lookup) | `AIRBYTE_API_URL` |
| Trigger Sync (Manual Job) | `requests.post(f"{api_url}/jobs", json={"connectionId": connection_id, "jobType": "sync"})` | `AIRBYTE_CONNECTION_ID` |
| Get Job Status | (polling after trigger) | (captured from response) |

**Before running the DAG**, validate all 4 tests pass in Postman.

---

## Troubleshooting

### "401 Unauthorized" on List Workspaces
**Cause**: API key is invalid, expired, or hasn't been generated yet.
**Fix**:
1. Go to https://cloud.airbyte.com/workspaces/{WS_ID}/settings/api-keys
2. Delete the old key
3. Create a new one
4. Copy immediately (it won't be shown again)
5. Update `airbyte_api_key` in Postman and `.env`

### "JWT token is EXPIRED" in Decode JWT test
**Cause**: Your token's `exp` claim is in the past.
**Fix**:
1. Refresh the token (run `/login` endpoint or regenerate with longer TTL)
2. Update `jwt_token` in Postman
3. Re-run the test

### Control Center returns 404 on /api/status
**Cause**: Endpoint doesn't exist or is named differently.
**Fix**:
1. Check Main.py for actual protected routes
2. Update the URL in the Postman request to match
3. Or test with a route you know exists (e.g., `/health` should always work)

### Job creation succeeds but status is "cancelled"
**Cause**: Airbyte detected an issue (usually schema mismatch or connection error).
**Fix**:
1. Go to https://cloud.airbyte.com/workspaces/{WS_ID}/connections/{CONN_ID}
2. Click the connection → check **Last Sync** for error logs
3. Fix the issue (e.g., update schema mapping, check source connectivity)
4. Retry in Postman

---

## Bot Integration Checklist

Before starting any bot (Titan, Vega, Rigel, Dogon, Orion, etc.):

- [ ] **Airbyte**
  - [ ] `AIRBYTE_API_KEY` is set and valid (passes Postman List Workspaces)
  - [ ] `AIRBYTE_CONNECTION_ID` is set (from List Connections)
  - [ ] `AIRBYTE_API_URL` is set to `https://api.airbyte.com/v1`
  - [ ] Manual trigger in Postman succeeds

- [ ] **JWT / Control Center**
  - [ ] `jwt_token` collection variable is set in Postman
  - [ ] Token decodes successfully (pre-request script passes)
  - [ ] Token is not expired (test passes)
  - [ ] Control Center is running on port 5001 (health check passes)
  - [ ] Bearer token is accepted by protected endpoint (no 401/403)

- [ ] **Airflow**
  - [ ] `AIRFLOW_HOME` is set (usually `~/airflow`)
  - [ ] `Airbyt_sync_DAG_3.py` (or equivalent) has `AIRBYTE_CONNECTION_ID` and `AIRBYTE_API_KEY` from .env
  - [ ] DAG is enabled in Airflow UI
  - [ ] First manual trigger in Airflow UI succeeds

---

## FAQ

**Q: Do I need Airbyte Docker if I'm using Airbyte Cloud?**  
A: No. Airbyte Cloud is fully hosted at `api.airbyte.com`. You don't need to run local Docker containers. The old Docker-based approach in `start_airbyte_docker.ps1` and `setup_airbyte_fix.ps1` is for the self-hosted version, which requires significant infrastructure management.

**Q: Where do I store these credentials?**  
A: `.env` file (git-ignored), Streamlit secrets, Railway environment variables, or GitHub Actions secrets. **NEVER commit real keys**.

**Q: What if I want self-hosted Airbyte instead of Cloud?**  
A: Run `docker compose -f docker/docker-compose-airbyte.yml up -d` and change `airbyte_api_url` in Postman to `http://localhost:8001/api/v1`. Self-hosted doesn't require API keys, but you'll need to manage the entire Airbyte infrastructure.

**Q: Can I test Airbyte + JWT offline?**  
A: No. Both require network access to their respective services (cloud.airbyte.com and your Control Center endpoint). Confirm connectivity before running Postman tests.

---

## Next Steps

1. **Immediate**: Follow steps 1–5 above and validate all Postman tests pass.
2. **Short-term**: Update your Airflow DAGs to use the validated credentials.
3. **Long-term**: Integrate Postman test results into your CI/CD pipeline to catch auth failures early.

Happy syncing!
