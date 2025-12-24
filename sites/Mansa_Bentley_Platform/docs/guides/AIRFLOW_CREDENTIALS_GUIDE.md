# Airflow Variables & Connections Setup Guide

## Overview

This guide shows how to securely manage Plaid credentials using **Airflow Variables** and **Airflow Connections** instead of hardcoding them in environment files.

### Benefits:
✅ **Centralized management** - All credentials in Airflow UI  
✅ **Encryption** - Airflow encrypts sensitive values using Fernet key  
✅ **Access control** - Role-based permissions for credential access  
✅ **Audit logging** - Track who accessed what credentials  
✅ **Dynamic updates** - Change credentials without redeploying DAGs  
✅ **No .env files** - Eliminate risk of committing secrets  

---

## Part 1: Setting Up Airflow Variables

### Option A: Using Airflow Web UI (Recommended)

1. **Open Airflow UI**: http://localhost:8080
2. **Login**: admin / admin
3. **Navigate**: Admin → Variables
4. **Add each variable**:

| Key | Value | Description |
|-----|-------|-------------|
| `plaid_client_id` | `your_plaid_client_id` | Plaid client ID from dashboard |
| `plaid_secret` | `your_plaid_secret` | Plaid secret (will be encrypted) |
| `plaid_access_token` | `access-sandbox-xxx` | Plaid access token |
| `plaid_env` | `sandbox` | Environment: sandbox/development/production |
| `plaid_start_date` | `2025-11-01` | Default start date for transactions |
| `plaid_end_date` | `2025-11-23` | Default end date for transactions |

**Important**: Airflow automatically encrypts variables containing keywords like:
- `password`
- `secret`
- `token`
- `api_key`

These will be hidden in the UI with `***` after saving.

### Option B: Using Airflow CLI

```powershell
# Inside Airflow scheduler container
docker exec bentley-airflow-scheduler airflow variables set plaid_client_id "your_client_id"
docker exec bentley-airflow-scheduler airflow variables set plaid_secret "your_secret"
docker exec bentley-airflow-scheduler airflow variables set plaid_access_token "access-sandbox-xxx"
docker exec bentley-airflow-scheduler airflow variables set plaid_env "sandbox"
docker exec bentley-airflow-scheduler airflow variables set plaid_start_date "2025-11-01"
docker exec bentley-airflow-scheduler airflow variables set plaid_end_date "2025-11-23"
```

### Option C: Bulk Import JSON

Create `plaid_variables.json`:
```json
{
  "plaid_client_id": "your_client_id",
  "plaid_secret": "your_secret",
  "plaid_access_token": "access-sandbox-xxx",
  "plaid_env": "sandbox",
  "plaid_start_date": "2025-11-01",
  "plaid_end_date": "2025-11-23"
}
```

Import:
```powershell
# Copy file to container
docker cp plaid_variables.json bentley-airflow-scheduler:/tmp/

# Import variables
docker exec bentley-airflow-scheduler airflow variables import /tmp/plaid_variables.json
```

### Verify Variables

```powershell
# List all variables
docker exec bentley-airflow-scheduler airflow variables list

# Get specific variable (secrets will show ***)
docker exec bentley-airflow-scheduler airflow variables get plaid_client_id
```

---

## Part 2: Setting Up Airflow Connections

### MySQL Connection for Transaction Storage

#### Option A: Using Airflow Web UI

1. **Navigate**: Admin → Connections
2. **Click**: + (Add a new record)
3. **Fill in details**:

| Field | Value | Description |
|-------|-------|-------------|
| Connection Id | `mysql_default` | Standard MySQL connection ID |
| Connection Type | `MySQL` | Select from dropdown |
| Host | `mysql` | Docker service name (or `localhost` for external) |
| Schema | `mansa_bot` | Database name |
| Login | `root` | MySQL username |
| Password | `root` | MySQL password (will be encrypted) |
| Port | `3306` | Internal port (use 3307 for external) |
| Extra | `{}` | Leave empty or add JSON config |

**Click "Save"**

#### Option B: Using Airflow CLI

```powershell
# Create MySQL connection
docker exec bentley-airflow-scheduler airflow connections add 'mysql_default' `
  --conn-type 'mysql' `
  --conn-host 'mysql' `
  --conn-schema 'mansa_bot' `
  --conn-login 'root' `
  --conn-password 'root' `
  --conn-port 3306
```

#### Option C: Using Connection URI

```powershell
docker exec bentley-airflow-scheduler airflow connections add 'mysql_default' `
  --conn-uri 'mysql://root:root@mysql:3306/mansa_bot'
```

### Verify Connection

```powershell
# List all connections
docker exec bentley-airflow-scheduler airflow connections list

# Get specific connection (password hidden)
docker exec bentley-airflow-scheduler airflow connections get mysql_default

# Test connection (requires mysql-connector-python)
docker exec bentley-airflow-scheduler airflow connections test mysql_default
```

---

## Part 3: Using in DAGs

### Updated Plaid Client

The `plaid_client.py` now supports **automatic credential discovery**:

```python
from plaid_client import PlaidClient, plaid_ingest

# 1. Auto-loads from Airflow Variables (if available)
# 2. Falls back to environment variables
# 3. Raises error if not found

client = PlaidClient(use_airflow=True)
```

### Example DAG with Variables

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from plaid_client import plaid_ingest

with DAG(
    "plaid_sync_dag",
    start_date=datetime(2023, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=['data-ingestion', 'plaid', 'secure']
) as dag:
    
    # Task automatically uses Airflow Variables
    fetch_transactions = PythonOperator(
        task_id="fetch_plaid_transactions",
        python_callable=plaid_ingest
    )
    
    # Can also access variables directly in tasks
    def print_config(**context):
        env = Variable.get("plaid_env", default_var="sandbox")
        print(f"Using Plaid environment: {env}")
    
    check_config = PythonOperator(
        task_id="check_config",
        python_callable=print_config
    )
    
    check_config >> fetch_transactions
```

---

## Part 4: Security Best Practices

### 1. Fernet Key Encryption

Airflow uses Fernet encryption for sensitive values. Verify your key:

```powershell
# Check Fernet key in docker-compose-airflow.yml
docker exec bentley-airflow-webserver env | grep FERNET_KEY
```

Current key in your setup:
```
AIRFLOW__CORE__FERNET_KEY=ZqWX8ht3KYRLjKTf1RrL4gFKjh5dBv6zB9IqYjXzKjM=
```

**⚠️ Important**: 
- Never change this key after storing encrypted values
- Back up this key securely
- Use same key across all Airflow services

### 2. Variable Naming Conventions

Use these keywords to trigger automatic encryption:
- `password`
- `secret`
- `passwd`
- `authorization`
- `api_key`
- `apikey`
- `access_token`

Example: `plaid_secret` will be encrypted automatically ✅

### 3. Role-Based Access Control (RBAC)

Restrict who can view variables:

1. **Admin → Users** - Create roles
2. **Permissions**: 
   - `can_read` on `Variables`
   - `can_edit` on `Variables`
3. **Assign to users**

### 4. Audit Logs

Track variable access:
```powershell
# View Airflow logs
docker exec bentley-airflow-scheduler tail -f /opt/airflow/logs/scheduler/latest/*.log
```

### 5. Secrets Backend (Advanced)

For production, use external secrets manager:

**AWS Secrets Manager**:
```python
# In airflow.cfg or environment
AIRFLOW__SECRETS__BACKEND=airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
AIRFLOW__SECRETS__BACKEND_KWARGS={"connections_prefix":"airflow/connections","variables_prefix":"airflow/variables"}
```

**Azure Key Vault**:
```python
AIRFLOW__SECRETS__BACKEND=airflow.providers.microsoft.azure.secrets.key_vault.AzureKeyVaultBackend
AIRFLOW__SECRETS__BACKEND_KWARGS={"vault_url":"https://your-vault.vault.azure.net/"}
```

**HashiCorp Vault**:
```python
AIRFLOW__SECRETS__BACKEND=airflow.providers.hashicorp.secrets.vault.VaultBackend
AIRFLOW__SECRETS__BACKEND_KWARGS={"url":"https://vault.example.com:8200","token":"your-token"}
```

---

## Part 5: Migration from Environment Variables

### Step 1: Export Current .env Values

```powershell
# Create migration script
$envFile = Get-Content .env

# Parse and convert to Airflow Variables
foreach ($line in $envFile) {
    if ($line -match '^PLAID_(.+)=(.+)$') {
        $key = "plaid_" + $matches[1].ToLower()
        $value = $matches[2].Trim('"')
        
        Write-Host "Setting: $key"
        docker exec bentley-airflow-scheduler airflow variables set $key $value
    }
}
```

### Step 2: Test DAG Execution

```powershell
# Trigger test run
docker exec bentley-airflow-scheduler airflow dags trigger plaid_sync_dag

# Monitor logs
docker exec bentley-airflow-scheduler airflow tasks test plaid_sync_dag fetch_plaid_transactions 2025-11-23
```

### Step 3: Remove from .env

Once verified working, comment out in `.env`:
```env
# Migrated to Airflow Variables
# PLAID_CLIENT_ID=xxx
# PLAID_SECRET=xxx
# PLAID_ACCESS_TOKEN=xxx
```

---

## Part 6: Troubleshooting

### Error: "Variable plaid_client_id does not exist"

**Solution**: Set the variable using UI or CLI
```powershell
docker exec bentley-airflow-scheduler airflow variables set plaid_client_id "your_value"
```

### Error: "Connection mysql_default not found"

**Solution**: Create the connection
```powershell
docker exec bentley-airflow-scheduler airflow connections add 'mysql_default' \
  --conn-uri 'mysql://root:root@mysql:3306/mansa_bot'
```

### Variables Not Loading in DAG

**Check import**:
```python
from airflow.models import Variable

# In task function
value = Variable.get("plaid_client_id")
```

**Verify variable exists**:
```powershell
docker exec bentley-airflow-scheduler airflow variables list
```

### Connection Test Fails

**Test manually**:
```python
from airflow.hooks.base import BaseHook

conn = BaseHook.get_connection("mysql_default")
print(f"Host: {conn.host}, Port: {conn.port}, DB: {conn.schema}")
```

---

## Part 7: Quick Setup Script

Create `setup_airflow_credentials.ps1`:

```powershell
#!/usr/bin/env pwsh
# Setup Airflow Variables and Connections for Plaid

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Airflow Credentials Setup" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

# Prompt for Plaid credentials
$clientId = Read-Host "Enter Plaid Client ID"
$secret = Read-Host "Enter Plaid Secret" -AsSecureString
$secretPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
)
$accessToken = Read-Host "Enter Plaid Access Token" -AsSecureString
$accessTokenPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($accessToken)
)
$env = Read-Host "Enter Plaid Environment (sandbox/development/production)" -Default "sandbox"

Write-Host "`nSetting Airflow Variables..." -ForegroundColor Yellow

# Set variables
docker exec bentley-airflow-scheduler airflow variables set plaid_client_id $clientId
docker exec bentley-airflow-scheduler airflow variables set plaid_secret $secretPlain
docker exec bentley-airflow-scheduler airflow variables set plaid_access_token $accessTokenPlain
docker exec bentley-airflow-scheduler airflow variables set plaid_env $env
docker exec bentley-airflow-scheduler airflow variables set plaid_start_date "2025-11-01"
docker exec bentley-airflow-scheduler airflow variables set plaid_end_date "2025-11-23"

Write-Host "`nSetting MySQL Connection..." -ForegroundColor Yellow

docker exec bentley-airflow-scheduler airflow connections add 'mysql_default' `
  --conn-type 'mysql' `
  --conn-host 'mysql' `
  --conn-schema 'mansa_bot' `
  --conn-login 'root' `
  --conn-password 'root' `
  --conn-port 3306

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nVerify at: http://localhost:8080" -ForegroundColor White
Write-Host "  - Admin → Variables" -ForegroundColor Gray
Write-Host "  - Admin → Connections`n" -ForegroundColor Gray
```

Run it:
```powershell
.\setup_airflow_credentials.ps1
```

---

## Summary

### ✅ What You've Achieved:

1. **Centralized credential management** using Airflow Variables
2. **Secure database connections** using Airflow Connections  
3. **Automatic encryption** for sensitive values
4. **No hardcoded secrets** in code or .env files
5. **Production-ready security** with RBAC and audit logs

### 🎯 Next Steps:

1. Run `setup_airflow_credentials.ps1` to migrate credentials
2. Test DAG execution with `airflow dags trigger plaid_sync_dag`
3. Remove credentials from `.env` file
4. Configure RBAC roles for your team
5. (Optional) Set up external secrets backend for production

---

**Your Plaid client now follows Airflow security best practices!** 🔐
