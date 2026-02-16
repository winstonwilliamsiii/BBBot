# RBAC Access Flow & Architecture
## Visual Guide - Bentley Budget Bot Role-Based Access Control

---

## 🎯 Complete User Journey & Access Flow

### 1️⃣ GUEST User Journey (Public Access)

```
┌──────────────────────┐
│  Mansacap.com Home   │
│  Landing Page        │
└──────────┬───────────┘
           │
           └─→ "Explore Bentley"
               │
               ├─→ ✅ Page 1: Dashboard
               │   • Portfolio overview
               │   • Featured bot summaries
               │   • Links to sign up
               │
               └─→ ✅ Page 2: Budget Tool
                   • Basic budget tracker
                   • Budget tips
                   • "Sign up for bank sync"
                   
┌──────────────────────────────────────────┐
│ Wants more? → "Sign up for CLIENT account"│
│              (Mansacap.com registration)  │
└──────────────────────────────────────────┘

Access: Pages 1-2 ONLY ✅
Login Required: NO
Bot Info: View on Page 1, can't manage
```

---

### 2️⃣ CLIENT User Journey (SDK Traders)

```
┌─────────────────────────────────┐
│ Mansacap.com - CLIENT Signup    │
│ • Email verification            │
│ • Account setup                 │
│ • Asset Mgmt Agreement (Mansacap) │
└──────────────┬──────────────────┘
               │
               └─→ Bentley Bot Login
                   ├─ Via Mansacap SSO (Future)
                   ├─ Or separate CLIENT account
                   │
                   └─→ ✅ Page 1: Dashboard
                       • Full portfolio overview
                       • Bot summaries + "Purchase" buttons
                       │
                   └─→ ✅ Page 2: Budget
                       • Full budget management
                       • Plaid bank connections
                       │
                   └─→ ✅ Page 3: Investment Analysis
                       • Market research tools
                       • Stock analysis
                       │
                   └─→ ✅ Page 4: Crypto Dashboard
                       • Cryptocurrency tracking
                       • Price alerts
                       │
                   ❌ Page 5+: Access Denied
                       • "Upgrade to INVESTOR"
                       
┌──────────────────────────────────────────────┐
│ Use Case: Purchase & backtest trading SDKs    │
│ • Backtesting tools                          │
│ • Strategy development                       │
│ • One-time SDK fee or subscription model     │
└──────────────────────────────────────────────┘

Access: Pages 1-4 ✅
Login Required: YES (Mansacap)
KYC Required: Optional (Mansacap handles)
Agreement: Asset Management (implied)
Bot Info: View summaries, purchase SDKs
```

---

### 3️⃣ INVESTOR User Journey (Asset Management)

```
┌──────────────────────────────────┐
│  Bentley Bot - INVESTOR Signup   │
│  • Identity verification         │
│  • KYC process (10-15 min)      │
│  • Address verification          │
│  • Source of funds docs          │
│  • Accreditation review          │
└──────────────┬───────────────────┘
               │
               ├─→ Step 2: Legal Documentation
               │   • Review Investor Mgmt Agreement
               │   │   OR
               │   │  Private Placement Memo (PPM)
               │   │
               │   └─→ E-sign agreement
               │       (via DocuSign)
               │
               └─→ Step 3: Account Activation
                   • KYC Verification: ✅ Complete
                   • Agreement Signed: ✅ Complete
                   │
                   └─→ Full Access Granted!
                       │
                       ├─→ ✅ Page 1: Dashboard
                       │   • Complete portfolio management
                       │   • Asset allocation tools
                       │   • Performance reporting
                       │
                       ├─→ ✅ Page 2: Budget
                       │   • Comprehensive budget analysis
                       │   • Multi-account tracking
                       │   │
                       ├─→ ✅ Page 3: Investment Analysis
                       │   • Advanced research tools
                       │   • Fund allocation
                       │   │
                       ├─→ ✅ Page 4: Crypto Dashboard
                       │   • Crypto portfolio management
                       │   • Alternative asset tracking
                       │   │
                       ├─→ ✅ Page 5: Broker Trading
                       │   • Multi-broker connections
                       │   • Trade execution
                       │   • Account management
                       │   • Portfolio monitoring
                       │
                       ❌ Pages 6-8: Access Denied
                           • Admin development tools only

┌─────────────────────────────────────────────┐
│ Use Case: Professional asset management      │
│ • Passive investment management              │
│ • Professional advisory                      │
│ • Tax-advantaged strategies                  │
│ • Multi-account coordination                 │
│ • Regulatory compliance tracking             │
└─────────────────────────────────────────────┘

Access: Pages 1-5 ✅
Login Required: YES
KYC Required: YES ✅ MUST COMPLETE
Agreement Required: YES ✅ MUST SIGN
Bot Info: View summaries (no management)
```

---

### 4️⃣ ADMIN User Journey (You - Winston)

```
┌──────────────────────────────────┐
│ Bentley Bot Admin Credentials    │
│ Username: admin                  │
│ Password: [secure password]      │
└──────────────┬───────────────────┘
               │
               └─→ Login
                   │
                   └─→ ✅ FULL ACCESS - All Pages 1-8
                       │
                       ├─→ Page 1: Dashboard
                       │   • All portfolio features
                       │   • Bot summaries
                       │   • Edit & configure bots
                       │
                       ├─→ Page 2: Budget
                       │   • All budget features
                       │   • Admin configuration
                       │
                       ├─→ Page 3: Investment Analysis
                       │   • All analysis features
                       │   • Research tool config
                       │
                       ├─→ Page 4: Crypto Dashboard
                       │   • All crypto features
                       │   • Data source config
                       │
                       ├─→ Page 5: Broker Trading
                       │   • All trading features
                       │   • Broker integrations
                       │
                       ├─→ ✅ Page 6: Trading Bot Manager
                       │   • Create/edit bots
                       │   • Backtest strategies
                       │   • Deploy bots
                       │   • View bot performance
                       │   • Manage bot inventory
                       │   • Configure SDK pricing
                       │
                       ├─→ ✅ Page 7: Plaid Test
                       │   • Test Plaid connections
                       │   • Debug bank sync
                       │   • Transaction mapping
                       │   • Connection troubleshooting
                       │
                       ├─→ ✅ Page 8: Multi-Broker Tools
                       │   • Multi-broker integration
                       │   • Strategy development
                       │   • API testing
                       │   • Broker connector config
                       │
                       └─→ Admin Panel
                           • System configuration
                           • User management
                           • Audit logs
                           • Settings

┌─────────────────────────────────────────────┐
│ Admin Capabilities:                          │
│ • Full system access (all pages)            │
│ • Bot management & deployment                │
│ • Development & testing tools               │
│ • Compliance & audit review                 │
│ • User account management                   │
│ • System configuration                      │
│ • KYC/Agreement processing                  │
│ • Performance monitoring                    │
└─────────────────────────────────────────────┘

Access: Pages 1-8 ✅✅✅ ALL PAGES
Login Required: YES
KYC Required: YES
Agreement Required: YES
Bot Info: Full management + deployment
```

---

## 📊 Role Comparison Matrix

```
┌─────────────────────┬──────────┬───────────┬──────────────┬──────────┐
│ Feature             │  GUEST   │  CLIENT   │  INVESTOR    │  ADMIN   │
├─────────────────────┼──────────┼───────────┼──────────────┼──────────┤
│ Login Required      │    NO    │    YES    │     YES      │   YES    │
│ Pages Accessible    │   1-2    │   1-4     │    1-5       │  1-8 ALL │
│                     │          │           │              │          │
│ KYC Completion      │    NO    │  OPT      │     YES ✅   │   YES ✅ │
│ Legal Agreement     │    NO    │  YES      │     YES ✅   │   YES ✅ │
│ Bank Connections    │    NO    │    YES    │     YES      │   YES    │
│ Portfolio Mgmt      │    VIEW  │   FULL    │     FULL     │   FULL   │
│ Trading Execution   │    NO    │    NO     │     YES      │   YES    │
│                     │          │           │              │          │
│ Bot View Summary    │    YES   │    YES    │     YES      │   YES    │
│ Bot Purchase SDK    │    NO    │    YES    │     NO       │   YES    │
│ Bot Manage/Deploy   │    NO    │    NO     │     NO       │   YES    │
│ Bot Backtest        │    NO    │    NO     │     NO       │   YES    │
│                     │          │           │              │          │
│ Plaid Testing       │    NO    │    NO     │     NO       │   YES    │
│ Multi-Broker Dev    │    NO    │    NO     │     NO       │   YES    │
│ Admin Panel         │    NO    │    NO     │     NO       │   YES    │
│ System Config       │    NO    │    NO     │     NO       │   YES    │
└─────────────────────┴──────────┴───────────┴──────────────┴──────────┘
```

---

## 🔄 Permission Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│              PERMISSION HIERARCHY TREE                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🎯 Core Access (Pages 1-2)                            │
│   ├─ VIEW_DASHBOARD (Page 1)      ← GUEST, all+       │
│   └─ VIEW_BUDGET (Page 2)         ← GUEST, all+       │
│                                                         │
│  📊 Client Access (Pages 3-4)                          │
│   ├─ VIEW_ANALYSIS (Page 3)       ← CLIENT+           │
│   ├─ VIEW_CRYPTO (Page 4)         ← CLIENT+           │
│   └─ CONNECT_BANK (Plaid)         ← CLIENT+           │
│                                                         │
│  💼 Investor Access (Page 5)                           │
│   ├─ VIEW_BROKER_TRADING (Page 5) ← INVESTOR+         │
│   ├─ MANAGE_BUDGET                ← INVESTOR+         │
│   ├─ TRADE_EXECUTION              ← INVESTOR+         │
│   └─ [Requires KYC + Agreement]   ← MANDATORY         │
│                                                         │
│  🤖 Admin Access (Pages 6-8)                           │
│   ├─ VIEW_TRADING_BOT             ← ADMIN only        │
│   ├─ ADMIN_PANEL                  ← ADMIN only        │
│   ├─ Page 6: Trading Bot Manager  ← ADMIN only        │
│   ├─ Page 7: Plaid Test           ← ADMIN only        │
│   └─ Page 8: Multi-Broker Tools   ← ADMIN only        │
│                                                         │
└─────────────────────────────────────────────────────────┘

Legend:
  ← X+        = X role and higher (CLIENT+ = CLIENT, INVESTOR, ADMIN)
  ← only      = Exclusive to that role
  MANDATORY   = Required for access (e.g., KYC for INVESTOR)
```

---

## 🔐 Authentication Flow Diagram

```
┌─────────────┐
│ User visits │
│ Bentley.com │
└──────┬──────┘
       │
       ├─→ Pages 1-2?
       │   └─→ ✅ Allow direct access (GUEST)
       │       └─→ Show login option in sidebar
       │
       ├─→ Pages 3-4?
       │   └─→ Is authenticated?
       │       ├─→ NO: Show login form
       │       │   └─→ LOGIN (client/client123)
       │       │       ├─→ Success ✅
       │       │       │   └─→ Grant CLIENT role ✅
       │       │       │       └─→ Access Pages 1-4
       │       │       │
       │       │       └─→ Fail ❌
       │       │           └─→ Show error, try again
       │       │
       │       └─→ YES: Has VIEW_ANALYSIS permission?
       │           ├─→ YES ✅ → Display page
       │           └─→ NO ❌ → Show access denied
       │
       ├─→ Page 5?
       │   └─→ Is authenticated?
       │       ├─→ NO: Show login form
       │       │   └─→ LOGIN (investor/investor123)
       │       │       ├─→ Has VIEW_BROKER_TRADING?
       │       │       │   ├─→ NO ❌ Access denied
       │       │       │   └─→ YES ✅ Continue
       │       │       │
       │       │       └─→ KYC Completed?
       │       │           ├─→ NO ❌ Show KYC prompt
       │       │           └─→ YES ✅ Continue
       │       │
       │       └─→ Agreement Signed?
       │           ├─→ NO ❌ Show agreement prompt
       │           └─→ YES ✅ Grant access ✅
       │
       └─→ Pages 6-8?
           └─→ Is authenticated?
               ├─→ NO: Show login form
               │   └─→ LOGIN (admin/admin123)
               │
               └─→ YES: Has VIEW_TRADING_BOT?
                   ├─→ NO ❌ Show admin-only message
                   └─→ YES ✅ Full access to all pages
```

---

## 📋 Compliance Checkpoints

```
GUEST USER
├─ Show landing page (Pages 1-2)
├─ "Want more features?" → Sign up for CLIENT
└─ No compliance required

CLIENT USER (Mansacap.com signup)
├─ Mansacap.com handles KYC (optional)
├─ Implied Asset Management Agreement
├─ Granted: Pages 1-4
├─ Can purchase SDKs
└─ No additional compliance

INVESTOR USER (Bentley platform)
├─ ✅ CHECKPOINT 1: Identity Verification (KYC)
│   └─ Verify full name, DOB, SSN
├─ ✅ CHECKPOINT 2: Address Verification
│   └─ Current residential address
├─ ✅ CHECKPOINT 3: Source of Funds
│   └─ Employment, investment history
├─ ✅ CHECKPOINT 4: Accreditation Check
│   └─ Income/net worth verification
├─ ✅ CHECKPOINT 5: Legal Document
│   └─ Sign Investment Agreement OR PPM
├─ After all checks: Granted Pages 1-5
└─ Full asset management available

ADMIN USER
├─ Internal credentials only
├─ All checks bypassed
├─ Full system access (Pages 1-8)
└─ Development tools enabled
```

---

## 🚀 Deployment Scenarios

### Scenario 1: Marketing Website
```
User lands on Mansacap.com
    ↓
"Explore Bentley Bot" link
    ↓
Opens Pages 1-2 (GUEST view)
    ↓
"Sign up for CLIENT account"
    ↓
Redirect to Mansacap signup
```

### Scenario 2: Client SDK Purchase
```
CLIENT logs into Bentley (via Mansacap)
    ↓
Views Page 1: Dashboard with bot summaries
    ↓
"Purchase SDK" button on bot card
    ↓
Redirect to SDK purchasing page
    ↓
One-time or subscription payment
    ↓
Download SDK + documentation
```

### Scenario 3: Investor Onboarding
```
User signs up on Bentley Bot
    ↓
Begins KYC process (5-10 forms)
    ↓
Uploads documents (ID, address, etc.)
    ↓
Receives verification email
    ↓
Reviews Investment Agreement
    ↓
E-signs via DocuSign
    ↓
System marks agreement_signed = TRUE
    ↓
Pages 1-5 unlocked ✅
```

### Scenario 4: Admin Development
```
Winston logs in as admin
    ↓
Views all Pages 1-8
    ↓
Creates new trading bot (Page 6)
    ↓
Backtests strategy
    ↓
Configures bot for CLIENT purchase (Page 1)
    ↓
Tests Plaid connections (Page 7)
    ↓
Configures multi-broker strategy (Page 8)
    ↓
Monitors all user access
```

---

## 💡 Key Design Principles

1. **Principle: Zero Trust for Sensitive Pages**
   - Pages 5-8 require explicit authentication + compliance checks
   - No implicit assumptions about user status

2. **Principle: Graceful Degradation**
   - GUEST users see Pages 1-2 by default
   - Login prompts appear in sidebar for more access
   - Clear "upgrade" prompts to higher tiers

3. **Principle: Compliance-First**
   - INVESTOR access blocked until KYC + legal docs complete
   - Audit trails for all compliance checks
   - Regulatory requirements enforced in code

4. **Principle: Separation of Concerns**
   - Admin tools completely hidden from normal users
   - Dev/testing pages only for Winston
   - Client SDK tools separate from investor management

5. **Principle: Clear User Expectations**
   - Role displayed prominently in sidebar
   - Page access summary shown
   - Compliance status visible ("KYC: ✅", "Agreement: ❌")

---

## 🎯 Next Implementation Steps

1. **Add page-level access checks** (see PAGE_ACCESS_CONTROL_TEMPLATE.md)
2. **Hide Pages 6-8 from sidebar** for non-ADMIN users
3. **Add bot info to Page 1** (all roles can see)
4. **Test each role** with demo credentials
5. **Integrate Mansacap SSO** (future phase)
6. **Replace demo users** with production database

---

*Access Flow & Architecture v1.0*  
*Last Updated: January 16, 2026*  
*Visual Guide - Ready for Implementation*
