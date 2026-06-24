# Bentley Budget Bot - Connection Configuration Fix Summary

**Generated:** January 17, 2026  
**Status:** In Progress

## Executive Summary

The project has **three separate MySQL databases** running on different ports and hosts, but the code was using hardcoded values that conflicted with the actual `.env` configuration. This document identifies all configuration mismatches and provides fixes.

---

## Current Configuration (from `.env`)

### 1. **Main MySQL Database** - mansa_bot (Port 3306)
- **Host:** 127.0.0.1
- **Port:** 3306
- **Database:** mansa_bot
- **User:** root
- **Password:** root
- **Purpose:** General application data, Appwrite integration, Plaid data
- **Environment Variables:**
  - `MYSQL_HOST=127.0.0.1`
  - `MYSQL_PORT=3306`
  - `MYSQL_DATABASE=mansa_bot`

### 2. **Budget Database** - mydb (Port 3306)
- **Host:** 127.0.0.1
- **Port:** 3306
- **Database:** mydb
- **User:** root
- **Password:** root
- **Purpose:** Plaid integration and budget data
- **Environment Variables:**
  - `BUDGET_MYSQL_HOST=127.0.0.1`
  - `BUDGET_MYSQL_PORT=3306`
  - `BUDGET_MYSQL_DATABASE=mydb`

### 3. **Operational Database** - bbbot1 (Port 3307 - Docker)
- **Host:** 127.0.0.1
- **Port:** 3307
- **Database:** bbbot1
- **User:** root
- **Password:** root
- **Purpose:** Stock data (yfinance, Tiingo), operational metrics
- **Environment Variables:**
  - `BBBOT1_MYSQL_HOST=127.0.0.1`
  - `BBBOT1_MYSQL_PORT=3307`
  - `BBBOT1_MYSQL_DATABASE=bbbot1`

### 4. **MLflow Database** (Port 3307 - Docker)
- **Host:** 127.0.0.1
- **Port:** 3307
- **Database:** mlflow_db
- **User:** root
- **Password:** root
- **Purpose:** MLflow experiment tracking and model registry
- **Environment Variables:**
  - `MLFLOW_MYSQL_HOST=127.0.0.1`
  - `MLFLOW_MYSQL_PORT=3307`
  - `MLFLOW_MYSQL_DATABASE=mlflow_db`

---

## Issues Identified

### Issue 1: MySQL Connection Defaults
**Problem:** Code uses hardcoded `localhost:3307/bentleybot` as fallback instead of reading from `.env`  
**Impact:** Primary MySQL connections fail when `.env` is not properly loaded  
**Files Affected:** `diagnose_integration_errors.py` (line 33)  
**Fix:** Use `.env` values with proper defaults that match actual setup

### Issue 2: Plaid Docker Backend Not Running
**Problem:** Backend expected at `http://localhost:5001` but no health check or status indicator  
**Impact:** Plaid connections fail silently  
**Endpoints Expected:**
- POST `/link/token/create` - Create Plaid link token
- POST `/item/public_token/exchange` - Exchange public token for access token
- POST `/accounts/get` - Fetch accounts
- POST `/transactions/get` - Fetch transactions

**Fix:** Add proper health check and startup instructions

### Issue 3: Missing Economic Data API Keys
**Problem:** No economic data API keys configured in `.env`  
**Impact:** Economic calendar and fundamental data features unavailable
**Missing Services:**
- **FRED API** (Federal Reserve Economic Data)
- **QUANDL API** (Alternative Data)
- **INFLATIONAPI** (Inflation Data)
- **OPENWEATHER API** (Market sentiment)

**Fix:** Document required keys and provide template

---

## Fixes Applied

### Fix 1: Update diagnose_integration_errors.py
- ✅ Change MySQL default port from 3307 to 3306
- ✅ Change MySQL default database from "bentleybot" to "mansa_bot"
- ✅ Use environment variable lookup properly
- ✅ Add connection status for all three databases

### Fix 2: Add Plaid Backend Health Check
- ✅ Add endpoint to check if Plaid backend is running
- ✅ Provide port and URL verification
- ✅ Show startup commands for Docker

### Fix 3: Add Economic Data API Key Status
- ✅ Check which economic data keys are configured
- ✅ Show which services are available/unavailable
- ✅ Provide configuration template

---

## Database Connection Matrix

| Service/Component | Database | Host | Port | Database Name |
|---|---|---|---|---|
| Streamlit App (main) | Main MySQL | 127.0.0.1 | 3306 | mansa_bot |
| Plaid Integration | Budget MySQL | 127.0.0.1 | 3306 | mydb |
| Stock Data (yfinance) | Operational | 127.0.0.1 | 3307 | bbbot1 |
| Technical Analysis | Operational | 127.0.0.1 | 3307 | bbbot1 |
| MLflow Tracking | MLflow | 127.0.0.1 | 3307 | mlflow_db |

---

## Required Actions

### 1. Docker Services Status
```bash
# Check which MySQL containers are running
docker ps | grep mysql

# Expected:
# - MySQL 8.0 on port 3306 (main + budget databases)
# - MySQL 8.0 on port 3307 (bbbot1 + mlflow_db)
```

### 2. Verify .env Configuration
```bash
# Current .env is correct. Verify:
- MYSQL_HOST=127.0.0.1 ✓
- MYSQL_PORT=3306 ✓
- MYSQL_DATABASE=mansa_bot ✓
```

### 3. Add Missing API Keys (if needed)
Create `.env.local.example` with required fields:
```
# Economic Data APIs (optional)
FRED_API_KEY=your_fred_api_key
QUANDL_API_KEY=your_quandl_key
INFLATIONAPI_KEY=your_inflation_api_key
OPENWEATHER_API_KEY=your_weather_key
```

---

## Testing Checklist

- [ ] Run `python diagnose_integration_errors.py` and verify all connections pass
- [ ] Check MySQL main database at 127.0.0.1:3306/mansa_bot
- [ ] Check MySQL operational database at 127.0.0.1:3307/bbbot1
- [ ] Verify Plaid backend health at http://localhost:5001/health
- [ ] Verify Alpaca connection with credentials
- [ ] Verify MT5 connection at http://localhost:8000

---

## Related Files

- [diagnose_integration_errors.py](diagnose_integration_errors.py) - Updated diagnostic script
- [.env](.env) - Current configuration (already correct)
- [docker-compose.yml](docker-compose.yml) - Docker services configuration
