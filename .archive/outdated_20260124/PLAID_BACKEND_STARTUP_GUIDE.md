# Plaid Backend Startup Guide

## Quick Start - How to Run Plaid Backend

### Directory Location
The Plaid quickstart backend is located at:
```
C:\Users\winst\plaid-quickstart
```

### Command to Change Directory
```powershell
cd C:\Users\winst\plaid-quickstart
```

### Start the Backend
Once you're in the correct directory, run:
```powershell
docker compose up -d
```

## What's Happening Now

✅ **Docker Compose is currently building the Plaid backend containers**
- This is the FIRST TIME build, so it will take 5-10 minutes
- Docker is downloading base images (Node, Python, Ruby, Java, Go)
- Building multiple container services for the Plaid quickstart
- Installing dependencies for each service

## Current Status

🔄 **Building in progress...**
- Node.js container - ✅ Complete
- Python container - 🔄 Installing dependencies
- Ruby container - 🔄 Downloading base image
- Java container - 🔄 Downloading Maven image
- Go container - 🔄 Downloading Golang image
- Frontend container - 🔄 Installing npm packages

## When Build Completes

Once the build finishes, you'll see:
```
[+] Running 6/6
 ✔ Container plaid-quickstart-node-1     Started
 ✔ Container plaid-quickstart-python-1   Started
 ✔ Container plaid-quickstart-ruby-1     Started
 ✔ Container plaid-quickstart-java-1     Started
 ✔ Container plaid-quickstart-go-1       Started
 ✔ Container plaid-quickstart-frontend-1 Started
```

## Verify Backend is Running

After the containers start, run the diagnostic:
```powershell
cd C:\Users\winst\BentleyBudgetBot
python diagnose_integration_errors.py
```

You should see:
```
✅ Plaid backend is RUNNING (http://localhost:5001)
```

## Test the Plaid Link Button

1. Start the Streamlit app:
   ```powershell
   cd C:\Users\winst\BentleyBudgetBot
   streamlit run streamlit_app.py
   ```

2. Navigate to the Plaid Test page: **🏦 Plaid Test**

3. Click the **"Connect a Bank Account"** button

4. The Plaid Link widget should open and allow you to:
   - Select a bank
   - Enter sandbox credentials
   - Link your account

## Troubleshooting

### Frontend not talking to backend
- Add the API host to the Plaid quickstart `.env` (same folder as docker-compose):
   ```powershell
   cd C:\Users\winst\plaid-quickstart
   Add-Content .env "REACT_APP_API_HOST=http://localhost:5001"
   docker compose up -d --build
   ```
- The frontend expects `REACT_APP_API_HOST`; without it, Link tests fail.

### "Method Not Allowed" on /api/info
- Plaid quickstart APIs expect `POST` for `/api/info` and most setup routes.
- Test with:
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:5001/api/info" -Method POST -ContentType "application/json"
   ```

### If "Connection Refused" Error
The backend may still be starting. Wait 30 seconds and try again.

### If "Port Already in Use"
Another service is using port 5001. Stop it first:
```powershell
docker ps
docker stop <container-id>
```

### Multiple backend images mapping port 5001
- The compose file maps Go/Java/Node/Python/Ruby to the same host port 5001; only one can bind.
- Keep a single backend up (easiest: Python). Stop the others if they auto-create:
   ```powershell
   docker stop plaid-quickstart-node-1 plaid-quickstart-ruby-1 plaid-quickstart-go-1 plaid-quickstart-java-1
   ```
   or remove their `ports:` entries if you only need Python.

### Check Container Logs
```powershell
cd C:\Users\winst\plaid-quickstart
docker compose logs -f node
```

## Configuration

The Plaid credentials are already configured in:
```
C:\Users\winst\plaid-quickstart\.env
```

Current settings:
- PLAID_CLIENT_ID: 68b8718ec2f428002456a84c
- PLAID_SECRET: 1849c4090173dfbce2bda5453e7048
- PLAID_ENV: sandbox
- PLAID_PRODUCTS: transactions
- PLAID_COUNTRY_CODES: US

## Next Steps

1. ⏳ Wait for Docker build to complete (~5-10 minutes)
2. ✅ Verify backend is running with diagnostic script
3. 🚀 Start Streamlit app
4. 🏦 Test Plaid Link button
5. ✅ Link a bank account using sandbox credentials

---

**Current Status**: 🔄 Building containers...  
**Estimated Time**: 5-10 minutes for first build  
**Command Running**: `docker compose up -d` in `C:\Users\winst\plaid-quickstart`
