# Save Plaid Logo
# This script helps you save the Plaid logo to the correct location

Write-Host "📥 Plaid Logo Setup" -ForegroundColor Cyan
Write-Host "=" * 60

$logoPath = "c:\Users\winst\BentleyBudgetBot\resources\images\plaid_logo.png"
$logoDir = Split-Path $logoPath -Parent

# Create directory if it doesn't exist
if (-not (Test-Path $logoDir)) {
    New-Item -ItemType Directory -Path $logoDir -Force | Out-Null
    Write-Host "✅ Created directory: $logoDir" -ForegroundColor Green
}

Write-Host ""
Write-Host "📋 Instructions to add Plaid logo:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Option 1: Save the PNG file you have" -ForegroundColor White
Write-Host "   1. Save your Plaid logo PNG file to:" -ForegroundColor Gray
Write-Host "      $logoPath" -ForegroundColor Cyan
Write-Host ""

Write-Host "Option 2: Download from Plaid Brand Assets" -ForegroundColor White
Write-Host "   1. Visit: https://plaid.com/company/brand/" -ForegroundColor Gray
Write-Host "   2. Download the Plaid logo PNG" -ForegroundColor Gray
Write-Host "   3. Save it to:" -ForegroundColor Gray
Write-Host "      $logoPath" -ForegroundColor Cyan
Write-Host ""

Write-Host "Option 3: Use PowerShell to copy from current location" -ForegroundColor White
Write-Host "   If you have the file already, copy it:" -ForegroundColor Gray
Write-Host "   Copy-Item 'C:\path\to\your\plaid_logo.png' '$logoPath'" -ForegroundColor Cyan
Write-Host ""

Write-Host "=" * 60
Write-Host ""

# Check if logo exists
if (Test-Path $logoPath) {
    Write-Host "✅ Plaid logo found at: $logoPath" -ForegroundColor Green
    
    # Get file info
    $fileInfo = Get-Item $logoPath
    Write-Host "   Size: $([math]::Round($fileInfo.Length / 1KB, 2)) KB" -ForegroundColor Gray
    Write-Host "   Modified: $($fileInfo.LastWriteTime)" -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "🚀 Ready to use! Restart your Streamlit app." -ForegroundColor Green
} else {
    Write-Host "⚠️  Logo not found. Please add the file to:" -ForegroundColor Yellow
    Write-Host "   $logoPath" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "💡 Tip: You can drag and drop the PNG file into VS Code" -ForegroundColor Gray
    Write-Host "   at: resources/images/" -ForegroundColor Gray
}

Write-Host ""
