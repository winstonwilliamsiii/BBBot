# MySQL Portfolio Integration - Complete Setup

**Created:** December 25, 2025

## 🎯 Architecture Overview

```
Streamlit App (Frontend)
    ↓
Appwrite Function (Bridge)
    ↓
MySQL Database (Data Store)
    ↑
Returns Portfolio Data
```

---

## ✅ **What Was Created:**

### **1. MySQL Query Service** (`services/mysql_portfolio.py`)
- Direct MySQL queries for portfolio data
- Functions: `get_user_portfolio()`, `get_user_transactions()`, `get_portfolio_summary()`
- Used for local development/testing

### **2. Appwrite Function** (`appwrite-functions/get_portfolio_mysql/`)
- Node.js function that queries MySQL
- Actions: `get_holdings`, `get_summary`, `get_transactions`
- Requires `mysql2` npm package

### **3. Streamlit Service Wrapper** (`services/portfolio.py`)
- Calls Appwrite Function from Streamlit
- Functions: `get_portfolio_holdings()`, `get_portfolio_summary()`, `get_portfolio_transactions()`

### **4. Investment Page Integration** (`pages/02_📈_Investment_Analysis.py`)
- Added "📊 Use My Portfolio" checkbox
- Loads real holdings from MySQL via Appwrite
- Falls back to demo tickers if portfolio empty

---

## 📋 **Deployment Steps:**

### **Step 1: Deploy Appwrite Function**

```powershell
cd C:\Users\winst\OneDrive\Documentos\GitHub\BBBot\appwrite-functions

# Package the new function
tar -czf get_portfolio_mysql.tar.gz -C get_portfolio_mysql .

# Move to deployments folder
Move-Item get_portfolio_mysql.tar.gz ..\appwrite-deployments-targz\
```

### **Step 2: Upload to Appwrite Console**

1. Go to https://cloud.appwrite.io/console/project-68869ef500017ca73772/functions
2. Click **"Create Function"**
3. **Name:** `get_portfolio_mysql`
4. **Runtime:** Node.js 18.0
5. **Upload:** `get_portfolio_mysql.tar.gz`
6. **Entrypoint:** `index.js`

### **Step 3: Add Environment Variables**

In Appwrite Function Settings → Variables:

```bash
# Appwrite
APPWRITE_FUNCTION_ENDPOINT=https://fra.cloud.appwrite.io/v1
APPWRITE_FUNCTION_PROJECT_ID=68869ef500017ca73772
APPWRITE_API_KEY=<your-api-key>

# MySQL Connection
MYSQL_HOST=<your-mysql-host>
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=<your-mysql-password>
MYSQL_DATABASE=mansa_bot
```

### **Step 4: Copy Function ID**

After deployment, copy the Function ID and add to `.env`:

```bash
APPWRITE_FUNCTION_ID_GET_PORTFOLIO_MYSQL=<paste-function-id-here>
```

### **Step 5: Test the Function**

**Test Payload:**
```json
{
  "user_id": "test_user",
  "action": "get_holdings"
}
```

**Expected Response:**
```json
{
  "holdings": [
    {
      "ticker": "IONQ",
      "total_quantity": 100,
      "avg_cost_basis": 25.50,
      "total_invested": 2550.00
    }
  ],
  "user_id": "test_user"
}
```

---

## 🧪 **Testing:**

### **Test 1: Local MySQL Connection**

```python
# In Python terminal or Streamlit
from services.mysql_portfolio import get_user_portfolio

result = get_user_portfolio("your_user_id")
print(result)
```

### **Test 2: Appwrite Function**

```python
from services.portfolio import get_portfolio_holdings

result = get_portfolio_holdings("your_user_id")
print(result)
```

### **Test 3: Investment Page**

1. Go to https://bbbot305.streamlit.app/
2. Navigate to **Investment Analysis** page
3. Check **"📊 Use My Portfolio"** in sidebar
4. Should load your actual holdings from MySQL

---

## 🗄️ **MySQL Schema Requirements:**

Your MySQL database needs these tables:

### **portfolios Table:**
```sql
CREATE TABLE portfolios (
    portfolio_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    quantity DECIMAL(15,4) NOT NULL,
    purchase_price DECIMAL(15,4),
    total_value DECIMAL(15,4),
    current_price DECIMAL(15,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_ticker (user_id, ticker)
);
```

### **transactions Table:**
```sql
CREATE TABLE transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    transaction_type ENUM('BUY', 'SELL') NOT NULL,
    quantity DECIMAL(15,4) NOT NULL,
    price DECIMAL(15,4) NOT NULL,
    total_value DECIMAL(15,4) NOT NULL,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_date (user_id, transaction_date)
);
```

---

## 🔐 **Security Considerations:**

1. **Never commit MySQL passwords** - Use environment variables
2. **Use read-only MySQL user** for portfolio queries
3. **Enable SSL** for MySQL connections in production
4. **Rate limit** Appwrite Function executions
5. **Validate user_id** before queries (prevent SQL injection)

---

## 🚀 **Usage in Streamlit:**

```python
# In your Streamlit pages
from services.portfolio import get_portfolio_holdings, get_portfolio_summary

# Get current user
user_id = st.session_state.get('user_id', 'demo_user')

# Fetch portfolio
portfolio = get_portfolio_holdings(user_id)

if "error" not in portfolio:
    for holding in portfolio['holdings']:
        st.write(f"{holding['ticker']}: {holding['total_quantity']} shares")
```

---

## ✅ **Next Steps:**

1. **Deploy Appwrite Function** (15 min)
2. **Test with sample data** (5 min)
3. **Push to git & Streamlit Cloud** (auto-deploys)
4. **Verify on https://bbbot305.streamlit.app/**

---

## 🆘 **Troubleshooting:**

### **"Database connection failed"**
- Check MySQL host/port in environment variables
- Verify MySQL user has SELECT permissions
- Confirm database name is correct

### **"Function timeout"**
- Increase timeout in Appwrite Function settings
- Optimize MySQL queries (add indexes)
- Limit result sets with LIMIT clauses

### **"Missing configuration"**
- Verify all environment variables are set
- Check Function ID in .env file
- Ensure mysql2 package is in dependencies

---

**Architecture:** Streamlit → Appwrite → MySQL  
**Status:** Ready for deployment ✅
