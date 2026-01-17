# RBAC Quick Reference Guide
## Bentley Budget Bot Access Control

---

## 📱 One-Page Access Matrix

### User Roles & Page Access

```
╔════════════════════════════════════════════════════════════════════════════════╗
║                          PAGE ACCESS BY ROLE                                   ║
╠════════════╦═════════╦═════════╦═════════════╦═══════════╦════════════════════╣
║    Page    ║  GUEST  ║ CLIENT  ║  INVESTOR   ║   ADMIN   ║   Description      ║
╠════════════╬═════════╬═════════╬═════════════╬═══════════╬════════════════════╣
║ Page 1     ║   ✅    ║   ✅    ║      ✅      ║     ✅     ║ Dashboard          ║
║ Page 2     ║   ✅    ║   ✅    ║      ✅      ║     ✅     ║ Budget             ║
║ Page 3     ║   ❌    ║   ✅    ║      ✅      ║     ✅     ║ Investment Anlys   ║
║ Page 4     ║   ❌    ║   ✅    ║      ✅      ║     ✅     ║ Crypto Dashboard   ║
║ Page 5     ║   ❌    ║   ❌    ║      ✅      ║     ✅     ║ Broker Trading     ║
║ Page 6     ║   ❌    ║   ❌    ║      ❌      ║     ✅     ║ Trading Bot (ADMIN) ║
║ Page 7     ║   ❌    ║   ❌    ║      ❌      ║     ✅     ║ Plaid Test (ADMIN) ║
║ Page 8     ║   ❌    ║   ❌    ║      ❌      ║     ✅     ║ Multi-Broker(ADMIN)║
╚════════════╩═════════╩═════════╩═════════════╩═══════════╩════════════════════╝
```

---

## 🎯 Role Descriptions

### GUEST
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
