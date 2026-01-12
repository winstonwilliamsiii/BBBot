# 🚀 Appwrite Functions Deployment Script
# This script creates deployment packages and provides manual upload instructions

param(
    [switch]$CreatePackages = $false,
    [switch]$Help = $false
)

if ($Help) {
    Write-Host @"

🚀 Appwrite Functions Deployment Script

USAGE:
    .\deploy_appwrite_functions.ps1 -CreatePackages

OPTIONS:
    -CreatePackages    Create ZIP files for manual upload
    -Help              Show this help message

MANUAL DEPLOYMENT PROCESS:
    1. Run with -CreatePackages to create ZIP files
    2. Go to https://cloud.appwrite.io/console/project-68869ef500017ca73772/functions
    3. Click "Create Function" for each ZIP file
    4. Upload the corresponding ZIP file
    5. Set Runtime: Node.js 18.0
    6. Entry Point: index.js
    7. Add environment variables
    8. Deploy and get Function ID

"@
    exit 0
}

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "🚀 APPWRITE FUNCTIONS DEPLOYMENT" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

# Load environment variables
Write-Host "`n📋 Step 1: Loading Appwrite configuration..." -ForegroundColor Yellow
$envPath = ".\.env"
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.+)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [System.Environment]::SetEnvironmentVariable($key, $value, 'Process')
        }
    }
    Write-Host "✅ Configuration loaded from .env" -ForegroundColor Green
} else {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    exit 1
}

$endpoint = $env:APPWRITE_ENDPOINT
$projectId = $env:APPWRITE_PROJECT_ID
$apiKey = $env:APPWRITE_API_KEY

Write-Host "`n📊 Appwrite Configuration:" -ForegroundColor Cyan
Write-Host "   Endpoint: $endpoint" -ForegroundColor White
Write-Host "   Project ID: $projectId" -ForegroundColor White
Write-Host "   API Key: $($apiKey.Substring(0,20))..." -ForegroundColor White

if ($CreatePackages) {
    Write-Host "`n📦 Step 2: Creating deployment packages..." -ForegroundColor Yellow
    
    # Run the package creator script
    if (Test-Path ".\create_deployment_packages.ps1") {
        & .\create_deployment_packages.ps1
    } else {
        Write-Host "❌ create_deployment_packages.ps1 not found!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "`n⚠️  CLI deployment is not fully supported due to authentication." -ForegroundColor Yellow
    Write-Host "   Appwrite CLI requires interactive login which cannot be automated." -ForegroundColor Gray
    
    Write-Host "`n📋 RECOMMENDED APPROACH: Manual Upload via Console" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Gray
    
    Write-Host "`n1️⃣ Create Deployment Packages:" -ForegroundColor Yellow
    Write-Host "   .\deploy_appwrite_functions.ps1 -CreatePackages" -ForegroundColor White
    
    Write-Host "`n2️⃣ Go to Appwrite Console:" -ForegroundColor Yellow
    Write-Host "   https://cloud.appwrite.io/console/project-$projectId/functions" -ForegroundColor White
    
    Write-Host "`n3️⃣ For Each Function:" -ForegroundColor Yellow
    Write-Host "   a) Click 'Create Function'" -ForegroundColor White
    Write-Host "   b) Name: [function name]" -ForegroundColor White
    Write-Host "   c) Runtime: Node.js 18.0" -ForegroundColor White
    Write-Host "   d) Execute Access: Any (or specific roles)" -ForegroundColor White
    Write-Host "   e) Upload corresponding ZIP from appwrite-deployments\" -ForegroundColor White
    Write-Host "   f) Entry Point: index.js" -ForegroundColor White
    Write-Host "   g) Add these environment variables:" -ForegroundColor White
    Write-Host "      - APPWRITE_FUNCTION_ENDPOINT=$endpoint" -ForegroundColor Gray
    Write-Host "      - APPWRITE_FUNCTION_PROJECT_ID=$projectId" -ForegroundColor Gray
    Write-Host "      - APPWRITE_API_KEY=$apiKey" -ForegroundColor Gray
    Write-Host "      - APPWRITE_DATABASE_ID=[your_database_id]" -ForegroundColor Gray
    Write-Host "   h) Click 'Create Deployment'" -ForegroundColor White
    Write-Host "   i) Wait for build (green checkmark)" -ForegroundColor White
    Write-Host "   j) Copy Function ID for .env file" -ForegroundColor White
    
    Write-Host "`n4️⃣ Priority Functions to Deploy First:" -ForegroundColor Yellow
    $priorityFunctions = @(
        "get_transactions_streamlit",
        "add_to_watchlist_streamlit",
        "get_watchlist_streamlit",
        "get_user_profile_streamlit"
    )
    
    foreach ($func in $priorityFunctions) {
        Write-Host "   ✓ $func.zip" -ForegroundColor White
    }
    
    Write-Host "`n5️⃣ After Deployment:" -ForegroundColor Yellow
    Write-Host "   Update .env with Function IDs:" -ForegroundColor White
    Write-Host "   APPWRITE_FUNCTION_ID_GET_TRANSACTIONS=[function_id]" -ForegroundColor Gray
    Write-Host "   APPWRITE_FUNCTION_ID_ADD_WATCHLIST=[function_id]" -ForegroundColor Gray
    Write-Host "   APPWRITE_FUNCTION_ID_GET_WATCHLIST=[function_id]" -ForegroundColor Gray
    Write-Host "   APPWRITE_FUNCTION_ID_GET_PROFILE=[function_id]" -ForegroundColor Gray
    
    Write-Host "`n📚 Full Guide: See APPWRITE_DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan
    
    Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
    Write-Host "💡 TIP: Run with -CreatePackages to generate ZIP files" -ForegroundColor Yellow
    Write-Host ("=" * 70) -ForegroundColor Cyan
}

Write-Host ""
