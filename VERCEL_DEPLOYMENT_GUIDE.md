# 🚀 Deploying BentleyBudgetBot to Vercel

## 📁 Project Structure

```
vercel-frontend/
├── lib/
│   └── appwriteClient.js      # Appwrite integration
├── pages/
│   └── dashboard.js            # Main dashboard page
├── .env.local.example          # Environment variables template
├── .env.local                  # Your actual env vars (gitignored)
├── package.json                # Dependencies
└── next.config.js              # Next.js configuration
```

## 🔧 Setup Steps

### 1. Create Next.js Project (if not exists)

```bash
cd vercel-frontend
npm init -y
npm install next react react-dom
```

### 2. Add Scripts to package.json

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  }
}
```

### 3. Configure Environment Variables

**Copy the example file:**
```bash
cp .env.local.example .env.local
```

**Your `.env.local` should have:**
```env
NEXT_PUBLIC_APPWRITE_ENDPOINT=https://fra.cloud.appwrite.io/v1
NEXT_PUBLIC_APPWRITE_PROJECT_ID=68869ef500017ca73772
NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_TRANSACTIONS=694c4dec8cb3c16cbaf4
NEXT_PUBLIC_APPWRITE_FUNCTION_ID_ADD_WATCHLIST=694c4dec8ad5bb43d8f8
NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_WATCHLIST=694c4dec8b2e8d2c8838
NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_USER_PROFILE=694c4dec8482e5af0a60
```

### 4. Test Locally

```bash
npm run dev
```

Visit: http://localhost:3000/dashboard

### 5. Deploy to Vercel

**Option A: Via Vercel CLI**
```bash
npm install -g vercel
vercel login
vercel --prod
```

**Option B: Via Vercel Dashboard**
1. Go to https://vercel.com
2. Import your GitHub repository
3. Add environment variables in Vercel Dashboard
4. Deploy!

## 🌐 Add Environment Variables to Vercel

In Vercel Dashboard:
1. Go to Project → Settings → Environment Variables
2. Add each variable from `.env.local`:
   - `NEXT_PUBLIC_APPWRITE_ENDPOINT`
   - `NEXT_PUBLIC_APPWRITE_PROJECT_ID`
   - `NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_TRANSACTIONS`
   - `NEXT_PUBLIC_APPWRITE_FUNCTION_ID_ADD_WATCHLIST`
   - `NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_WATCHLIST`
   - `NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_USER_PROFILE`
3. Set scope to: Production, Preview, Development
4. Click "Save"

## ✅ Verification

Once deployed, your apps will be at:
- **BentleyBudgetBot**: https://bentleybudgetbot.vercel.app
- **Mansa Cap**: https://mansacap.vercel.app

Test by:
1. Opening the dashboard
2. Clicking "Refresh" button
3. Should see either:
   - ✅ "No transactions yet" (database empty - expected!)
   - ✅ Transaction data (if you added sample data)
   - ❌ Error message (then we debug)

## 🔒 Security Notes

**✅ DO:**
- Use `NEXT_PUBLIC_` prefix for public vars (endpoint, project ID, function IDs)
- These are safe to expose in browser

**❌ DON'T:**
- Never use `NEXT_PUBLIC_` prefix for API keys
- API keys should only be in serverless functions
- Never commit `.env.local` to Git

## 🐛 Troubleshooting

### Error: "Function ID not set"
- Check environment variables in Vercel Dashboard
- Redeploy after adding variables

### Error: "Cannot find module"
- Run `npm install` locally
- Check package.json has all dependencies

### Error: "Appwrite function error: 404"
- Function ID is wrong
- Check IDs in Appwrite Console match .env

### Error: "CORS policy"
- Add your Vercel domain to Appwrite Project → Settings → Platforms
- Add: `https://bentleybudgetbot.vercel.app`

## 📋 Next Steps After Deployment

1. ✅ Test Appwrite Functions (done after current test!)
2. ✅ Add authentication (user login)
3. ✅ Add more pages (portfolio, budget, etc.)
4. ✅ Style with CSS framework (Tailwind, etc.)
5. ✅ Connect to real user IDs (not hardcoded 'user123')

---

**Your current status:** Functions deployed, testing in progress!
