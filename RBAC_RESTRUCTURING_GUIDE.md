# RBAC System Restructuring Guide

## Overview

The Bentley Budget Bot RBAC system has been completely restructured to support database-level access control with 5 distinct roles replacing the old 4-role model (GUEST, CLIENT, INVESTOR, ADMIN).

## New Role Structure

### 1. CLIENT
**Purpose:** Personal budget and financial transaction management  
**Database Access:** `mydb` (read + write)  
**Tables:** budgets, transactions  
**Permissions:**
- `CLIENT_READ_BUDGETS` - Read personal budget data
- `CLIENT_WRITE_BUDGETS` - Update budget allocations  
- `CLIENT_READ_TRANSACTIONS` - View transaction history (via Plaid)
- `CLIENT_WRITE_TRANSACTIONS` - Record manual transactions
- `VIEW_DASHBOARD` - Access home dashboard
- `VIEW_BUDGET` - Access budget page

**Use Case:** Individual users managing personal finances through Plaid bank connections

**Demo Credentials:**
```
Username: client
Password: client123
```

---

### 2. INVESTOR
**Purpose:** Read-only access to investment market data and performance metrics  
**Database Access:** `bbbot1` (read-only)  
**Tables:** prices_daily, fundamentals_raw, technicals_raw  
**Permissions:**
- `INVESTOR_READ_PRICES` - Historical stock prices
- `INVESTOR_READ_FUNDAMENTALS` - Company fundamentals (earnings, ratios, etc.)
- `INVESTOR_READ_TECHNICALS` - Technical indicators (RSI, MACD, Bollinger Bands, etc.)
- `INVESTOR_READ_PERFORMANCE` - Bot performance metrics
- `VIEW_DASHBOARD` - Access home dashboard
- `VIEW_ANALYSIS` - Access investment analysis page
- `VIEW_BROKER_TRADING` - View broker connections (read-only)

**Requirements:** KYC (Know Your Customer) + Legal agreement (Investor Management Agreement or Private Placement Memorandum)

**Use Case:** Accredited investors monitoring investment portfolio data without trading capabilities

**Demo Credentials:**
```
Username: investor
Password: investor123
KYC Completed: Yes
Agreement Signed: Yes
```

---

### 3. ANALYST
**Purpose:** Access trading signals and machine learning experiment data  
**Database Access:** `mansa_quant`, `mlflow_db` (read + write)  
**Tables:** 
- mansa_quant: trading_signals, portfolio_positions, trade_history, ml_predictions
- mlflow_db: ml_models, experiments, metrics, sentiment_analysis

**Permissions:**
- `ANALYST_READ_MANSA_QUANT` - Read trading signals
- `ANALYST_WRITE_MANSA_QUANT` - Update trading signal predictions
- `ANALYST_READ_MLFLOW` - View ML experiments and metrics
- `ANALYST_WRITE_MLFLOW` - Log new ML experiments
- `ANALYST_READ_SENTIMENT` - Access sentiment analysis data
- `ANALYST_WRITE_SENTIMENT` - Update sentiment scores
- `VIEW_DASHBOARD` - Access home dashboard
- `VIEW_ANALYSIS` - Access investment analysis page

**Use Case:** Data scientists and quantitative analysts developing and testing trading strategies

**Demo Credentials:**
```
Username: analyst
Password: analyst123
KYC Completed: Yes
Agreement Signed: Yes
```

---

### 4. ADMIN
**Purpose:** Full administrative access to all databases and operations  
**Database Access:** ALL (mansa_bot, bbbot1, mlflow_db, mansa_quant, mydb)  
**Permissions:** All read/write permissions across all databases

**Capabilities:**
- `ADMIN_READ_MANSA_BOT` / `ADMIN_WRITE_MANSA_BOT` - Airflow orchestration metadata
- `ADMIN_READ_BBBOT1` / `ADMIN_WRITE_BBBOT1` - Stock data, fundamentals
- `ADMIN_READ_MLFLOW` / `ADMIN_WRITE_MLFLOW` - ML experiments
- `ADMIN_READ_MANSA_QUANT` / `ADMIN_WRITE_MANSA_QUANT` - Trading signals
- `ADMIN_READ_MYDB` / `ADMIN_WRITE_MYDB` - Budget and transaction data
- All page access (dashboard, budget, analysis, crypto, broker, trading bot)

**Use Case:** Platform administrators and system maintainers managing all aspects of the application

**Demo Credentials:**
```
Username: admin
Password: admin123
KYC Completed: Yes
Agreement Signed: Yes
Email: winston@bentleybot.com
```

---

### 5. PARTNER
**Purpose:** External integrations and third-party service access  
**Services:** Stripe payments, KYC verification, Lovable Cloud functions  
**Permissions:**
- `PARTNER_STRIPE` - Payment processing integration
- `PARTNER_KYC` - KYC verification services
- `PARTNER_LOVABLE` - Lovable Cloud function access

**Use Case:** Third-party service providers integrating with Bentley Bot ecosystem

**Demo Credentials:**
```
Username: partner
Password: partner123
KYC Completed: Yes
Agreement Signed: Yes
```

---

## Database Access Matrix

| Database | CLIENT | INVESTOR | ANALYST | ADMIN | PARTNER |
|----------|--------|----------|---------|-------|---------|
| **mydb** | RW | - | - | RW | - |
| **bbbot1** | - | R | - | RW | - |
| **mansa_quant** | - | - | RW | RW | - |
| **mlflow_db** | - | - | RW | RW | - |
| **mansa_bot** | - | - | - | RW | - |

Legend: R = Read, W = Write, RW = Read+Write, - = No Access

---

## Database-Level Permissions

### Client Permissions (mydb)
```python
Permission.CLIENT_READ_BUDGETS
Permission.CLIENT_WRITE_BUDGETS
Permission.CLIENT_READ_TRANSACTIONS
Permission.CLIENT_WRITE_TRANSACTIONS
```

### Investor Permissions (bbbot1)
```python
Permission.INVESTOR_READ_PRICES          # bbbot1.prices_daily
Permission.INVESTOR_READ_FUNDAMENTALS    # bbbot1.fundamentals_raw
Permission.INVESTOR_READ_TECHNICALS      # bbbot1.technicals_raw
Permission.INVESTOR_READ_PERFORMANCE     # Bot metrics
```

### Analyst Permissions (mansa_quant + mlflow_db)
```python
Permission.ANALYST_READ_MANSA_QUANT
Permission.ANALYST_WRITE_MANSA_QUANT
Permission.ANALYST_READ_MLFLOW
Permission.ANALYST_WRITE_MLFLOW
Permission.ANALYST_READ_SENTIMENT
Permission.ANALYST_WRITE_SENTIMENT
```

### Admin Permissions (ALL databases)
```python
Permission.ADMIN_READ_MANSA_BOT
Permission.ADMIN_WRITE_MANSA_BOT
Permission.ADMIN_READ_BBBOT1
Permission.ADMIN_WRITE_BBBOT1
Permission.ADMIN_READ_MLFLOW
Permission.ADMIN_WRITE_MLFLOW
Permission.ADMIN_READ_MANSA_QUANT
Permission.ADMIN_WRITE_MANSA_QUANT
Permission.ADMIN_READ_MYDB
Permission.ADMIN_WRITE_MYDB
```

### Partner Permissions (External Services)
```python
Permission.PARTNER_STRIPE
Permission.PARTNER_KYC
Permission.PARTNER_LOVABLE
```

---

## Implementation Details

### Files Updated

1. **`frontend/utils/rbac.py`** (Primary RBAC Implementation)
   - UserRole enum (removed GUEST, added PARTNER)
   - Permission enum (database-level permissions)
   - ROLE_PERMISSIONS mapping
   - Database helper methods:
     - `check_db_access(user, database, operation)`
     - `get_user_databases(user)`
     - `get_role_databases(role)`
   - Demo users updated with new roles

2. **`frontend/components/rbac.py`** (Secondary RBAC)
   - UserRole enum updated
   - Permission enum updated
   - ROLE_PERMISSIONS mapping updated
   - Maintains backward compatibility with page-based permissions

3. **`sites/Mansa_Bentley_Platform/frontend/utils/rbac.py`** (Alternative Implementation)
   - Same updates as secondary RBAC
   - Ensures consistency across multiple implementations

### New Helper Methods in RBACManager

```python
@staticmethod
def check_db_access(user: Optional[User], database: str, operation: str = 'read') -> bool:
    """Check if user has access to a database for specific operation"""
    
@staticmethod
def get_user_databases(user: Optional[User]) -> List[str]:
    """Get list of databases user can access"""
    
@staticmethod
def get_role_databases(role: UserRole) -> Dict[str, List[str]]:
    """Get databases accessible by a role with their operations"""
```

---

## Migration Guide

### For Existing Users

Old Role → New Role Mapping:
- `GUEST` (removed) → Based on use case:
  - Public read-only users → Require login as CLIENT or INVESTOR
  - Dev/Testing users → Use CLIENT or ANALYST role
- `CLIENT` → `CLIENT` (budgets, transactions)
- `INVESTOR` → `INVESTOR` (market data read-only)
- `ADMIN` → `ADMIN` (all databases)

### Creating Migration Script

```python
# Recommended migration approach:
# 1. Backup existing user data
# 2. Map old roles to new roles based on database access patterns
# 3. Update user records with new role
# 4. Test each role through UI to verify database access

migration_map = {
    UserRole.GUEST: UserRole.CLIENT,  # Default to CLIENT
    UserRole.CLIENT: UserRole.CLIENT,
    UserRole.INVESTOR: UserRole.INVESTOR,
    UserRole.ADMIN: UserRole.ADMIN,
}
```

---

## Page Access Control Updates

### Dashboard (Page 1)
- **CLIENT**: Full access
- **INVESTOR**: Full access  
- **ANALYST**: Full access
- **ADMIN**: Full access
- **PARTNER**: No direct page access

### Budget Management (Page 2)
- **CLIENT**: Full access (via CLIENT_READ/WRITE_BUDGETS, CLIENT_READ/WRITE_TRANSACTIONS)
- **INVESTOR**: Read-only (view budget summary)
- **ANALYST**: No access
- **ADMIN**: Full access (via ADMIN_READ/WRITE_MYDB)
- **PARTNER**: No access

### Investment Analysis (Page 3)
- **CLIENT**: No direct access (depends on permissions)
- **INVESTOR**: Full access (via INVESTOR_READ_PRICES/FUNDAMENTALS/TECHNICALS)
- **ANALYST**: Full access (via ANALYST_READ_MANSA_QUANT/MLFLOW)
- **ADMIN**: Full access
- **PARTNER**: No access

### Live Crypto Dashboard (Page 4)
- **CLIENT**: Limited access
- **INVESTOR**: Limited access
- **ANALYST**: No access
- **ADMIN**: Full access
- **PARTNER**: No access

### Broker Trading (Page 5)
- **CLIENT**: View only
- **INVESTOR**: Full access (via INVESTOR_READ_PERFORMANCE)
- **ANALYST**: No access (trading not allowed)
- **ADMIN**: Full access
- **PARTNER**: No access

### Trading Bot (Page 6)
- **CLIENT**: No access
- **INVESTOR**: Monitor only
- **ANALYST**: Full access (via ANALYST_READ/WRITE_MANSA_QUANT)
- **ADMIN**: Full access
- **PARTNER**: No access

---

## Database Configuration

### Environment Variables (.env)

```
# Client Database (Budget & Transactions)
CLIENT_MYSQL_HOST=localhost
CLIENT_MYSQL_PORT=3306
CLIENT_MYSQL_USER=bentley_user
CLIENT_MYSQL_PASSWORD=***
CLIENT_MYSQL_DATABASE=mydb

# Investor Database (Market Data)
INVESTOR_MYSQL_HOST=localhost
INVESTOR_MYSQL_PORT=3307
INVESTOR_MYSQL_USER=bentley_user
INVESTOR_MYSQL_PASSWORD=***
INVESTOR_MYSQL_DATABASE=bbbot1

# Analyst Databases (Trading & ML)
ANALYST_MYSQL_HOST=localhost
ANALYST_MYSQL_PORT=3307
ANALYST_MYSQL_USER=bentley_user
ANALYST_MYSQL_PASSWORD=***
ANALYST_MYSQL_DATABASE_QUANT=mansa_quant
ANALYST_MYSQL_DATABASE_ML=mlflow_db

# Admin Databases (All access)
ADMIN_MYSQL_HOST=localhost
ADMIN_MYSQL_PORT=3306
ADMIN_MYSQL_USER=admin_user
ADMIN_MYSQL_PASSWORD=***
```

---

## Testing the RBAC System

### Test Cases by Role

**CLIENT Test:**
1. Login as client/client123
2. Verify access to Dashboard (Page 1) ✓
3. Verify access to Budget (Page 2) ✓
4. Attempt access to Investment Analysis (Page 3) - Should redirect
5. Verify can read/write budgets and transactions from mydb

**INVESTOR Test:**
1. Login as investor/investor123
2. Verify KYC and agreement status shows as completed ✓
3. Verify access to Dashboard, Analysis, Broker Trading
4. Verify read-only access to bbbot1 (prices, fundamentals, technicals)
5. Attempt write operation - Should be rejected

**ANALYST Test:**
1. Login as analyst/analyst123
2. Verify access to Dashboard and Analysis pages
3. Verify read/write access to mansa_quant tables
4. Verify read/write access to mlflow_db tables
5. Verify can log ML experiments and view sentiment data

**ADMIN Test:**
1. Login as admin/admin123
2. Verify access to ALL pages (1-6)
3. Verify read/write access to all 5 databases
4. Test creating/updating records in each database
5. Verify can switch database contexts

---

## Changes from Previous System

### Removed
- `UserRole.GUEST` - No more public/anonymous access without role
- `Permission.MANAGE_BUDGET` - Replaced with CLIENT_WRITE_BUDGETS
- `Permission.CONNECT_BANK` - Now implicit with CLIENT role
- `Permission.TRADE_EXECUTION` - Replaced with ANALYST role permissions
- `Permission.ADMIN_PANEL` - Removed (ADMIN has all permissions)

### Added
- `UserRole.ANALYST` - New role for data scientists
- `UserRole.PARTNER` - New role for external integrations
- Database-level permissions (ADMIN_READ_*, ANALYST_READ/WRITE_*, etc.)
- Helper methods for database access checking
- Sentiment analysis permissions

### Improved
- Fine-grained database-level access control instead of page-based
- Clearer role boundaries with explicit database access
- Support for multi-database architectures
- Better separation of concerns (budgets, market data, trading, ML)

---

## Compliance & Legal

### KYC Requirements
- **CLIENT**: Optional (basic financial data)
- **INVESTOR**: Required (accredited investor verification)
- **ANALYST**: Required (data scientist background check)
- **ADMIN**: Required (system administrator verification)
- **PARTNER**: Required (third-party integration verification)

### Legal Agreements
- **CLIENT**: Asset Management Agreement (implicit via Plaid)
- **INVESTOR**: Investor Management Agreement or PPM (Private Placement Memorandum)
- **ANALYST**: Data Science Agreement
- **ADMIN**: Admin Services Agreement
- **PARTNER**: Partner Integration Agreement

---

## Future Enhancements

1. **Role-Based Row-Level Security**: Further restrict access at table row level
2. **Temporary Role Elevation**: Allow temporary admin access with approval workflow
3. **Audit Logging**: Log all database access attempts and modifications by role
4. **Dynamic Role Assignment**: Programmatically assign roles based on compliance status
5. **Federated Authentication**: Integrate with OAuth providers (Google, Microsoft)
6. **Service Accounts**: System accounts for automated tasks with limited permissions

---

## Support & Troubleshooting

### Common Issues

**Q: User cannot access their database after login**
- Check `RBACManager.check_db_access(user, database, 'read')`
- Verify user role has correct permissions in ROLE_PERMISSIONS
- Check .env database credentials are correct

**Q: Admin cannot access PARTNER services**
- PARTNER permissions are separate service integrations
- ADMIN role designed for database access, not external services
- Create separate PARTNER account for external integrations

**Q: How do I upgrade a user's role?**
```python
from frontend.utils.rbac import RBACManager, UserRole
# Update user role in database/session state
user.role = UserRole.INVESTOR  # or ANALYST, ADMIN, etc.
```

---

## References

- Main RBAC Implementation: [frontend/utils/rbac.py](frontend/utils/rbac.py)
- Secondary RBAC: [frontend/components/rbac.py](frontend/components/rbac.py)
- Database Specifications: [DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md)
- Deployment Guide: [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md)
