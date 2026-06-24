# Streamlit Cloud Import Path Fixes

**Date:** January 15, 2026  
**Issue:** ModuleNotFoundError on Streamlit Cloud for broker and Plaid connectors
**Root Cause:** Import paths were referencing `frontend.utils.*` but files moved to `frontend.components.*`

## Error Reported

```
ModuleNotFoundError: This app has encountered an error.
Traceback:
File "/mount/src/bbbot/pages/06_🏦_Plaid_Test.py", line 33, in <module>
    from frontend.utils.plaid_quickstart_connector import PlaidQuickstartClient
```

Additional errors: Alpaca, Plaid, and MySQL connections failing

## Files Fixed

### 1. Plaid Quickstart Connector Imports
**Files Updated:**
- [pages/06_🏦_Plaid_Test.py](pages/06_🏦_Plaid_Test.py#L33)
- [frontend/pages/06_🏦_Plaid_Test.py](frontend/pages/06_🏦_Plaid_Test.py#L33)

**Change:**
```python
# OLD (BROKEN)
from frontend.utils.plaid_quickstart_connector import PlaidQuickstartClient, render_quickstart_plaid_link

# NEW (FIXED)
from frontend.components.plaid_quickstart_connector import PlaidQuickstartClient, render_quickstart_plaid_link
```

### 2. Alpaca Connector Imports
**Files Updated:**
- [pages/04_💼_Broker_Trading.py](pages/04_💼_Broker_Trading.py#L116) (2 occurrences)
- [frontend/pages/04_💼_Broker_Trading.py](frontend/pages/04_💼_Broker_Trading.py#L116) (2 occurrences)

**Changes:**
```python
# OLD (BROKEN) - Line 116
from frontend.utils.alpaca_connector import AlpacaConnector

# NEW (FIXED)
from frontend.components.alpaca_connector import AlpacaConnector

# OLD (BROKEN) - Line 220
from frontend.utils.alpaca_connector import AlpacaConnector

# NEW (FIXED)
from frontend.components.alpaca_connector import AlpacaConnector
```

### 3. Broker Connections Imports
**Files Updated:**
- [pages/02_📈_Investment_Analysis.py](pages/02_📈_Investment_Analysis.py#L188)
- [frontend/pages/02_📈_Investment_Analysis.py](frontend/pages/02_📈_Investment_Analysis.py#L188)

**Change:**
```python
# OLD (BROKEN)
from frontend.utils.broker_connections import (
    display_broker_connections,
    display_webull_funds,
    display_position_analysis,
    display_connection_health,
)

# NEW (FIXED)
from frontend.components.broker_connections import (
    display_broker_connections,
    display_webull_funds,
    display_position_analysis,
    display_connection_health,
)
```

## File Locations Confirmed

### Components (NEW location)
```
frontend/components/
├── alpaca_connector.py ✅
├── broker_connections.py ✅
├── plaid_quickstart_connector.py ✅
├── ibkr_connector.py
├── mt5_connector.py
├── webull_integration.py
└── ...
```

### Utils (OLD location - some files still here)
```
frontend/utils/
├── broker_connections.py (duplicate)
├── plaid_link.py ✅ (still used)
├── styling.py ✅ (still used)
├── yahoo.py ✅ (still used)
├── rbac.py ✅ (still used)
└── ...
```

## Why This Happened

During refactoring, broker and Plaid connector files were moved from `frontend.utils/` to `frontend.components/` to better organize the codebase:
- **Components** = Feature-specific integrations (Alpaca, Plaid, IBKR, MT5, etc.)
- **Utils** = Shared utilities (styling, RBAC, Yahoo scraping, etc.)

However, import statements in the Streamlit pages were not updated to reflect this change.

## Testing Checklist

### Local Testing
```bash
# Test imports work
python -c "from frontend.components.alpaca_connector import AlpacaConnector; print('✅ Alpaca import OK')"
python -c "from frontend.components.plaid_quickstart_connector import PlaidQuickstartClient; print('✅ Plaid import OK')"
python -c "from frontend.components.broker_connections import display_broker_connections; print('✅ Broker import OK')"
```

### Streamlit Cloud Testing
After deployment, verify these pages work:
1. ✅ **🏦 Plaid Test** - Should load without ModuleNotFoundError
2. ✅ **💼 Broker Trading** - Alpaca connection test should work
3. ✅ **📈 Investment Analysis** - Broker connections should display

## MySQL Connection Issues

If MySQL errors persist on Streamlit Cloud, verify secrets are correctly configured:

### Required Secrets in Streamlit Cloud
```toml
# Main MySQL
MYSQL_HOST = "nozomi.proxy.rlwy.net"
MYSQL_PORT = "54537"
MYSQL_USER = "root"
MYSQL_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"

# Budget MySQL (Plaid)
BUDGET_MYSQL_HOST = "nozomi.proxy.rlwy.net"
BUDGET_MYSQL_PORT = "54537"
BUDGET_MYSQL_DATABASE = "mydb"
BUDGET_MYSQL_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"

# BBBot1 MySQL (Stock Data)
BBBOT1_MYSQL_HOST = "nozomi.proxy.rlwy.net"
BBBOT1_MYSQL_PORT = "54537"
BBBOT1_MYSQL_DATABASE = "bbbot1"
BBBOT1_MYSQL_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"

# MLflow MySQL (Experiments)
MLFLOW_MYSQL_HOST = "nozomi.proxy.rlwy.net"
MLFLOW_MYSQL_PORT = "54537"
MLFLOW_MYSQL_DATABASE = "mlflow_db"
MLFLOW_MYSQL_PASSWORD = "cBlIUSygvPJCgPbNKHePJekQlClRamri"
```

### Common MySQL Errors & Solutions

**Error:** `Can't connect to MySQL server on '127.0.0.1:3306'`
**Solution:** Change `MYSQL_HOST` from `127.0.0.1` to `nozomi.proxy.rlwy.net` and `MYSQL_PORT` from `3306` to `54537`

**Error:** `Access denied for user 'root'@'...'`
**Solution:** Verify `MYSQL_PASSWORD` matches Railway MySQL service password

**Error:** `Unknown database 'mydb'`
**Solution:** Create database on Railway or update `BUDGET_MYSQL_DATABASE` to existing database name

## Alpaca API Issues

If Alpaca errors persist, verify:

```toml
ALPACA_API_KEY = "PKAYRIJUWUPO5VVWVTIWDXPRJ3"
ALPACA_SECRET_KEY = "HDegV257ex4j1Wc7C3714mVBLoyircYYMTxTozZKWeaA"
ALPACA_PAPER = "true"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
```

Test locally:
```bash
python tests/test_alpaca_connection.py
# Should show: ✅ READY TO TRADE!
```

## Plaid API Issues

If Plaid errors persist, verify:

```toml
PLAID_CLIENT_ID = "677f5a06bfb57e001d2ca8e9"
PLAID_SECRET = "7ce1f012fdd48c25854e3ecc5d1a91"
PLAID_ENV = "sandbox"
```

## MLflow Database Tables

**Question:** "Do we need to add tables to mlflow_db?"

**Answer:** No. MLflow automatically creates its own tables via Alembic migrations when you first connect. We already did this:

```bash
python setup_mlflow_railway.py
# Created 34 tables automatically:
# - experiments, runs, metrics, params, tags, registered_models, etc.
```

If tables are missing, re-run:
```bash
python setup_mlflow_railway.py
```

## Requirements Verification

All required packages are in [requirements.txt](requirements.txt):

```pip-requirements
# Database
mysql-connector-python>=8.0.0
sqlalchemy>=1.4.0
pymysql>=1.1.0

# Plaid
plaid-python>=14.0.0

# MLflow (if using Investment Analysis)
mlflow>=2.0.0

# Alpaca
alpaca-py>=0.12.0
```

## Deployment Steps

1. **Commit changes:**
   ```bash
   git add pages/ frontend/pages/
   git commit -m "fix: Update import paths for broker and Plaid connectors"
   git push origin main
   ```

2. **Streamlit Cloud auto-deploys** from GitHub push

3. **Verify deployment:**
   - Go to https://bbbot305.streamlit.app/
   - Check "Manage app" → "Logs" for any remaining errors
   - Test each page: Plaid Test, Broker Trading, Investment Analysis

4. **If errors persist:**
   - Check Streamlit Cloud secrets match above configuration
   - Verify Railway MySQL is running (https://railway.app/)
   - Check package versions in deployed environment logs

## Related Files

- [CLOUD_SERVICES_CONFIG.md](CLOUD_SERVICES_CONFIG.md) - Full cloud services documentation
- [MLFLOW_RAILWAY_SETUP.md](MLFLOW_RAILWAY_SETUP.md) - MLflow setup documentation
- [tests/test_alpaca_connection.py](tests/test_alpaca_connection.py) - Alpaca connection test
- [setup_mlflow_railway.py](setup_mlflow_railway.py) - MLflow Railway setup script

---

**Fixed:** January 15, 2026  
**Status:** ✅ Import paths corrected  
**Next:** Deploy to Streamlit Cloud and verify
