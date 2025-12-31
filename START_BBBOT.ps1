# BBBot Fresh Start - Activates venv and starts Streamlit properly

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  BBBot Fresh Start" -ForegroundColor Cyan  
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Stop any running Streamlit
Write-Host "[1/5] Stopping old Streamlit processes..." -ForegroundColor Yellow
Get-Process streamlit -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*streamlit*"} | Stop-Process -Force
Start-Sleep -Seconds 2
Write-Host "  ✓ Stopped" -ForegroundColor Green

# 2. Clear caches
Write-Host ""
Write-Host "[2/5] Clearing caches..." -ForegroundColor Yellow
Remove-Item -Recurse -Force "$env:USERPROFILE\.streamlit\cache" -ErrorAction SilentlyContinue
Get-ChildItem -Recurse __pycache__ -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Write-Host "  ✓ Caches cleared" -ForegroundColor Green

# 3. Activate virtual environment
Write-Host ""
Write-Host "[3/5] Activating virtual environment..." -ForegroundColor Yellow
$venvPath = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
    Write-Host "  ✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "  ⚠ No virtual environment found at $venvPath" -ForegroundColor Yellow
    Write-Host "  Continuing with system Python..." -ForegroundColor Yellow
}

# 4. Verify Streamlit is available
Write-Host ""
Write-Host "[4/5] Verifying Streamlit..." -ForegroundColor Yellow
$venvStreamlit = & .\.venv\Scripts\python.exe -m streamlit --version 2>&1
if ($venvStreamlit -match "Streamlit") {
    Write-Host "  ✓ Virtual env Streamlit: $venvStreamlit" -ForegroundColor Green
} else {
    Write-Host "  ❌ Streamlit not found in venv!" -ForegroundColor Red
    Write-Host "  Installing Streamlit..." -ForegroundColor Yellow
    & .\.venv\Scripts\python.exe -m pip install streamlit
}

# 5. Display login info and start
Write-Host ""
Write-Host "[5/5] Starting Streamlit with VIRTUAL ENVIRONMENT Python..." -ForegroundColor Yellow
Write-Host "  Using: .venv\Scripts\python.exe" -ForegroundColor Cyan
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "           LOGIN CREDENTIALS" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Username: " -NoNewline -ForegroundColor White
Write-Host "admin" -ForegroundColor Cyan
Write-Host "  Password: " -NoNewline -ForegroundColor White
Write-Host "admin123" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Opening browser in 3 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Start-Process "http://localhost:8501"

Write-Host ""
Write-Host "🚀 Starting Streamlit..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Use VIRTUAL ENVIRONMENT Python (Streamlit 1.52.1)
& .\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
