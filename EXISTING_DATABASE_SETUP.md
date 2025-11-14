# Using Existing Bentley_Bot Database for Airflow

## ✅ Perfect! You can absolutely use your existing database structure.

### 🗄️ Your Database Structure:
- **Database Name**: `Bentley_Bot` 
- **Schema**: `mansa_bot`
- **Use Case**: Airflow will share this database but create its own tables

### 🔧 Configuration Updated

I've updated your Airflow configuration to use:
```
Database: Bentley_Bot
Connection: mysql+pymysql://root:password@localhost:3306/Bentley_Bot
```

### 📝 **YOU NEED TO UPDATE THE PASSWORD**

Please update the connection string in `airflow_config/airflow.cfg` with your actual MySQL credentials:

```ini
# Replace 'password' with your actual MySQL root password
sql_alchemy_conn = mysql+pymysql://root:YOUR_ACTUAL_PASSWORD@localhost:3306/Bentley_Bot
```

Or if you have a different MySQL user:
```ini
sql_alchemy_conn = mysql+pymysql://YOUR_USERNAME:YOUR_PASSWORD@localhost:3306/Bentley_Bot
```

### 🛡️ How Airflow Will Use Your Database

**What Airflow Does:**
1. **Creates its own tables** in your `Bentley_Bot` database
2. **Table names start with `airflow_`** (e.g., `airflow_dag`, `airflow_task_instance`)
3. **Your existing `mansa_bot` tables remain untouched**
4. **No conflicts** - Airflow and your app can coexist

**Example of what you'll see:**
```
Bentley_Bot database:
├── your_existing_table_1      # Your data
├── your_existing_table_2      # Your data  
├── mansa_bot_transactions     # Your mansa_bot schema
├── mansa_bot_users           # Your mansa_bot schema
├── airflow_dag               # Airflow system table
├── airflow_task_instance     # Airflow system table
└── airflow_variable          # Airflow system table
```

### 🚀 **Next Steps:**

1. **Update Password** in `airflow_config/airflow.cfg`:
   ```ini
   sql_alchemy_conn = mysql+pymysql://root:YOUR_REAL_PASSWORD@localhost:3306/Bentley_Bot
   ```

2. **Test Connection**:
   ```bash
   .\airflow.bat test
   ```

3. **Initialize Airflow** (creates Airflow tables in your existing database):
   ```bash
   .\airflow.bat init
   ```

4. **Verify Everything Works**:
   ```bash
   .\airflow.bat config
   ```

### 🔒 **Security Note:**

For production, consider creating a dedicated user for Airflow:
```sql
CREATE USER 'airflow_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON Bentley_Bot.* TO 'airflow_user'@'localhost';
FLUSH PRIVILEGES;
```

### ✅ **Benefits of This Approach:**

- ✅ **Shared Database**: One database for both your app and Airflow
- ✅ **Data Integration**: Easy to create DAGs that work with your existing data
- ✅ **Simplified Management**: One database to backup/maintain
- ✅ **No Data Duplication**: Airflow can directly access your mansa_bot tables

**Just update the password in the config file and you're ready to go!** 🎉