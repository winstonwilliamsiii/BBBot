<#
.SYNOPSIS
    MT5 Paper Trading Setup - Quick Start Script
    
.DESCRIPTION
    Sets up and starts the MT5 REST API server for paper trading (demo account).
    This script will:
    1. Check if MT5 terminal is running
    2. Install/verify dependencies
    3. Start the REST API server on localhost:8080
    
.NOTES
    Author: BentleyBot
    Date: February 12, 2026
    Requirements:
    - MetaTrader 5 installed and logged into DEMO account
    - Python 3.11+ with venv activated
#>

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   MT5 Paper Trading Server Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Check if MT5 is running
Write-Host "[1/5] Checking MetaTrader 5 status..." -ForegroundColor Yellow
$mt5Process = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue

if ($mt5Process) {
    Write-Host "  ✅ MT5 Terminal is running (PID: $($mt5Process.Id))" -ForegroundColor Green
} else {
    Write-Host "  ❌ MT5 Terminal not detected!" -ForegroundColor Red
    Write-Host "`n  Please start MetaTrader 5 and log into your DEMO account" -ForegroundColor Yellow
    Write-Host "  Then run this script again.`n" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 2: Test MT5 connection
Write-Host "`n[2/5] Testing MT5 connection..." -ForegroundColor Yellow
$testResult = python test_mt5_connection.py 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ MT5 connected and logged in" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  MT5 connection test failed" -ForegroundColor Yellow
    Write-Host "`n  IMPORTANT: Please log into your MT5 DEMO account:" -ForegroundColor Red
    Write-Host "  1. Open MetaTrader 5 terminal" -ForegroundColor Yellow
    Write-Host "  2. Click File → Open an Account" -ForegroundColor Yellow
    Write-Host "  3. Select or create a DEMO account" -ForegroundColor Yellow
    Write-Host "  4. Log in with your credentials" -ForegroundColor Yellow
    Write-Host "`n  Then run this script again.`n" -ForegroundColor Yellow
    Write-Host "  See TONIGHT_MT5_SETUP.md for detailed instructions" -ForegroundColor Cyan
    Read-Host "`nPress Enter to exit"
    exit 1
}

# Step 3: Activate virtual environment
Write-Host "`n[3/5] Activating Python environment..." -ForegroundColor Yellow
$venvPath = ".\.venv\Scripts\Activate.ps1"

if (Test-Path $venvPath) {
    & $venvPath
    Write-Host "  ✅ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "  ❌ Virtual environment not found at .venv" -ForegroundColor Red
    Write-Host "  Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    & $venvPath
}

# Step 4: Install MetaTrader5 package if missing
Write-Host "`n[4/5] Checking dependencies..." -ForegroundColor Yellow
$mt5Installed = pip show MetaTrader5 2>$null

if (-not $mt5Installed) {
    Write-Host "  📦 Installing MetaTrader5 package (Windows-only)..." -ForegroundColor Yellow
    pip install -r requirements-mt5.txt --quiet
    Write-Host "  ✅ MetaTrader5 package installed" -ForegroundColor Green
} else {
    Write-Host "  ✅ MetaTrader5 package already installed" -ForegroundColor Green
}

# Step 5: Configure and start server
Write-Host "`n[5/5] Starting MT5 REST API Server..." -ForegroundColor Yellow

# Set environment variables for the server
$env:HOST = "0.0.0.0"
$env:PORT = "8080"

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "   🚀 MT5 REST API Server Starting" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Server URL: http://localhost:8080" -ForegroundColor Cyan
Write-Host "`nAvailable Endpoints:" -ForegroundColor White
Write-Host "  GET  /health                              - Server health check" -ForegroundColor Gray
Write-Host "  POST /connect                             - Connect to MT5 account" -ForegroundColor Gray
Write-Host "  GET  /account                             - Get account info" -ForegroundColor Gray
Write-Host "  GET  /positions                           - Get open positions" -ForegroundColor Gray
Write-Host "  GET  /position/<symbol>                   - Get specific position" -ForegroundColor Gray
Write-Host "  GET  /symbol/<symbol>                     - Get symbol info" -ForegroundColor Gray
Write-Host "  GET  /market-data?symbol=X&timeframe=H1   - Get historical data" -ForegroundColor Gray
Write-Host "  GET  /price/<symbol>                       - Get current price" -ForegroundColor Gray
Write-Host "  POST /trade                               - Place trade" -ForegroundColor Gray
Write-Host "  POST /close                               - Close position" -ForegroundColor Gray
Write-Host "  POST /modify                              - Modify order" -ForegroundColor Gray
Write-Host "`nPress Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Green

# Start the server (mt5_rest.py in root directory)
try {
    python mt5_rest.py
} catch {
    Write-Host "`n❌ Server failed to start: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
