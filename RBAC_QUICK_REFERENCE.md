# RBAC Quick Reference Card

## Login Credentials (Testing)

```
CLIENT        | client/client123      | mydb (budgets, transactions)
INVESTOR      | investor/investor123  | bbbot1 (market data - read only)
ANALYST       | analyst/analyst123    | mansa_quant + mlflow_db (trading + ML)
ADMIN         | admin/admin123        | All databases (full access)
PARTNER       | partner/partner123    | External services (Stripe/KYC/Lovable)
```

## Role → Database Access

```python
# Check if user can access a database
from frontend.utils.rbac import RBACManager

user = RBACManager.get_current_user()

# Read from database
if RBACManager.check_db_access(user, 'mydb', 'read'):
    # User can read mydb
    
# Write to database  
if RBACManager.check_db_access(user, 'mansa_quant', 'write'):
    # User can write to mansa_quant

# Get all accessible databases
databases = RBACManager.get_user_databases(user)
print(databases)  # ['mydb'] for CLIENT, ['bbbot1'] for INVESTOR, etc.
```

## Check Specific Permissions

```python
from frontend.utils.rbac import RBACManager, Permission

# Direct permission check
if user.has_permission(Permission.CLIENT_WRITE_BUDGETS):
    # User can modify budgets
    
# Using manager
if RBACManager.has_permission(Permission.ANALYST_WRITE_MANSA_QUANT):
    # Current user can write trading signals
    
# Check page access
if user.can_access_page(1):  # Page 1 = Dashboard
    # User has access
```

## Protection Decorator

```python
@require_permission_decorator(Permission.INVESTOR_READ_PRICES)
def show_stock_prices():
    # Only users with this permission can execute
    st.dataframe(prices_df)

@require_authentication
def protected_feature():
    # Must be logged in
    st.write("You are authenticated")
```

## Database-Level Permissions Map

| Permission | Role | Database | Operation |
|-----------|------|----------|-----------|
| CLIENT_READ_BUDGETS | CLIENT | mydb | SELECT |
| CLIENT_WRITE_BUDGETS | CLIENT | mydb | INSERT/UPDATE |
| INVESTOR_READ_PRICES | INVESTOR | bbbot1 | SELECT prices |
| ANALYST_WRITE_MANSA_QUANT | ANALYST | mansa_quant | INSERT/UPDATE |
| ADMIN_WRITE_MYDB | ADMIN | mydb | Full access |

## Common Operations

### Authentication
```python
from frontend.utils.rbac import RBACManager

# Check if logged in
if RBACManager.is_authenticated():
    user = RBACManager.get_current_user()
    print(f"Logged in as: {user.username} ({user.role.value})")

# Protect a page
if not RBACManager.is_authenticated():
    st.warning("Please login first")
    show_login_form()
```

### Role-Based Display
```python
from frontend.utils.rbac import UserRole

user = RBACManager.get_current_user()

if user.role == UserRole.ADMIN:
    st.write("Admin panel available")
elif user.role == UserRole.ANALYST:
    st.write("ML Experiments panel")
elif user.role == UserRole.INVESTOR:
    st.write("Investment analysis")
elif user.role == UserRole.CLIENT:
    st.write("Budget management")
elif user.role == UserRole.PARTNER:
    st.write("Integration settings")
```

### Database Selection
```python
from frontend.utils.rbac import RBACManager

# Get accessible databases for user
databases = RBACManager.get_user_databases(user)

if 'mydb' in databases:
    # Connect to mydb (CLIENT data)
    
if 'mansa_quant' in databases:
    # Connect to mansa_quant (ANALYST data)
    
if 'bbbot1' in databases:
    # Connect to bbbot1 (INVESTOR data)
```

## Migration Checklist

- [ ] Update existing UserRole references (remove GUEST)
- [ ] Update permission checks to use database-level permissions
- [ ] Test each role through complete user flow
- [ ] Verify database connections for each role
- [ ] Update page guards with new permission checks
- [ ] Test Streamlit app deployment
- [ ] Verify Plaid integration works for CLIENT role
- [ ] Test trading signals access for ANALYST role
- [ ] Verify market data access for INVESTOR role
- [ ] Confirm ADMIN can access all databases
- [ ] Document any custom permission requirements

## Role Summary

### CLIENT 🏠
- **Use**: Personal budget management
- **DB**: mydb (budgets, transactions via Plaid)
- **Access**: Dashboard, Budget pages
- **Operations**: Read/Write personal financial data

### INVESTOR 📈
- **Use**: Investment monitoring (read-only)
- **DB**: bbbot1 (market data)
- **Access**: Dashboard, Analysis, Broker pages
- **Operations**: Read stock prices, fundamentals, technicals
- **Requirement**: KYC + Agreement

### ANALYST 🤖
- **Use**: Trading signals & ML experiments
- **DB**: mansa_quant + mlflow_db
- **Access**: Dashboard, Analysis pages
- **Operations**: Read/Write trading signals, ML experiments
- **Requirement**: KYC + Agreement

### ADMIN 🔧
- **Use**: System administration
- **DB**: All (mansa_bot, bbbot1, mlflow_db, mansa_quant, mydb)
- **Access**: All pages
- **Operations**: Full CRUD across all databases

### PARTNER 🤝
- **Use**: External integrations
- **Services**: Stripe, KYC, Lovable
- **Access**: API access (not pages)
- **Operations**: Third-party service integration

## Database Locations

| Database | Port | Purpose |
|----------|------|---------|
| mydb | 3306 | Budgets, transactions (CLIENT) |
| bbbot1 | 3307 | Market data (INVESTOR) |
| mansa_quant | 3307 | Trading signals (ANALYST) |
| mlflow_db | 3307 | ML experiments (ANALYST) |
| mansa_bot | 3306 | Airflow metadata (ADMIN) |

## Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Permission Denied" | User lacks required permission | Verify user role and database access |
| "Database Not Found" | Role cannot access database | Check RBACManager.get_user_databases() |
| "Authentication Required" | User not logged in | Call show_login_form() |
| "Invalid Credentials" | Wrong username/password | Check DEMO_USERS credentials |

## Testing Commands

```bash
# Test RBAC in Python
python -c "
from frontend.utils.rbac import RBACManager, UserRole
user = RBACManager.authenticate('admin', 'admin123')
print(f'Role: {user.role.value}')
print(f'Databases: {RBACManager.get_user_databases(user)}')
"

# Run Streamlit with debugging
streamlit run streamlit_app.py --logger.level=debug
```

## File Locations

| File | Purpose |
|------|---------|
| `frontend/utils/rbac.py` | Main RBAC implementation |
| `frontend/components/rbac.py` | Secondary RBAC (UI components) |
| `sites/Mansa_Bentley_Platform/frontend/utils/rbac.py` | Alternative implementation |
| `RBAC_RESTRUCTURING_GUIDE.md` | Detailed documentation |
| `streamlit_app.py` | Main app using RBAC |

## Key Changes from Previous System

✅ **New**: Database-level permissions (ADMIN_READ_*, ANALYST_WRITE_*, etc.)  
✅ **New**: ANALYST role for data scientists  
✅ **New**: PARTNER role for integrations  
✅ **Removed**: GUEST role  
✅ **Improved**: Fine-grained access control  
✅ **Added**: Helper methods for database access checking  

## Common Issues & Solutions

**Issue**: User can't access budget page
```python
# Solution: Check CLIENT_READ_BUDGETS permission
if not user.has_permission(Permission.CLIENT_READ_BUDGETS):
    # Grant permission or switch to CLIENT role
```

**Issue**: Analyst can't write to mansa_quant
```python
# Solution: Verify ANALYST_WRITE_MANSA_QUANT permission
if not RBACManager.check_db_access(user, 'mansa_quant', 'write'):
    # User needs ANALYST role
```

**Issue**: Admin doesn't see all databases
```python
# Solution: Verify ADMIN role and all ADMIN_* permissions
dbs = RBACManager.get_user_databases(admin_user)
print(dbs)  # Should show: ['mansa_bot', 'bbbot1', 'mlflow_db', 'mansa_quant', 'mydb']
```### GUEST
- **Pages:** 1-2
- **Login:** Not required (public access)
- **Link:** Mansacap.com
- **Use Case:** Public browsing, product exploration
- **Bot Info:** View performance links on Page 1 only

### CLIENT
- **Pages:** 1-4
- **Login:** Required (Mansacap.com)
- **KYC:** Optional (Mansacap handles)
- **Agreement:** Asset Management Agreement
- **Services:** Trading bot SDK purchase (one-time or subscription)
- **Use Case:** Tech-savvy traders, SDK users
- **Bot Access:** View summaries on Page 1, purchase SDKs

### INVESTOR
- **Pages:** 1-5
- **Login:** Required (Bentley platform)
- **KYC:** ✅ REQUIRED
- **Agreement:** ✅ REQUIRED (Investor Mgmt or PPM)
- **Services:** Full asset management
- **Use Case:** Passive investors seeking professional management
- **Bot Access:** View summaries on Page 1, full management disabled

### ADMIN (You)
- **Pages:** 1-8 (ALL)
- **Login:** admin / admin123
- **Access:** Complete system control
- **Dev Tools:** Pages 6, 7, 8 (Bot, Plaid, Multi-Broker)
- **Features:** Admin panel, system configuration

---

## 🔑 Demo Credentials

| Role | Username | Password | Pages | Login |
|------|----------|----------|-------|-------|
| GUEST | guest | guest123 | 1-2 | None |
| CLIENT | client | client123 | 1-4 | Mansacap |
| INVESTOR | investor | investor123 | 1-5 | Bentley |
| ADMIN | admin | admin123 | 1-8 | Bentley |

---

## ⚙️ Quick Implementation Checklist

- [x] RBAC permissions updated
- [x] Demo credentials configured
- [x] Page access matrix defined (1-8)
- [x] GUEST limited to Pages 1-2
- [x] CLIENT limited to Pages 1-4
- [x] INVESTOR limited to Pages 1-5
- [ ] Add page access guards to page files
- [ ] Hide Pages 6-8 from sidebar for non-ADMIN
- [ ] Add bot info display to Page 1
- [ ] Test each role's page access

---

## 🚀 Bot Information Display Strategy

**Location:** Page 1 (Dashboard) - accessible to all roles

**Display Components:**
1. **Featured Bot Cards** (same for all roles)
   - Bot name
   - Performance (YTD %)
   - Backtest win rate
   - Last updated date

2. **Role-Specific Actions:**
   - **GUEST/CLIENT:** "Purchase SDK" button
   - **INVESTOR:** "View Details" (read-only)
   - **ADMIN:** "Full Details" + "Edit Bot" links

3. **Links:**
   - ADMIN: Direct link to Page 6 (Trading Bot Manager)
   - Others: SDK purchase or more info pages

---

## 📋 Compliance Requirements by Role

| Requirement | GUEST | CLIENT | INVESTOR | ADMIN |
|------------|-------|--------|----------|-------|
| Login | ❌ | ✅ | ✅ | ✅ |
| KYC | ❌ | ⚠️ Mansacap | ✅ | ✅ |
| Legal Agreement | ❌ | ✅ Asset Mgmt | ✅ PPM/Inv Mgmt | ✅ |
| Bank Connect | ❌ | ✅ | ✅ | ✅ |
| Trade Execute | ❌ | ❌ | ✅ | ✅ |

---

## 🔒 Authorization Rules

```python
# GUEST: Pages 1-2 (no login required)
if page_num in [1, 2]:
    allow_access = True

# CLIENT: Pages 1-4 (login required)
if page_num in [1, 2, 3, 4]:
    allow_access = authenticated and role == CLIENT

# INVESTOR: Pages 1-5 (login + KYC + legal)
if page_num in [1, 2, 3, 4, 5]:
    allow_access = (authenticated and role == INVESTOR 
                   and kyc_completed and agreement_signed)

# ADMIN: Pages 1-8 (all)
if page_num in [1, 2, 3, 4, 5, 6, 7, 8]:
    allow_access = authenticated and role == ADMIN
```

---

## 🌐 Mansacap.com Integration Points

1. **GUEST Users:** Landing page link to public pages
2. **CLIENT Users:** SSO login redirects to Pages 1-4
3. **Shared Data:** Optional portfolio sync between platforms
4. **KYC:** Mansacap handles CLIENT KYC (optional for SDK users)

---

## ❓ FAQ

**Q: Can GUEST access without logging in?**
A: Yes! Pages 1-2 are public. Mansacap.com links directly to these pages.

**Q: Can CLIENT see Broker Trading (Page 5)?**
A: No. Only INVESTOR+ have access to Page 5.

**Q: Do INVESTOR users need Mansacap login?**
A: No. They have separate Bentley platform accounts with full compliance tracking.

**Q: Where are trading bot details?**
A: Page 6 (ADMIN only). Page 1 shows summary & performance for all users.

**Q: Can INVESTOR see trading bot management?**
A: No. Pages 6-8 are ADMIN-only for development/testing.

---

## 🔗 File References

- **RBAC Core:** `/frontend/utils/rbac.py`
- **Pages:** `/pages/01_*.py` through `/pages/07_*.py`
- **Main App:** `/streamlit_app.py`
- **Documentation:** This file + `RBAC_IMPLEMENTATION.md`

---

*Quick Reference v1.0 - Last Updated: January 16, 2026*
