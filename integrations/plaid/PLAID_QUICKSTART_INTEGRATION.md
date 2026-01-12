# Plaid Quickstart Docker Integration Guide

## 🎯 Overview

You're integrating your **Streamlit frontend** with the **Plaid quickstart Docker backend**. This is the perfect way to test the flow before moving to production.

---

## 📋 Setup Checklist

### ✅ Step 1: Verify Docker Backend is Running

```bash
# Check if container is running
docker ps

# You should see something like:
# CONTAINER ID   IMAGE                    PORTS
# abc123def456   plaid-quickstart-server  0.0.0.0:8000->8000/tcp
```

**If not running:**
```bash
cd plaid-quickstart
docker-compose up
```

**Check logs:**
```bash
docker-compose logs -f
```

---

### ✅ Step 2: Find the Correct Port

The backend might be on different ports:
- **Python/Flask:** `http://localhost:8000`
- **Node.js/Express:** `http://localhost:8080`
- **Development server:** `http://localhost:3000`

**Test which port works:**
```bash
# Test port 8000
curl http://localhost:8000/

# Test port 8080
curl http://localhost:8080/

# Test port 3000
curl http://localhost:3000/
```

---

### ✅ Step 3: Verify Backend Endpoints

Your backend should expose these endpoints:

```bash
# Create link token
curl -X POST http://localhost:8000/api/create_link_token \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}'

# Should return:
# {"link_token": "link-sandbox-...", "expiration": "..."}
```

---

### ✅ Step 4: Run Test Page

```bash
# From your project root
streamlit run test_plaid_quickstart.py
```

This will open: `http://localhost:8501`

**Update the backend URL** in the page if needed (8080, 3000, etc.)

---

## 🔧 Integration Steps

### Access the Test Page

**In BBBot multi-page app:**
1. Start Streamlit: `streamlit run streamlit_app.py`
2. Open browser: `http://localhost:8501`
3. Click **🏦 Plaid Test** in the sidebar
4. Update Backend URL to: `http://localhost:5001`

### 1. **Click "Open Plaid Link"**
   - The test page will call your Docker backend's `/api/create_link_token`
   - Backend generates a link token
   - Plaid Link widget initializes with that token

### 2. **Select Bank (Sandbox)**
   - Choose "Chase" or "Bank of America"
   - Click Continue

### 3. **Login with Test Credentials**
   ```
   Username: user_good
   Password: pass_good
   MFA Code: 1234 (if prompted)
   ```

### 4. **Token Exchange (Automatic)**
   - Plaid Link returns a `public_token`
   - Frontend sends it to `/api/set_access_token`
   - Backend exchanges for `access_token`
   - Backend stores access token in memory/database

### 5. **Fetch Transactions**
   - Use date range picker
   - Click "Fetch Transactions"
   - Calls `/api/transactions` on your backend
   - Backend uses stored access token to fetch from Plaid

---

## 🎨 What the Files Do

### `plaid_quickstart_connector.py`
**Purpose:** Python client to interact with your Docker backend

**Key Functions:**
- `create_link_token()` → POST to `/api/create_link_token`
- `exchange_public_token()` → POST to `/api/set_access_token`
- `get_transactions()` → POST to `/api/transactions`
- `health_check()` → Verifies backend is running

### `test_plaid_quickstart.py`
**Purpose:** Streamlit test page to verify integration

**Features:**
- Backend health check
- Interactive Plaid Link widget
- Transaction fetching
- Troubleshooting guides

---

## 🐛 Troubleshooting

### Issue: "Backend Offline"

**Check if Docker is running:**
```bash
docker ps
```

**Start the backend:**
```bash
cd plaid-quickstart
docker-compose up
```

---

### Issue: "Connection Refused"

**Try different ports:**
- Current: `5001` (Python backend)
- Alternative: `8080` (Node backend)
- Frontend: `3000` (React)

**Check Docker port mapping:**
```bash
docker ps
# Look at PORTS column: 0.0.0.0:5001->8000/tcp (Python backend)
```

---

### Issue: "CORS Error"

**Symptoms:**
- Browser console shows: `Access-Control-Allow-Origin error`
- Backend logs show request but no response

**Solution:**
Add CORS headers to your Docker backend:

**If Python (Flask):**
```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["http://localhost:8501"])
```

**If Node.js (Express):**
```javascript
const cors = require('cors');
app.use(cors({ origin: 'http://localhost:8501' }));
```

---

### Issue: "Invalid Credentials"

**Check .env file in plaid-quickstart:**
```bash
cd plaid-quickstart
cat .env
```

**Should contain:**
```
PLAID_CLIENT_ID=68b8718ec2...
PLAID_SECRET=1849c40901...
PLAID_ENV=sandbox
```

**Restart after editing:**
```bash
docker-compose down
docker-compose up --build
```

---

### Issue: "Token Exchange Failed"

**Check backend logs:**
```bash
docker-compose logs -f
```

**Verify endpoint exists:**
```bash
curl -X POST http://localhost:8000/api/set_access_token \
  -H "Content-Type: application/json" \
  -d '{"public_token": "test"}'
```

---

## 📊 Expected Flow

```
┌─────────────┐
│  Streamlit  │
│  Frontend   │
└──────┬──────┘
       │ 1. Request link token
       │ POST /api/create_link_token
       ▼
┌─────────────┐
│   Docker    │
│   Backend   │ ← Your local Plaid quickstart
└──────┬──────┘
       │ 2. Call Plaid API
       │ Generate link token
       ▼
┌─────────────┐
│  Plaid API  │
│  (Sandbox)  │
└──────┬──────┘
       │ 3. Return link token
       │ link-sandbox-abc123...
       ▼
┌─────────────┐
│  Streamlit  │
│  Plaid Link │ ← User connects bank
└──────┬──────┘
       │ 4. Return public token
       │ public-sandbox-xyz789...
       ▼
┌─────────────┐
│   Docker    │
│   Backend   │
└──────┬──────┘
       │ 5. Exchange for access token
       │ POST /item/public_token/exchange
       ▼
┌─────────────┐
│  Plaid API  │
└──────┬──────┘
       │ 6. Return access token
       │ access-sandbox-abc123...
       ▼
┌─────────────┐
│   Docker    │
│   Backend   │ ← Stores access token
└─────────────┘
```

---

## ✅ Success Checklist

After successful integration, you should see:

- [x] ✅ Backend health check passes
- [x] ✅ Link token generated (link-sandbox-...)
- [x] ✅ Plaid Link opens successfully
- [x] ✅ Can login with test credentials
- [x] ✅ Token exchange completes
- [x] ✅ Can fetch transactions
- [x] ✅ Transactions display in table

---

## 🚀 Next Steps

Once everything works with the Docker backend:

1. **Understand the flow** - Review Docker backend code
2. **Replicate in Appwrite** - Port the logic to your Functions
3. **Deploy to production** - Move from sandbox to production
4. **Add to Streamlit** - Integrate with your main app

---

## 📚 Reference

### Docker Backend Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/create_link_token` | POST | Generate link token |
| `/api/set_access_token` | POST | Exchange public token |
| `/api/transactions` | POST | Fetch transactions |
| `/api/accounts` | GET | Get connected accounts |
| `/api/balance` | GET | Get account balances |

### Plaid Sandbox Test Credentials

| Field | Value |
|-------|-------|
| Bank | Chase or Bank of America |
| Username | `user_good` |
| Password | `pass_good` |
| MFA | `1234` |

### Useful Commands

```bash
# Start Python backend (recommended)
cd C:\Users\winst\plaid-quickstart
docker compose up python -d

# Start all services
docker-compose up

# Stop backend
docker-compose down

# Restart with rebuild
docker-compose up --build

# View logs
docker-compose logs -f

# Check backend health
curl http://localhost:8000/

# Test link token creation
curl -X POST http://localhost:8000/api/create_link_token \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test"}'
```

---

**Last Updated:** January 9, 2026  
**Status:** ✅ Ready for Testing
