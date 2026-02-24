#!/usr/bin/env pwsh
# Create PR for Technical Indicator Bot

$title = "feat(trading): Multi-ETF Technical Indicator Bot with production safety controls"

$body = @"
## Summary
Production-ready Technical Indicator Trading Bot with support for multiple ETF tickers and comprehensive safety controls.

## Changes Made
### Core Features
- ✅ Multi-indicator trading strategy (RSI, MACD, Bollinger Bands, SMA)
- ✅ Support for 12 symbols: VOO, SQQQ, MAGS, BITI, XLF, QUTM, NUKZ, PINK, DFEN, VXX, IONZ, VIX
- ✅ Automated signal generation and trade execution
- ✅ Position sizing based on account equity and risk tolerance
- ✅ Comprehensive error handling and logging

### Safety Controls
- ✅ Dry run mode enabled by default
- ✅ Trading disabled by default (requires explicit enable)
- ✅ Position size limits (max 100 shares)
- ✅ Risk management (2% per trade)
- ✅ Minimum account balance requirement (\$1,000)
- ✅ Independent processing per symbol with error isolation

### Testing & Quality
- ✅ 21 comprehensive unit tests (all passing)
- ✅ Mocked Alpaca API for testing
- ✅ Edge case handling (empty data, insufficient data, API errors)
- ✅ Configuration validation
- ✅ Code quality verified with flake8

## Files Changed
- \`scripts/technical_indicator_bot.py\` - Main bot implementation
- \`tests/test_technical_indicator_bot.py\` - Comprehensive test suite
- \`TECHNICAL_INDICATOR_BOT_DEPLOYMENT.md\` - Deployment guide
- \`TECH_BOT_UPDATE_SUMMARY.md\` - Update summary
- \`scripts/create_pr_technical_bot.ps1\` - PR creation script

## Testing
\`\`\`
============================= 21 passed in 6.40s ==============================
\`\`\`

All tests passing locally:
- Technical indicator calculations
- Configuration validation
- Bot initialization and account management
- Position tracking
- Signal generation (BUY/SELL/HOLD)
- Trade execution with safety controls
- Error handling and edge cases

## Configuration
The bot uses environment variables for all configuration:
\`\`\`bash
TRADING_SYMBOLS=VOO,SQQQ,MAGS,BITI,XLF,QUTM,NUKZ,PINK,DFEN,VXX,IONZ,VIX
ALPACA_API_KEY=<your_key>
ALPACA_SECRET_KEY=<your_secret>
ALPACA_BASE_URL=https://paper-api.alpaca.markets
DRY_RUN=true
ENABLE_TRADING=false
\`\`\`

## Deployment Checklist
- [ ] CI/CD pipelines pass
- [ ] Code review approved
- [ ] Environment variables configured
- [ ] Test in dry-run mode with paper trading
- [ ] Verify signals and indicator calculations
- [ ] Enable live trading only after validation

## Risk Assessment
**Risk Level**: Low (with default settings)
- Dry run mode prevents actual trades
- Trading explicitly disabled by default
- Multi-layer safety controls
- Comprehensive logging for audit trail
- Position sizing limits downside risk

**Risk Level**: Medium (when enabled for production)
- Automated trading with real funds
- Requires proper monitoring
- Market volatility can impact results
- Recommended to start with small position sizes

## Breaking Changes
None - this is a new feature addition

## Dependencies
- alpaca-trade-api
- pandas
- numpy
- python-ta (technical analysis library)

All dependencies already in requirements.txt

## Related Issues
Closes issues related to ETF trading automation

## Ready for Production
✅ Yes - with safety controls enabled by default
⚠️ Requires proper configuration and testing before live trading

---
**Type**: feat (new feature)  
**Scope**: trading  
**Ready for Merge**: Pending CI/CD ✅  
**Ready for Trading**: Requires environment setup and validation ⏳
"@

Write-Host "Creating PR..." -ForegroundColor Cyan

try {
    # First check if gh is available and authenticated
    $ghVersion = gh --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ GitHub CLI (gh) not found or not authenticated" -ForegroundColor Red
        Write-Host "Please install gh and run: gh auth login" -ForegroundColor Yellow
        exit 1
    }
    
    # Create the PR
    gh pr create `
        --title $title `
        --body $body `
        --base main `
        --head feature/technical-indicator-bot `
        --label "enhancement,trading,production" `
        --assignee "@me"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ PR created successfully!" -ForegroundColor Green
        Write-Host "Opening PR in browser..." -ForegroundColor Cyan
        gh pr view --web
    } else {
        Write-Host "❌ Failed to create PR" -ForegroundColor Red
        Write-Host "You can create it manually at:" -ForegroundColor Yellow
        Write-Host "https://github.com/winstonwilliamsiii/BBBot/compare/main...feature/technical-indicator-bot" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Error creating PR: $_" -ForegroundColor Red
    Write-Host "You can create it manually at:" -ForegroundColor Yellow
    Write-Host "https://github.com/winstonwilliamsiii/BBBot/compare/main...feature/technical-indicator-bot" -ForegroundColor Cyan
}
