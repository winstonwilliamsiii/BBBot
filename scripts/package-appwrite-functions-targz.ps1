# package-appwrite-functions-targz.ps1
# Package Appwrite functions as .tar.gz for CLI deployment
# Run from: C:\Users\winst\BentleyBudgetBot

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "📦 APPWRITE FUNCTIONS TAR.GZ PACKAGER" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

# Paths
$sourcePath = ".\appwrite-functions"
$outputPath = ".\appwrite-deployments-targz"

# Check if source exists
if (-not (Test-Path $sourcePath)) {
    Write-Host "`n❌ ERROR: appwrite-functions folder not found!" -ForegroundColor Red
    exit 1
}

# Create output directory
Write-Host "`n📁 Creating output directory..." -ForegroundColor Yellow
if (Test-Path $outputPath) {
    Write-Host "   Cleaning existing .tar.gz files..." -ForegroundColor Gray
    Remove-Item -Path "$outputPath\*.tar.gz" -Force -ErrorAction SilentlyContinue
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
    
    $funcPath = Join-Path $sourcePath $func
    
    # Check if function directory exists
    if (-not (Test-Path $funcPath)) {
        Write-Host "   ❌ Function directory not found: $funcPath" -ForegroundColor Red
        $failCount++
        continue
    }
    
    try {
        # Create temp directory for packaging
        $tempDir = Join-Path $outputPath "temp_$func"
        New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
        
        # Copy function files
        Copy-Item -Path "$funcPath\*" -Destination $tempDir -Recurse -Force
        
        # Copy shared folder
        $sharedPath = Join-Path $sourcePath "_shared"
        if (Test-Path $sharedPath) {
            Copy-Item -Path $sharedPath -Destination (Join-Path $tempDir "_shared") -Recurse -Force
        }
        
        # Create package.json if it doesn't exist
        $packageJsonPath = Join-Path $tempDir "package.json"
        if (-not (Test-Path $packageJsonPath)) {
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
            
            Set-Content -Path $packageJsonPath -Value $packageJson
        }
        
        # Create .tar.gz using tar command
        $tarGzPath = Join-Path $outputPath "$func.tar.gz"
        
        # Remove old tar.gz if exists
        if (Test-Path $tarGzPath) {
            Remove-Item -Path $tarGzPath -Force
        }
        
        # Create tar.gz using absolute paths
        $absoluteTempDir = (Resolve-Path $tempDir).Path
        $absoluteTarGzPath = (Resolve-Path $outputPath).Path + "\$func.tar.gz"
        
        # Change to temp directory
        Push-Location $absoluteTempDir
        
        # Create tar.gz with all content (use . to include everything)
        tar -czf $absoluteTarGzPath .
        
        Pop-Location
        
        # Check if tar.gz was created
        if (Test-Path $tarGzPath) {
            $tarGzSize = (Get-Item $tarGzPath).Length
            $tarGzSizeKB = [math]::Round($tarGzSize / 1KB, 2)
            
            Write-Host "   ✅ Created: " -NoNewline -ForegroundColor Green
            Write-Host "$func.tar.gz " -NoNewline -ForegroundColor White
            Write-Host "($tarGzSizeKB KB)" -ForegroundColor Gray
            
            $successCount++
            $packagedFiles += [PSCustomObject]@{
                Name = $func
                File = "$func.tar.gz"
                Size = $tarGzSizeKB
                Path = $tarGzPath
            }
        } else {
            Write-Host "   ❌ Failed to create tar.gz" -ForegroundColor Red
            $failCount++
        }
        
        # Clean up temp directory
        Remove-Item -Path $tempDir -Recurse -Force
        
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

Write-Host "`n📁 Output Location:" -ForegroundColor Yellow
Write-Host "   $outputPath" -ForegroundColor White

Write-Host "`n🚀 Ready for Appwrite CLI Deployment!" -ForegroundColor Green
Write-Host "`nNext: Use Appwrite CLI to deploy:" -ForegroundColor Cyan
Write-Host "   cd appwrite-deployments-targz" -ForegroundColor White
Write-Host "   appwrite push function" -ForegroundColor White

Write-Host ""
