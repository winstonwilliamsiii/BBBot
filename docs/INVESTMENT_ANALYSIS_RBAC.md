# Investment Analysis RBAC System

## Overview

The Investment Analysis page now includes a **Role-Based Access Control (RBAC)** system that restricts access to broker connections and fund displays based on user roles and compliance status.

## Features

### 🔐 Authentication System
- Secure login with password hashing (SHA-256)
- Session-based authentication using Streamlit session state
- Demo users for testing different access levels

### 🎭 Role Hierarchy
1. **Guest** - Basic portfolio viewing
2. **Client** - Portfolio + analysis + connections (with KYC)
3. **Investor** - Client permissions + trade execution
4. **Admin** - Full system access

### 📋 Compliance Requirements

To access the **Broker Connections** tab, users must:
1. ✅ Complete KYC (Know Your Customer) verification
2. ✅ Sign Investment Management Agreement

### 🔗 Broker Connections Tab

Available only to authorized users (Clients, Investors, Admins with KYC + Agreement):

#### Sub-tabs:
1. **🏦 Accounts** - View connected broker accounts
   - Account balances
   - Connection status
   - Last sync timestamps
   - Position counts

2. **💼 WeFolio Funds** - Webull WeFolio fund management
   - Fund NAV and values
   - Daily performance tracking
   - Portfolio allocation charts
   - Performance comparison
   - Database sync functionality

3. **📊 Positions** - Cross-broker position analysis
   - Consolidated view (coming soon)
   - Duplicate detection (coming soon)
   - Sector exposure (coming soon)

4. **🔍 Health Monitor** - Connection health monitoring
   - Real-time sync status
   - Connection diagnostics
   - Manual refresh controls

## Demo Credentials

### Guest User
```
Username: guest
Password: guest123
Permissions: View Portfolio only
```

### Client User
```
Username: client
Password: client123
Permissions: Portfolio + Analysis + Connections
KYC: ✅ Completed
Agreement: ✅ Signed
```

### Investor User
```
Username: investor
Password: investor123
Permissions: Client + Trade Execution
KYC: ✅ Completed
Agreement: ✅ Signed
```

### Admin User
```
Username: admin
Password: admin123
Permissions: Full Access
KYC: ✅ Completed
Agreement: ✅ Signed
```

## Usage

### 1. Login
Navigate to the Investment Analysis page and use the login form in the sidebar:

```python
# The RBAC system automatically checks authentication
RBACManager.init_session_state()

if not RBACManager.is_authenticated():
    show_login_form()
```

### 2. Access Broker Connections
Once logged in with proper credentials (client/investor/admin), the **Broker Connections** tab will appear:

```python
if RBACManager.require_connections_access():
    # Show connections tab
    display_broker_connections_tab()
```

### 3. View and Manage Funds
In the WeFolio Funds sub-tab:
- Toggle between demo data and real API
- Enter Webull API token for live data
- View fund allocations and performance
- Sync to database

## Technical Implementation

### File Structure
```
frontend/
├── utils/
│   ├── rbac.py                    # RBAC system
│   ├── broker_connections.py      # Broker connection displays
│   ├── styling.py                 # UI styling
│   └── yahoo.py                   # Yahoo Finance integration
pages/
└── 01_📈_Investment_Analysis.py  # Updated with RBAC
```

### Key Classes

#### `RBACManager`
Central authentication and authorization manager:
- `authenticate(username, password)` - Authenticate user
- `login(username, password)` - Login and store in session
- `logout()` - Clear session
- `require_permission(permission)` - Check permission
- `require_connections_access()` - Check connections access

#### `User`
User model with compliance tracking:
- `has_permission(permission)` - Check permission
- `can_view_connections()` - Check connections access

#### `BrokerConnection`
Represents a broker account:
- Account details
- Balance and positions
- Sync status

#### `WebullFund`
Represents a WeFolio fund:
- NAV and shares
- Daily performance
- Value tracking

### Permissions

```python
class Permission(Enum):
    VIEW_PORTFOLIO = "view_portfolio"
    VIEW_ANALYSIS = "view_analysis"
    VIEW_CONNECTIONS = "view_connections"
    TRADE_EXECUTION = "trade_execution"
    VIEW_FUNDS = "view_funds"
    ADMIN_PANEL = "admin_panel"
```

### Role-Permission Mapping

```python
ROLE_PERMISSIONS = {
    UserRole.GUEST: {VIEW_PORTFOLIO},
    UserRole.CLIENT: {VIEW_PORTFOLIO, VIEW_ANALYSIS, VIEW_CONNECTIONS, VIEW_FUNDS},
    UserRole.INVESTOR: {VIEW_PORTFOLIO, VIEW_ANALYSIS, VIEW_CONNECTIONS, VIEW_FUNDS, TRADE_EXECUTION},
    UserRole.ADMIN: {ALL_PERMISSIONS},
}
```

## Integration with Webull API

### Fetching Funds

```python
from frontend.utils.broker_connections import BrokerConnectionManager

# Fetch funds from Webull API
funds = BrokerConnectionManager.fetch_webull_funds(api_token)

# Save to database
db_config = {
    "host": "localhost",
    "user": "user",
    "password": "pass",
    "database": "bentley_budget"
}
BrokerConnectionManager.save_funds_to_db(funds, db_config)
```

### Database Schema

Required MySQL table:
```sql
CREATE TABLE wefolio_funds (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    nav DECIMAL(10, 2),
    shares DECIMAL(15, 4),
    value DECIMAL(15, 2),
    daily_change DECIMAL(15, 2),
    daily_change_pct DECIMAL(5, 2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## Security Considerations

### Current Implementation (Demo)
- ✅ Password hashing (SHA-256)
- ✅ Session-based authentication
- ✅ Role-based permissions
- ✅ Compliance tracking
- ⚠️ Hardcoded demo users (for development)

### Production Recommendations
1. **Use Database Authentication**
   - Store users in MySQL/PostgreSQL
   - Implement proper password policies
   - Add password reset functionality

2. **Enhanced Security**
   - Use bcrypt/argon2 for password hashing
   - Implement rate limiting
   - Add 2FA support
   - Use environment variables for secrets

3. **Audit Logging**
   - Log authentication attempts
   - Track permission checks
   - Monitor data access

4. **Token-Based Auth**
   - Consider JWT tokens
   - Implement refresh tokens
   - Add token expiration

## Customization

### Adding New Roles
```python
class UserRole(Enum):
    # Add new role
    PREMIUM_CLIENT = "premium_client"

# Add permissions
ROLE_PERMISSIONS[UserRole.PREMIUM_CLIENT] = {
    Permission.VIEW_PORTFOLIO,
    Permission.VIEW_ANALYSIS,
    Permission.VIEW_CONNECTIONS,
    Permission.VIEW_FUNDS,
    Permission.CUSTOM_PERMISSION,
}
```

### Adding New Permissions
```python
class Permission(Enum):
    # Add new permission
    CUSTOM_PERMISSION = "custom_permission"
```

### Custom Permission Checks
```python
@require_permission_decorator(Permission.CUSTOM_PERMISSION)
def custom_feature():
    st.write("Custom feature for authorized users")
```

## Troubleshooting

### Import Errors
If you see "RBAC system not available":
1. Ensure `frontend/utils/rbac.py` exists
2. Check Python path includes the project root
3. Verify no circular imports

### Login Not Working
1. Check credentials match demo users
2. Clear browser cache and cookies
3. Check session state initialization
4. Verify `st.rerun()` is called after login

### Connections Tab Not Showing
1. Verify user role is Client/Investor/Admin
2. Check KYC and agreement status
3. Ensure `RBAC_AVAILABLE = True`
4. Check permissions in `ROLE_PERMISSIONS`

## Future Enhancements

- [ ] Database-backed user management
- [ ] OAuth2 integration
- [ ] Multi-factor authentication
- [ ] Audit logging
- [ ] Custom role creation
- [ ] Permission templates
- [ ] User self-service KYC
- [ ] Automated compliance workflows
- [ ] Real-time position consolidation
- [ ] Advanced analytics dashboard

## Support

For issues or questions:
- Email: support@bentleybot.com
- GitHub Issues: [BentleyBudgetBot](https://github.com/winstonwilliamsiii/BBBot)
