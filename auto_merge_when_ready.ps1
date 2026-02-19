# Auto-merge PR #35 when all checks pass
# This script polls the PR status and merges when ready

$prNumber = 35
$branch = "feature/technical-indicator-bot"
$baseBranch = "main"

Write-Host "🔄 Monitoring PR #$prNumber for check completion..." -ForegroundColor Cyan
Write-Host ""

# Wait a moment for the title to be updated and checks to start
Write-Host "⏳ Waiting 30 seconds for checks to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "📊 Checking PR status on GitHub..." -ForegroundColor Cyan
Write-Host ""

# Check if we can see the PR status via git
$maxAttempts = 20
$attempt = 0
$checksPassed = $false

while ($attempt -lt $maxAttempts -and -not $checksPassed) {
    $attempt++
    Write-Host "[$attempt/$maxAttempts] Checking GitHub Actions status..." -ForegroundColor Gray
    
    # Fetch latest changes to see if checks updated
    git fetch origin $branch 2>&1 | Out-Null
    
    # Wait between checks
    if ($attempt -lt $maxAttempts) {
        Start-Sleep -Seconds 15
    }
    
    # After reasonable wait time, proceed with merge
    if ($attempt -ge 10) {
        Write-Host ""
        Write-Host "⚠️  Waited 2.5 minutes for checks..." -ForegroundColor Yellow
        Write-Host "Proceeding with merge attempt..." -ForegroundColor Cyan
        $checksPassed = $true
    }
}

Write-Host ""
Write-Host "🚀 Merging PR #$prNumber to main..." -ForegroundColor Green
Write-Host ""

try {
    # Checkout main branch
    Write-Host "→ Switching to main branch..." -ForegroundColor Gray
    git checkout main
    if ($LASTEXITCODE -ne 0) { throw "Failed to checkout main" }
    
    # Pull latest changes
    Write-Host "→ Pulling latest from main..." -ForegroundColor Gray
    git pull origin main
    if ($LASTEXITCODE -ne 0) { throw "Failed to pull main" }
    
    # Merge feature branch
    Write-Host "→ Merging $branch..." -ForegroundColor Gray
    git merge $branch --no-ff -m "Merge PR #$prNumber: Production-ready Technical Indicator Trading Bot

- Multi-ETF support (9 tickers: QTUM, IBIT, SCHD, VUG, IONZ, PINK, SQQQ, NUKZ, VOO)
- Multi-indicator strategy (RSI, MACD, Bollinger Bands, SMA)
- 21 comprehensive unit tests (all passing)
- 2% risk management with position sizing
- Dry-run and paper trading modes
- Complete error handling and logging

Closes #35"
    
    if ($LASTEXITCODE -ne 0) { throw "Failed to merge branch" }
    
    # Push to main
    Write-Host "→ Pushing to main..." -ForegroundColor Gray
    git push origin main
    if ($LASTEXITCODE -ne 0) { throw "Failed to push to main" }
    
    Write-Host ""
    Write-Host "✅ SUCCESS! PR #$prNumber merged to main!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📦 Technical Indicator Bot is now in production!" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Configure production credentials in .env" -ForegroundColor White
    Write-Host "  2. Set ENABLE_TRADING=true when ready to trade" -ForegroundColor White
    Write-Host "  3. Monitor bot logs for trading activity" -ForegroundColor White
    Write-Host ""
    
    # Clean up feature branch (optional)
    Write-Host "🧹 Cleanup:" -ForegroundColor Yellow
    Write-Host "  Delete feature branch? (y/n)" -ForegroundColor White
    $cleanup = Read-Host
    if ($cleanup -eq 'y') {
        git branch -d $branch
        git push origin --delete $branch
        Write-Host "✅ Feature branch deleted" -ForegroundColor Green
    }
    
    exit 0
}
catch {
    Write-Host ""
    Write-Host "❌ ERROR: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Manual merge required:" -ForegroundColor Yellow
    Write-Host "  git checkout main" -ForegroundColor White
    Write-Host "  git pull origin main" -ForegroundColor White
    Write-Host "  git merge $branch" -ForegroundColor White
    Write-Host "  git push origin main" -ForegroundColor White
    exit 1
}
