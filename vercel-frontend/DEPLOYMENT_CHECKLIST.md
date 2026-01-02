# Vercel Deployment Checklist & Configuration

## Environment Variables to Add to Vercel

Complete this checklist before deploying to production.

### 1. Connect to Vercel Dashboard
- [ ] Go to https://vercel.com/dashboard
- [ ] Import BentleyBudgetBot repository
- [ ] Set root directory to `vercel-frontend` (if using monorepo)

### 2. Add Environment Variables

Go to **Project Settings → Environment Variables** and add:

#### ✅ PUBLIC VARIABLES (Client-Side Safe)
```
Name: NEXT_PUBLIC_APPWRITE_ENDPOINT
Value: https://cloud.appwrite.io/v1

Name: NEXT_PUBLIC_APPWRITE_PROJECT_ID
Value: 68869ef500017ca73772

Name: NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_TRANSACTION
Value: 694db02c58495b52f6e6

Name: NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_TRANSACTIONS
Value: 694daffaae8121bb7837

Name: NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_PAYMENT
Value: 694dab48338627afc96a

Name: NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_PAYMENTS
Value: 694daddc3fed56721c52

Name: NEXT_PUBLIC_APPWRITE_FUNCTION_ID_ADD_WATCHLIST
Value: 694da7003804de8bb29a

Name: NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_WATCHLIST
Value: 694da75bd55dc6d65fb9

Name: NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_USER_PROFILE
Value: 694da7aedf6018cc8266

Name: NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_AUDIT_LOG
Value: 694dab48338627afc96a

Name: NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_AUDIT_LOGS
Value: 694daaad91f3b1b6d68c

Name: NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_BOT_METRIC
Value: 694dadc18bd08f7a3895

Name: NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_BOT_METRICS
Value: 694dadba22d1eeada62d

Name: NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_BOT_METRICS_STATS
Value: 694dada2b9c2ddef7c56
```

#### ✅ PRIVATE VARIABLES (Server-Side Only - KEEP SECRET!)
```
Name: APPWRITE_API_KEY
Value: [Copy from Appwrite Console → Settings → API Keys]
Note: This should be your server API key with full permissions

Name: APPWRITE_DATABASE_ID
Value: 6944821e4f5f5f4f7d10
```

### 3. Verify Environment Variables
- [ ] All NEXT_PUBLIC_* variables are set
- [ ] APPWRITE_API_KEY is set (not exposed in browser)
- [ ] Double-check function IDs are correct
- [ ] Use "Production" environment

### 4. Test Deployment
```bash
# After pushing to GitHub, verify deployment:
curl https://your-vercel-domain.com/api/health

# You should see:
# {
#   "status": "healthy",
#   "service": "bentley-budget-bot-vercel",
#   ...
# }
```

### 5. Test API Routes

#### Test Health Check
```bash
curl https://your-vercel-domain.com/api/health
```

#### Test Create Payment
```bash
curl -X POST https://your-vercel-domain.com/api/createPayment \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "amount": 100,
    "currency": "USD",
    "description": "Test payment",
    "payment_method": "credit_card"
  }'
```

#### Test Record Bot Metrics
```bash
curl -X POST https://your-vercel-domain.com/api/recordBotMetrics \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "bot_id": "test-bot",
    "experiment_id": "exp_test_001",
    "metrics": {
      "accuracy": 0.92,
      "sharpe_ratio": 1.5,
      "win_rate": 0.7
    },
    "data_source": "yfinance",
    "status": "completed"
  }'
```

### 6. Security Verification
- [ ] APPWRITE_API_KEY is NOT visible in browser DevTools
- [ ] Check Network tab - sensitive data isn't logged
- [ ] Verify audit logs are being created
- [ ] Test that invalid requests are rejected

### 7. Monitoring & Logs
- [ ] Check Vercel Deployments tab for any errors
- [ ] Monitor function execution in Appwrite Console
- [ ] Set up optional: Sentry for error tracking
- [ ] Set up optional: Analytics for usage tracking

### 8. CI/CD Configuration (Optional)

If you want automatic tests before deployment:

Create `.github/workflows/vercel-tests.yml`:
```yaml
name: Vercel Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Use Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: npm install
      working-directory: ./vercel-frontend
    
    - name: Run tests
      run: npm test
      working-directory: ./vercel-frontend
      env:
        NEXT_PUBLIC_APPWRITE_ENDPOINT: ${{ secrets.APPWRITE_ENDPOINT }}
        NEXT_PUBLIC_APPWRITE_PROJECT_ID: ${{ secrets.APPWRITE_PROJECT_ID }}
```

## Files Created/Modified

✅ **Client Libraries**
- `/lib/appwriteClient.js` - Client-side calls (browser-safe)
- `/lib/serverAppwriteClient.js` - Server-side secure client

✅ **API Routes** (All in `/pages/api/`)
- `createPayment.js` - POST payment creation with audit logging
- `createTransaction.js` - POST transaction creation with validation
- `recordBotMetrics.js` - POST ML metrics recording (your ML experiments!)
- `getBotMetrics.js` - GET metrics with optional stats
- `auditLog.js` - POST/GET audit logging
- `health.js` - GET health check endpoint
- `_middleware.js` - Security headers (optional)

✅ **Documentation**
- `VERCEL_SETUP_GUIDE.md` - Comprehensive setup guide
- `INTEGRATION_EXAMPLES.js` - Code examples for integration
- `DEPLOYMENT_CHECKLIST.md` - This file!

✅ **Configuration**
- `.env.local.example` - Environment variable template

## Quick Start Command

1. **Deploy to Vercel** (if using Git)
```bash
git add .
git commit -m "Add Vercel frontend with secure API routes"
git push origin main
```

Vercel will auto-deploy!

2. **Or Deploy Manually**
```bash
npm install -g vercel
cd vercel-frontend
vercel --prod
```

3. **Set Environment Variables in Dashboard**
- Go to Project Settings
- Add all environment variables from checklist above

## Common Issues & Solutions

### Issue: 401 Unauthorized on API routes
**Solution**: Verify APPWRITE_API_KEY is set in Vercel environment variables (not in .env.local)

### Issue: Function not found (404)
**Solution**: Check function IDs match your Appwrite deployment. Copy from:
https://cloud.appwrite.io/console/project-68869ef500017ca73772/functions

### Issue: CORS errors
**Solution**: Shouldn't happen with server-side routes. If using browser client directly, check Appwrite CORS in console.

### Issue: Data not being audited
**Solution**: Verify NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_AUDIT_LOG is set correctly

### Issue: Bot metrics not recording
**Solution**: Ensure your Python/Node.js script sends correct format to /api/recordBotMetrics

## Production Best Practices

1. **Enable Vercel Analytics** - Monitor API performance
2. **Use Environment Secrets** - Never commit .env files
3. **Enable Edge Runtime** (Optional) - For lower latency
4. **Set up Error Tracking** - Sentry integration
5. **Monitor Function Execution** - Watch Appwrite Console
6. **Rotate API Keys** - Update APPWRITE_API_KEY periodically
7. **Enable Request Logging** - For debugging
8. **Set up Alerts** - For failed requests or errors

## Next Steps After Deployment

### 1. Test ML Integration
- Run your Python ML training scripts
- Send metrics to `/api/recordBotMetrics`
- View metrics in dashboard

### 2. Create Frontend Dashboards
- Build components using React/Vue to display metrics
- Use `/api/getBotMetrics` to fetch experiment results
- Create charts/graphs for visualization

### 3. Set Up Continuous Monitoring
- Monitor bot performance over time
- Track experiment results
- Compare different model versions

### 4. Integrate with Your Pipeline
- Python ML scripts → POST to `/api/recordBotMetrics`
- yfinance data → Store via transactions
- Results → Visualize in dashboard

## Support URLs

- **Vercel Docs**: https://vercel.com/docs
- **Appwrite Docs**: https://appwrite.io/docs
- **Next.js Docs**: https://nextjs.org/docs
- **Your Project**: https://cloud.appwrite.io/console/project-68869ef500017ca73772

---

**Last Updated**: January 1, 2026
**Status**: Ready for deployment ✅
