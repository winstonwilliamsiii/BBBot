# Development Environment - Quick Fix Guide

## Current Status

### ✅ Working
- **yFinance**: Fully operational for stock data
- **Plaid SDK**: Installed and ready
- **Kalshi**: Configured with credentials
- **Python Packages**: All installed

### ❌ Needs Configuration

#### 1. MySQL Connection
**Issue**: Root password not set in .env.development

**Fix**:
1. Find your MySQL root password (check MySQL installation notes)
2. Update `.env.development`:
   ```env
   DB_PASSWORD=your_mysql_root_password
   ```
3. Or create database manually:
   ```powershell
   # If you know the password:
   mysql -u root -p
   # Then run:
   CREATE DATABASE IF NOT EXISTS bentley_bot_dev;
   USE bentley_bot_dev;
   
   # Create users table
   CREATE TABLE IF NOT EXISTS users (
       id INT PRIMARY KEY AUTO_INCREMENT,
       username VARCHAR(50) UNIQUE NOT NULL,
       password_hash VARCHAR(255) NOT NULL,
       email VARCHAR(100),
       role VARCHAR(20) DEFAULT 'VIEWER',
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   
   # Create default admin user (password: admin123)
   INSERT IGNORE INTO users (username, password_hash, email, role)
   VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqQqZ5wQ5u', 'admin@localhost', 'ADMIN');
   ```

#### 2. Alpaca API Keys
**Issue**: Placeholder credentials in .env.development

**Fix**:
1. Sign up at https://alpaca.markets (FREE paper trading)
2. Get API keys from Dashboard
3. Update `.env.development`:
   ```env
   ALPACA_API_KEY=PK...your_key
   ALPACA_SECRET_KEY=...your_secret
   ```

#### 3. Plaid API Keys
**Issue**: Placeholder credentials in .env.development

**Fix**:
1. Sign up at https://plaid.com (FREE sandbox)
2. Get credentials from Dashboard → Team Settings → Keys
3. Update `.env.development`:
   ```env
   PLAID_CLIENT_ID=...your_client_id
   PLAID_SECRET=...your_secret
   ```

#### 4. MLflow Server (Optional for ML Signals)
**Status**: Not running but not critical

**To Enable**:
```powershell
# In a separate terminal:
mlflow server --host localhost --port 5000
```

#### 5. AlphaVantage (Optional)
**Status**: Not set but optional

**To Enable**:
1. Get free key: https://www.alphavantage.co/support/#api-key
2. Add to `.env.development`:
   ```env
   ALPHA_VANTAGE_API_KEY=your_key
   ```

## Quick Start (Minimum Configuration)

To get the app running with basic features:

1. **Set MySQL Password**:
   ```env
   # In .env.development
   DB_PASSWORD=your_mysql_password
   ```

2. **Run Setup**:
   ```powershell
   python fix_dev_apis.py
   ```

3. **Start Streamlit**:
   ```powershell
   streamlit run streamlit_app.py
   ```

## What Works Without API Keys

- ✅ Main dashboard with portfolio overview
- ✅ Investment Analysis (yFinance data)
- ✅ Economic calendar widget
- ✅ Basic RBAC authentication
- ❌ Personal Budget (needs MySQL + Plaid)
- ❌ Broker Trading (needs Alpaca/MT5)
- ❌ Trading Bot (needs Alpaca + MLflow)
- ⚠️ Prediction Analytics (has Kalshi but needs ADMIN login)

## Testing Connections

After updating credentials, run:
```powershell
python fix_dev_apis.py
```

This will test all API connections and show what's working.

## Support

If you need help:
1. Check error messages in terminal
2. Verify credentials are copied correctly (no extra spaces)
3. Make sure you're using development/sandbox credentials
4. Check that MySQL service is running: `Get-Service MySQL*`
