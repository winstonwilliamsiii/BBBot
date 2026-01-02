# Vercel Frontend Integration Setup Guide

## Overview
This guide walks you through setting up the Node.js/Next.js Vercel frontend to securely call Appwrite Functions and enable ML experiments, metrics tracking, and data visualization.

## Architecture

```
Vercel Frontend (Next.js)
    ↓
/pages/api/* (Secure API Routes)
    ↓
Appwrite Functions
    ↓
yfinance / MySQL / Appwrite Database
```

## Quick Start

### 1. Environment Variables Setup

Copy this to your Vercel Dashboard or `.env.local`:

#### PUBLIC Variables (Client-side, safe to expose):
```env
NEXT_PUBLIC_APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
NEXT_PUBLIC_APPWRITE_PROJECT_ID=68869ef500017ca73772

# Function IDs for client-side calls
NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_TRANSACTIONS=694daffaae8121bb7837
NEXT_PUBLIC_APPWRITE_FUNCTION_ID_ADD_WATCHLIST=694da7003804de8bb29a
NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_WATCHLIST=694da75bd55dc6d65fb9
NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_USER_PROFILE=694da7aedf6018cc8266
NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_TRANSACTION=694db02c58495b52f6e6
NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_PAYMENT=694dab48338627afc96a
NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_PAYMENTS=694daddc3fed56721c52
NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_AUDIT_LOG=694dab48338627afc96a
NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_AUDIT_LOGS=694daaad91f3b1b6d68c
NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_BOT_METRIC=694dadc18bd08f7a3895
NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_BOT_METRICS=694dadba22d1eeada62d
NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_BOT_METRICS_STATS=694dada2b9c2ddef7c56
```

#### PRIVATE Variables (Server-side only, keep secret):
```env
# From: https://cloud.appwrite.io/console/project-68869ef500017ca73772/settings/api-keys
APPWRITE_API_KEY=your_server_api_key_here
APPWRITE_DATABASE_ID=6944821e4f5f5f4f7d10

# Optional: Direct database access
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=mansa_bot
```

### 2. Vercel Deployment Steps

1. **Connect Repository**
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Import your GitHub repository
   - Select `vercel-frontend` as root directory (if using monorepo)

2. **Add Environment Variables**
   - Project Settings → Environment Variables
   - Add all PUBLIC variables (marked with `NEXT_PUBLIC_`)
   - Add all PRIVATE variables (these won't be exposed to browser)

3. **Deploy**
   - Vercel auto-deploys on git push
   - Check deployment logs for errors

## API Routes

All API routes are in `/pages/api/` and use server-side authentication.

### POST /api/createPayment
Create a payment transaction
```javascript
const response = await fetch('/api/createPayment', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user123',
    amount: 100.50,
    currency: 'USD',
    description: 'Stock purchase',
    payment_method: 'credit_card'
  })
});
const result = await response.json();
```

### POST /api/createTransaction
Record a stock transaction
```javascript
await fetch('/api/createTransaction', {
  method: 'POST',
  body: JSON.stringify({
    user_id: 'user123',
    symbol: 'AAPL',
    quantity: 10,
    price: 150.00,
    type: 'buy', // or 'sell'
    transaction_date: '2026-01-01T10:00:00Z'
  })
});
```

### POST /api/recordBotMetrics
Record ML experiment metrics (for your ML experiments!)
```javascript
await fetch('/api/recordBotMetrics', {
  method: 'POST',
  body: JSON.stringify({
    user_id: 'user123',
    bot_id: 'bot_trading_v1',
    experiment_id: 'exp_ml_test_001',
    metrics: {
      accuracy: 0.95,
      sharpe_ratio: 1.23,
      max_drawdown: -0.15,
      total_return: 0.25,
      win_rate: 0.62,
      trades_executed: 45
    },
    data_source: 'yfinance', // yfinance, mysql, or appwrite
    status: 'completed',
    notes: 'Test run with new ML model'
  })
});
```

### GET /api/getBotMetrics
Retrieve bot metrics for visualization
```javascript
const response = await fetch('/api/getBotMetrics?user_id=user123&include_stats=true');
const data = await response.json();
```

### POST /api/auditLog
Create manual audit log entry
```javascript
await fetch('/api/auditLog', {
  method: 'POST',
  body: JSON.stringify({
    user_id: 'user123',
    action: 'RUN_ML_EXPERIMENT',
    entity_type: 'experiment',
    entity_id: 'exp_001',
    changes: { model: 'v2', parameters: 'updated' },
    details: 'Trained new model with updated parameters'
  })
});
```

### GET /api/health
Health check endpoint
```javascript
const response = await fetch('/api/health');
const status = await response.json();
```

## Client-Side Usage (Browser)

Use the client-side library for browser calls:

```javascript
import { 
  getTransactions, 
  addToWatchlist, 
  createPayment 
} from '@/lib/appwriteClient';

// Get transactions
const transactions = await getTransactions('user123', 10);

// Add to watchlist
await addToWatchlist('user123', 'TSLA', 'Growth stock');

// Create payment (uses browser-side client)
await createPayment({
  user_id: 'user123',
  amount: 500,
  currency: 'USD',
  payment_method: 'debit_card'
});
```

## Server-Side Usage (API Routes)

For secure operations, use server-side client:

```javascript
import { createPaymentSecure, createBotMetricsSecure } from '@/lib/serverAppwriteClient';

// These use APPWRITE_API_KEY (server-side only)
const payment = await createPaymentSecure({...});
const metrics = await createBotMetricsSecure({...});
```

## ML Experiments Workflow

### 1. Run ML Experiment (Python)
```python
import requests

# Your ML model runs and generates metrics
metrics = {
    "accuracy": 0.92,
    "sharpe_ratio": 1.45,
    "max_drawdown": -0.12,
    "total_return": 0.32,
    "win_rate": 0.68,
    "trades_executed": 52
}

# Send to Vercel API
response = requests.post(
    "https://your-vercel-domain.com/api/recordBotMetrics",
    json={
        "user_id": "user123",
        "bot_id": "ml_bot_v2",
        "experiment_id": f"exp_{int(time.time())}",
        "metrics": metrics,
        "data_source": "yfinance",
        "status": "completed",
        "notes": "Tested strategy X with parameters Y"
    }
)
```

### 2. Visualize in Dashboard
```javascript
// Frontend dashboard component
const [metrics, setMetrics] = useState([]);

useEffect(() => {
  const loadMetrics = async () => {
    const response = await fetch('/api/getBotMetrics?user_id=user123&include_stats=true');
    const data = await response.json();
    setMetrics(data.data);
  };
  loadMetrics();
}, []);

// Display metrics in charts/tables
```

### 3. Automated Logging
All API routes automatically log:
- User ID
- Action taken
- Entity type and ID
- Changes made
- User IP
- Timestamp

## Security Features

✅ **Server-side API Key**: APPWRITE_API_KEY never exposed to browser
✅ **Input Validation**: All routes validate and sanitize input
✅ **Audit Logging**: Every action is logged with user IP and timestamp
✅ **Error Handling**: Detailed errors in development, safe messages in production
✅ **Environment Separation**: Public vs private variables clearly separated

## Troubleshooting

### 401 Unauthorized
- Check `APPWRITE_API_KEY` is set in Vercel
- Verify key has proper permissions in Appwrite console

### Function not found (404)
- Verify function IDs match your Appwrite deployment
- Check functions are deployed in Appwrite

### CORS errors
- This shouldn't happen with server-side API routes
- If using browser client directly, check Appwrite CORS settings

### Vercel deployment fails
- Check all NEXT_PUBLIC_* variables are set
- View deployment logs in Vercel dashboard

## Next Steps

1. ✅ Copy environment variables to Vercel
2. ✅ Deploy to Vercel
3. ✅ Test API routes with curl or Postman
4. ✅ Integrate into your ML pipeline
5. ✅ Create dashboards to visualize metrics

## Files Created

- `/lib/appwriteClient.js` - Client-side Appwrite client
- `/lib/serverAppwriteClient.js` - Server-side secure client
- `/pages/api/createPayment.js` - Payment creation
- `/pages/api/createTransaction.js` - Transaction creation
- `/pages/api/recordBotMetrics.js` - Metrics recording (for ML experiments!)
- `/pages/api/getBotMetrics.js` - Metrics retrieval
- `/pages/api/auditLog.js` - Audit logging
- `/pages/api/health.js` - Health check

## Support

For issues:
1. Check Vercel logs: Project → Deployments → View Logs
2. Check Appwrite console for function errors
3. Verify environment variables are correctly set
4. Test with curl: `curl https://your-domain.com/api/health`
