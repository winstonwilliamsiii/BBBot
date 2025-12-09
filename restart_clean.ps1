# BBBot Complete Restart Procedure - PowerShell Version
# Fixes: Plaid credentials not loading, database errors, cached old values

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  BBBot Complete Restart Procedure" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 1. Stop Streamlit
Write-Host "[1/6] Stopping Streamlit processes..." -ForegroundColor Yellow
Get-Process streamlit -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# 2. Test Plaid credentials
Write-Host "[2/6] Testing Plaid credentials..." -ForegroundColor Yellow
$result = python test_plaid_credentials.py
Write-Host $result
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ERROR: Plaid credentials test failed!" -ForegroundColor Red
    Write-Host "Check your .env file" -ForegroundColor Red
    pause
    exit 1
}

# 3. Test database
Write-Host ""
Write-Host "[3/6] Testing database connection..." -ForegroundColor Yellow
$result = python test_budget_database.py
Write-Host $result
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ERROR: Database test failed!" -ForegroundColor Red
    Write-Host "Check MySQL is running on port 3306" -ForegroundColor Red
    pause
    exit 1
}

# 4. Clear Python cache
Write-Host ""
Write-Host "[4/6] Clearing Python cache..." -ForegroundColor Yellow
Get-ChildItem -Recurse __pycache__ -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force

# 5. Clear Streamlit cache
Write-Host "[5/6] Clearing Streamlit cache..." -ForegroundColor Yellow
$streamlitCache = "$env:USERPROFILE\.streamlit\cache"
if (Test-Path $streamlitCache) {
    Remove-Item -Recurse -Force $streamlitCache -ErrorAction SilentlyContinue
}

# 6. Start Streamlit
Write-Host ""
Write-Host "[6/6] Starting Streamlit..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   LOGIN CREDENTIALS:" -ForegroundColor Green
Write-Host "   Username: admin" -ForegroundColor White
Write-Host "   Password: admin123" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "✅ All tests passed!" -ForegroundColor Green
Write-Host "Opening browser in 3 seconds..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

# Open browser to Personal Budget page
Start-Process "http://localhost:8501"

# Start Streamlit
Write-Host ""
Write-Host "🚀 Starting Streamlit..." -ForegroundColor Cyan
streamlit run streamlit_app.py
