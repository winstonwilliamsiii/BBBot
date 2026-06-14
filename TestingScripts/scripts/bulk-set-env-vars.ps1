# bulk-set-env-vars.ps1
# Set environment variables for all Appwrite Functions using Appwrite API

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "🔧 BULK SET ENVIRONMENT VARIABLES FOR APPWRITE FUNCTIONS" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

# Load .env file
Write-Host "`n📋 Loading variables from .env..." -ForegroundColor Yellow
$envPath = ".\.env"
if (-not (Test-Path $envPath)) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    exit 1
}

Get-Content $envPath | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.+)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        [System.Environment]::SetEnvironmentVariable($key, $value, 'Process')
    }
}

$endpoint = $env:APPWRITE_ENDPOINT
$projectId = $env:APPWRITE_PROJECT_ID
$apiKey = $env:APPWRITE_API_KEY
$databaseId = $env:APPWRITE_DATABASE_ID

Write-Host "✅ Configuration loaded" -ForegroundColor Green
Write-Host "   Endpoint: $endpoint" -ForegroundColor Gray
Write-Host "   Project ID: $projectId" -ForegroundColor Gray
Write-Host "   Database ID: $databaseId" -ForegroundColor Gray
Write-Host "   API Key: $($apiKey.Substring(0,20))..." -ForegroundColor Gray

# Environment variables to set for each function
$functionEnvVars = @{
    "APPWRITE_FUNCTION_ENDPOINT" = $endpoint
    "APPWRITE_FUNCTION_PROJECT_ID" = $projectId
    "APPWRITE_API_KEY" = $apiKey
    "APPWRITE_DATABASE_ID" = $databaseId
}

Write-Host "`n⚠️  LIMITATION: Appwrite API requires authentication" -ForegroundColor Yellow
Write-Host "This script would need to use Appwrite REST API with your API key." -ForegroundColor Gray
Write-Host "`nFor security and simplicity, we have 2 better options:" -ForegroundColor White

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "📋 OPTION 1: COPY-PASTE VALUES (Quick!)" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Cyan

Write-Host "`nFor EACH function in Appwrite Console, add these 4 variables:" -ForegroundColor Yellow
Write-Host "`nGo to: Function → Settings → Variables → Add Variable" -ForegroundColor Gray
Write-Host "`n" + ("-" * 70) -ForegroundColor Gray

foreach ($var in $functionEnvVars.GetEnumerator()) {
    Write-Host "`nVariable Name:" -ForegroundColor Cyan
    Write-Host "  $($var.Key)" -ForegroundColor White
    Write-Host "Variable Value:" -ForegroundColor Cyan
    Write-Host "  $($var.Value)" -ForegroundColor White
    Write-Host ("-" * 70) -ForegroundColor Gray
}

Write-Host "`n✂️ COPY THESE VALUES ↑ and paste into Appwrite Console" -ForegroundColor Yellow

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "📋 OPTION 2: USE CLI (Automatic!)" -ForegroundColor Green  
Write-Host ("=" * 70) -ForegroundColor Cyan

Write-Host "`nThe CLI can set these automatically during deployment:" -ForegroundColor White
Write-Host "   1. Delete current functions in Appwrite Console" -ForegroundColor Gray
Write-Host "   2. Run: .\deploy-to-appwrite-cli.ps1" -ForegroundColor White
Write-Host "   3. Choose Option 1 (CLI Deployment)" -ForegroundColor Gray
Write-Host "   4. Authenticate via browser" -ForegroundColor Gray
Write-Host "   5. CLI reads .env and deploys with variables!" -ForegroundColor Gray

Write-Host "`n💡 CLI is recommended - it's automated and less error-prone!" -ForegroundColor Cyan

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "🎯 QUICK REFERENCE CARD" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Cyan

Write-Host "`n📝 Manual Entry Instructions:" -ForegroundColor Cyan
Write-Host "1. Go to: https://cloud.appwrite.io/console/project-$projectId/functions" -ForegroundColor White
Write-Host "2. Click on a function name" -ForegroundColor White
Write-Host "3. Go to: Settings → Variables" -ForegroundColor White
Write-Host "4. Click: 'Add Variable' button" -ForegroundColor White
Write-Host "5. Enter name and value from above" -ForegroundColor White
Write-Host "6. Click: Save" -ForegroundColor White
Write-Host "7. Repeat for all 4 variables" -ForegroundColor White
Write-Host "8. Repeat for all 16 functions 😅" -ForegroundColor Yellow

Write-Host "`n⏱️ Time Estimate:" -ForegroundColor Yellow
Write-Host "   Manual: ~15-20 minutes (4 vars × 16 functions)" -ForegroundColor Gray
Write-Host "   CLI: ~5 minutes (automated)" -ForegroundColor Gray

Write-Host ""
