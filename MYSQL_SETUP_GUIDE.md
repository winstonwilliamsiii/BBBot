# MySQL Configuration for Airflow - Complete Setup Guide

## ✅ Configuration Updated

Your Airflow is now configured to use MySQL with the database name `mansa_bot`. Here's what was changed:

### 🔧 Updated Configuration Files

1. **`airflow_config/airflow.cfg`**:
   - Database connection: `mysql+pymysql://airflow:airflow123@localhost:3306/mansa_bot`
   - Executor: Changed to `LocalExecutor` (better for MySQL)
   - Result backend: Updated for MySQL

2. **Installed MySQL Dependencies**:
   - `pymysql` - MySQL driver for Python
   - `mysqlclient` - Native MySQL client
   - `apache-airflow[mysql]` - Airflow MySQL extras

## 🚀 Setup Steps

### Step 1: Install and Start MySQL
Make sure MySQL is installed and running on your system:
```bash
# Check if MySQL is running
mysql --version
```

### Step 2: Create Database and User
Run the SQL commands in `mysql_setup.sql`:

**Option A: Using MySQL Command Line**
```bash
mysql -u root -p < mysql_setup.sql
```

**Option B: Using MySQL Workbench/phpMyAdmin**
Open `mysql_setup.sql` and execute the commands:
```sql
CREATE DATABASE IF NOT EXISTS mansa_bot 
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'airflow'@'localhost' IDENTIFIED BY 'airflow123';
GRANT ALL PRIVILEGES ON mansa_bot.* TO 'airflow'@'localhost';
FLUSH PRIVILEGES;
```

### Step 3: Update Credentials (if needed)
Edit `airflow_config/airflow.cfg` if you want different credentials:
```ini
sql_alchemy_conn = mysql+pymysql://YOUR_USER:YOUR_PASSWORD@localhost:3306/mansa_bot
```

### Step 4: Test Connection
```bash
.\airflow.bat test
```

### Step 5: Initialize Database
```bash
.\airflow.bat init
```

### Step 6: Start Services
```bash
# Start webserver
.\airflow.bat webserver

# In another terminal, start scheduler
.\airflow.bat scheduler
```

## 🔍 Troubleshooting

### MySQL Connection Issues
1. **Check MySQL is running**: `mysql -u root -p`
2. **Verify database exists**: `SHOW DATABASES;`
3. **Check user permissions**: `SELECT User, Host FROM mysql.user WHERE User = 'airflow';`

### Common Errors
- **"Access denied"**: Update username/password in `airflow.cfg`
- **"Database doesn't exist"**: Run the SQL setup commands
- **"Connection refused"**: Make sure MySQL service is running

### Test Commands
```bash
# Test MySQL connection
.\airflow.bat test

# Show current configuration  
.\airflow.bat config

# Initialize database (run once)
.\airflow.bat init
```

## 📋 Current Configuration

- **Database**: `mansa_bot`
- **Host**: `localhost:3306`
- **User**: `airflow`
- **Password**: `airflow123`
- **Connection**: `mysql+pymysql://airflow:airflow123@localhost:3306/mansa_bot`
- **Executor**: `LocalExecutor`

## 🔐 Security Notes

For production use:
1. Change the default password `airflow123`
2. Use environment variables for credentials
3. Enable SSL connections
4. Create dedicated MySQL user with minimal privileges

## ✅ What's Next

1. **Setup MySQL database** (Step 2 above)
2. **Test connection**: `.\airflow.bat test`
3. **Initialize database**: `.\airflow.bat init`
4. **Start Airflow**: `.\airflow.bat webserver`

Your Airflow is now configured for MySQL! 🎉