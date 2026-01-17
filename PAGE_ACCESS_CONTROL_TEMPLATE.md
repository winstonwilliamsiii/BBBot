# Page Access Control Template
## How to Add RBAC to Each Page File

Every page file should include access control checks. Use this template:

---

## Template for Pages 1-2 (GUEST Access)

```python
"""
Page 1 & 2: Dashboard & Budget
Access: GUEST+ (anyone)
No authentication required
"""

import streamlit as st
from frontend.utils.rbac import RBACManager, show_login_form, show_user_info

# Initialize RBAC
RBACManager.init_session_state()

# Pages 1-2 are publicly accessible - show login option if user wants to access more pages
st.set_page_config(page_title="Dashboard", page_icon="💰", layout="wide")

# Show user info if logged in, otherwise prompt to login for full access
show_user_info()

if not RBACManager.is_authenticated():
    with st.info("💡 Tip"):
        st.write("Login to Mansacap.com to access **Investment Analysis**, **Crypto Dashboard** (Pages 3-4)")

# =========== PAGE CONTENT HERE ===========
st.title("Page Content")
# ... your page implementation ...
```

---

## Template for Pages 3-4 (CLIENT Access)

```python
"""
Page 3: Investment Analysis
Page 4: Live Crypto Dashboard
Access: CLIENT+ (requires Mansacap login)
"""

import streamlit as st
from frontend.utils.rbac import RBACManager, Permission, show_login_form, show_user_info

# Initialize RBAC
RBACManager.init_session_state()

# Set page config
st.set_page_config(page_title="Investment Analysis", page_icon="📊", layout="wide")

# Show user info
show_user_info()

# ===== ACCESS CONTROL =====
# CLIENT+ required (Pages 3-4)
if not RBACManager.is_authenticated() or not RBACManager.has_permission(Permission.VIEW_ANALYSIS):
    st.error("🚫 Access Denied - CLIENT Role Required")
    st.info("""
    This page requires **CLIENT** or higher access level.
    
    **How to access:**
    1. Login via Mansacap.com (for CLIENT users)
    2. Or complete KYC + Legal documents for INVESTOR access
    """)
    show_login_form()
    st.stop()

# =========== PAGE CONTENT HERE ===========
st.title("Page Content")
# ... your page implementation ...
```

---

## Template for Page 5 (INVESTOR Access)

```python
"""
Page 5: Broker Trading
Access: INVESTOR+ (requires KYC + Legal documents)
"""

import streamlit as st
from frontend.utils.rbac import RBACManager, Permission, show_login_form, show_user_info, show_permission_denied

# Initialize RBAC
RBACManager.init_session_state()

# Set page config
st.set_page_config(page_title="Broker Trading", page_icon="💼", layout="wide")

# Show user info
show_user_info()

# ===== ACCESS CONTROL =====
# INVESTOR+ required with KYC + Legal docs
if not RBACManager.is_authenticated():
    st.error("🔐 Authentication Required")
    show_login_form()
    st.stop()

current_user = RBACManager.get_current_user()

# Check role
if not RBACManager.has_permission(Permission.VIEW_BROKER_TRADING):
    show_permission_denied("INVESTOR Role with KYC + Legal Documents")
    st.warning("""
    **Why you can't access this page:**
    - Broker Trading is restricted to INVESTOR tier users
    - INVESTOR users have completed full KYC verification
    - INVESTOR users have signed investment agreements
    """)
    st.stop()

# Check KYC status
if not current_user.kyc_completed:
    st.warning("⚠️ KYC Verification Incomplete")
    st.info("Please complete your KYC (Know Your Customer) verification to access trading features.")
    st.stop()

# Check agreement status
if not current_user.investment_agreement_signed:
    st.warning("⚠️ Investment Agreement Not Signed")
    st.info("Please sign your Investment Management Agreement to access trading features.")
    st.stop()

# =========== PAGE CONTENT HERE ===========
st.title("Broker Trading")
st.write(f"Welcome, {current_user.username}! You have full access to broker trading.")
# ... your page implementation ...
```

---

## Template for Pages 6-8 (ADMIN Only)

```python
"""
Page 6: Trading Bot Manager
Page 7: Plaid Test Interface
Page 8: Multi-Broker Trading (API)
Access: ADMIN ONLY
"""

import streamlit as st
from frontend.utils.rbac import RBACManager, Permission, show_login_form, show_user_info, show_permission_denied

# Initialize RBAC
RBACManager.init_session_state()

# Set page config
st.set_page_config(page_title="Trading Bot Manager", page_icon="🤖", layout="wide")

# Show user info
show_user_info()

# ===== ACCESS CONTROL =====
# ADMIN ONLY - No exceptions
if not RBACManager.is_authenticated():
    st.error("🔐 Authentication Required")
    show_login_form()
    st.stop()

if not RBACManager.has_permission(Permission.VIEW_TRADING_BOT):
    st.error("🚫 ADMIN ACCESS REQUIRED")
    st.warning("""
    **This page is for system administration only:**
    - Trading Bot Manager: Configure and test trading strategies
    - Plaid Test Interface: Debug banking connections
    - Multi-Broker Tools: Develop broker integration features
    
    **Your current access level:** {0}
    """.format(RBACManager.get_current_user().role.value.upper()))
    
    st.info("If you believe this is an error, contact the system administrator (Winston).")
    st.stop()

# =========== PAGE CONTENT HERE ===========
st.title("🤖 Trading Bot Manager - ADMIN ONLY")
current_user = RBACManager.get_current_user()
st.success(f"Welcome, {current_user.username}! Full admin access enabled.")

# ... your page implementation ...
```

---

## Quick Copy-Paste Access Checks

### For Pages 1-2 (No check needed)
```python
RBACManager.init_session_state()
show_user_info()
# No stop() needed - pages are public
```

### For Pages 3-4 (CLIENT+)
```python
RBACManager.init_session_state()
show_user_info()

if not RBACManager.is_authenticated() or not RBACManager.has_permission(Permission.VIEW_ANALYSIS):
    st.error("🚫 Access Denied - CLIENT Role Required")
    show_login_form()
    st.stop()
```

### For Page 5 (INVESTOR+)
```python
RBACManager.init_session_state()
show_user_info()

if not RBACManager.is_authenticated():
    show_login_form()
    st.stop()

if not RBACManager.has_permission(Permission.VIEW_BROKER_TRADING):
    show_permission_denied("INVESTOR Role with KYC + Legal Documents")
    st.stop()

user = RBACManager.get_current_user()
if not (user.kyc_completed and user.investment_agreement_signed):
    st.warning("⚠️ KYC and Legal Agreement Required")
    st.stop()
```

### For Pages 6-8 (ADMIN Only)
```python
RBACManager.init_session_state()
show_user_info()

if not RBACManager.is_authenticated():
    show_login_form()
    st.stop()

if not RBACManager.has_permission(Permission.VIEW_TRADING_BOT):
    st.error("🚫 ADMIN ACCESS REQUIRED")
    st.stop()
```

---

## Best Practices

1. **Always call `RBACManager.init_session_state()`** at the start of each page
2. **Always call `show_user_info()`** to display user role in sidebar
3. **Use `st.stop()`** after permission denial to prevent page rendering
4. **Show helpful messages** explaining why access was denied
5. **For Pages 1-2**, no access control is needed (they're public)
6. **For Pages 6-8**, always check for ADMIN permission

---

## Testing Access Control

### Test GUEST Access
1. Clear browser cookies
2. Navigate to Pages 1-2 → ✅ Works
3. Try to access Page 3 → Should show login form or redirect
4. Login as `guest` → Still can't access Page 3

### Test CLIENT Access
1. Login as `client` / `client123`
2. Access Pages 1-4 → ✅ Works
3. Try Page 5 → ❌ Access Denied
4. Try Page 6 → ❌ Access Denied

### Test INVESTOR Access
1. Login as `investor` / `investor123`
2. Access Pages 1-5 → ✅ Works (after KYC check)
3. Try Pages 6-8 → ❌ Access Denied

### Test ADMIN Access
1. Login as `admin` / `admin123`
2. All pages 1-8 → ✅ Works

---

## File Locations

- **RBAC Core:** `/frontend/utils/rbac.py`
- **Page Files:** `/pages/01_*.py` through `/pages/07_*.py`
- **Main App:** `/streamlit_app.py`

---

*Template v1.0 - Use for all page files - Updated: January 16, 2026*
