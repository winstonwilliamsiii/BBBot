# BBBot Streamlit Restart - Comprehensive Version
# Shows all output and handles errors gracefully

param(
    [switch]$SkipTests
)

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  BBBot Streamlit Application Restart" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Stop Streamlit
Write-Host "► Step 1: Stopping Streamlit processes..." -ForegroundColor Yellow
$processes = Get-Process streamlit -ErrorAction SilentlyContinue
if ($processes) {
    $processes | Stop-Process -Force
    Write-Host "  ✓ Stopped $($processes.Count) Streamlit process(es)" -ForegroundColor Green
} else {
    Write-Host "  • No Streamlit processes running" -ForegroundColor Gray
}
Start-Sleep -Seconds 1

if (-not $SkipTests) {
    # Test Plaid credentials
    Write-Host ""
    Write-Host "► Step 2: Verifying Plaid credentials..." -ForegroundColor Yellow
    Write-Host ""
    
    $plaidTest = python test_plaid_credentials.py 2>&1
    Write-Host $plaidTest
    
    if ($plaidTest -match "SUCCESS") {
        Write-Host "  ✓ Plaid credentials verified" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "  ⚠ Warning: Plaid test didn't show SUCCESS" -ForegroundColor Yellow
        Write-Host "  Continuing anyway... (credentials may still work)" -ForegroundColor Yellow
    }
    
    # Test database
    Write-Host ""
    Write-Host "► Step 3: Verifying database connection..." -ForegroundColor Yellow
    Write-Host ""
    
    $dbTest = python test_budget_database.py 2>&1
    Write-Host $dbTest
    
    if ($dbTest -match "Successfully connected") {
        Write-Host "  ✓ Database connection verified" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "  ⚠ Warning: Database test didn't confirm connection" -ForegroundColor Yellow
        Write-Host "  Continuing anyway... (database may still work)" -ForegroundColor Yellow
    }
    
    $stepNum = 4
} else {
    Write-Host ""
    Write-Host "  • Skipping tests (use without -SkipTests to run tests)" -ForegroundColor Gray
    $stepNum = 2
}

# Clear Python cache
Write-Host ""
Write-Host "► Step $stepNum`: Clearing Python cache..." -ForegroundColor Yellow
$pycache = Get-ChildItem -Recurse __pycache__ -ErrorAction SilentlyContinue
if ($pycache) {
    $pycache | Remove-Item -Recurse -Force
    Write-Host "  ✓ Cleared Python cache" -ForegroundColor Green
} else {
    Write-Host "  • No cache to clear" -ForegroundColor Gray
}

# Clear Streamlit cache
$stepNum++
Write-Host ""
Write-Host "► Step $stepNum`: Clearing Streamlit cache..." -ForegroundColor Yellow
$streamlitCache = "$env:USERPROFILE\.streamlit\cache"
if (Test-Path $streamlitCache) {
    Remove-Item -Recurse -Force $streamlitCache -ErrorAction SilentlyContinue
    Write-Host "  ✓ Cleared Streamlit cache" -ForegroundColor Green
} else {
    Write-Host "  • No Streamlit cache found" -ForegroundColor Gray
}

# Show login info
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "           LOGIN CREDENTIALS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Username: " -NoNewline -ForegroundColor White
Write-Host "admin" -ForegroundColor Green
Write-Host "  Password: " -NoNewline -ForegroundColor White
Write-Host "admin123" -ForegroundColor Green
Write-Host ""
Write-Host "  (all lowercase, case-sensitive)" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan

# Start Streamlit
$stepNum++
Write-Host ""
Write-Host "► Step $stepNum`: Starting Streamlit..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Opening browser in 3 seconds..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

Start-Process "http://localhost:8501"

Write-Host ""
Write-Host "  🚀 Streamlit is starting..." -ForegroundColor Green
Write-Host "  📱 Browser should open automatically" -ForegroundColor Green
Write-Host "  🔗 If not, visit: http://localhost:8501" -ForegroundColor Green
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

streamlit run streamlit_app.py
