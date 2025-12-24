# 📦 Appwrite Functions Deployment Package Creator
# This script creates ready-to-upload ZIP files for all Appwrite Functions

$functionsPath = "C:\Users\winst\BentleyBudgetBot\appwrite-functions"
$outputPath = "C:\Users\winst\BentleyBudgetBot\appwrite-deployments"

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "📦 APPWRITE FUNCTIONS DEPLOYMENT PACKAGER" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan

# Create output directory
Write-Host "`n📁 Creating output directory..." -ForegroundColor Yellow
if (Test-Path $outputPath) {
    Write-Host "   Cleaning existing packages..." -ForegroundColor Gray
    Remove-Item -Path "$outputPath\*.zip" -Force -ErrorAction SilentlyContinue
} else {
    New-Item -ItemType Directory -Force -Path $outputPath | Out-Null
}
Write-Host "   ✅ Output directory ready: $outputPath" -ForegroundColor Green

# List of functions to package
$functions = @(
    "create_transaction",
    "get_transactions",
    "get_transactions_streamlit",
    "add_to_watchlist_streamlit",
    "get_watchlist_streamlit",
    "get_user_profile_streamlit",
    "create_audit_log",
    "get_audit_logs",
    "create_payment",
    "get_payments",
    "manage_roles",
    "manage_permissions",
    "create_bot_metric",
    "get_bot_metrics",
    "get_bot_metrics_stats",
    "create_all_indexes"
)

Write-Host "`n📋 Functions to package: $($functions.Count)" -ForegroundColor Yellow
Write-Host ""

$successCount = 0
$failCount = 0
$packagedFiles = @()

foreach ($func in $functions) {
    Write-Host "📦 Packaging: " -NoNewline -ForegroundColor Cyan
    Write-Host $func -ForegroundColor White
    
    $funcPath = Join-Path $functionsPath $func
    
    # Check if function directory exists
    if (-not (Test-Path $funcPath)) {
        Write-Host "   ❌ Function directory not found: $funcPath" -ForegroundColor Red
        $failCount++
        continue
    }
    
    try {
        # Create temp directory
        $tempDir = Join-Path $outputPath "temp_$func"
        New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
        
        # Copy function files
        Copy-Item -Path "$funcPath\*" -Destination $tempDir -Recurse -Force
        
        # Copy shared folder if exists
        $sharedPath = Join-Path $functionsPath "_shared"
        if (Test-Path $sharedPath) {
            Copy-Item -Path $sharedPath -Destination (Join-Path $tempDir "_shared") -Recurse -Force
        }
        
        # Create package.json
        $packageJson = @{
            name = $func
            version = "1.0.0"
            description = "Appwrite Function: $func"
            main = "index.js"
            scripts = @{
                start = "node index.js"
            }
            dependencies = @{
                "node-appwrite" = "^11.0.0"
            }
        } | ConvertTo-Json -Depth 10
        
        Set-Content -Path (Join-Path $tempDir "package.json") -Value $packageJson
        
        # Create .gitignore
        $gitignore = @"
node_modules/
.env
*.log
"@
        Set-Content -Path (Join-Path $tempDir ".gitignore") -Value $gitignore
        
        # Create README
        $readme = @"
# $func

Appwrite Function for BentleyBot

## Deployment

1. Upload this ZIP to Appwrite Cloud Console
2. Select Runtime: Node.js 18.0 or later
3. Set Entry Point: index.js
4. Add environment variables:
   - APPWRITE_FUNCTION_ENDPOINT
   - APPWRITE_FUNCTION_PROJECT_ID
   - APPWRITE_API_KEY
   - APPWRITE_DATABASE_ID
5. Deploy and test

## Function ID

After deployment, copy the Function ID and add to your .env file:
``````env
APPWRITE_FUNCTION_ID_$(($func.ToUpper() -replace '-','_'))=your_function_id_here
``````
"@
        Set-Content -Path (Join-Path $tempDir "README.md") -Value $readme
        
        # Create zip
        $zipPath = Join-Path $outputPath "$func.zip"
        
        # Remove old zip if exists
        if (Test-Path $zipPath) {
            Remove-Item -Path $zipPath -Force
        }
        
        # Create new zip
        Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -CompressionLevel Optimal
        
        # Get zip size
        $zipSize = (Get-Item $zipPath).Length
        $zipSizeKB = [math]::Round($zipSize / 1KB, 2)
        
        Write-Host "   ✅ Created: " -NoNewline -ForegroundColor Green
        Write-Host "$func.zip " -NoNewline -ForegroundColor White
        Write-Host "($zipSizeKB KB)" -ForegroundColor Gray
        
        # Clean up temp
        Remove-Item -Path $tempDir -Recurse -Force
        
        $successCount++
        $packagedFiles += [PSCustomObject]@{
            Name = $func
            File = "$func.zip"
            Size = $zipSizeKB
            Path = $zipPath
        }
        
    } catch {
        Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
}

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "📊 PACKAGING COMPLETE" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

Write-Host "`n✅ Success: " -NoNewline -ForegroundColor Green
Write-Host "$successCount functions" -ForegroundColor White
if ($failCount -gt 0) {
    Write-Host "❌ Failed: " -NoNewline -ForegroundColor Red
    Write-Host "$failCount functions" -ForegroundColor White
}

# Calculate total size
$totalSize = ($packagedFiles | Measure-Object -Property Size -Sum).Sum
Write-Host "`n📦 Total Size: " -NoNewline -ForegroundColor Yellow
Write-Host "$([math]::Round($totalSize, 2)) KB" -ForegroundColor White

# Show packaged files
Write-Host "`n📋 Packaged Functions:" -ForegroundColor Yellow
Write-Host ""
$packagedFiles | Format-Table -AutoSize | Out-String | ForEach-Object { 
    $_ -split "`n" | ForEach-Object { 
        if ($_.Trim()) { Write-Host "   $_" -ForegroundColor White }
    }
}

# Create deployment instructions
$instructionsPath = Join-Path $outputPath "DEPLOYMENT_INSTRUCTIONS.txt"
$instructions = @"
🚀 APPWRITE FUNCTIONS DEPLOYMENT INSTRUCTIONS
==============================================

📦 Package Location: $outputPath
📋 Total Functions: $successCount
📏 Total Size: $([math]::Round($totalSize, 2)) KB

STEP-BY-STEP DEPLOYMENT:
========================

1. Login to Appwrite Cloud
   URL: https://cloud.appwrite.io
   Select your project

2. Navigate to Functions
   Click "Functions" in left sidebar
   Click "Create Function" button

3. For Each Function ($successCount total):
   
   A. Basic Configuration:
      - Name: [function name without .zip]
      - Runtime: Node.js 18.0 or later
      - Execute Access: Any (or specific roles)
   
   B. Upload Code:
      - Click "Settings" tab
      - Scroll to "Deployment" section
      - Choose "Manual" deployment
      - Click "Upload" button
      - Select corresponding .zip file from:
        $outputPath
      - Entry Point: index.js
      - Click "Create Deployment"
   
   C. Environment Variables:
      Add these in "Variables" section:
      
      APPWRITE_FUNCTION_ENDPOINT=https://cloud.appwrite.io/v1
      APPWRITE_FUNCTION_PROJECT_ID=[your_project_id]
      APPWRITE_API_KEY=[your_server_api_key]
      APPWRITE_DATABASE_ID=[your_database_id]
      
      Replace values in [brackets] with your actual IDs
   
   D. Test Function:
      - Click "Execute" tab
      - Add test body (JSON)
      - Click "Execute Now"
      - Verify response
   
   E. Copy Function ID:
      - Click on function name
      - Copy Function ID (e.g., 6abc123def456...)
      - Save for .env file

4. Update Your .env File
   After deploying all functions, add Function IDs:
   
   APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
   APPWRITE_PROJECT_ID=your_project_id
   APPWRITE_DATABASE_ID=your_database_id
   APPWRITE_API_KEY=your_server_api_key
   
   # Function IDs
"@

# Add function ID placeholders
foreach ($func in $functions) {
    $envVar = "APPWRITE_FUNCTION_ID_$($func.ToUpper() -replace '-','_')"
    $instructions += "`n   $envVar=your_function_id_here"
}

$instructions += @"


PRIORITY DEPLOYMENT ORDER:
=========================

Deploy these first for core StreamLit functionality:
1. get_transactions_streamlit.zip
2. add_to_watchlist_streamlit.zip
3. get_watchlist_streamlit.zip
4. get_user_profile_streamlit.zip

Then deploy RBAC functions:
5. create_transaction.zip
6. get_transactions.zip

Then utilities:
7. create_all_indexes.zip (run once after deployment)

Then remaining functions as needed.

ESTIMATED TIME:
==============
- Per Function: 2-3 minutes
- Total Time: ~$([math]::Ceiling($successCount * 2.5)) minutes

VERIFICATION:
============
After each deployment:
☑ Function shows "Active" status (green)
☑ Latest deployment shows "Ready" (green checkmark)
☑ Test execution returns expected response
☑ Function ID copied to .env file

TROUBLESHOOTING:
===============
- "Module not found": Make sure package.json is included (it is!)
- "Cannot find _shared": Make sure _shared folder is in ZIP (it is!)
- "Timeout": Increase timeout in Function Settings (default 15s)
- "Invalid credentials": Check API key has correct scopes

SUPPORT:
========
- Appwrite Docs: https://appwrite.io/docs/functions
- Discord: https://appwrite.io/discord
- GitHub: https://github.com/appwrite/appwrite

Good luck with your deployment! 🚀
"@

Set-Content -Path $instructionsPath -Value $instructions
Write-Host "`n📄 Created: " -NoNewline -ForegroundColor Green
Write-Host "DEPLOYMENT_INSTRUCTIONS.txt" -ForegroundColor White

# Create deployment checklist
$checklistPath = Join-Path $outputPath "DEPLOYMENT_CHECKLIST.md"
$checklist = @"
# ✅ Appwrite Functions Deployment Checklist

## Before You Start
- [ ] Login to Appwrite Cloud (https://cloud.appwrite.io)
- [ ] Have your Project ID ready
- [ ] Have your Database ID ready
- [ ] Have your Server API Key ready
- [ ] All ZIP files ready in: $outputPath

## Core Functions (Priority)
- [ ] get_transactions_streamlit.zip → Function ID: __________________
- [ ] add_to_watchlist_streamlit.zip → Function ID: __________________
- [ ] get_watchlist_streamlit.zip → Function ID: __________________
- [ ] get_user_profile_streamlit.zip → Function ID: __________________

## RBAC Functions
- [ ] create_transaction.zip → Function ID: __________________
- [ ] get_transactions.zip → Function ID: __________________

## Audit Functions
- [ ] create_audit_log.zip → Function ID: __________________
- [ ] get_audit_logs.zip → Function ID: __________________

## Payment Functions
- [ ] create_payment.zip → Function ID: __________________
- [ ] get_payments.zip → Function ID: __________________

## RBAC Management
- [ ] manage_roles.zip → Function ID: __________________
- [ ] manage_permissions.zip → Function ID: __________________

## Bot Metrics
- [ ] create_bot_metric.zip → Function ID: __________________
- [ ] get_bot_metrics.zip → Function ID: __________________
- [ ] get_bot_metrics_stats.zip → Function ID: __________________

## Utilities
- [ ] create_all_indexes.zip → Function ID: __________________ (run once)

## After Deployment
- [ ] All functions show "Active" status
- [ ] All deployments show "Ready" status
- [ ] Updated .env file with all Function IDs
- [ ] Tested at least one function execution
- [ ] Restarted StreamLit app to load new .env

## Environment Variables Set
For each function, verify these variables are set:
- [ ] APPWRITE_FUNCTION_ENDPOINT
- [ ] APPWRITE_FUNCTION_PROJECT_ID
- [ ] APPWRITE_API_KEY
- [ ] APPWRITE_DATABASE_ID

---

**Deployment Date:** __________________
**Completed By:** __________________
**Notes:**

"@

Set-Content -Path $checklistPath -Value $checklist
Write-Host "📄 Created: " -NoNewline -ForegroundColor Green
Write-Host "DEPLOYMENT_CHECKLIST.md" -ForegroundColor White

# Final output
Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "🎉 ALL PACKAGES READY FOR DEPLOYMENT!" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Cyan

Write-Host "`n📁 Output Location:" -ForegroundColor Yellow
Write-Host "   $outputPath" -ForegroundColor White

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Open: $outputPath" -ForegroundColor White
Write-Host "   2. Read: DEPLOYMENT_INSTRUCTIONS.txt" -ForegroundColor White
Write-Host "   3. Use: DEPLOYMENT_CHECKLIST.md to track progress" -ForegroundColor White
Write-Host "   4. Go to: https://cloud.appwrite.io" -ForegroundColor White
Write-Host "   5. Start uploading the .zip files!" -ForegroundColor White

Write-Host "`n⏱️ Estimated deployment time: " -NoNewline -ForegroundColor Yellow
Write-Host "~$([math]::Ceiling($successCount * 2.5)) minutes for all $successCount functions" -ForegroundColor White

Write-Host "`n✨ Good luck with your deployment!" -ForegroundColor Green
Write-Host ""
