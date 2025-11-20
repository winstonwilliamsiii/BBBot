# 🚀 Bentley Budget Bot - Quick Start Guide

## Problem: Can't Access Airflow/Airbyte in Browser?

If you've run the start command and services show as running but you can't 
access the UIs in your browser, follow this guide.

## ✅ Solution Steps

### Step 1: Verify Docker is Running

```powershell
docker --version
docker ps
```

If Docker is not running, start Docker Desktop and wait for it to fully start.

### Step 2: Start All Services Properly

```powershell
# Stop any existing services first
.\manage_services.ps1 -Service all -Action stop

# Wait 10 seconds for clean shutdown
Start-Sleep -Seconds 10

# Start all services
.\manage_services.ps1 -Service all -Action start
```

### Step 3: Wait for Services to Initialize

**IMPORTANT**: Services can take 30-60 seconds to fully start!

```powershell
# Watch the logs in real-time
.\manage_services.ps1 -Service airflow -Action logs
```

Look for these success messages:
- Airflow: "Webserver started"
- Airbyte: "Server started"
- MLflow: "Listening at"

### Step 4: Verify Services are Running

```powershell
# Run the troubleshooting script
.\troubleshoot_services.ps1
```

This will check:
- Docker status
- Port availability
- Container health
- Service accessibility

### Step 5: Access the Services

Open these URLs in your browser:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Streamlit App** | http://localhost:8501 | None |
| **Airflow UI** | http://localhost:8080 | admin / admin |
| **Airbyte UI** | http://localhost:8000 | None |
| **MLflow UI** | http://localhost:5000 | None |

## 🔧 Common Issues and Fixes

### Issue 1: "Connection Refused" or "Cannot Connect"

**Cause**: Services haven't finished starting yet.

**Fix**:
```powershell
# Check if containers are running
docker ps

# Check specific container logs
docker logs bentley-airflow-webserver --tail 100
docker logs bentley-airbyte-webapp --tail 100
docker logs bentley-mlflow --tail 100
```

Wait 30-60 seconds and try again.

### Issue 2: "Port Already in Use"

**Cause**: Another application is using the required ports.

**Fix**:
```powershell
# Check what's using port 8080 (Airflow)
netstat -ano | findstr :8080

# Check what's using port 8000 (Airbyte)
netstat -ano | findstr :8000

# Kill the process using the port
taskkill /PID <PID> /F
```

Or change the port mapping in the docker-compose files.

### Issue 3: Container Keeps Restarting

**Cause**: Database not initialized or configuration error.

**Fix**:
```powershell
# Check container status
docker ps -a

# View container logs to see error
docker logs <container-name>

# Common fix: Reset the database
docker-compose -f docker-compose-airflow.yml down -v
docker-compose -f docker-compose-airflow.yml up -d
```

### Issue 4: Blank Page or 404 Error

**Cause**: Service started but web interface not ready.

**Fix**:
1. Wait another 30 seconds
2. Clear browser cache (Ctrl+Shift+Delete)
3. Try incognito/private mode
4. Check container logs for errors

### Issue 5: Airflow Shows "503 Service Unavailable"

**Cause**: Airflow scheduler or worker not running.

**Fix**:
```powershell
# Check all Airflow containers are running
docker ps | findstr airflow

# Restart Airflow services
.\manage_services.ps1 -Service airflow -Action stop
.\manage_services.ps1 -Service airflow -Action start
```

## 🎯 MLflow Integration Workflow

Now that MLflow is integrated, here's how to use it:

### 1. Access Airflow UI

Go to http://localhost:8080 and login with `admin` / `admin`

### 2. Enable the DAG

1. Find `bentleybot_dag` in the list
2. Toggle the switch to enable it
3. Click the play button to trigger manually

### 3. Monitor Execution

1. Click on the DAG name
2. View the graph of tasks
3. Click individual tasks to see logs
4. Verify `log_mlflow` task completes successfully

### 4. View Results in MLflow

1. Go to http://localhost:5000
2. Select "BentleyBudgetBot-Trading" experiment
3. View metrics, parameters, and artifacts
4. Compare different runs

## 📊 Service Architecture

```
Your Browser (localhost)
         │
         ├─→ http://localhost:8501  → Streamlit App
         ├─→ http://localhost:8080  → Airflow UI
         ├─→ http://localhost:8000  → Airbyte UI
         └─→ http://localhost:5000  → MLflow UI
                     │
           ┌─────────┴─────────┐
           │                   │
    Docker Network      Docker Network
    bentley-network     airbyte-network
           │                   │
    ┌──────┴──────┐     ┌─────┴──────┐
    │   Airflow   │     │  Airbyte   │
    │   MLflow    │     │  Services  │
    │   Streamlit │     │            │
    │   MySQL     │     │ PostgreSQL │
    └─────────────┘     └────────────┘
```

## 💻 Command Reference

### Start/Stop Services

```powershell
# Start all services
.\manage_services.ps1 -Service all -Action start

# Start individual service
.\manage_services.ps1 -Service airflow -Action start
.\manage_services.ps1 -Service airbyte -Action start

# Stop all services
.\manage_services.ps1 -Service all -Action stop

# Check status
.\manage_services.ps1 -Action status
```

### View Logs

```powershell
# View Airflow logs
.\manage_services.ps1 -Service airflow -Action logs

# View Airbyte logs
.\manage_services.ps1 -Service airbyte -Action logs

# View specific container logs
docker logs bentley-airflow-webserver
docker logs bentley-airbyte-webapp
docker logs bentley-mlflow
```

### Troubleshooting

```powershell
# Run diagnostics
.\troubleshoot_services.ps1

# Fix common issues automatically
.\troubleshoot_services.ps1 -Fix

# Check running containers
docker ps

# Check all containers (including stopped)
docker ps -a

# Restart a specific container
docker restart <container-name>
```

### Database Access

```powershell
# Connect to MySQL
docker exec -it bentley-mysql mysql -u root -p
# Password: root

# View databases
SHOW DATABASES;
USE mansa_bot;
SHOW TABLES;

# Check MLflow database
USE mlflow_db;
SHOW TABLES;
```

## 🔒 Security Notes

**Default Credentials** (Change in production!):

- **Airflow**: admin / admin
- **MySQL**: root / root
- **Airbyte**: No authentication (configure in UI)
- **MLflow**: No authentication (open access)

## 📚 Next Steps

1. ✅ Verify all services are accessible
2. ✅ Configure Airbyte data sources
3. ✅ Update DAG with your Airbyte connection IDs
4. ✅ Test the complete workflow
5. ✅ Monitor MLflow for experiment results

## 🆘 Still Having Issues?

If services still aren't accessible:

1. **Check Docker Resources**
   - Docker Desktop → Settings → Resources
   - Minimum: 8GB RAM, 4 CPUs, 10GB Disk

2. **Check Windows Firewall**
   - May need to allow Docker Desktop through firewall
   - Allow private and public network access

3. **Reset Everything**
   ```powershell
   # Nuclear option - deletes all data!
   docker-compose -f docker-compose-airflow.yml down -v
   docker-compose -f docker-compose-airbyte.yml down -v
   
   # Remove dangling volumes
   docker volume prune -f
   
   # Start fresh
   .\manage_services.ps1 -Service all -Action start
   ```

4. **Check System Resources**
   ```powershell
   # Check if Docker has enough resources
   docker stats
   ```

## ✨ Success Checklist

- [ ] Docker Desktop is running
- [ ] All containers show as "Up" in `docker ps`
- [ ] Streamlit loads at http://localhost:8501
- [ ] Airflow UI loads at http://localhost:8080
- [ ] Airbyte UI loads at http://localhost:8000
- [ ] MLflow UI loads at http://localhost:5000
- [ ] Can login to Airflow with admin/admin
- [ ] Can see `bentleybot_dag` in Airflow
- [ ] Can trigger DAG manually
- [ ] Can see experiments in MLflow

---

**Ready to orchestrate ML workflows!** 🚀

See [MLFLOW_INTEGRATION.md](MLFLOW_INTEGRATION.md) for detailed MLflow usage.
