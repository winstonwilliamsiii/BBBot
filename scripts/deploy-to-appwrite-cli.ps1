# deploy-to-appwrite-cli.ps1
# Bulk deploy Appwrite functions using CLI

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "🚀 APPWRITE CLI BULK DEPLOYMENT" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

# Check if Appwrite CLI is installed
Write-Host "`n🔍 Checking Appwrite CLI..." -ForegroundColor Yellow
$appwriteCheck = Get-Command appwrite -ErrorAction SilentlyContinue
if (-not $appwriteCheck) {
    Write-Host "❌ Appwrite CLI not installed!" -ForegroundColor Red
    Write-Host "Installing..." -ForegroundColor Yellow
    npm install -g appwrite-cli
}

Write-Host "✅ Appwrite CLI ready" -ForegroundColor Green
appwrite --version

# Load environment variables from .env
Write-Host "`n📋 Loading configuration from .env..." -ForegroundColor Yellow
$envPath = ".\.env"
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.+)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [System.Environment]::SetEnvironmentVariable($key, $value, 'Process')
        }
    }
    Write-Host "✅ Configuration loaded" -ForegroundColor Green
} else {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    exit 1
}

Write-Host "`n⚠️  APPWRITE CLI AUTHENTICATION REQUIRED" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Gray
Write-Host "`nThe Appwrite CLI needs authentication to deploy functions." -ForegroundColor White
Write-Host "You have two options:" -ForegroundColor White

Write-Host "`n📋 OPTION 1: Interactive Login (Browser)" -ForegroundColor Cyan
Write-Host "   Pro: Easy, uses your existing account" -ForegroundColor Gray
Write-Host "   Con: Requires browser interaction" -ForegroundColor Gray
Write-Host "   Command: appwrite login" -ForegroundColor White

Write-Host "`n📋 OPTION 2: Manual Upload (Recommended)" -ForegroundColor Cyan
Write-Host "   Pro: No CLI issues, visual feedback" -ForegroundColor Gray
Write-Host "   Con: Manual work (but only ~10 minutes)" -ForegroundColor Gray
Write-Host "   Steps:" -ForegroundColor White
Write-Host "   1. Go to: https://cloud.appwrite.io/console/project-68869ef500017ca73772/functions" -ForegroundColor Gray
Write-Host "   2. Click 'Create Function'" -ForegroundColor Gray
Write-Host "   3. Upload .tar.gz files from: appwrite-deployments-targz\" -ForegroundColor Gray
Write-Host "   4. Configure and deploy" -ForegroundColor Gray

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
$choice = Read-Host "Choose option (1 for CLI, 2 for Manual, Q to quit)"

if ($choice -eq "1") {
    Write-Host "`n🔐 Starting Appwrite CLI login..." -ForegroundColor Cyan
    Write-Host "A browser window will open for authentication." -ForegroundColor Gray
    Write-Host ""
    
    appwrite login --endpoint https://fra.cloud.appwrite.io/v1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Login successful!" -ForegroundColor Green
        
        # Initialize project
        Write-Host "`n📋 Initializing Appwrite project..." -ForegroundColor Yellow
        appwrite init project --projectId 68869ef500017ca73772
        
        Write-Host "`n🚀 Deploying functions..." -ForegroundColor Cyan
        Write-Host "This will deploy all 16 functions to Appwrite Cloud." -ForegroundColor Gray
        Write-Host "Estimated time: 5-10 minutes" -ForegroundColor Gray
        Write-Host ""
        
        $confirm = Read-Host "Ready to deploy? (Y/N)"
        if ($confirm -eq "Y" -or $confirm -eq "y") {
            # Deploy using appwrite.json
            appwrite push function
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "`n✅ Deployment complete!" -ForegroundColor Green
                Write-Host "`n📋 Next steps:" -ForegroundColor Yellow
                Write-Host "   1. Copy Function IDs from Appwrite Console" -ForegroundColor White
                Write-Host "   2. Update .env with Function IDs" -ForegroundColor White
                Write-Host "   3. Restart Streamlit" -ForegroundColor White
            } else {
                Write-Host "`n❌ Deployment failed!" -ForegroundColor Red
                Write-Host "Check error messages above and try manual upload." -ForegroundColor Yellow
            }
        } else {
            Write-Host "`n❌ Deployment cancelled" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`n❌ Login failed!" -ForegroundColor Red
        Write-Host "Try Option 2 (Manual Upload) instead." -ForegroundColor Yellow
    }
    
} elseif ($choice -eq "2") {
    Write-Host "`n📦 Manual Upload Selected" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Gray
    
    Write-Host "`n✅ TAR.GZ files ready in: appwrite-deployments-targz\" -ForegroundColor Green
    Write-Host "`n📋 Priority Functions to Deploy First:" -ForegroundColor Yellow
    Write-Host "   1. get_transactions_streamlit.tar.gz" -ForegroundColor White
    Write-Host "   2. add_to_watchlist_streamlit.tar.gz" -ForegroundColor White
    Write-Host "   3. get_watchlist_streamlit.tar.gz" -ForegroundColor White
    Write-Host "   4. get_user_profile_streamlit.tar.gz" -ForegroundColor White
    
    Write-Host "`n📝 For Each Function:" -ForegroundColor Yellow
    Write-Host "   1. Go to Appwrite Console → Functions → Create Function" -ForegroundColor White
    Write-Host "   2. Name: [function name]" -ForegroundColor White
    Write-Host "   3. Runtime: Node.js 18.0" -ForegroundColor White
    Write-Host "   4. Execute Access: Any" -ForegroundColor White
    Write-Host "   5. Upload corresponding .tar.gz file" -ForegroundColor White
    Write-Host "   6. Entry Point: index.js" -ForegroundColor White
    Write-Host "   7. Add environment variables (see DEPLOYMENT_INSTRUCTIONS.txt)" -ForegroundColor White
    Write-Host "   8. Deploy and copy Function ID" -ForegroundColor White
    
    Write-Host "`n💡 Opening deployment folder and browser..." -ForegroundColor Cyan
    Start-Sleep -Seconds 2
    
    # Open deployment folder
    explorer .\appwrite-deployments-targz
    
    # Open Appwrite Console
    Start-Process "https://cloud.appwrite.io/console/project-68869ef500017ca73772/functions"
    
    Write-Host "`n✅ Folders and browser opened!" -ForegroundColor Green
    Write-Host "Follow the steps above to deploy each function." -ForegroundColor White
    
} else {
    Write-Host "`n❌ Deployment cancelled" -ForegroundColor Yellow
}

Write-Host ""
