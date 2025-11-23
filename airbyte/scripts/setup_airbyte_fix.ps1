# Quick Airbyte Setup Script
# This uses the official Airbyte local installation

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   Airbyte Quick Setup for Bentley Budget Bot" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 Current Situation:" -ForegroundColor Yellow
Write-Host "   • Airflow: ✅ Working (http://localhost:8080)" -ForegroundColor Green
Write-Host "   • MLflow: ⏳ Starting up" -ForegroundColor Yellow  
Write-Host "   • Airbyte: ❌ Configuration issues" -ForegroundColor Red
Write-Host ""

Write-Host "🎯 Recommended Solution:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Option 1: Airbyte Cloud (EASIEST - Recommended)" -ForegroundColor Green
Write-Host "   • Go to: https://cloud.airbyte.com"
Write-Host "   • Sign up for free"
Write-Host "   • Configure sources/destinations in UI"
Write-Host "   • Get API key for Airflow integration"
Write-Host "   • No Docker headaches!"
Write-Host ""

Write-Host "Option 2: Use abctl (Official CLI)" -ForegroundColor Yellow
Write-Host "   Run these commands:"
Write-Host "   curl -LsfS https://get.airbyte.com | bash -" -ForegroundColor Cyan
Write-Host "   abctl local install" -ForegroundColor Cyan
Write-Host ""

Write-Host "Option 3: Continue with Docker (Advanced)" -ForegroundColor Yellow  
Write-Host "   This requires downloading official docker-compose"
Write-Host ""

Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$choice = Read-Host "What would you like to do? (1=Cloud Setup Guide, 2=Try abctl, 3=Skip for now)"

switch ($choice) {
    "1" {
        Write-Host "`n✅ Opening Airbyte Cloud..." -ForegroundColor Green
        Start-Process "https://cloud.airbyte.com"
        Write-Host "`nFollow these steps:" -ForegroundColor Cyan
        Write-Host "1. Create free account"
        Write-Host "2. Click 'Create Source' to add data sources"
        Write-Host "3. Click 'Create Destination' for your database"
        Write-Host "4. Create connections between sources and destinations"
        Write-Host "5. Get your API key from Settings > API Keys"
        Write-Host "6. Update your Airflow DAGs with the cloud API endpoint"
    }
    "2" {
        Write-Host "`n📥 Installing abctl..." -ForegroundColor Yellow
        Write-Host "This requires WSL (Windows Subsystem for Linux)" -ForegroundColor Yellow
        Write-Host "`nRun this in WSL/PowerShell:" -ForegroundColor Cyan
        Write-Host "curl -LsfS https://get.airbyte.com | bash -" -ForegroundColor White
    }
    "3" {
        Write-Host "`n👍 No problem! You can:" -ForegroundColor Green
        Write-Host "   • Focus on Airflow and MLflow for now"
        Write-Host "   • Use direct database connections"
        Write-Host "   • Come back to Airbyte later"
        Write-Host "`nYour Airflow is working great - start building DAGs!"
    }
    default {
        Write-Host "`nSee AIRBYTE_FIX_GUIDE.md for detailed options" -ForegroundColor Cyan
    }
}

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host ""
