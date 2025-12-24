# Plaid Integration Roadmap for Personal Budget Analysis

## 📋 Current State Analysis

### ✅ What You Have
1. **Plaid Client** (`.vscode/plaid_client.py`)
   - Fetch transactions from Plaid API
   - Store transactions in MySQL database
   - Support for Airflow and environment variables
   - Transaction table schema defined

2. **RBAC System** (`frontend/utils/rbac.py`)
   - User authentication with roles (Guest, Client, Investor, Admin)
   - Permission-based access control
   - Session management
   - KYC/agreement tracking

3. **Home Page** (`streamlit_app.py`)
   - Portfolio analysis
   - Yahoo Finance integration
   - Metric cards and visualizations

4. **Environment Configuration**
   - Plaid credentials structure in `.env`
   - MySQL connection ready
   - Airflow DAG support

### ⏳ What's Missing
1. **Personal Budget Analysis UI Component**
2. **Transaction categorization and analysis**
3. **Cash flow visualization**
4. **Budget vs Actual tracking**
5. **Integration with home page authentication**
6. **User-specific transaction storage**

---

## 🎯 Implementation Plan

### Phase 1: Database Schema Updates (1-2 hours)

#### 1.1 Create User-Specific Transaction Tables
```sql
-- Add user_id to transactions table
ALTER TABLE transactions ADD COLUMN user_id INT;
ALTER TABLE transactions ADD INDEX idx_user_date (user_id, date);

-- Create budget categories table
CREATE TABLE IF NOT EXISTS budget_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    parent_category VARCHAR(100),
    monthly_budget DECIMAL(10,2) DEFAULT 0,
    color_hex VARCHAR(7) DEFAULT '#FF8C00',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_category (user_id, category_name),
    INDEX idx_user (user_id)
);

-- Create budget tracking table
CREATE TABLE IF NOT EXISTS budget_tracking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    month DATE NOT NULL,
    category VARCHAR(100) NOT NULL,
    budgeted DECIMAL(10,2) DEFAULT 0,
    actual DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_month_category (user_id, month, category),
    INDEX idx_user_month (user_id, month)
);

-- Create Plaid access tokens table (secure storage)
CREATE TABLE IF NOT EXISTS user_plaid_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    access_token VARCHAR(255) NOT NULL,
    item_id VARCHAR(255) NOT NULL,
    institution_name VARCHAR(100),
    last_sync TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user (user_id)
);

-- Create cash flow summary table
CREATE TABLE IF NOT EXISTS cash_flow_summary (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    month DATE NOT NULL,
    total_income DECIMAL(10,2) DEFAULT 0,
    total_expenses DECIMAL(10,2) DEFAULT 0,
    net_cash_flow DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_month (user_id, month),
    INDEX idx_user_month (user_id, month)
);
```

#### 1.2 Update RBAC User Table
```sql
-- Add Plaid connection status to users
ALTER TABLE users ADD COLUMN plaid_connected BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN plaid_last_sync TIMESTAMP NULL;
```

### Phase 2: Backend Integration (3-4 hours)

#### 2.1 Create Budget Analysis Module
**File: `frontend/utils/budget_analysis.py`**

Key Features:
- Fetch user transactions from MySQL
- Categorize transactions (income/expense)
- Calculate cash flow metrics
- Compare budget vs actual
- Generate insights and alerts
- Cache results per user

#### 2.2 Create Plaid Integration Module
**File: `frontend/utils/plaid_integration.py`**

Key Features:
- Generate Plaid Link token for user
- Exchange public token for access token
- Store encrypted tokens in database
- Fetch transactions for authenticated user
- Handle Plaid webhooks
- Sync transactions on schedule

#### 2.3 Update RBAC Permissions
**File: `frontend/utils/rbac.py`**

Add new permissions:
```python
class Permission(Enum):
    # ... existing permissions
    VIEW_BUDGET = "view_budget"
    MANAGE_BUDGET = "manage_budget"
    CONNECT_BANK = "connect_bank"
```

Update role permissions:
```python
UserRole.CLIENT: {
    # ... existing permissions
    Permission.VIEW_BUDGET,
    Permission.CONNECT_BANK,
}

UserRole.INVESTOR: {
    # ... existing permissions
    Permission.VIEW_BUDGET,
    Permission.MANAGE_BUDGET,
    Permission.CONNECT_BANK,
}
```

### Phase 3: Frontend Components (4-5 hours)

#### 3.1 Create Budget Dashboard Component
**File: `frontend/components/budget_dashboard.py`**

Components:
- **Cash Flow Summary Card**
  - Total Income
  - Total Expenses
  - Net Cash Flow
  - Month-over-month comparison

- **Budget vs Actual Chart**
  - Horizontal bar chart per category
  - Color-coded (green=under, red=over)
  - Percentage indicators

- **Transaction Timeline**
  - Recent transactions (last 30 days)
  - Filterable by category
  - Searchable

- **Category Breakdown**
  - Pie chart of expenses
  - Top spending categories
  - Trend lines

#### 3.2 Create Plaid Connection Component
**File: `frontend/components/plaid_connector.py`**

Components:
- **Plaid Link Button**
  - Initialize Plaid Link modal
  - Handle success/error callbacks
  - Show connection status

- **Connected Accounts Display**
  - List of linked bank accounts
  - Last sync time
  - Sync now button
  - Disconnect option

#### 3.3 Update Home Page
**File: `streamlit_app.py`**

Add Budget Section:
```python
# After portfolio section, before footer

# Personal Budget Analysis (authenticated users only)
if RBAC_AVAILABLE and RBACManager.is_authenticated():
    user = RBACManager.get_current_user()
    
    if RBACManager.has_permission(Permission.VIEW_BUDGET):
        st.markdown("---")
        st.header("💰 Personal Budget Analysis")
        
        # Check if Plaid is connected
        if user.plaid_connected:
            display_budget_dashboard(user)
        else:
            display_plaid_connection_prompt(user)
```

### Phase 4: Streamlit Integration (2-3 hours)

#### 4.1 Add Budget Page
**File: `pages/03_💰_Personal_Budget.py`**

Full budget management interface:
- Connect/manage bank accounts
- Set budget categories and limits
- View detailed transaction history
- Export transactions (CSV)
- Monthly/yearly summaries
- Custom date range analysis

#### 4.2 Update Sidebar Navigation
Show budget section only for authenticated users:
```python
if RBACManager.is_authenticated() and RBACManager.has_permission(Permission.VIEW_BUDGET):
    st.sidebar.page_link("pages/03_💰_Personal_Budget.py", label="Personal Budget")
```

### Phase 5: Security & Testing (2-3 hours)

#### 5.1 Security Measures
- [ ] Encrypt Plaid tokens in database (AES-256)
- [ ] Implement token refresh mechanism
- [ ] Add rate limiting for API calls
- [ ] Sanitize transaction data
- [ ] Add audit logging for budget access
- [ ] Implement data retention policies

#### 5.2 Testing Checklist
- [ ] Test Plaid Link flow (sandbox)
- [ ] Test transaction fetching
- [ ] Test cash flow calculations
- [ ] Test budget vs actual comparisons
- [ ] Test with multiple users
- [ ] Test error handling (expired tokens, API errors)
- [ ] Test data privacy (user isolation)

---

## 🚀 Quick Start Implementation

### Step 1: Database Setup (10 minutes)
```bash
# Run SQL scripts
mysql -u root -p -h localhost -P 3307 mansa_bot < scripts/setup/budget_schema.sql
```

### Step 2: Install Dependencies (5 minutes)
```bash
pip install plaid-python cryptography
```

Update `requirements.txt`:
```
plaid-python>=14.0.0
cryptography>=41.0.0
```

### Step 3: Configure Plaid (15 minutes)

1. **Get Plaid Credentials:**
   - Sign up at https://dashboard.plaid.com/signup
   - Get Client ID and Sandbox Secret
   - Create Link token for testing

2. **Update `.env`:**
```bash
# Plaid Configuration (Sandbox for testing)
PLAID_CLIENT_ID=your_client_id_here
PLAID_SECRET=your_sandbox_secret_here
PLAID_ENV=sandbox
PLAID_BASE_URL=https://sandbox.plaid.com
```

3. **Test Connection:**
```bash
python -c "from plaid_client import PlaidClient; client = PlaidClient(); print('✅ Plaid connected')"
```

### Step 4: Create Core Components (30 minutes)

Create these minimal files to start:

1. **`frontend/utils/budget_analysis.py`** - Basic cash flow calculator
2. **`frontend/components/budget_dashboard.py`** - Simple metrics display
3. **`pages/03_💰_Personal_Budget.py`** - Basic budget page

### Step 5: Integrate with Home Page (15 minutes)

Add budget section after portfolio analysis in `streamlit_app.py`:
```python
# Personal Budget Section (Authenticated Users Only)
if RBAC_AVAILABLE:
    from frontend.components.budget_dashboard import show_budget_summary
    
    if RBACManager.is_authenticated():
        user = RBACManager.get_current_user()
        if RBACManager.has_permission(Permission.VIEW_BUDGET):
            st.markdown("---")
            show_budget_summary(user.user_id)
```

---

## 📊 Expected User Flow

### For Unauthenticated Users (Guests)
1. Visit home page
2. See portfolio analysis only
3. **Budget section is invisible**
4. Login prompt if they try to access budget

### For Authenticated Users (Clients/Investors)
1. Login to system
2. See portfolio analysis
3. **See "Personal Budget Analysis" section on home page**
4. Options:
   - **If not connected:** "Connect Your Bank" button → Plaid Link modal
   - **If connected:** Mini dashboard with:
     - This month's cash flow
     - Budget status (3 categories max)
     - Link to full budget page

5. Click "View Full Budget" → Navigate to detailed budget page

### On Budget Page (`03_💰_Personal_Budget.py`)
1. **Header:** Account connection status
2. **Tabs:**
   - Overview (cash flow, trends)
   - Transactions (searchable table)
   - Budgets (set limits per category)
   - Reports (monthly/yearly summaries)

---

## 🎨 UI/UX Design Mockup

### Home Page Budget Section (for logged-in users)

```
┌─────────────────────────────────────────────────────────────┐
│ 💰 Personal Budget Analysis                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Income    │  │  Expenses   │  │ Net Flow    │       │
│  │  $8,450     │  │  $6,230     │  │  +$2,220    │       │
│  │  ↑ 5%      │  │  ↓ 3%      │  │  ↑ 12%     │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                              │
│  📊 Top Categories This Month                               │
│  ────────────────────────────────────────────────           │
│  🏠 Housing        $2,100  ████████████░░░░  85%           │
│  🍔 Food & Dining  $890    ██████████░░░░░░  60%           │
│  🚗 Transportation $540    ████████░░░░░░░░  90%           │
│                                                              │
│  [View Full Budget Dashboard →]                             │
│                                                              │
│  Last synced: 2 hours ago | Bank of America ✓              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Home Page   │  │ Budget Page  │  │ RBAC Login   │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                  │                  │             │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼─────────────┐
│         │     Frontend Components Layer       │             │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐    │
│  │   Budget     │  │    Plaid     │  │     RBAC     │    │
│  │  Dashboard   │  │  Connector   │  │   Manager    │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼─────────────┐
│         │      Backend Services Layer         │             │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐    │
│  │   Budget     │  │    Plaid     │  │   Database   │    │
│  │  Analysis    │  │    Client    │  │   Manager    │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────────┐
│                   Data Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  MySQL DB    │  │   Plaid API  │  │  Cache Layer │    │
│  │(Transactions)│  │ (Bank Data)  │  │  (Redis?)    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 File Structure

```
BentleyBudgetBot/
├── streamlit_app.py                    # ← UPDATE: Add budget section
├── pages/
│   ├── 01_📈_Investment_Analysis.py   # Existing
│   ├── 02_🔗_Broker_Connections.py   # Existing (RBAC)
│   └── 03_💰_Personal_Budget.py       # ← NEW: Full budget page
├── frontend/
│   ├── components/                     # ← NEW FOLDER
│   │   ├── __init__.py
│   │   ├── budget_dashboard.py        # Budget metrics & charts
│   │   └── plaid_connector.py         # Plaid Link integration
│   └── utils/
│       ├── rbac.py                     # ← UPDATE: Add budget permissions
│       ├── budget_analysis.py          # ← NEW: Cash flow calculations
│       └── plaid_integration.py        # ← NEW: Plaid API wrapper
├── .vscode/
│   └── plaid_client.py                 # ← UPDATE: Add user_id support
├── scripts/
│   └── setup/
│       └── budget_schema.sql           # ← NEW: Database migrations
└── mysql_setup.sql/
    └── budget_tables.sql               # ← NEW: Budget-specific tables
```

---

## 🔐 Security Considerations

### 1. Token Encryption
```python
from cryptography.fernet import Fernet

# Generate encryption key (store in environment)
ENCRYPTION_KEY = os.getenv('PLAID_ENCRYPTION_KEY')

def encrypt_token(token: str) -> str:
    f = Fernet(ENCRYPTION_KEY)
    return f.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    f = Fernet(ENCRYPTION_KEY)
    return f.decrypt(encrypted_token.encode()).decode()
```

### 2. Data Isolation
- All queries filtered by `user_id`
- Session-based user identification
- No cross-user data leakage

### 3. API Rate Limiting
- Implement request throttling
- Cache transaction data locally
- Batch API calls

---

## 📈 Success Metrics

- [ ] Users can connect bank accounts via Plaid
- [ ] Transactions automatically sync daily
- [ ] Cash flow metrics visible on home page (auth users only)
- [ ] Budget vs Actual comparison accurate
- [ ] Page load time < 2 seconds
- [ ] Zero data leakage between users
- [ ] 99% uptime for transaction sync

---

## 🎯 Next Immediate Actions

1. **Review this plan** - Confirm approach and priorities
2. **Set up Plaid account** - Get sandbox credentials
3. **Run database migrations** - Create budget tables
4. **Create skeleton files** - Start with Phase 2 & 3
5. **Test with demo user** - Verify RBAC integration
6. **Deploy and iterate** - Start with minimal viable product

---

## 🤝 Need Help With?

Please confirm:
1. Should I proceed with creating the database schema files?
2. Do you want me to build the budget dashboard component first?
3. Should we start with sandbox/test mode or go straight to production Plaid?
4. Any specific transaction categories you want pre-configured?
5. Preferred visualization library (Plotly, Altair, or Matplotlib)?

Let me know which phase you'd like to tackle first, and I'll create the implementation files! 🚀
