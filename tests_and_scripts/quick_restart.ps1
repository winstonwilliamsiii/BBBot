# Quick Restart - No Tests
# Use this if tests are passing but you just need to restart Streamlit

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  BBBot Quick Restart" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 1. Stop Streamlit
Write-Host "[1/4] Stopping Streamlit..." -ForegroundColor Yellow
Get-Process streamlit -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# 2. Clear caches
Write-Host "[2/4] Clearing caches..." -ForegroundColor Yellow
Get-ChildItem -Recurse __pycache__ -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
$streamlitCache = "$env:USERPROFILE\.streamlit\cache"
if (Test-Path $streamlitCache) {
    Remove-Item -Recurse -Force $streamlitCache -ErrorAction SilentlyContinue
}

# 3. Show login info
Write-Host ""
Write-Host "[3/4] Login Information:" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Username: admin" -ForegroundColor White
Write-Host "   Password: admin123" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 4. Start Streamlit
Write-Host "[4/4] Starting Streamlit..." -ForegroundColor Yellow
Write-Host "Opening browser in 3 seconds..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
Start-Process "http://localhost:8501"

Write-Host ""
Write-Host "🚀 Starting Streamlit..." -ForegroundColor Cyan
streamlit run streamlit_app.py
