# Appwrite Functions - Fix Shared Folder Structure
# This script:
# 1. Removes any nested _shared folders
# 2. Copies clean _shared/appwriteClient.js to each function
# 3. Fixes require paths in index.js files

Write-Host "`n🔧 FIXING APPWRITE FUNCTIONS STRUCTURE..." -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Gray

# Change to appwrite-functions directory
$functionsDir = "c:\Users\winst\BentleyBudgetBot\appwrite-functions"
Set-Location $functionsDir

# Source _shared file
$sourceSharedFile = Join-Path $functionsDir "_shared\appwriteClient.js"

if (-Not (Test-Path $sourceSharedFile)) {
    Write-Host "❌ Source file not found: $sourceSharedFile" -ForegroundColor Red
    exit 1
}

Write-Host "`n📁 Source: _shared\appwriteClient.js" -ForegroundColor Yellow

# Get all function directories (exclude _shared itself)
$functionDirs = Get-ChildItem -Directory | Where-Object { $_.Name -ne "_shared" }

Write-Host "`n🧹 Step 1: Cleaning nested _shared folders..." -ForegroundColor Cyan
foreach ($funcDir in $functionDirs) {
    $nestedShared = Join-Path $funcDir.FullName "_shared\_shared"
    if (Test-Path $nestedShared) {
        Remove-Item -Path $nestedShared -Recurse -Force
        Write-Host "  ✅ Removed nested: $($funcDir.Name)\_shared\_shared" -ForegroundColor Green
    }
}

Write-Host "`n📋 Step 2: Copying _shared to all functions..." -ForegroundColor Cyan
foreach ($funcDir in $functionDirs) {
    $targetSharedDir = Join-Path $funcDir.FullName "_shared"
    
    # Remove existing _shared and recreate clean
    if (Test-Path $targetSharedDir) {
        Remove-Item -Path $targetSharedDir -Recurse -Force
    }
    
    New-Item -ItemType Directory -Path $targetSharedDir -Force | Out-Null
    Copy-Item $sourceSharedFile -Destination $targetSharedDir -Force
    
    Write-Host "  ✅ $($funcDir.Name)\_shared\appwriteClient.js" -ForegroundColor Green
}

Write-Host "`n🔧 Step 3: Fixing require paths in index.js..." -ForegroundColor Cyan
foreach ($funcDir in $functionDirs) {
    $indexFile = Join-Path $funcDir.FullName "index.js"
    if (Test-Path $indexFile) {
        $content = Get-Content $indexFile -Raw
        $originalContent = $content
        
        # Fix all variations to correct path
        $content = $content -replace "require\('\.\./_shared/appwriteClient'\)", "require('./_shared/appwriteClient')"
        $content = $content -replace "require\('\./_shared/_shared/appwriteClient'\)", "require('./_shared/appwriteClient')"
        
        if ($content -ne $originalContent) {
            $content | Set-Content $indexFile -NoNewline
            Write-Host "  ✅ Fixed require in: $($funcDir.Name)\index.js" -ForegroundColor Green
        }
    }
}

Write-Host "`n✅ ALL FUNCTIONS FIXED!" -ForegroundColor Green
Write-Host "   • Nested folders removed" -ForegroundColor White
Write-Host "   • Clean _shared copied to all functions" -ForegroundColor White
Write-Host "   • require paths corrected" -ForegroundColor White
Write-Host "`n🚀 Ready to deploy!" -ForegroundColor Cyan