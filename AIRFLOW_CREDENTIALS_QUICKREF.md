# Airflow Credentials - Quick Reference

## Setup Commands

### 1. Run Setup Script (Interactive)
```powershell
.\setup_airflow_credentials.ps1
```

### 2. Manual Variable Setup
```powershell
docker exec bentley-airflow-scheduler airflow variables set plaid_client_id "your_client_id"
docker exec bentley-airflow-scheduler airflow variables set plaid_secret "your_secret"
docker exec bentley-airflow-scheduler airflow variables set plaid_access_token "access-sandbox-xxx"
docker exec bentley-airflow-scheduler airflow variables set plaid_env "sandbox"
docker exec bentley-airflow-scheduler airflow variables set plaid_start_date "2025-11-01"
docker exec bentley-airflow-scheduler airflow variables set plaid_end_date "2025-11-23"
```

### 3. MySQL Connection
```powershell
docker exec bentley-airflow-scheduler airflow connections add 'mysql_default' \
  --conn-uri 'mysql://root:root@mysql:3306/mansa_bot'
```

---

## Verify Setup

### List Variables
```powershell
docker exec bentley-airflow-scheduler airflow variables list
```

### List Connections
```powershell
docker exec bentley-airflow-scheduler airflow connections list
```

### Get Specific Variable
```powershell
docker exec bentley-airflow-scheduler airflow variables get plaid_client_id
```

### Test Connection
```powershell
docker exec bentley-airflow-scheduler airflow connections get mysql_default
```

---

## Using in Python Code

### Automatic Discovery (Recommended)
```python
from plaid_client import PlaidClient, plaid_ingest

# Automatically tries Airflow Variables first, then environment
client = PlaidClient(use_airflow=True)
```

### Manual Variable Access
```python
from airflow.models import Variable

client_id = Variable.get("plaid_client_id")
secret = Variable.get("plaid_secret")
access_token = Variable.get("plaid_access_token")
```

### Manual Connection Access
```python
from airflow.hooks.base import BaseHook

mysql_conn = BaseHook.get_connection("mysql_default")
conn_params = {
    "host": mysql_conn.host,
    "port": mysql_conn.port,
    "user": mysql_conn.login,
    "password": mysql_conn.password,
    "database": mysql_conn.schema
}
```

---

## DAG Example

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from plaid_client import plaid_ingest

with DAG(
    "plaid_sync_dag",
    start_date=datetime(2023, 1, 1),
    schedule_interval="@daily",
    catchup=False
) as dag:
    
    # Uses Airflow Variables automatically
    fetch = PythonOperator(
        task_id="fetch_plaid_transactions",
        python_callable=plaid_ingest
    )
```

---

## Airflow UI Access

**URL**: http://localhost:8080  
**Login**: admin / admin

### View Variables
Admin → Variables

### View Connections
Admin → Connections

### Encrypted Fields
Variables/connections with these keywords are auto-encrypted:
- `password`
- `secret`
- `token`
- `api_key`
- `passwd`
- `authorization`

---

## Troubleshooting

### Variable Not Found
```powershell
# Check if exists
docker exec bentley-airflow-scheduler airflow variables list | grep plaid

# Set if missing
docker exec bentley-airflow-scheduler airflow variables set plaid_client_id "value"
```

### Connection Not Found
```powershell
# Check if exists
docker exec bentley-airflow-scheduler airflow connections list | grep mysql

# Add if missing
docker exec bentley-airflow-scheduler airflow connections add 'mysql_default' \
  --conn-uri 'mysql://root:root@mysql:3306/mansa_bot'
```

### Permission Denied
```powershell
# Ensure user has Variable.can_read permission
# Check in Airflow UI: Security → List Roles → Admin
```

---

## Security Notes

✅ **Fernet Key**: `ZqWX8ht3KYRLjKTf1RrL4gFKjh5dBv6zB9IqYjXzKjM=`  
   - Do NOT change after storing encrypted values
   - Back up securely

✅ **Encrypted by Default**: Variables with sensitive keywords  
✅ **RBAC**: Control access via Security → List Roles  
✅ **Audit Logs**: All access logged in Airflow logs  
✅ **No .env Files**: Eliminate risk of committing secrets  

---

## Priority Order

The `plaid_client.py` checks credentials in this order:

1. **Parameters** passed to `PlaidClient()` or `store_transactions()`
2. **Airflow Variables** (if `use_airflow=True` and Airflow available)
3. **Airflow Connections** (for MySQL connection)
4. **Environment variables** (fallback)

---

## Required Airflow Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `plaid_client_id` | Plaid client ID | `5f8a9b2c3d1e4f` |
| `plaid_secret` | Plaid secret (encrypted) | `abc123xyz` |
| `plaid_access_token` | Access token (encrypted) | `access-sandbox-xxx` |
| `plaid_env` | Environment | `sandbox` |
| `plaid_start_date` | Start date | `2025-11-01` |
| `plaid_end_date` | End date | `2025-11-23` |

## Required Airflow Connection

| Connection | Type | Details |
|------------|------|---------|
| `mysql_default` | MySQL | `mysql://root:root@mysql:3306/mansa_bot` |

---

📖 **Full Guide**: See `AIRFLOW_CREDENTIALS_GUIDE.md`  
🔧 **Setup Script**: Run `.\setup_airflow_credentials.ps1`  
🎯 **Test**: `docker exec bentley-airflow-scheduler airflow dags trigger plaid_sync_dag`
