# Quick Streamlit Restart - Use Virtual Environment Python

Write-Host ""
Write-Host "🔄 RESTARTING STREAMLIT (CLEAN)" -ForegroundColor Cyan
Write-Host "="*50 -ForegroundColor Cyan
Write-Host ""

# 1. Kill all Python/Streamlit processes
Write-Host "[1/4] Stopping all Python processes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like '*python*'} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "  ✓ Stopped" -ForegroundColor Green

# 2. Clear Streamlit cache
Write-Host ""
Write-Host "[2/4] Clearing Streamlit cache..." -ForegroundColor Yellow
Remove-Item -Recurse -Force "$env:USERPROFILE\.streamlit\cache" -ErrorAction SilentlyContinue
Write-Host "  ✓ Cache cleared" -ForegroundColor Green

# 3. Check virtual environment
Write-Host ""
Write-Host "[3/4] Checking virtual environment..." -ForegroundColor Yellow
if (Test-Path ".\.venv\Scripts\python.exe") {
    $version = & .\.venv\Scripts\python.exe -m streamlit --version
    Write-Host "  ✓ Found: $version" -ForegroundColor Green
} else {
    Write-Host "  ❌ Virtual environment not found!" -ForegroundColor Red
    exit 1
}

# 4. Start Streamlit with venv Python
Write-Host ""
Write-Host "[4/4] Starting Streamlit..." -ForegroundColor Yellow
Write-Host "  Using: .venv\Scripts\python.exe" -ForegroundColor Cyan
Write-Host "  Version: Streamlit 1.52.1" -ForegroundColor Cyan
Write-Host ""
Write-Host "="*50 -ForegroundColor Green
Write-Host "  LOCAL:   http://localhost:8501" -ForegroundColor Green
Write-Host "="*50 -ForegroundColor Green
Write-Host ""
Write-Host "💡 IMPORTANT: Clear your browser cache!" -ForegroundColor Yellow
Write-Host "   Press: Ctrl + Shift + R (or Ctrl + F5)" -ForegroundColor Yellow
Write-Host ""

& .\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
