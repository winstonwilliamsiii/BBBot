@echo off
REM Quick Start: Vercel Frontend Deployment (Windows)
REM Run this file to see quick start instructions

echo.
echo ==================================================
echo Bentley Budget Bot - Vercel Frontend Quick Start
echo ==================================================
echo.
echo STEP 1: Install dependencies
echo   cd vercel-frontend
echo   npm install
echo.
echo STEP 2: Test locally
echo   npm run dev
echo   Visit: http://localhost:3000/api/health
echo.
echo STEP 3: Connect to Vercel
echo   1. Go to https://vercel.com/dashboard
echo   2. Import your GitHub repository
echo   3. Set root directory to 'vercel-frontend'
echo.
echo STEP 4: Add Environment Variables
echo   In Vercel Project Settings ^> Environment Variables, add:
echo.
echo   PUBLIC VARIABLES:
echo   NEXT_PUBLIC_APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
echo   NEXT_PUBLIC_APPWRITE_PROJECT_ID=68869ef500017ca73772
echo.
echo   NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_TRANSACTION=694db02c58495b52f6e6
echo   NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_TRANSACTIONS=694daffaae8121bb7837
echo   NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_PAYMENT=694dab48338627afc96a
echo   NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_PAYMENTS=694daddc3fed56721c52
echo   NEXT_PUBLIC_APPWRITE_FUNCTION_ID_ADD_WATCHLIST=694da7003804de8bb29a
echo   NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_WATCHLIST=694da75bd55dc6d65fb9
echo   NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_USER_PROFILE=694da7aedf6018cc8266
echo   NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_AUDIT_LOG=694dab48338627afc96a
echo   NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_AUDIT_LOGS=694daaad91f3b1b6d68c
echo   NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_BOT_METRIC=694dadc18bd08f7a3895
echo   NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_BOT_METRICS=694dadba22d1eeada62d
echo   NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_BOT_METRICS_STATS=694dada2b9c2ddef7c56
echo.
echo   PRIVATE VARIABLES:
echo   APPWRITE_API_KEY=[Get from Appwrite Console]
echo   APPWRITE_DATABASE_ID=6944821e4f5f5f4f7d10
echo.
echo STEP 5: Deploy
echo   git add .
echo   git commit -m "Add Vercel frontend with secure API routes"
echo   git push origin main
echo.
echo STEP 6: Test Deployment
echo   curl https://your-vercel-domain.com/api/health
echo.
echo STEP 7: Record Your First ML Metrics!
echo   PowerShell -Command ^"
echo   $json = '@{
echo     "user_id": "test",
echo     "bot_id": "ml_bot",
echo     "experiment_id": "exp_001",
echo     "metrics": { "accuracy": 0.92, "sharpe_ratio": 1.5 },
echo     "data_source": "yfinance",
echo     "status": "completed"
echo   }' ^| ConvertFrom-Json ^| ConvertTo-Json
echo   Invoke-WebRequest -Uri 'https://your-vercel-domain.com/api/recordBotMetrics' -Method POST -Body $json -ContentType 'application/json'
echo   ^"
echo.
echo ==================================================
echo Integration Complete! Ready for ML Experiments
echo ==================================================
echo.
pause
