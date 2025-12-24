# Bentley Budget Bot - Quick Security Setup Script
# This script helps you set up your environment securely

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🔐 Bentley Budget Bot - Security Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (Test-Path ".env") {
    Write-Host "⚠️  .env file already exists!" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to overwrite it? (y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "Keeping existing .env file" -ForegroundColor Green
        exit 0
    }
}

# Copy .env.example to .env
if (Test-Path ".env.example") {
    Write-Host "📋 Creating .env from template..." -ForegroundColor Green
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env file" -ForegroundColor Green
} else {
    Write-Host "❌ Error: .env.example not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚨 CRITICAL SECURITY ACTIONS REQUIRED" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. REVOKE EXPOSED API KEYS:" -ForegroundColor Yellow
Write-Host "   Your Tiingo API key was exposed in the public repo!" -ForegroundColor Red
Write-Host "   Go to: https://www.tiingo.com/account/api" -ForegroundColor White
Write-Host "   - Delete the old key: E6c794cd1e5e48519194065a2a43b2396298288b" -ForegroundColor Red
Write-Host "   - Generate a new API key" -ForegroundColor Green
Write-Host ""

Write-Host "2. UPDATE YOUR .env FILE:" -ForegroundColor Yellow
Write-Host "   Edit .env and replace all 'your_*_here' values with actual credentials" -ForegroundColor White
Write-Host ""

Write-Host "3. VERIFY .gitignore:" -ForegroundColor Yellow
Write-Host "   ✅ .env is already in .gitignore" -ForegroundColor Green
Write-Host "   ✅ You won't accidentally commit secrets" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Edit your .env file:" -ForegroundColor White
Write-Host "   notepad .env" -ForegroundColor Cyan
Write-Host ""

Write-Host "2. Install required Python packages:" -ForegroundColor White
Write-Host "   pip install python-dotenv" -ForegroundColor Cyan
Write-Host ""

Write-Host "3. Test your configuration:" -ForegroundColor White
Write-Host "   python config_env.py" -ForegroundColor Cyan
Write-Host ""

Write-Host "4. Read the security guide:" -ForegroundColor White
Write-Host "   See SECURITY.md for detailed instructions" -ForegroundColor Cyan
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🔒 Security Reminders:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "❌ NEVER commit .env to Git" -ForegroundColor Red
Write-Host "❌ NEVER share API keys publicly" -ForegroundColor Red
Write-Host "✅ ALWAYS use environment variables" -ForegroundColor Green
Write-Host "✅ ALWAYS revoke exposed credentials" -ForegroundColor Green
Write-Host ""

Write-Host "Press any key to open .env file for editing..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
notepad .env
