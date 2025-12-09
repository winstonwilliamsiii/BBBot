# RBAC Page Access Control - December 9, 2025

## 📋 Page Structure

| Page # | Name | Description |
|--------|------|-------------|
| 1 | 🤖 Bentley Dashboard | Home page with portfolio overview and AI assistant |
| 2 | 💰 Personal Budget | Budget tracking and Plaid integration |
| 3 | 📈 Investment Analysis | Portfolio analysis and broker connections |
| 4 | 🔴 Live Crypto Dashboard | Cryptocurrency tracking |
| 5 | 💼 Broker Trading | Multi-broker trading interface |
| 6 | 🤖 Trading Bot | Automated trading strategies |

## 🔐 Access Control Matrix

| Role | Pages | Agreement Required | Description |
|------|-------|-------------------|-------------|
| **Guest** | 1-6 | Dev/Testing | Development and testing access |
| **Client** | 1-4 | Asset Management Agreement | Standard client access |
| **Investor** | 1-5 | Investor Management Agreement OR Private Placement Memorandum (PPM) | Enhanced investor access |
| **Admin** | 1-6 + Admin Panel | Admin | Full read/write access for production patches |

## 👥 User Roles

### Guest (Development/Testing)
- **Access:** All pages (1-6)
- **Credentials:** `guest` / `guest123`
- **Purpose:** Development and testing phase
- **Agreement Type:** `dev_testing`
- **KYC Status:** ✅ Complete (for testing)
- **Features:**
  - Full application testing
  - All features accessible
  - Used during development phase

### Client
- **Access:** Pages 1-4 (Dashboard, Budget, Investment, Crypto)
- **Credentials:** `client` / `client123`
- **Agreement Required:** Asset Management Agreement
- **Agreement Type:** `asset_mgmt`
- **KYC Status:** ✅ Required
- **Features:**
  - Portfolio viewing
  - Budget management (view only)
  - Investment analysis
  - Cryptocurrency tracking
  - Bank account connection (Plaid)

### Investor
- **Access:** Pages 1-5 (Dashboard, Budget, Investment, Crypto, Broker Trading)
- **Credentials:** `investor` / `investor123`
- **Agreement Required:** 
  - Investor Management Agreement, OR
  - Private Placement Memorandum (PPM)
- **Agreement Type:** `investor_mgmt` or `ppm`
- **KYC Status:** ✅ Required
- **Features:**
  - All Client features, plus:
  - Budget management (full RW access)
  - Broker trading interface
  - Trade execution capabilities
  - WeBull, IBKR, Binance, NinjaTrader, Meta5 connections

### Admin
- **Access:** All pages (1-6) + Admin Panel
- **Credentials (Production - GCP):** `admin` / `admin123`
- **Agreement Type:** `admin`
- **KYC Status:** ✅ Complete
- **Purpose:** Production patches and system administration
- **Features:**
  - Full read/write access to all pages
  - Admin panel access
  - All user management functions
  - System configuration
  - Used for GCP deployment patches

## 📊 Permission Breakdown

### Page-Based Permissions

```python
Permission.VIEW_DASHBOARD       # Page 1: Home
Permission.VIEW_BUDGET          # Page 2: Personal Budget
Permission.VIEW_ANALYSIS        # Page 3: Investment Analysis
Permission.VIEW_CRYPTO          # Page 4: Live Crypto Dashboard
Permission.VIEW_BROKER_TRADING  # Page 5: Broker Trading
Permission.VIEW_TRADING_BOT     # Page 6: Trading Bot
```

### Feature-Based Permissions

```python
Permission.MANAGE_BUDGET        # Full budget management
Permission.CONNECT_BANK         # Plaid bank connection
Permission.TRADE_EXECUTION      # Execute trades
Permission.ADMIN_PANEL          # Admin access
```

## 🔑 Credentials Reference

### Development Phase
```
Username: guest
Password: guest123
Access: All pages (1-6)
Purpose: Development and testing
```

### Client Users
```
Username: client
Password: client123
Access: Pages 1-4
Agreement: Asset Management
```

### Investor Users
```
Username: investor
Password: investor123
Access: Pages 1-5
Agreement: Investor Management OR PPM
```

### Production Admin (GCP)
```
Username: admin
Password: admin123
Access: All pages + Admin panel
Purpose: Production patches
```

## 🎯 Compliance Requirements

### KYC (Know Your Customer)
All users (except Guest in dev) must complete KYC verification:
- ✅ **Guest:** Complete (for testing)
- ✅ **Client:** Required
- ✅ **Investor:** Required
- ✅ **Admin:** Complete

### Investment Agreements

#### Client - Asset Management Agreement
- **Document:** Asset Management Agreement
- **Access Granted:** Pages 1-4
- **Features:**
  - Portfolio viewing
  - Budget tracking (view)
  - Investment analysis
  - Crypto dashboard
  - Bank connections

#### Investor - Investor Management OR PPM
- **Document Options:**
  1. Investor Management Agreement
  2. Private Placement Memorandum (PPM)
- **Access Granted:** Pages 1-5
- **Features:**
  - All Client features
  - Budget management (full RW)
  - Broker trading
  - Trade execution

## 🧪 Testing Instructions

### Run Verification Tests
```powershell
# Activate virtual environment
& C:/Users/winst/BentleyBudgetBot/.venv/Scripts/Activate.ps1

# Run page access tests
python test_rbac_page_access.py

# Expected output: 5/5 tests passing
```

### Test in Application
```powershell
# Run Streamlit app
streamlit run streamlit_app.py

# Test each role:
1. Login as: guest/guest123
   - Verify: Access to ALL pages (1-6)
   
2. Login as: client/client123
   - Verify: Access to pages 1-4 only
   - Verify: Page 5, 6 show permission denied
   
3. Login as: investor/investor123
   - Verify: Access to pages 1-5
   - Verify: Page 6 shows permission denied
   
4. Login as: admin/admin123
   - Verify: Access to ALL pages (1-6)
   - Verify: Admin panel accessible
```

## 📝 Implementation Details

### User Model Properties
```python
class User:
    username: str
    role: UserRole
    kyc_completed: bool
    investment_agreement_signed: bool
    kyc_date: Optional[datetime]
    agreement_date: Optional[datetime]
    email: Optional[str]
    user_id: int
    agreement_type: Optional[str]  # NEW
    
    def can_access_page(self, page_number: int) -> bool
```

### Agreement Types
```python
'dev_testing'    # Guest - Development/Testing
'asset_mgmt'     # Client - Asset Management Agreement
'investor_mgmt'  # Investor - Investor Management Agreement
'ppm'            # Investor - Private Placement Memorandum
'admin'          # Admin - Full access
```

## 🚀 Deployment Notes

### Development Phase
- Use `guest/guest123` for all testing
- All pages accessible for development
- Agreement requirements enforced but pre-completed for testing

### Production Phase (GCP)
- Use `admin/admin123` for patches only
- Client/Investor roles for real users
- Agreement documents must be signed before access granted
- KYC must be completed and verified

## 📚 Related Files

- `frontend/utils/rbac.py` - Core RBAC implementation
- `test_rbac_page_access.py` - Comprehensive test suite
- `test_rbac_fix.py` - Original AttributeError fix tests
- `docs/QUICKSTART_INVESTMENT_RBAC.md` - RBAC system documentation
- `docs/PAGE_ORGANIZATION.md` - Page structure reference

## ⚠️ Important Notes

### Production Security
- Change default passwords before production deployment
- Store credentials securely (environment variables, secrets manager)
- Implement proper session management
- Enable HTTPS for all connections
- Add rate limiting for login attempts
- Log all access attempts

### Agreement Management
- Client agreements stored securely
- Investor agreements verified before page 5 access
- PPM documents require legal review
- Agreement dates tracked for compliance
- Renewal tracking for expired agreements

### Compliance Tracking
- KYC completion dates recorded
- Agreement signature dates recorded
- Audit trail for all permission changes
- Regular compliance reviews required
- Document retention policies enforced

---

**Last Updated:** December 9, 2025
**Version:** 2.0 (Page-based access control)
**Status:** ✅ Tested and verified
