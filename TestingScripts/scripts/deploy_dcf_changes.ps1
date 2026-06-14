# DCF Analysis Integration - Deployment Script
# This script stages and commits all DCF-related changes for GitHub push

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " DCF Analysis - Git Deployment" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Ensure we're on dev branch
Write-Host "Checking current branch..." -ForegroundColor Yellow
$currentBranch = git branch --show-current
if ($currentBranch -ne "dev") {
    Write-Host "⚠️  WARNING: Not on dev branch (currently on: $currentBranch)" -ForegroundColor Red
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        Write-Host "❌ Deployment cancelled" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ On dev branch" -ForegroundColor Green
}

Write-Host ""
Write-Host "Staging modified files..." -ForegroundColor Yellow

# Stage all DCF-related files
$filesToStage = @(
    "frontend/components/dcf_widget.py",
    "streamlit_app.py",
    "scripts/setup_dcf_db.py",
    "docs/DCF_IMPLEMENTATION_REPORT.md",
    "docs/DCF_TEST_PLAN.md",
    "scripts/deploy_dcf_changes.ps1"
)

foreach ($file in $filesToStage) {
    if (Test-Path $file) {
        git add $file
        Write-Host "  ✅ Staged: $file" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Not found: $file" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Git status:" -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "Committing changes..." -ForegroundColor Yellow

$commitMessage = @"
feat: Add DCF CSV upload and sidebar login repositioning

- Enhanced DCF widget with CSV batch upload functionality
- Added login section above Mansa Funds in sidebar
- Created automated database setup script with password handling
- Implemented comprehensive test documentation
- Added CSV template download and results export

Features:
- Dual-mode DCF analysis (single ticker + batch CSV)
- Progress tracking for batch analysis
- Color-coded valuation results
- Downloadable results with timestamp
- User authentication in sidebar
- Graceful RBAC degradation

Testing:
- Database setup script with interactive password prompt
- Single ticker DCF analysis (AAPL, MSFT sample data)
- Batch CSV upload with template download
- Error handling for invalid tickers

Files:
- frontend/components/dcf_widget.py: Added CSV upload mode
- streamlit_app.py: Repositioned login above Mansa Funds
- scripts/setup_dcf_db.py: Automated DB setup with .env support
- docs/DCF_IMPLEMENTATION_REPORT.md: Complete implementation guide
- docs/DCF_TEST_PLAN.md: Testing procedures and checklist
"@

git commit -m $commitMessage

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Commit successful!" -ForegroundColor Green
    Write-Host ""
    
    # Show commit details
    Write-Host "Latest commit:" -ForegroundColor Yellow
    git log -1 --oneline
    
    Write-Host ""
    Write-Host "Ready to push to remote?" -ForegroundColor Cyan
    Write-Host "Command: git push origin dev" -ForegroundColor White
    Write-Host ""
    
    $push = Read-Host "Push now? (y/n)"
    if ($push -eq "y") {
        Write-Host ""
        Write-Host "Pushing to origin/dev..." -ForegroundColor Yellow
        git push origin dev
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "🎉 Successfully pushed to GitHub!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Next steps:" -ForegroundColor Cyan
            Write-Host "1. Go to GitHub repository" -ForegroundColor White
            Write-Host "2. Create Pull Request: dev → main" -ForegroundColor White
            Write-Host "3. Add reviewers and link to DCF_IMPLEMENTATION_REPORT.md" -ForegroundColor White
            Write-Host "4. Run database setup: python scripts/setup_dcf_db.py" -ForegroundColor White
            Write-Host "5. Test DCF widget functionality" -ForegroundColor White
            Write-Host ""
        } else {
            Write-Host ""
            Write-Host "❌ Push failed. Check git output above." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host ""
        Write-Host "⏸️  Commit created but not pushed. Run manually:" -ForegroundColor Yellow
        Write-Host "   git push origin dev" -ForegroundColor White
        Write-Host ""
    }
} else {
    Write-Host ""
    Write-Host "❌ Commit failed. Check git output above." -ForegroundColor Red
    exit 1
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Deployment Complete" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
