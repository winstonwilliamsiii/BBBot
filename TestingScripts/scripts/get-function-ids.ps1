# get-function-ids.ps1
# Helper script to extract Function IDs after deployment

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "🔍 GET APPWRITE FUNCTION IDs" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

Write-Host "`n⏳ Checking deployment status..." -ForegroundColor Yellow

# Check if CLI is authenticated
$loginCheck = appwrite account get 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Not logged in to Appwrite CLI!" -ForegroundColor Red
    Write-Host "Run: appwrite login" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ CLI authenticated" -ForegroundColor Green

# Load project ID from .env
$projectId = $null
if (Test-Path ".\.env") {
    Get-Content ".\.env" | ForEach-Object {
        if ($_ -match '^APPWRITE_PROJECT_ID=(.+)$') {
            $projectId = $matches[1].Trim()
        }
    }
}

if (-not $projectId) {
    Write-Host "❌ APPWRITE_PROJECT_ID not found in .env!" -ForegroundColor Red
    exit 1
}

Write-Host "📦 Project ID: $projectId" -ForegroundColor Cyan

# List functions
Write-Host "`n📋 Fetching functions..." -ForegroundColor Yellow
$functionsOutput = appwrite functions list --project-id $projectId 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to fetch functions!" -ForegroundColor Red
    Write-Host $functionsOutput -ForegroundColor Red
    Write-Host "`n💡 TIP: Functions might still be deploying. Wait a few minutes and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "`n✅ FUNCTIONS FOUND!" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Gray

# Parse output (this is a simplified version - adjust based on actual CLI output format)
Write-Host "`n📝 Copy these IDs to your .env file:" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Gray

# The 4 priority functions for StreamLit integration
$priorityFunctions = @(
    "get_transactions_streamlit",
    "add_to_watchlist_streamlit",
    "get_watchlist_streamlit",
    "get_user_profile_streamlit"
)

Write-Host "`n🎯 PRIORITY FUNCTIONS (for StreamLit):" -ForegroundColor Yellow
Write-Host ""
Write-Host "# Add these to your .env file:" -ForegroundColor Gray

foreach ($funcName in $priorityFunctions) {
    Write-Host "APPWRITE_FUNCTION_ID_$($funcName.ToUpper().Replace('-', '_'))=<paste_id_here>" -ForegroundColor White
}

Write-Host "`n" + ("=" * 70) -ForegroundColor Gray
Write-Host "📊 ALL FUNCTIONS:" -ForegroundColor Yellow
Write-Host $functionsOutput

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "📋 NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Find each function ID from the list above" -ForegroundColor White
Write-Host "2. Open .env file in VS Code" -ForegroundColor White
Write-Host "3. Add the 4 function IDs to .env" -ForegroundColor White
Write-Host "4. Restart StreamLit: .\START_BBBOT.ps1" -ForegroundColor White
Write-Host ("=" * 70) -ForegroundColor Cyan

Write-Host "`n💡 ALTERNATIVE: Get IDs from Appwrite Console" -ForegroundColor Yellow
Write-Host "   URL: https://cloud.appwrite.io/console/project-$projectId/functions" -ForegroundColor Cyan
Write-Host "   Click each function → Copy Function ID" -ForegroundColor Gray
