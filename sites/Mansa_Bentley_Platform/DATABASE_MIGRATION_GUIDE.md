-- Active: 1737943595894@@127.0.0.1@3306@mansa_bot
# Database Migration Guide - bbbot1 to Multi-Database Architecture

**Date:** December 14, 2025  
**Status:** Ready to Execute  
**Estimated Time:** 15-30 minutes

---

## 🎯 What This Migration Does

### Before (Old - BROKEN)
```
bbbot1 → ❌ DELETED
├─ All data in one database
└─ Referenced in many files
```

### After (New - CORRECT)
```
USEUSEUSE mansa_bot;
SHOW TABLES;
```

---

## ✅ Step-by-Step Migration Process

### STEP 1: Add Missing Environment Variables

Add these lines to your `.env` file:

```bash
# ============================================================================
# Additional Database Configuration (for multi-database architecture)
# ============================================================================

# Quantitative Analysis Database
QUANT_MYSQL_DATABASE=mansa_quant

# MLFlow & Airflow Database  
MLFLOW_MYSQL_DATABASE=mlflow_db
MLFLOW_TRACKING_URI=mysql+pymysql://root:root@127.0.0.1:3306/mlflow_db

# Bulk Data Storage
BULK_MYSQL_DATABASE=mrgp_schema

# Airbyte Configuration (for data ingestion)
AIRBYTE_MYSQL_USER=airbyte
AIRBYTE_MYSQL_PASSWORD=airbyte_secure_password_2025
```

**How to do it:**
```powershell
# Open .env file in VS Code
code .env

# Add the lines above at the end
# Save and close
```

---

### STEP 2: Create All Databases and Tables

**Option A: Using MySQL Command Line** (Recommended)

1. Find your MySQL executable:
```powershell
# Common locations:
# C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe
# C:\xampp\mysql\bin\mysql.exe
# Or check: Get-Command mysql -ErrorAction SilentlyContinue
```

2. Run the initialization script:
```powershell
# Navigate to your project
cd C:\Users\winst\BentleyBudgetBot

# Run SQL script (adjust mysql path if needed)
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p < scripts\setup\init_all_databases.sql

# Enter password when prompted: root
```

**Option B: Using Python Script**

If MySQL CLI isn't available, I can create a Python script to execute the SQL:

```powershell
python scripts/setup/create_databases.py
```

---

### STEP 3: Verify Database Creation

Run the verification script:

```powershell
python test_database_connections.py
```

**Expected Output:**
```
✅ Successful: 5/5
Connected Databases:
Database                  Tables     Size (MB)
---------------------------------------------
mydb (Budget)            9          0.05
mansa_bot (Metrics)      12         0.03
mansa_quant (Quant)      11         0.02
mlflow_db (MLFlow)       0          0.00
mrgp_schema (Bulk)       10         0.01
```

---

### STEP 4: Update Code References (Already Identified)

Files that need updating (I can do this for you):

#### A. Rename bbbot1_pipeline Directory
```powershell
# Old structure
bbbot1_pipeline/
├─ ingest_alpha_vantage.py
├─ ingest_yfinance.py
└─ ...

# New structure (rename to)
mansa_pipeline/
├─ ingest_alpha_vantage.py
├─ ingest_yfinance.py
└─ ...
```

#### B. Update Import Statements

Files to update:
- `#alphavantage_fundamentals.py`
- `#yfinance_fundamentals.py`
- `#stock_pipeline_DAG.py`
- `airflow/dags/bbbot1_master_pipeline.py` → rename to `mansa_master_pipeline.py`

Change:
```python
# OLD
from bbbot1_pipeline.ingest_yfinance import fetch_prices

# NEW
from mansa_pipeline.ingest_yfinance import fetch_prices
```

#### C. Update Connection Strings

Files to update:
- `#alphavantage_fundamentals.py` (line 7)

Change:
```python
# OLD
return create_engine("mysql+pymysql://user:pass@localhost:3306/bbbot1")

# NEW
return create_engine("mysql+pymysql://root:root@localhost:3306/mansa_quant")
```

---

### STEP 5: Test Each Database Feature

Test each part of your application:

```powershell
# Test budget database
streamlit run "pages/01_💰_Personal_Budget.py"

# Test investment analysis (uses mansa_quant)
streamlit run "pages/02_📈_Investment_Analysis.py"

# Test metrics (uses mansa_bot)
python test_tiingo.py
```

---

## 🔧 What I Can Do For You Now

### Option 1: Automatic Migration (Recommended)
I can:
1. ✅ Create Python script to execute SQL (if MySQL CLI unavailable)
2. ✅ Rename `bbbot1_pipeline/` to `mansa_pipeline/`
3. ✅ Update all import statements automatically
4. ✅ Update all connection strings
5. ✅ Add missing env variables to `.env` template

**Command:** Just say "Run automatic migration"

### Option 2: Manual Migration (If You Prefer Control)
I'll provide:
- ✅ Detailed checklist with specific file paths and line numbers
- ✅ Before/after code snippets for each change
- ✅ Verification steps after each change

**Command:** Say "Give me manual checklist"

---

## 📊 Migration Impact Assessment

### Files to Change: **25 files**

| Category | Files | Risk Level |
|----------|-------|------------|
| Environment | .env | Low |
| Database Schema | init_all_databases.sql | Low (new file) |
| Pipeline Code | bbbot1_pipeline/* (13 files) | Medium |
| Airflow DAGs | 4 files | Medium |
| Legacy Scripts | 6 files | Low (commented out) |
| Testing | test_database_connections.py | Low (new file) |

### Estimated Time:
- **Automatic:** 5 minutes
- **Manual:** 30-45 minutes

### Backup Required:
- ✅ `.env` file (backup before changes)
- ✅ MySQL databases (if you have data in bbbot1)

---

## ⚠️ Pre-Migration Checklist

Before proceeding, ensure:

- [ ] MySQL is running and accessible on port 3306
- [ ] You have root access to MySQL (password: root)
- [ ] No critical processes are using bbbot1 database
- [ ] You've backed up any important data from bbbot1
- [ ] Streamlit is stopped (no port 8501 conflicts)

---

## 🚨 Rollback Plan

If something goes wrong:

1. **Restore .env file:**
```powershell
Copy-Item .env.backup .env
```

2. **Keep old bbbot1 database:**
Don't drop bbbot1 until you verify new databases work

3. **Revert code changes:**
```powershell
git checkout -- bbbot1_pipeline/
git checkout -- airflow/dags/
```

---

## 🎯 Post-Migration Verification

After migration, verify:

1. ✅ All 5 databases exist and are accessible
2. ✅ Budget page loads without errors
3. ✅ Investment Analysis displays data
4. ✅ No import errors in console
5. ✅ `test_database_connections.py` shows 5/5 success

---

## 💬 Next Steps

**Choose your path:**

**Path A: Let me handle it** (Fast, automatic)
- Say: "Run automatic migration"
- I'll update all files and create helper scripts
- Takes ~5 minutes
- Risk: Low (I'll backup first)

**Path B: You handle it** (Manual, controlled)
- Say: "Give me manual checklist"
- You make changes step by step
- Takes ~30-45 minutes  
- Risk: Medium (human error possible)

**Path C: Just create databases** (Minimal, safe)
- Say: "Just create databases, I'll update code later"
- Creates schemas only, no code changes
- Takes ~2 minutes
- Risk: None (additive only)

---

**Ready to proceed?** Choose your path and I'll guide you through it!
