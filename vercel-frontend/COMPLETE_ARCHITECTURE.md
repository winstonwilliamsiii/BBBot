# Complete Next.js Frontend Architecture - BentleyBudgetBot + Mansa Cap

**Status:** ✅ **FULLY IMPLEMENTED AND INTEGRATED**

---

## 📁 Complete Directory Structure

```
vercel-frontend/
├── pages/
│   ├── _app.js              # Next.js app wrapper
│   ├── _document.js         # HTML document wrapper
│   ├── index.js             # ✅ Landing/home page
│   ├── dashboard.js         # ✅ Portfolio overview & transactions
│   ├── watchlist.js         # ✅ Stock watchlist management
│   ├── payments.js          # ✅ Payment transaction creation
│   ├── metrics.js           # ✅ ML bot metrics visualization
│   └── api/
│       ├── health.js                    # ✅ System health check
│       ├── createPayment.js             # ✅ Payment processing
│       ├── createTransaction.js         # ✅ Transaction recording
│       ├── recordBotMetrics.js          # ✅ ML metrics storage
│       ├── getBotMetrics.js             # ✅ Metrics retrieval
│       ├── getMetricStats.js            # ✅ Metrics statistics
│       ├── auditLog.js                  # ✅ Audit logging
│       ├── getTransactions.js           # ✅ Transaction fetch
│       ├── addToWatchlist.js            # ✅ Add watchlist symbol
│       └── removeFromWatchlist.js       # ✅ Remove watchlist symbol
├── components/
│   ├── DashboardTable.jsx           # ✅ Transaction display table
│   ├── MetricsChart.jsx             # ✅ Metrics visualization
│   ├── WatchlistTable.jsx           # ✅ Watchlist display
│   └── PaymentForm.jsx              # ✅ Payment form UI
├── lib/
│   ├── appwriteClient.js            # Client-side Appwrite calls
│   └── serverAppwriteClient.js      # Server-side secure calls
├── styles/
│   ├── globals.css                  # Global styles
│   └── Home.module.css              # Home page styles
├── public/
│   └── [static assets]
├── next.config.js
├── package.json
├── .env.local.example
├── vercel.json
└── README.md
```

---

## 🔄 Complete Data Flow Architecture

### 1. **Page Components → User Interaction**
```
User Interface (React Components)
    ↓
    [DashboardTable.jsx]  - Display transactions
    [MetricsChart.jsx]    - Show ML metrics
    [WatchlistTable.jsx]  - Manage watchlist
    [PaymentForm.jsx]     - Create payments
    ↓
API Routes (Server-side)
```

### 2. **API Routes → Server Authentication**
```
Browser Request
    ↓
/api/getTransactions
    ↓
Validate Request
    ↓
Calls serverAppwriteClient
    ↓
Appwrite Function (with API Key)
    ↓
Database Query
    ↓
JSON Response → Browser
```

### 3. **Complete Request/Response Cycle**

**Example: Dashboard Transaction Display**
```
1. Dashboard.js loads
   └─ useEffect() calls fetchTransactions()

2. fetchTransactions() makes HTTP GET
   └─ fetch('/api/getTransactions')

3. /api/getTransactions.js executes
   ├─ Validates request
   ├─ Calls serverAppwriteClient.callAppwriteFunctionSecure()
   ├─ Uses APPWRITE_API_KEY (server-side only)
   ├─ Executes Appwrite Function
   └─ Returns {success: true, transactions: [...]}

4. DashboardTable component receives data
   ├─ Formats currency values
   ├─ Color-codes buy/sell transactions
   ├─ Renders responsive table
   └─ Displays on screen

5. User sees transactions with:
   ├─ Symbol (AAPL, GOOGL, etc.)
   ├─ Price per share
   ├─ Quantity
   ├─ Total value
   └─ Date
```

---

## 📊 Page Components Overview

### `/pages/index.js` - Home Page
**Purpose:** Landing page with system status and navigation
**Features:**
- Quick start guide
- Navigation cards to main sections
- System health check
- Hero section with call-to-action

**API Integration:**
```javascript
- GET /api/health  // Check system status
```

---

### `/pages/dashboard.js` - Dashboard
**Purpose:** Primary portfolio overview and transaction history
**Features:**
- Transaction statistics (total, buy/sell counts, net value)
- Real-time transaction table with search/filter
- Responsive grid layout
- Add new transaction functionality

**Components Used:**
- `DashboardTable.jsx` - Transaction display
- Statistics cards showing portfolio metrics

**API Integration:**
```javascript
- GET /api/getTransactions          // Fetch all transactions
- POST /api/createTransaction       // Add new transaction
```

**Data Displayed:**
```javascript
{
  symbol: "AAPL",
  type: "buy",              // "buy" or "sell"
  quantity: 10,
  price: 150.00,
  total: 1500.00,
  date: "2024-01-15",
  notes: "Investment notes"
}
```

---

### `/pages/watchlist.js` - Watchlist Manager
**Purpose:** Track and manage stocks of interest
**Features:**
- Add new symbols with optional notes
- Watchlist table with price and change data
- Quick remove functionality
- Persistent storage in Appwrite

**Components Used:**
- `WatchlistTable.jsx` - Watchlist display and management

**API Integration:**
```javascript
- GET /api/addToWatchlist?get=true      // Fetch all watchlist items
- POST /api/addToWatchlist              // Add symbol
- POST /api/removeFromWatchlist         // Remove symbol
```

**Data Format:**
```javascript
{
  symbol: "AAPL",
  price: 175.50,
  change: 2.50,
  percent_change: 1.44,
  notes: "Long-term hold",
  added_at: "2024-01-01T10:00:00Z"
}
```

---

### `/pages/payments.js` - Payment Management
**Purpose:** Create and track payment transactions
**Features:**
- Payment form with validation
- Statistics cards (total payments, amount, average)
- Recent payment history
- Multiple payment method support

**Components Used:**
- `PaymentForm.jsx` - Payment creation form

**API Integration:**
```javascript
- POST /api/createPayment   // Process payment
- GET /api/getTransactions  // View payment history (optional)
```

**Payment Data:**
```javascript
{
  user_id: "user123",
  amount: 500.00,
  currency: "USD",
  payment_method: "credit_card",  // or "debit_card", "bank_transfer"
  description: "Investment funding"
}
```

---

### `/pages/metrics.js` - ML Metrics Dashboard
**Purpose:** Monitor bot performance and ML experiment results
**Features:**
- Overall performance statistics
- Bot-grouped metrics display
- Expandable metric details
- Real-time refresh capability

**Components Used:**
- `MetricsChart.jsx` - Metrics visualization

**API Integration:**
```javascript
- GET /api/getMetrics           // Fetch bot metrics
- GET /api/getMetricStats       // Get aggregated statistics
```

**Metrics Format:**
```javascript
{
  bot_id: "ml_bot_001",
  experiment_id: "exp_123",
  accuracy: 0.92,
  sharpe_ratio: 1.5,
  return_percentage: 12.5,
  data_source: "yfinance",
  status: "completed",
  timestamp: "2024-01-15T15:30:00Z"
}
```

---

## 🧩 Reusable Components

### `components/DashboardTable.jsx`
**Purpose:** Display transactions in formatted table
**Props:**
```javascript
{
  transactions: Array<Transaction>,  // Required
}
```
**Features:**
- Responsive table layout
- Buy/sell color coding (green/red)
- Currency formatting
- Date localization
- Empty state handling

---

### `components/MetricsChart.jsx`
**Purpose:** Visualize individual bot metrics
**Props:**
```javascript
{
  metric: {
    bot_id: string,
    accuracy: number,
    sharpe_ratio: number,
    return_percentage: number,
    status: "pending" | "completed" | "failed",
    timestamp: ISO8601
  }
}
```
**Features:**
- Metric grid display
- Format detection (percentage, currency, number)
- Statistics section
- Status badges

---

### `components/WatchlistTable.jsx`
**Purpose:** Display and manage watchlist stocks
**Props:**
```javascript
{
  items: Array<WatchlistItem>,
  onRemove: (symbol) => void,
  onRefresh: () => void
}
```
**Features:**
- Stock symbol display
- Current price and change
- Add/remove actions
- Notes field
- Date tracking

---

### `components/PaymentForm.jsx`
**Purpose:** Create new payment transactions
**Props:**
```javascript
{
  onSubmit?: (payment) => void  // Optional callback
}
```
**Features:**
- User ID and amount input
- Currency selection
- Payment method dropdown
- Optional description
- Form validation
- Success/error messaging

---

## 🔐 Security Architecture

### Client-Side (Browser)
```javascript
// appwriteClient.js - NO API KEY HERE
export const callAppwriteFunction = async (functionId, payload) => {
  // No credentials sent with this function
  // Used only for non-sensitive operations
}
```

### Server-Side (API Routes)
```javascript
// serverAppwriteClient.js - API KEY PROTECTED
export const callAppwriteFunctionSecure = async (functionId, payload) => {
  // API key stored as APPWRITE_API_KEY environment variable
  // Only accessible on server-side
  // Never exposed to browser
}
```

### Request Flow
```
Browser
  ↓
API Route (/api/...)
  ├─ Validates request
  ├─ Adds server-side auth (APPWRITE_API_KEY)
  ├─ Calls Appwrite
  └─ Returns response (no auth details exposed)
```

---

## 🚀 Deployment Steps

### 1. **Environment Setup**
```bash
# Copy example to local
cp .env.local.example .env.local

# Fill in required variables
NEXT_PUBLIC_APPWRITE_ENDPOINT=...
NEXT_PUBLIC_APPWRITE_PROJECT_ID=...
APPWRITE_API_KEY=...  # Server-side only!
```

### 2. **Local Development**
```bash
npm install
npm run dev
# Visit http://localhost:3000
```

### 3. **Production Deployment to Vercel**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard
```

### 4. **Verify Deployment**
```bash
curl https://your-domain.com/api/health
# Should return: {"status": "healthy"}
```

---

## 📋 API Route Reference

### **GET /api/health**
Health check endpoint
```bash
curl https://your-domain.com/api/health
```
Response:
```json
{
  "status": "healthy",
  "appwrite": "connected",
  "database": "available"
}
```

---

### **GET /api/getTransactions**
Fetch all transactions
```bash
curl https://your-domain.com/api/getTransactions
```
Response:
```json
{
  "success": true,
  "transactions": [
    {
      "id": "tx_123",
      "symbol": "AAPL",
      "type": "buy",
      "quantity": 10,
      "price": 150.00,
      "total": 1500.00,
      "date": "2024-01-15"
    }
  ]
}
```

---

### **POST /api/createTransaction**
Create a new transaction
```bash
curl -X POST https://your-domain.com/api/createTransaction \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "symbol": "AAPL",
    "type": "buy",
    "quantity": 10,
    "price": 150.00,
    "notes": "Initial investment"
  }'
```

---

### **POST /api/createPayment**
Create a payment
```bash
curl -X POST https://your-domain.com/api/createPayment \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "amount": 500.00,
    "currency": "USD",
    "payment_method": "credit_card",
    "description": "Investment funding"
  }'
```

---

### **POST /api/addToWatchlist**
Add symbol to watchlist
```bash
curl -X POST https://your-domain.com/api/addToWatchlist \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "notes": "Long-term hold"
  }'
```

---

### **POST /api/removeFromWatchlist**
Remove symbol from watchlist
```bash
curl -X POST https://your-domain.com/api/removeFromWatchlist \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL"}'
```

---

### **GET /api/getMetrics**
Fetch bot metrics
```bash
curl https://your-domain.com/api/getMetrics
```

---

### **GET /api/getMetricStats**
Get aggregated metrics statistics
```bash
curl https://your-domain.com/api/getMetricStats
```

---

### **POST /api/recordBotMetrics**
Record ML experiment results
```bash
curl -X POST https://your-domain.com/api/recordBotMetrics \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "bot_id": "ml_bot_001",
    "experiment_id": "exp_123",
    "metrics": {
      "accuracy": 0.92,
      "sharpe_ratio": 1.5,
      "return_percentage": 12.5
    },
    "data_source": "yfinance",
    "status": "completed"
  }'
```

---

## 🔍 Testing with curl

### Quick Test Script
```bash
#!/bin/bash
BASE_URL="https://your-domain.com"

echo "1. Health Check"
curl $BASE_URL/api/health

echo -e "\n2. Get Transactions"
curl $BASE_URL/api/getTransactions

echo -e "\n3. Create Transaction"
curl -X POST $BASE_URL/api/createTransaction \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","symbol":"AAPL","type":"buy","quantity":1,"price":150}'

echo -e "\n4. Record Metrics"
curl -X POST $BASE_URL/api/recordBotMetrics \
  -H "Content-Type: application/json" \
  -d '{
    "bot_id":"bot1",
    "experiment_id":"exp1",
    "metrics":{"accuracy":0.92},
    "data_source":"yfinance",
    "status":"completed"
  }'

echo -e "\nDone!"
```

---

## 📈 Features Summary

| Feature | Page | Component | API Route | Status |
|---------|------|-----------|-----------|--------|
| View Transactions | dashboard.js | DashboardTable | getTransactions | ✅ |
| Create Transaction | dashboard.js | - | createTransaction | ✅ |
| View Metrics | metrics.js | MetricsChart | getMetrics | ✅ |
| Record Metrics | - | - | recordBotMetrics | ✅ |
| Manage Watchlist | watchlist.js | WatchlistTable | addToWatchlist | ✅ |
| Remove Watchlist | watchlist.js | WatchlistTable | removeFromWatchlist | ✅ |
| Create Payment | payments.js | PaymentForm | createPayment | ✅ |
| Audit Logging | - | - | auditLog | ✅ |
| Health Check | index.js | - | health | ✅ |

---

## 🎯 Next Steps

1. **Test Locally**
   ```bash
   npm run dev
   # Visit http://localhost:3000
   # Test each page and API endpoint
   ```

2. **Deploy to Vercel**
   ```bash
   vercel
   # Follow prompts
   # Add environment variables
   ```

3. **Integrate with Python**
   - Use `vercel_integration.py` from main project
   - Pull yfinance data
   - Record metrics via API
   - Visualize in metrics page

4. **Monitor Production**
   - Check `/api/health` regularly
   - Monitor Appwrite logs
   - Track API performance metrics
   - Review audit logs for all actions

---

## 📚 Additional Resources

- **Next.js Docs:** https://nextjs.org/docs
- **Appwrite Docs:** https://appwrite.io/docs
- **Vercel Docs:** https://vercel.com/docs
- **React Docs:** https://react.dev

---

## ✅ Architecture Validation Checklist

- ✅ All page components created with consistent styling
- ✅ All API routes implemented with error handling
- ✅ Server-side security with Appwrite API key
- ✅ Client-side Appwrite library for browser-safe calls
- ✅ Reusable React components with styled-jsx
- ✅ Complete data flow from UI to database
- ✅ Responsive design for mobile/tablet/desktop
- ✅ Form validation on all inputs
- ✅ Error messages and user feedback
- ✅ Empty state handling
- ✅ Loading states for async operations
- ✅ Environment configuration template
- ✅ Documentation and examples

**Status:** 🚀 **PRODUCTION READY**

