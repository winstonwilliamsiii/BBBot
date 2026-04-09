# 🔧 MySQL Connection Issue - Fixed!

## Issue Date: March 9, 2026

### 🐛 Problems Identified

1. **Stale Connections** - Long-running idle connections (14+ hours) blocking resources
2. **Config File Permissions** - World-writable config file causing security warnings
3. **Duplicate Connection Names** - Confusing VS Code SQL Tools connections
4. **Missing Timeout Settings** - Connections timing out without proper reconnection

---

## ✅ Solutions Implemented

### 1. **Created Diagnostic & Repair Script**
   - **File**: `fix_mysql_connections.ps1`
   - **Features**:
     - Auto-starts Docker if not running
     - Kills stale connections (idle > 1 hour)
     - Fixes config file permissions
     - Tests all database connections
     - Provides detailed status reporting

### 2. **Updated VS Code SQL Connections**
   - **File**: `.vscode/settings.json`
   - **Changes**:
     - Fixed all connections to use port **3307** (Docker container)
     - Added connection timeout settings (60 seconds)
     - Renamed connections with emojis for easy identification:
       - 📊 Demo_Bots - Mansa Bot
       - 📈 Bbbot1 - Equities Database
       - 🔬 MLflow Database
       - 📉 Mansa Quant
       - 💰 Bentley Budget

### 3. **Fixed MySQL Configuration**
   - Corrected file permissions on `custom.cnf` (644)
   - Eliminated security warnings

### 4. **Added VS Code Task**
   - **Task**: "🔧 Fix MySQL Connections (Diagnostic & Repair)"
   - **Access**: `Ctrl+Shift+P` → "Run Task" → "Fix MySQL Connections"

---

## 📊 Connection Status (All Green!)

```
✅ Docker is running
✅ Container 'bentley-mysql' is running
✅ MySQL is responding to connections
✅ No stale connections
✅ Config file permissions fixed
✅ All 5 databases accessible:
   • bbbot1
   • mansa_bot
   • mlflow_db
   • mansa_quant
   • Bentley_Budget
✅ Port 3307 accessible from host
✅ Connection usage: 13/151 (8.6% - healthy)
```

---

## 🔄 How to Reconnect in VS Code

### Option 1: Automatic (Recommended)
```powershell
# Close VS Code and reopen - connections will auto-refresh
```

### Option 2: Manual Reconnect
1. Open SQLTools sidebar (database icon)
2. Find your connection (e.g., "📊 Demo_Bots - Mansa Bot")
3. Right-click → **Disconnect**
4. Right-click → **Connect**
5. Enter password: `root`

### Option 3: Run Diagnostic
```powershell
# Press Ctrl+Shift+P
# Type: "Run Task"
# Select: "🔧 Fix MySQL Connections (Diagnostic & Repair)"
```

---

## 🛠️ Maintenance Commands

### Regular Use
```powershell
# Run diagnostic & repair
.\fix_mysql_connections.ps1

# Start MySQL if stopped
.\start_mysql_docker.ps1

# View logs
docker logs bentley-mysql --tail 50

# Test connection
docker exec bentley-mysql mysql -uroot -proot -e "SHOW DATABASES;"
```

### Emergency Recovery
```powershell
# Restart MySQL container
docker restart bentley-mysql

# Stop and recreate container
cd docker
docker-compose -f docker-compose-airflow.yml down mysql
docker-compose -f docker-compose-airflow.yml up -d mysql
```

---

## 📝 Connection Details

All databases are on the same MySQL instance:

```
Host:     127.0.0.1
Port:     3307
Username: root
Password: root
```

**Databases:**
- `bbbot1` - Equities Bulk Database (Tiingo, Massive, Barchart, AlphaVantage, StockTwits, yfinance)
- `mansa_bot` - Main application database
- `mlflow_db` - Airflow Metadata, Airflow DAG, MLflow Logging Experiments, StockTwits Sentiment Analysis Pipeline DAG
- `mansa_quant` - Quantitative analysis data
- `Bentley_Budget` - Budget tracking data

---

## 🎯 Prevention

### Auto-Cleanup (Recommended)
The `fix_mysql_connections.ps1` script can be scheduled to run:

```powershell
# Add to Windows Task Scheduler
# Run daily at midnight to clean up stale connections
```

### Manual Monitoring
```powershell
# Check for stale connections
docker exec bentley-mysql mysql -uroot -proot -e "SELECT COUNT(*) FROM INFORMATION_SCHEMA.PROCESSLIST WHERE COMMAND='Sleep' AND TIME>3600;"

# View active connections
docker exec bentley-mysql mysql -uroot -proot -e "SHOW PROCESSLIST;"
```

---

## 📚 Related Files

- **Scripts**:
  - `fix_mysql_connections.ps1` - Diagnostic & repair tool
  - `start_mysql_docker.ps1` - Auto-start Docker & MySQL
  
- **Configuration**:
  - `.vscode/settings.json` - SQL connection settings
  - `.vscode/tasks.json` - VS Code tasks
  - `mysql_config/my.cnf` - MySQL server config
  - `docker/docker-compose-airflow.yml` - Container definition

- **Documentation**:
  - `MYSQL_AUTO_START_GUIDE.md` - Quick reference
  - `.vscode/README.md` - Detailed docs

---

## ✨ Summary

**All MySQL connections are now working!** 🎉

The issue was caused by stale connections and configuration problems. The diagnostic script will keep things healthy going forward.

**Next Steps:**
1. Restart VS Code to refresh connections
2. Test connecting to any database from SQLTools
3. Run `.\fix_mysql_connections.ps1` anytime you have connection issues

---

*Issue resolved on: March 9, 2026 8:32 AM*
