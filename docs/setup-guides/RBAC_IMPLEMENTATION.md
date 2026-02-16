# Role-Based Access Control (RBAC) Implementation
## Bentley Budget Bot - Mansacap.com Integration

**Last Updated:** January 16, 2026

---

## 🎯 Overview

This document describes the complete role-based access control system for the Bentley Budget Bot platform integrated with Mansacap.com. The system provides granular page access control based on user roles and compliance status.

---

## 📋 User Roles & Access Model

### 1. **GUEST** (Public Access - No Login Required)
- **Landing Pages:** Pages 1-2 only
  - Page 1: 💰 Dashboard (Portfolio Overview)
  - Page 2: 📈 Budget Management
- **Login Requirement:** None (public access via Mansacap.com homepage)
- **Compliance:** No KYC, no legal agreement required
- **Description:** General public visitors exploring the platform
- **Use Case:** Window shopping, exploring available services

#### Page Access Matrix:
```
Page 1 (Dashboard) ✅
Page 2 (Budget)    ✅
Page 3 (Analysis)  ❌
Page 4 (Crypto)    ❌
Page 5 (Broker)    ❌
Page 6 (Bot)       ❌
Page 7 (Plaid)     ❌
Page 8 (MultiBroker) ❌
```

---

### 2. **CLIENT** (Technology-Savvy Traders)
- **Landing Pages:** Pages 1-4
  - Page 1: 💰 Dashboard
  - Page 2: 📈 Personal Budget
  - Page 3: 📊 Investment Analysis
  - Page 4: 🔴 Live Crypto Dashboard
- **Login Requirement:** Must login via Mansacap.com
- **Compliance:** Asset Management Agreement (implied via Mansacap.com signup)
- **SDKs & Bots:** Purchase trading bots and SDKs
  - **Pricing Models:**
    - One-time fee for static bot strategies
    - Subscription-based for regular code updates
- **Bank Connection:** Can connect Plaid for budget analysis
- **Description:** Technology-savvy users who purchase and backtest trading strategies using the SDK
- **KYC:** Optional (handled via Mansacap.com)

#### Page Access Matrix:
```
Page 1 (Dashboard) ✅
Page 2 (Budget)    ✅
Page 3 (Analysis)  ✅
Page 4 (Crypto)    ✅
Page 5 (Broker)    ❌
Page 6 (Bot)       ❌
Page 7 (Plaid)     ❌
Page 8 (MultiBroker) ❌
```

---

### 3. **INVESTOR** (Asset Management Clients)
- **Landing Pages:** Pages 1-5
  - Page 1: 💰 Dashboard
  - Page 2: 📈 Personal Budget
  - Page 3: 📊 Investment Analysis
  - Page 4: 🔴 Live Crypto Dashboard
  - Page 5: 💼 Broker Trading
- **Login Requirement:** Yes (separate platform login, NOT via Mansacap.com)
- **Compliance Requirements:**
  - ✅ **KYC (Know Your Customer) Verification** - REQUIRED
  - ✅ **Legal Documents** - REQUIRED
    - Investor Management Agreement OR
    - Private Placement Memorandum (PPM)
- **Services:** Full asset management services
  - Professional portfolio management
  - Broker connections (Plaid integration)
  - Trade execution capabilities
- **Bank Connection:** Can connect multiple brokers for comprehensive tracking
- **Description:** Less tech-savvy investors seeking professional asset management services
- **Access Control:** Full compliance gates in place; cannot access trading bots or development tools

#### Page Access Matrix:
```
Page 1 (Dashboard) ✅
Page 2 (Budget)    ✅
Page 3 (Analysis)  ✅
Page 4 (Crypto)    ✅
Page 5 (Broker)    ✅
Page 6 (Bot)       ❌
Page 7 (Plaid)     ❌
Page 8 (MultiBroker) ❌
```

---

### 4. **ADMIN** (Winston - Full System Access)
- **Landing Pages:** ALL pages (1-8)
  - Page 1: 💰 Dashboard
  - Page 2: 📈 Personal Budget
  - Page 3: 📊 Investment Analysis
  - Page 4: 🔴 Live Crypto Dashboard
  - Page 5: 💼 Broker Trading
  - Page 6: 🤖 Trading Bot Manager
  - Page 7: 🏦 Plaid Test Interface
  - Page 8: 🌐 Multi-Broker Trading
- **Login Requirement:** Yes (admin credentials)
- **Compliance:** All compliance checks bypassed
- **Permissions:** Complete read/write access to all systems
- **Development Tools:**
  - Trading Bot management (Page 6)
  - Plaid integration testing (Page 7)
  - Multi-broker strategy development (Page 8)
- **Admin Panel:** Full system configuration access
- **Description:** System administrator (You)

#### Page Access Matrix:
```
Page 1 (Dashboard) ✅
Page 2 (Budget)    ✅
Page 3 (Analysis)  ✅
Page 4 (Crypto)    ✅
Page 5 (Broker)    ✅
Page 6 (Bot)       ✅
Page 7 (Plaid)     ✅
Page 8 (MultiBroker) ✅
```

---

## 🔐 Authentication & Authorization

### Login Flow

#### GUEST Users
```
GUEST ACCESS
├─ No login required
├─ Public URL access to Pages 1-2
├─ Via Mansacap.com homepage
└─ Limited to Portfolio Overview + Budget tools
```

#### CLIENT Users
```
CLIENT LOGIN FLOW
├─ Login to Mansacap.com
├─ Redirect to Bentley Budget Bot
├─ Session maintained via SSO
├─ Access Pages 1-4
└─ Purchase SDKs + Bot Strategies
```

#### INVESTOR Users
```
INVESTOR LOGIN FLOW
├─ Login to Bentley Platform (separate from Mansacap)
├─ KYC Verification Required ✅
├─ Legal Document Sign-off Required ✅
├─ Access Pages 1-5
└─ Asset Management Services
```

#### ADMIN Users
```
ADMIN LOGIN FLOW
├─ Username: admin
├─ Password: [secure password]
├─ Access: All Pages 1-8
├─ Development Tools Enabled
└─ Full System Configuration
```

---

## 🏠 Home Page (Page 1) - Bot Information Display

The Dashboard (Page 1) will feature:

### Public Bot Performance Links
- **Available to:** GUEST, CLIENT, INVESTOR, ADMIN
- **Display Elements:**
  - Bot name
  - Historical performance metrics
  - Backtest results summary
  - Link to full bot details (page 6 for ADMIN only)

### Sample Card Layout
```
┌─────────────────────────────────────┐
│ Featured Trading Bot                │
├─────────────────────────────────────┤
│ Bot Name: "RSI-MACD Strategy"       │
│ Performance: +24.3% YTD              │
│ Backtest Win Rate: 68%               │
│ Last Updated: Jan 15, 2026           │
├─────────────────────────────────────┤
│ [View Details] (ADMIN only)          │
│ [Purchase SDK] (CLIENT)              │
│ [Learn More] (GUEST/all)             │
└─────────────────────────────────────┘
```

---

## 🔒 Permissions & Features by Role

| Feature | GUEST | CLIENT | INVESTOR | ADMIN |
|---------|-------|--------|----------|-------|
| View Dashboard | ✅ | ✅ | ✅ | ✅ |
| Manage Budget | ❌ | ✅ | ✅ | ✅ |
| View Investment Analysis | ❌ | ✅ | ✅ | ✅ |
| View Crypto Dashboard | ❌ | ✅ | ✅ | ✅ |
| Broker Trading (Page 5) | ❌ | ❌ | ✅ | ✅ |
| Bank Connection (Plaid) | ❌ | ✅ | ✅ | ✅ |
| Trade Execution | ❌ | ❌ | ✅ | ✅ |
| Trading Bot Mgmt (Page 6) | ❌ | ❌ | ❌ | ✅ |
| Plaid Testing (Page 7) | ❌ | ❌ | ❌ | ✅ |
| Multi-Broker Tools (Page 8) | ❌ | ❌ | ❌ | ✅ |
| Admin Panel | ❌ | ❌ | ❌ | ✅ |

---

## 📄 Page Structure & Naming Convention

### Pages Directory Structure
```
pages/
├── 01_💰_Personal_Budget.py        (Page 1: Dashboard)
├── 02_📈_Investment_Analysis.py    (Page 2: Budget Management)
├── 03_🔴_Live_Crypto_Dashboard.py  (Page 3: Investment Analysis)
├── 04_💼_Broker_Trading.py         (Page 4: Crypto Dashboard)
├── 05_🌐_Multi_Broker_Trading.py   (Page 5: Multi-Broker - ADMIN ONLY)
├── 06_🏦_Plaid_Test.py             (Page 6: Plaid Test - ADMIN ONLY)
├── 07_🤖_Trading_Bot.py            (Page 7: Trading Bot - ADMIN ONLY)
└── api/                             (API endpoints)
```

### Page Numbering (1-8)
| # | File Name | Display Name | Access |
|---|-----------|-------------|--------|
| 1 | 01_💰_... | Dashboard | GUEST+ |
| 2 | 02_📈_... | Budget | GUEST+ |
| 3 | 03_🔴_... | Investment Analysis | CLIENT+ |
| 4 | 04_💼_... | Crypto Dashboard | CLIENT+ |
| 5 | 05_🤖_... | Broker Trading | INVESTOR+ |
| 6 | 06_🏦_... | Trading Bot | ADMIN |
| 7 | 07_🌐_... | Plaid Test | ADMIN |
| 8 | api/* | Multi-Broker | ADMIN |

---

## 🔑 Demo Credentials (Testing Only)

### GUEST
```
Username: guest
Password: guest123
Pages: 1-2
Login: Public (no login via Mansacap.com)
```

### CLIENT
```
Username: client
Password: client123
Pages: 1-4
Login: Via Mansacap.com
Agreement: Asset Management
```

### INVESTOR
```
Username: investor
Password: investor123
Pages: 1-5
KYC: ✅ Completed
Agreement: Investor Management / PPM
```

### ADMIN
```
Username: admin
Password: admin123
Pages: 1-8 (All)
Full System Access
```

---

## 🛡️ Compliance & Legal Requirements

### GUEST Users
- ✅ No requirements
- ✅ Public access permitted
- ✅ No personal data collection

### CLIENT Users
- ✅ Mansacap.com account
- ✅ Asset Management Agreement (via Mansacap)
- ⚠️ KYC optional (handled by Mansacap)
- ✅ SDK Purchase Agreement

### INVESTOR Users
- ✅ **KYC Verification** (REQUIRED)
  - Identity verification
  - Accreditation verification
  - Source of funds documentation
- ✅ **Legal Agreement** (REQUIRED) - Choose one:
  - Investor Management Agreement
  - Private Placement Memorandum (PPM)
- ✅ Enhanced due diligence for high-value investors

### ADMIN Users
- ✅ System administrator
- ✅ All checks bypassed
- ✅ Full audit logging enabled

---

## 🚀 Implementation Details

### Page Access Guard
Each page file (Pages 1-8) includes a security gate at the top:

```python
from frontend.utils.rbac import RBACManager, show_login_form, show_permission_denied

# Initialize RBAC
RBACManager.init_session_state()

# Page 1-2: Anyone can view (no check needed)
# Page 3-4: CLIENT+ required
if not RBACManager.is_authenticated() or not RBACManager.has_permission(Permission.VIEW_ANALYSIS):
    show_login_form()
    show_permission_denied("CLIENT role with Mansacap login")
    st.stop()

# Page 5: INVESTOR+ required
if not RBACManager.has_permission(Permission.VIEW_BROKER_TRADING):
    show_permission_denied("INVESTOR role with KYC + Legal documents")
    st.stop()

# Page 6-8: ADMIN required
if not RBACManager.has_permission(Permission.VIEW_TRADING_BOT):
    show_permission_denied("ADMIN access required")
    st.stop()
```

### Sidebar Navigation
The sidebar automatically hides unavailable pages based on user role:

```python
# Show user info and role
show_user_info()

# Navigation will only display accessible pages
# GUEST: Pages 1-2
# CLIENT: Pages 1-4
# INVESTOR: Pages 1-5
# ADMIN: Pages 1-8
```

---

## 💡 Bot Information on Home Page

### Implementation
The Dashboard (Page 1) displays trading bot performance without requiring access to the full bot management page:

```python
# Show bot summaries (accessible to all authenticated users)
st.subheader("📊 Featured Trading Bots")

for bot in featured_bots:
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.write(f"**{bot['name']}**")
        st.caption(f"Performance: {bot['performance_ytd']}%")
    
    with col2:
        st.metric("Win Rate", f"{bot['win_rate']}%")
    
    with col3:
        if RBACManager.has_permission(Permission.VIEW_TRADING_BOT):
            st.button("Full Details", key=f"bot_{bot['id']}")
        else:
            st.button("Purchase SDK", key=f"purchase_{bot['id']}")
```

---

## 🔄 Session Management

### Session State Variables
```python
st.session_state.authenticated    # bool: Is user logged in?
st.session_state.current_user     # User: Current user object
st.session_state.portfolio_data   # dict: Cached portfolio data
```

### Logout
- Button available in sidebar when authenticated
- Clears session state
- Redirects to login form
- Accessible to all authenticated users

---

## 📊 Permission Model

### Core Permissions

| Permission | Description | Roles |
|------------|-------------|-------|
| `VIEW_DASHBOARD` | Access Page 1 | All |
| `VIEW_BUDGET` | Access Page 2 | All |
| `VIEW_ANALYSIS` | Access Page 3 | CLIENT+ |
| `VIEW_CRYPTO` | Access Page 4 | CLIENT+ |
| `VIEW_BROKER_TRADING` | Access Page 5 | INVESTOR+ |
| `VIEW_TRADING_BOT` | Access Pages 6-8 | ADMIN |
| `CONNECT_BANK` | Plaid integration | CLIENT+ |
| `MANAGE_BUDGET` | Budget editing | CLIENT+ |
| `TRADE_EXECUTION` | Execute trades | INVESTOR+ |
| `ADMIN_PANEL` | System configuration | ADMIN |

---

## 🔗 Integration with Mansacap.com

### Single Sign-On (SSO)
Currently using demo credentials. For production:

```python
# Future: Implement Mansacap.com SSO
def authenticate_with_mansacap(oauth_token):
    """Verify user against Mansacap.com OAuth"""
    # 1. Validate token with Mansacap API
    # 2. Fetch user role (CLIENT or INVESTOR)
    # 3. Retrieve KYC/Agreement status
    # 4. Create/update user session
    pass
```

### Current Demo Setup
- GUEST: Direct public access (no login)
- CLIENT: Simulated Mansacap login
- INVESTOR: Separate platform login
- ADMIN: Direct admin login

---

## 🐛 Troubleshooting

### User can't access Page 3+
**Problem:** User sees "Access Denied" on Investment Analysis
**Solution:** 
- Verify user role is CLIENT or higher
- Ensure Mansacap login is active
- Check KYC status for INVESTOR role

### GUEST sees "Please login"
**Problem:** GUEST trying Pages 1-2 sees login form
**Solution:**
- Pages 1-2 should NOT require login
- Check page implementation for redundant auth check
- GUEST role has `VIEW_DASHBOARD` + `VIEW_BUDGET` permissions

### INVESTOR can't see Broker Trading
**Problem:** INVESTOR missing Page 5 access
**Solution:**
- Verify KYC is marked as completed
- Verify investment agreement is signed
- Check agreement type is set (investor_mgmt or ppm)

---

## 📝 Next Steps

1. **Production Database:** Replace demo credentials with production DB
2. **Mansacap SSO:** Implement OAuth 2.0 integration
3. **KYC Provider:** Integrate with KYC verification service
4. **Audit Logging:** Add compliance audit trails
5. **2FA:** Implement two-factor authentication for INVESTOR/ADMIN
6. **Legal Document Management:** Build document storage and signing workflow

---

## 📞 Support

For questions about access levels or implementation, refer to the RBAC system in:
- `/frontend/utils/rbac.py` - Core RBAC logic
- `/streamlit_app.py` - Main authentication flow
- Individual page files for access guards

---

*Last Updated: January 16, 2026*
*Maintained by: Winston (ADMIN)*
