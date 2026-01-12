# 🏦 Plaid Test - Quick Reference

## ✅ Setup Complete

Your Plaid Docker backend is running and ready for testing!

---

## 🚀 Access Test Page

### Option 1: Multi-Page Streamlit App (Recommended)

```bash
cd C:\Users\winst\BentleyBudgetBot
.venv\Scripts\Activate.ps1
streamlit run streamlit_app.py
```

Then navigate to **🏦 Plaid Test** in the sidebar

**URL:** `http://localhost:8501`

---

### Option 2: Standalone Test Page

```bash
cd C:\Users\winst\BentleyBudgetBot
.venv\Scripts\Activate.ps1
streamlit run test_plaid_quickstart.py
```

**URL:** `http://localhost:8501`

---

## ⚙️ Configuration

| Setting | Value |
|---------|-------|
| **Backend URL** | `http://localhost:5001` |
| **Test User ID** | `winston_test_123` |
| **Plaid Environment** | `sandbox` |

---

## 🔄 Docker Backend Commands

### Start Backend
```bash
cd C:\Users\winst\plaid-quickstart
docker compose up python -d
```

### Check Status
```bash
docker ps
# Should show: plaid-quickstart-python-1 on port 5001
```

### View Logs
```bash
docker compose logs python -f
```

### Stop Backend
```bash
docker compose down
```

### Restart Backend
```bash
docker compose restart python
```

---

## 🧪 Testing Flow

1. **Check Backend Health**
   - Click "Check Backend Health" button
   - Should show: ✅ Backend is online

2. **Open Plaid Link**
   - Click "Open Plaid Link" button
   - Plaid modal will appear

3. **Select Bank**
   - Choose "Chase" or "Bank of America"
   - Click Continue

4. **Login with Test Credentials**
   ```
   Username: user_good
   Password: pass_good
   MFA Code: 1234 (if prompted)
   ```

5. **Token Exchange**
   - Happens automatically
   - Returns access_token and item_id

6. **Fetch Transactions**
   - Select date range (e.g., last 30 days)
   - Click "Fetch Transactions"
   - View transaction data

---

## 📊 Expected Results

### Successful Link Token Creation
```json
{
  "link_token": "link-sandbox-abc123...",
  "expiration": "2026-01-10T23:59:59Z"
}
```

### Successful Token Exchange
```json
{
  "access_token": "access-sandbox-xyz789...",
  "item_id": "item-sandbox-123..."
}
```

### Sample Transaction
```json
{
  "transaction_id": "txn_123",
  "amount": -12.50,
  "date": "2026-01-09",
  "name": "Starbucks",
  "category": ["Food and Drink", "Restaurants", "Coffee Shop"]
}
```

---

## 🛠️ Troubleshooting

### Backend Offline

**Check if container is running:**
```bash
docker ps
```

**Start backend if stopped:**
```bash
cd C:\Users\winst\plaid-quickstart
docker compose up python -d
```

---

### Port Conflict

If port 5001 is in use, modify docker-compose.yml:

```bash
cd C:\Users\winst\plaid-quickstart
# Edit docker-compose.yml
# Change: ports: ["5001:8000"] to ports: ["5002:8000"]
docker compose up python -d
```

Then update Backend URL in test page to `http://localhost:5002`

---

### CORS Error

**Symptom:** Browser console shows CORS error

**Solution:** Backend should already have CORS enabled for `http://localhost:8501`

If not working, check backend logs:
```bash
docker compose logs python -f
```

---

### Invalid Credentials

Make sure .env file in plaid-quickstart has:
```
PLAID_CLIENT_ID=68b8718ec2f428002456a84c
PLAID_SECRET=1849c4090173dfbce2bda5453e7048
PLAID_ENV=sandbox
```

Restart after changes:
```bash
docker compose restart python
```

---

## 🌐 Endpoints

### Backend (Port 5001)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `http://localhost:5001/api/create_link_token` | POST | Generate link token |
| `http://localhost:5001/api/set_access_token` | POST | Exchange public token |
| `http://localhost:5001/api/transactions` | POST | Fetch transactions |
| `http://localhost:5001/api/accounts` | GET | Get accounts |

### Test Frontend (Port 8501)

| URL | Page |
|-----|------|
| `http://localhost:8501` | Main BBBot app |
| `http://localhost:8501` → 🏦 Plaid Test | Plaid test page (sidebar) |

### Plaid Frontend (Port 3000)

| URL | Purpose |
|-----|---------|
| `http://localhost:3000` | React frontend (optional) |

---

## 📍 File Locations

| File | Path |
|------|------|
| **Test Page** | `c:\Users\winst\BentleyBudgetBot\pages\06_🏦_Plaid_Test.py` |
| **Connector** | `c:\Users\winst\BentleyBudgetBot\frontend\utils\plaid_quickstart_connector.py` |
| **Docker Compose** | `C:\Users\winst\plaid-quickstart\docker-compose.yml` |
| **Backend .env** | `C:\Users\winst\plaid-quickstart\.env` |

---

## ✅ Success Checklist

After successful test, you should see:

- [x] ✅ Backend health check passes
- [x] ✅ Link token generated
- [x] ✅ Plaid Link opens successfully
- [x] ✅ Can login with test credentials
- [x] ✅ Token exchange completes
- [x] ✅ Can fetch transactions
- [x] ✅ Transactions display correctly

---

## 🚀 Next Steps

Once Docker backend works:

1. **Understand the Code**
   - Review `plaid-quickstart/python/server.py`
   - Note how endpoints are structured

2. **Port to Appwrite Functions**
   - Migrate logic from Docker to Appwrite
   - Test with production credentials

3. **Integrate into Personal Budget**
   - Replace test connector with production code
   - Add to `pages/01_💰_Personal_Budget.py`

4. **Deploy to Production**
   - Change PLAID_ENV to `production`
   - Use real bank credentials
   - Enable webhook listeners

---

**Last Updated:** January 10, 2026  
**Status:** ✅ Ready for Testing
**Port:** 5001 (Python backend)
**Streamlit:** http://localhost:8501
