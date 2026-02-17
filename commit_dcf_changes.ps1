#!/usr/bin/env pwsh
# Commit and push DCF analysis changes

Write-Host "Adding DCF analysis files to git..." -ForegroundColor Cyan

git add frontend/components/dcf_analysis.py
git add frontend/components/dcf_widget.py
git add streamlit_app.py
git add .env.example

Write-Host "`nCommitting changes..." -ForegroundColor Cyan

git commit -m "feat: Add DCF fundamental analysis to dashboard

- Implements DCF valuation analysis backend
- Adds interactive DCF widget for dashboard
- Integrates into streamlit_app.py home page
- Updates environment variables with all API configs
- Supports MySQL database for fundamentals data
- Includes Kalshi, Polymarket, Bank of America API docs
- Comprehensive error handling and logging
"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nPushing to dev branch..." -ForegroundColor Cyan
    git push origin dev
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ SUCCESS! DCF analysis pushed to dev branch" -ForegroundColor Green
        Write-Host "`nNext steps:" -ForegroundColor Yellow
        Write-Host "  1. Review the changes on GitHub"
        Write-Host "  2. Create a Pull Request from dev to main"
        Write-Host "  3. Test the DCF widget on the dashboard"
    } else {
        Write-Host "`n❌ Push failed" -ForegroundColor Red
    }
} else {
    Write-Host "`n❌ Commit failed" -ForegroundColor Red
}
