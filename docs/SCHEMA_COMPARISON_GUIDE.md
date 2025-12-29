# Schema Comparison Tools - Quick Reference

## 📋 Overview

Two powerful tools for comparing MySQL database schemas across environments:

1. **compare_mysql_railway_schemas.py** - Compare local vs Railway production
2. **compare_all_databases.py** - Compare multiple databases simultaneously

---

## 🚀 Usage

### Option 1: Compare Local vs Railway (Production)
```bash
python compare_mysql_railway_schemas.py
```

**What it checks:**
- Missing tables in either database
- Missing columns in tables
- Column type mismatches (e.g., VARCHAR(255) vs TEXT)
- Index differences
- Default value differences

**Requirements:**
- Railway credentials must be in `.env` or Streamlit secrets:
  ```bash
  RAILWAY_MYSQL_HOST=nozomi.proxy.rlwy.net
  RAILWAY_MYSQL_PORT=54537
  RAILWAY_MYSQL_USER=root
  RAILWAY_MYSQL_PASSWORD=your_password
  RAILWAY_MYSQL_DATABASE=railway
  ```

### Option 2: Compare All Local Databases
```bash
python compare_all_databases.py
```

**What it compares:**
- `mydb` (port 3306) - Budget/Plaid database
- `mansa_bot` (port 3307) - Investment/trading database
- `railway` (if credentials available) - Production database

**Output:**
- Common tables across all databases
- Unique tables in each database
- Detailed structure comparison for key tables
- Saves full report to `schema_comparison_report.txt`

---

## 📊 Sample Output

### Successful Comparison
```
================================================================================
DATABASE SCHEMA COMPARISON REPORT
================================================================================

📊 Summary:
   Local tables: 19
   Railway tables: 22

⚠️  Tables in LOCAL but missing in RAILWAY (2):
   • plaid_items
   • user_plaid_tokens

⚠️  Tables in RAILWAY but missing in LOCAL (5):
   • production_table_1
   • production_table_2
   • production_table_3

🔧 Column Differences (3 tables):

   📋 Table: broker_api_credentials
      Missing in Railway: tenant_id
      
   📋 Table: users
      Type Mismatches:
         • email: varchar(255) (local) vs varchar(100) (remote)
         • is_active: tinyint(1) (local) vs boolean (remote)

✅ SCHEMAS ARE IDENTICAL - No differences found!
```

---

## 🔍 Key Findings from Your Databases

### ✅ Broker API Tables
**Status:** Present in BOTH `mydb` and `mansa_bot`

Tables confirmed:
- ✅ `broker_api_credentials` - Unified credentials
- ✅ `broker_connections` - Connection tracking

Required columns present:
- ✅ `is_active` (TINYINT(1))
- ✅ `tenant_id` (INT)
- ✅ `user_id` (INT)
- ✅ `broker` (ENUM)
- ✅ `access_token` (TEXT)

### 📌 Plaid Tables
**Status:** Only in `mydb` (Budget database)

Tables:
- `plaid_items` - New Plaid structure
- `user_plaid_tokens` - Legacy Plaid structure

**Note:** Code supports BOTH tables for backwards compatibility!

---

## 🛠️ Common Use Cases

### 1. Before Deploying to Production
```bash
# Compare your local schema with Railway before deploying
python compare_mysql_railway_schemas.py

# Review differences
cat schema_diff.txt
```

### 2. After Creating New Tables Locally
```bash
# Check if new tables need to be created in other databases
python compare_all_databases.py

# Generate SQL scripts for missing tables
grep "missing_in_remote" schema_diff.txt
```

### 3. Troubleshooting Column Errors
```bash
# When you get "Unknown column" errors in production
python compare_mysql_railway_schemas.py

# Look for column_differences section in output
```

### 4. Verifying Multi-Database Consistency
```bash
# Ensure broker tables exist everywhere
python compare_all_databases.py | grep "broker_"
```

---

## 📁 Output Files

Both scripts generate reports:

| File | Description |
|------|-------------|
| `schema_diff.txt` | Raw Python dict of all differences |
| `schema_comparison_report.txt` | Detailed table-by-table breakdown |
| Terminal output | Human-readable summary |

---

## ⚠️ Known Issues & Solutions

### Issue: Railway credentials not found
```
⚠️  Railway credentials not found in .env
   Set RAILWAY_MYSQL_* variables to compare with Railway
```

**Solution:** Add Railway credentials to `.env` (get from Streamlit Cloud secrets):
```bash
RAILWAY_MYSQL_HOST=nozomi.proxy.rlwy.net
RAILWAY_MYSQL_PORT=54537
RAILWAY_MYSQL_USER=root
RAILWAY_MYSQL_PASSWORD=<from streamlit secrets>
RAILWAY_MYSQL_DATABASE=railway
```

### Issue: SQL syntax error with table name "trigger"
```
❌ Error: (1064, "You have an error in your SQL syntax...")
```

**Solution:** Fixed! Scripts now escape table names with backticks:
```python
escaped_table = f"`{table}`"
cursor.execute(f"DESCRIBE {escaped_table};")
```

### Issue: Connection timeout
```
❌ Connection failed: (2003, "Can't connect to MySQL server...")
```

**Solutions:**
- Check MySQL is running: `netstat -an | Select-String "3306"`
- Verify port numbers in `.env`
- Test direct connection: `mysql -h 127.0.0.1 -P 3306 -u root -p`

---

## 🔐 Security Notes

- ⚠️ **Never commit** Railway credentials to Git
- ✅ Use `.env` for local credentials
- ✅ Use Streamlit secrets for production credentials
- ✅ Scripts automatically skip databases without credentials

---

## 📈 Integration with CI/CD

### GitHub Actions Example
```yaml
name: Schema Validation

on:
  pull_request:
    branches: [main]

jobs:
  validate-schema:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Compare schemas
        env:
          RAILWAY_MYSQL_PASSWORD: ${{ secrets.RAILWAY_MYSQL_PASSWORD }}
        run: python compare_mysql_railway_schemas.py
        
      - name: Upload diff report
        uses: actions/upload-artifact@v2
        with:
          name: schema-diff
          path: schema_diff.txt
```

---

## 🎯 Best Practices

1. **Run before every production deployment**
   ```bash
   python compare_mysql_railway_schemas.py
   ```

2. **Review differences carefully**
   - Missing tables → Create them in production
   - Missing columns → Run ALTER TABLE scripts
   - Type mismatches → Consider data migration

3. **Keep schemas in sync**
   - Commit SQL migration scripts to Git
   - Document schema changes in PR descriptions
   - Test migrations on Railway staging first

4. **Use version control for schemas**
   ```bash
   # Save current schema snapshot
   python compare_all_databases.py
   git add schema_comparison_report.txt
   git commit -m "chore: Update schema snapshot"
   ```

---

## 📚 Related Files

- `create_broker_api_tables.py` - Creates broker tables
- `create_plaid_items_table.py` - Creates Plaid tables
- `verify_mysql_status.py` - Verifies database connections
- `docs/BROKER_API_STATUS.md` - Broker integration status

---

## 🆘 Troubleshooting

Run these commands in order:

1. **Verify databases are running:**
   ```bash
   python verify_mysql_status.py
   ```

2. **Check schema differences:**
   ```bash
   python compare_all_databases.py
   ```

3. **Review detailed report:**
   ```bash
   notepad schema_comparison_report.txt
   ```

4. **Create missing tables:**
   ```bash
   python create_broker_api_tables.py
   ```

---

**Last Updated:** December 29, 2025  
**Status:** ✅ Both tools verified and working
