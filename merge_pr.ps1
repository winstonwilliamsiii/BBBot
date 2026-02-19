# Auto-merge script - Run AFTER PR title is updated
# This will merge the PR once all checks pass

$prNumber = 35
$repo = "winstonwilliamsiii/BBBot"

Write-Host "⏳ Waiting for PR title update..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Once you've updated the title on GitHub:" -ForegroundColor Yellow
Write-Host "  1. Wait ~2 minutes for all checks to pass" -ForegroundColor White
Write-Host "  2. Run this command:" -ForegroundColor White
Write-Host ""
Write-Host "     git checkout main" -ForegroundColor Green
Write-Host "     git pull origin main" -ForegroundColor Green  
Write-Host "     git merge feature/technical-indicator-bot" -ForegroundColor Green
Write-Host "     git push origin main" -ForegroundColor Green
Write-Host ""
Write-Host "Or merge via GitHub web interface:" -ForegroundColor Yellow
Write-Host "  https://github.com/$repo/pull/$prNumber" -ForegroundColor Cyan
Write-Host "  Click 'Merge pull request' button" -ForegroundColor White
Write-Host ""
