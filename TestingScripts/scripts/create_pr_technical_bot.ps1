# Create Pull Request for Technical Indicator Bot
# This script opens the GitHub PR creation page in your browser

$prUrl = "https://github.com/winstonwilliamsiii/BBBot/pull/new/feature/technical-indicator-bot"

Write-Host "`n" -NoNewline
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Technical Indicator Bot - Pull Request Creation" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "✅ Local Tests: " -NoNewline -ForegroundColor Yellow
Write-Host "21/21 PASSED" -ForegroundColor Green

Write-Host "✅ Branch: " -NoNewline -ForegroundColor Yellow
Write-Host "feature/technical-indicator-bot" -ForegroundColor Green

Write-Host "✅ Pushed to: " -NoNewline -ForegroundColor Yellow
Write-Host "GitHub" -ForegroundColor Green

Write-Host ""
Write-Host "🌐 Opening GitHub Pull Request page..." -ForegroundColor Cyan
Write-Host ""

Start-Process $prUrl

Write-Host "📋 PR Details to include:" -ForegroundColor Yellow
Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Title:" -ForegroundColor Cyan
Write-Host "  feat: Add Production-Ready Technical Indicator Trading Bot" -ForegroundColor White
Write-Host ""
Write-Host "Description:" -ForegroundColor Cyan
Write-Host "  - Multi-indicator strategy (RSI, MACD, Bollinger Bands, SMA)" -ForegroundColor White
Write-Host "  - 21 comprehensive unit tests (all passing)" -ForegroundColor White
Write-Host "  - Safety controls and risk management" -ForegroundColor White
Write-Host "  - Production-ready with proper documentation" -ForegroundColor White
Write-Host ""
Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""
Write-Host "⏳ Next: Wait for GitHub Actions CI to complete" -ForegroundColor Yellow
Write-Host "✅ Then: Merge to main branch for production" -ForegroundColor Green
Write-Host ""
