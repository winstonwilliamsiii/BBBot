# Plaid Integration - Quick Start Guide

## 🚀 What Was Built

The Plaid integration adds **Personal Budget Analysis** to your home page with full authentication. Users can:

- Connect bank accounts via Plaid
- Track income and expenses automatically
- Set budgets by category
- View spending trends
- Get AI-powered financial insights

## 📁 Files Created

### 1. Database Schema
**`scripts/setup/budget_schema.sql`** (350+ lines)
- Creates 6 new tables: `budget_categories`, `budget_tracking`, `user_plaid_tokens`, `cash_flow_summary`, `transaction_notes`
- Updates `transactions` and `users` tables
- Adds 3 views and 2 stored procedures

### 2. Budget Analysis Module
**`frontend/utils/budget_analysis.py`** (550+ lines)
- `BudgetAnalyzer` class for all budget calculations
- Cash flow analysis (income, expenses, net flow)
- Category breakdown and insights
- Budget vs actual comparisons
- Transaction fetching with caching

### 3. Budget Dashboard UI
**`frontend/components/budget_dashboard.py`** (650+ lines)
- `show_budget_summary()` - Compact view for home page
- `show_full_budget_dashboard()` - Full page with tabs
- Interactive charts (Plotly)
- Transaction history table
- Budget health indicators

### 4. Budget Page
**`pages/03_💰_Personal_Budget.py`** (175+ lines)
- Full budget management interface
- Tabs: Overview, Transactions, Trends, Insights
- Login/authentication for access
- Plaid connection management

### 5. Updated Files
- **`streamlit_app.py`** - Added authentication + budget section
- **`frontend/utils/rbac.py`** - Added budget permissions
- **`requirements.txt`** - Added dependencies

### 6. Setup Script
**`scripts/setup_plaid_integration.ps1`**
- Automated setup wizard
- Installs dependencies
- Runs database migrations
- Validates configuration

## 🔧 Quick Setup (5 minutes)

### Option 1: Automated Setup
```powershell
# Run the setup script
.\scripts\setup_plaid_integration.ps1
```

### Option 2: Manual Setup

#### Step 1: Install Dependencies
```bash
pip install plaid-python cryptography python-dateutil mysql-connector-python
```

#### Step 2: Setup Database
```bash
mysql -u root -p -h 127.0.0.1 -P 3306 mydb < scripts/setup/budget_schema.sql
```

#### Step 3: Configure Environment
Add to `.env`:
```bash
# Plaid Configuration
PLAID_CLIENT_ID=your_client_id_here
PLAID_SECRET=your_sandbox_secret_here
PLAID_ENV=sandbox

# MySQL Configuration
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=mydb
```

#### Step 4: Get Plaid Credentials
1. Sign up: https://dashboard.plaid.com/signup
2. Get Sandbox credentials (free for development)
3. Update `.env` with your credentials

#### Step 5: Start Application
```bash
streamlit run streamlit_app.py
```

## 🎯 User Flow

### For Unauthenticated Users
1. Visit home page → See portfolio analysis only
2. **Budget section is HIDDEN**
3. Login prompt shown in expandable section

### For Authenticated Users (Client/Investor/Admin)
1. Login → See portfolio analysis
2. **Budget section appears below portfolio**
3. Options:
   - **Not connected**: "Connect Your Bank" button
   - **Connected**: Mini dashboard with:
     - Income/Expenses/Net Flow cards
     - Top 3 spending categories
     - Budget progress bars
     - Link to full budget page

### On Budget Page (`03_💰_Personal_Budget.py`)
1. Full dashboard with 4 tabs:
   - **Overview**: Cash flow metrics, budget status, category pie chart
   - **Transactions**: Searchable/filterable table, export CSV
   - **Trends**: 6-month historical charts
   - **Insights**: AI-powered alerts and recommendations

## 📊 Database Schema

### Main Tables
```
transactions (updated)
├── user_id (new)
├── transaction_id
├── date
├── amount
├── category
└── merchant_name

user_plaid_tokens
├── user_id (unique)
├── access_token (encrypted)
├── institution_name
└── last_sync

budget_categories
├── user_id
├── category_name
├── monthly_budget
└── color_hex

budget_tracking
├── user_id
├── month
├── category
├── budgeted
├── actual
└── variance (computed)

cash_flow_summary
├── user_id
├── month
├── total_income
├── total_expenses
└── net_cash_flow (computed)
```

## 🔐 Permissions

Budget access controlled by RBAC:

| Role | VIEW_BUDGET | MANAGE_BUDGET | CONNECT_BANK |
|------|-------------|---------------|--------------|
| Guest | ❌ | ❌ | ❌ |
| Client | ✅ | ❌ | ✅ |
| Investor | ✅ | ✅ | ✅ |
| Admin | ✅ | ✅ | ✅ |

## 🧪 Testing

### Test Without Plaid (Database Only)
1. Insert sample transactions manually:
```sql
INSERT INTO transactions (user_id, transaction_id, date, name, amount, category)
VALUES (1, 'test-001', '2025-12-01', 'Grocery Store', -85.50, 'Food and Drink');
```

2. Login as a test user
3. View budget dashboard

### Test With Plaid Sandbox
1. Use Plaid Link to connect
2. Use test credentials: `user_good` / `pass_good`
3. Transactions auto-sync

## 📈 Key Features

### Cash Flow Tracking
- Real-time income/expense monitoring
- Month-over-month comparison
- Trend indicators (📈 📉 ➡️)

### Budget Management
- Set budgets per category
- Visual progress bars
- Color-coded status (🟢 🟡 🔴)

### Transaction Analysis
- Automatic categorization
- Search and filtering
- Export to CSV

### Financial Insights
- Overspending alerts
- Unusual transaction detection
- Personalized recommendations

## 🔍 Troubleshooting

### "Database connection error"
- Check MySQL is running on port 3306
- Verify credentials in `.env`
- Run: `mysql -u root -p mydb -e "SHOW TABLES;"`

### "RBAC module not available"
- Check `frontend/utils/rbac.py` exists
- Verify imports in `streamlit_app.py`

### "No transactions found"
- Check `user_plaid_tokens` table has entry
- Verify transactions have `user_id` set
- Run: `SELECT COUNT(*) FROM transactions WHERE user_id = 1;`

### "Budget section not showing"
- Login with Client/Investor/Admin role
- Check `VIEW_BUDGET` permission in RBAC
- Clear Streamlit cache: Press 'C' in browser

## 📚 API Reference

### BudgetAnalyzer Class
```python
from frontend.utils.budget_analysis import BudgetAnalyzer

analyzer = BudgetAnalyzer()

# Get cash flow for user
cash_flow = analyzer.calculate_cash_flow(user_id=1, month='2025-12')

# Get spending by category
categories = analyzer.get_spending_by_category(user_id=1, limit=5)

# Get budget status
budget_status = analyzer.get_budget_status(user_id=1)

# Generate insights
insights = analyzer.generate_insights(user_id=1)
```

### Budget Dashboard Functions
```python
from frontend.components.budget_dashboard import show_budget_summary

# Show on home page (compact view)
show_budget_summary(user_id=1)

# Show full dashboard (dedicated page)
show_full_budget_dashboard(user_id=1)
```

## 🎨 Customization

### Add New Categories
```sql
INSERT INTO budget_categories (user_id, category_name, monthly_budget, color_hex, icon)
VALUES (1, 'Pet Care', 150.00, '#FFB6C1', '🐕');
```

### Adjust Budget Limits
```sql
UPDATE budget_categories 
SET monthly_budget = 800.00 
WHERE user_id = 1 AND category_name = 'Food and Drink';
```

### Change Color Scheme
Edit `frontend/components/budget_dashboard.py`:
```python
# Budget status colors
status_colors = {
    'Under Budget': 'green',
    'On Track': 'orange',
    'Over Budget': 'red'
}
```

## 🚀 Next Steps

1. **Get Plaid credentials** - Sign up and get sandbox keys
2. **Run database setup** - Execute `budget_schema.sql`
3. **Configure `.env`** - Add Plaid and MySQL credentials
4. **Start app** - Login and connect your bank
5. **Explore features** - Set budgets, track spending!

## 📞 Support

Issues? Check:
- **Roadmap**: `docs/PLAID_INTEGRATION_ROADMAP.md`
- **Schema**: `scripts/setup/budget_schema.sql`
- **Code**: `frontend/utils/budget_analysis.py`

---

**Built with:** Python • Streamlit • Plaid API • MySQL • Plotly  
**Version:** 1.0.0 (December 2025)
