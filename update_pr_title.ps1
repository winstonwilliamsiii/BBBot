# Update PR #35 Title to Match Conventional Commits Format
# This script opens the PR edit page in your browser

$prNumber = 35
$newTitle = "feat(trading-bot): add production-ready technical indicator trading bot"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Update PR Title - Conventional Commits Format" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "Current Issue:" -ForegroundColor Yellow
Write-Host "  The PR title doesn't follow Conventional Commits format required by workflow" -ForegroundColor White
Write-Host ""

Write-Host "Required Format:" -ForegroundColor Yellow
Write-Host "  type(scope): description" -ForegroundColor White
Write-Host "  Example: feat(portfolio): add new dashboard widget" -ForegroundColor Gray
Write-Host ""

Write-Host "New PR Title:" -ForegroundColor Green
Write-Host "  $newTitle" -ForegroundColor White
Write-Host ""

Write-Host "Actions Required:" -ForegroundColor Yellow
Write-Host "  1. Browser will open to PR edit page" -ForegroundColor White
Write-Host "  2. Update the title field with the new title shown above" -ForegroundColor White
Write-Host "  3. Click 'Save' to update the PR" -ForegroundColor White
Write-Host ""

Write-Host "📋 Copy this title:" -ForegroundColor Cyan
Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "$newTitle" -ForegroundColor Yellow
Write-Host "───────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# Copy to clipboard
$newTitle | Set-Clipboard
Write-Host "✅ Title copied to clipboard!" -ForegroundColor Green
Write-Host ""

Write-Host "🌐 Opening PR edit page..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

# Open PR edit page
$editUrl = "https://github.com/winstonwilliamsiii/BBBot/pull/$prNumber"
Start-Process $editUrl

Write-Host ""
Write-Host "After updating the PR title:" -ForegroundColor Yellow
Write-Host "  - The Branch & PR Validation job will re-run automatically" -ForegroundColor White
Write-Host "  - The title validation will pass" -ForegroundColor White
Write-Host "  - Status Notification job will also pass" -ForegroundColor White
Write-Host ""
Write-Host "✅ Next: Click 'Edit' on the PR page and paste the new title" -ForegroundColor Green
Write-Host ""
