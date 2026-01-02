# Next.js Frontend Architecture - Implementation Guide

## Your Specified Structure

```
vercel-frontend/ (root)
├── .env.local
├── package.json
├── next.config.js
├── lib/
│   └── appwriteClient.js        ← Client-side calls (no API key)
│
├── pages/
│   ├── index.js                 ← Landing page
│   ├── dashboard.js             ← Dashboard UI (Load Transactions)
│   ├── watchlist.js             ← Watchlist UI (Add/Remove)
│   ├── payments.js              ← Payments UI (Create Payment)
│   ├── metrics.js               ← Metrics UI (Bot Stats)
│   │
│   └── api/                     ← SERVER-SIDE API ROUTES
│       ├── getTransactions.js   ← Calls Appwrite Function: get_transactions
│       ├── addToWatchlist.js    ← Calls add_to_watchlist_streamlit
│       ├── removeFromWatchlist.js
│       ├── createPayment.js     ← Calls create_payment
│       ├── getMetrics.js        ← Calls get_bot_metrics
│       └── getMetricStats.js    ← Calls get_bot_metrics_stats
│
└── components/
    ├── DashboardTable.jsx       ← Displays transactions
    ├── WatchlistTable.jsx       ← Displays watchlist
    ├── PaymentForm.jsx          ← Payment UI
    └── MetricsChart.jsx         ← Bot metrics visualization
```

---

## ✅ Implementation Status

### ✅ Already Created

**Libraries**:
- ✅ `/lib/appwriteClient.js` - Client-side Appwrite calls (browser-safe)

**API Routes** (Already created - call Appwrite functions):
- ✅ `/pages/api/createPayment.js` - Payment processing
- ✅ `/pages/api/createTransaction.js` - Transaction recording
- ✅ `/pages/api/recordBotMetrics.js` - ML metrics
- ✅ `/pages/api/getBotMetrics.js` - Get metrics

**Server Library**:
- ✅ `/lib/serverAppwriteClient.js` - Server-side secure client

---

### 📋 Still Needed

**Pages** (UI Components):
- ⚠️ `/pages/index.js` - Landing page
- ⚠️ `/pages/dashboard.js` - Dashboard (displays transactions)
- ⚠️ `/pages/watchlist.js` - Watchlist management
- ⚠️ `/pages/payments.js` - Payment form
- ⚠️ `/pages/metrics.js` - Bot metrics visualization

**Additional API Routes**:
- ⚠️ `/pages/api/getTransactions.js` - Fetch transactions
- ⚠️ `/pages/api/addToWatchlist.js` - Add to watchlist
- ⚠️ `/pages/api/removeFromWatchlist.js` - Remove from watchlist
- ⚠️ `/pages/api/getMetrics.js` - Get bot metrics
- ⚠️ `/pages/api/getMetricStats.js` - Get metrics stats

**Components** (Reusable UI):
- ⚠️ `/components/DashboardTable.jsx` - Transaction table
- ⚠️ `/components/WatchlistTable.jsx` - Watchlist table
- ⚠️ `/components/PaymentForm.jsx` - Payment input form
- ⚠️ `/components/MetricsChart.jsx` - Metrics visualization

---

## 🔄 Data Flow Architecture

```
User Interaction
    ↓
UI Component (React)
    ├─ /pages/dashboard.js
    ├─ /pages/watchlist.js
    ├─ /pages/payments.js
    └─ /pages/metrics.js
    ↓
Client-side Library
    └─ lib/appwriteClient.js
    ↓
Browser → API Route
    ↓
API Route Handler (Next.js)
    ├─ /pages/api/getTransactions.js
    ├─ /pages/api/addToWatchlist.js
    ├─ /pages/api/createPayment.js
    ├─ /pages/api/getMetrics.js
    └─ /pages/api/getMetricStats.js
    ↓
Server Library (with API key)
    └─ lib/serverAppwriteClient.js
    ↓
Appwrite Function
    ↓
Database Response
    ↓
Back to UI (JSON data)
    ↓
Reusable Components
    ├─ /components/DashboardTable.jsx
    ├─ /components/WatchlistTable.jsx
    ├─ /components/PaymentForm.jsx
    └─ /components/MetricsChart.jsx
    ↓
User sees results
```

---

## 📝 Wire-Up Pattern

Each page follows this pattern:

```javascript
// pages/dashboard.js (Example)
import { useState, useEffect } from 'react';
import DashboardTable from '@/components/DashboardTable';

export default function Dashboard() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Call API route (NOT Appwrite directly)
    fetch('/api/getTransactions?user_id=YOUR_USER_ID')
      .then(r => r.json())
      .then(data => {
        setTransactions(data.data);
        setLoading(false);
      });
  }, []);

  return (
    <div>
      <h1>Dashboard</h1>
      {loading ? <p>Loading...</p> : <DashboardTable data={transactions} />}
    </div>
  );
}
```

API routes call server library:

```javascript
// pages/api/getTransactions.js
import { getTransactionsSecure } from '@/lib/serverAppwriteClient';

export default async function handler(req, res) {
  try {
    const { user_id } = req.query;
    const transactions = await getTransactionsSecure(user_id);
    res.status(200).json({ success: true, data: transactions });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}
```

---

## 🎯 Implementation Priority

### Phase 1: Core Pages (Essential)
1. ✅ Dashboard page (displays transactions)
2. ✅ Metrics page (displays ML results)
3. ✅ Payments page (create payments)

### Phase 2: Supporting Pages
4. Watchlist page (manage watchlist)
5. Landing/Home page

### Phase 3: Components (Reusable)
6. DashboardTable component
7. MetricsChart component
8. PaymentForm component
9. WatchlistTable component

### Phase 4: Additional API Routes
10. getTransactions.js
11. getMetrics.js / getMetricStats.js
12. Watchlist routes

---

## 🔐 Security Boundary

```
BROWSER (Public)
├─ /pages/dashboard.js (client-side)
├─ /pages/watchlist.js (client-side)
├─ /pages/payments.js (client-side)
└─ /components/* (client-side)
        ↓ HTTP Request
NEXT.JS SERVER (Private - API Key Protected)
├─ /pages/api/*.js (server-side)
└─ /lib/serverAppwriteClient.js (APPWRITE_API_KEY used here)
        ↓ Secure Call (with API key)
APPWRITE (Backend)
```

**Key Rule**: Never use API key in browser. Only in `/pages/api/` routes!

---

## 📦 Package Dependencies

Make sure your `package.json` has:

```json
{
  "dependencies": {
    "react": "^18.0.0",
    "next": "^13.0.0",
    "node-appwrite": "^14.1.0"
  }
}
```

---

## 🚀 Getting Started

1. **Create pages/** directory structure
2. **Create components/** directory with reusable components
3. **Wire pages to API routes** (shown in pattern above)
4. **Test each page** before moving to next
5. **Deploy** to Vercel

---

## 💡 Example: Dashboard Page to Metrics Page

```
User clicks "Dashboard" button
    ↓
/pages/dashboard.js loads
    ↓
useEffect calls fetch('/api/getTransactions?user_id=123')
    ↓
/pages/api/getTransactions.js receives request
    ↓
Calls serverAppwriteClient.getTransactionsSecure()
    ↓
Sends APPWRITE_API_KEY to Appwrite Function
    ↓
Returns transaction data
    ↓
DashboardTable component displays data
    ↓
User clicks "View Metrics"
    ↓
/pages/metrics.js loads
    ↓
Calls fetch('/api/getMetrics?user_id=123')
    ↓
Same pattern: API route → server library → Appwrite
    ↓
MetricsChart component displays results
```

---

## ✅ Checklist for Full Implementation

### Pages to Create
- [ ] `/pages/index.js` - Landing page
- [ ] `/pages/dashboard.js` - Transactions
- [ ] `/pages/watchlist.js` - Watchlist
- [ ] `/pages/payments.js` - Payments
- [ ] `/pages/metrics.js` - Bot metrics

### Components to Create
- [ ] `/components/DashboardTable.jsx` - Transaction table
- [ ] `/components/WatchlistTable.jsx` - Watchlist table
- [ ] `/components/PaymentForm.jsx` - Payment form
- [ ] `/components/MetricsChart.jsx` - Metrics chart

### API Routes to Create/Verify
- [ ] `/pages/api/getTransactions.js`
- [ ] `/pages/api/addToWatchlist.js`
- [ ] `/pages/api/removeFromWatchlist.js`
- [ ] `/pages/api/getMetrics.js`
- [ ] `/pages/api/getMetricStats.js`
- ✅ `/pages/api/createPayment.js` (already created)
- ✅ `/pages/api/recordBotMetrics.js` (already created)

### Environment Setup
- [ ] `.env.local` configured
- [ ] `package.json` updated
- [ ] `next.config.js` created (if needed)

---

## 🎨 Component Structure Example

```javascript
// /components/DashboardTable.jsx
export default function DashboardTable({ data }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Quantity</th>
          <th>Price</th>
          <th>Total</th>
          <th>Type</th>
          <th>Date</th>
        </tr>
      </thead>
      <tbody>
        {data.map(transaction => (
          <tr key={transaction.id}>
            <td>{transaction.symbol}</td>
            <td>{transaction.quantity}</td>
            <td>${transaction.price}</td>
            <td>${(transaction.quantity * transaction.price).toFixed(2)}</td>
            <td>{transaction.type}</td>
            <td>{new Date(transaction.transaction_date).toLocaleDateString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

---

## 🌐 Routing Map

| URL | Page | Component | API Route | Data Source |
|-----|------|-----------|-----------|-------------|
| `/` | `index.js` | - | - | Static |
| `/dashboard` | `dashboard.js` | `DashboardTable` | `/api/getTransactions` | Appwrite |
| `/watchlist` | `watchlist.js` | `WatchlistTable` | `/api/getWatchlist` | Appwrite |
| `/payments` | `payments.js` | `PaymentForm` | `/api/createPayment` | Appwrite |
| `/metrics` | `metrics.js` | `MetricsChart` | `/api/getMetrics` | Appwrite |

---

## 📚 Reference

- **Appwrite Docs**: https://appwrite.io/docs
- **Next.js Docs**: https://nextjs.org/docs
- **React Hooks**: https://react.dev/reference/react/hooks

---

**Status**: Architecture defined, ready for implementation!
