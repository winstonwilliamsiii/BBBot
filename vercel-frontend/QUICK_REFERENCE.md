# 🚀 Quick Reference Card - BentleyBudgetBot Frontend

## Pages & Routes

| URL | Purpose | Component |
|-----|---------|-----------|
| `/` | Landing page | index.js |
| `/dashboard` | Transactions | dashboard.js + DashboardTable |
| `/watchlist` | Stock tracking | watchlist.js + WatchlistTable |
| `/payments` | Create payments | payments.js + PaymentForm |
| `/metrics` | ML results | metrics.js + MetricsChart |

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health` | Check system status |
| GET | `/api/getTransactions` | Fetch transactions |
| POST | `/api/createTransaction` | Record trade |
| POST | `/api/createPayment` | Create payment |
| GET | `/api/getMetrics` | Fetch metrics |
| POST | `/api/recordBotMetrics` | Store ML results |
| GET | `/api/getMetricStats` | Metrics stats |
| POST | `/api/addToWatchlist` | Add stock |
| POST | `/api/removeFromWatchlist` | Remove stock |
| POST | `/api/auditLog` | Audit logging |

## One-Minute Setup

```bash
# 1. Copy config template
cp .env.local.example .env.local

# 2. Edit .env.local with your credentials
# NEXT_PUBLIC_APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
# NEXT_PUBLIC_APPWRITE_PROJECT_ID=your_id
# APPWRITE_API_KEY=your_key

# 3. Start development
npm install
npm run dev

# 4. Open http://localhost:3000
```

## Quick API Test

```bash
# Health check
curl https://your-domain.com/api/health

# Create transaction
curl -X POST https://your-domain.com/api/createTransaction \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","symbol":"AAPL","type":"buy","quantity":1,"price":150}'

# Record metrics
curl -X POST https://your-domain.com/api/recordBotMetrics \
  -H "Content-Type: application/json" \
  -d '{"bot_id":"bot1","metrics":{"accuracy":0.92},"status":"completed"}'
```

## Environment Variables

```env
# Required - Public
NEXT_PUBLIC_APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
NEXT_PUBLIC_APPWRITE_PROJECT_ID=your_project_id

# Required - Private (server-side only!)
APPWRITE_API_KEY=your_api_key

# Function IDs (from Appwrite Console)
APPWRITE_FUNCTION_ID_PAYMENTS=func_xxx
APPWRITE_FUNCTION_ID_TRANSACTIONS=func_xxx
# ... etc
```

## Deployment

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard
# APPWRITE_API_KEY should be marked as sensitive
```

## Component Props Reference

### DashboardTable
```javascript
<DashboardTable 
  transactions={[
    {
      symbol: "AAPL",
      type: "buy",      // or "sell"
      quantity: 10,
      price: 150.00,
      date: "2024-01-15"
    }
  ]}
/>
```

### MetricsChart
```javascript
<MetricsChart
  metric={{
    bot_id: "ml_bot",
    accuracy: 0.92,
    sharpe_ratio: 1.5,
    return_percentage: 12.5,
    status: "completed"
  }}
/>
```

### WatchlistTable
```javascript
<WatchlistTable
  items={[
    {
      symbol: "AAPL",
      price: 175.50,
      change: 2.50,
      percent_change: 1.44,
      notes: "Hold"
    }
  ]}
  onRemove={(symbol) => {}}
  onRefresh={() => {}}
/>
```

### PaymentForm
```javascript
<PaymentForm
  onSubmit={(payment) => {
    console.log("Payment created:", payment);
  }}
/>
```

## Common Tasks

### Add a New Page
1. Create `pages/new-page.js`
2. Export React component
3. Use API routes to fetch data
4. Add to navigation links

### Create New API Route
1. Create `pages/api/new-route.js`
2. Handle GET/POST method
3. Validate input
4. Call `serverAppwriteClient`
5. Return JSON response

### Use Appwrite Function
1. Create function in Appwrite Console
2. Note the function ID
3. Call from API route: `callAppwriteFunctionSecure(functionId, payload)`

### Debug Issues
```bash
# Check Node version
node --version  # Should be 14+

# Check dependencies
npm list

# Clear and reinstall
rm -rf node_modules package-lock.json
npm install

# Check environment
cat .env.local

# View logs
npm run dev  # See console output
```

## File Structure
```
vercel-frontend/
├── pages/
│   ├── index.js, dashboard.js, etc.
│   └── api/
│       ├── health.js, getTransactions.js, etc.
├── components/
│   ├── DashboardTable.jsx, MetricsChart.jsx, etc.
├── lib/
│   ├── appwriteClient.js (client-safe)
│   └── serverAppwriteClient.js (with API key)
├── .env.local.example  (copy → .env.local)
├── package.json
└── Documentation files
```

## Security Rules

✅ DO:
- Store APPWRITE_API_KEY in .env (server-side only)
- Validate all inputs in API routes
- Use serverAppwriteClient in API routes
- Log all user actions
- Return safe error messages

❌ DON'T:
- Expose API_KEY in client-side code
- Trust user input
- Send credentials in fetch requests
- Ignore errors
- Log sensitive data

## Troubleshooting

| Problem | Solution |
|---------|----------|
| 404 Page | Create file in pages/ directory |
| 500 API Error | Check APPWRITE_API_KEY, verify function exists |
| CORS Error | Check middleware, verify headers |
| Env var not found | Restart npm run dev after editing .env.local |
| Styling not working | Check styled-jsx is in components |
| Page blank | Check browser console for errors |

## Performance Tips

- Use React.memo for expensive components
- Implement pagination for large lists
- Cache API responses with SWR or React Query
- Optimize images with next/image
- Use lazy loading for routes

## Resources

- **Docs:** See COMPLETE_ARCHITECTURE.md
- **Setup:** See INTEGRATION_COMPLETE.md
- **Summary:** See COMPLETION_SUMMARY.md
- **Inventory:** See FILE_MANIFEST.md

---

**Status:** 🚀 PRODUCTION READY  
**Total Files:** 26 created  
**Deployment Target:** Vercel

Happy building! 🎉

