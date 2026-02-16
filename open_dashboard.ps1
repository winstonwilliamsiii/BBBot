#!/usr/bin/env pwsh
# Quick launcher for Service Dashboard
# Opens dashboard and checks service health

Write-Host "🚀 Bentley Budget Bot - Service Dashboard Launcher" -ForegroundColor Cyan
Write-Host "==================================================`n" -ForegroundColor Cyan

# Path to dashboard
$DashboardPath = "C:\Users\winst\BentleyBudgetBot\sites\Mansa_Bentley_Platform\service_dashboard.html"

# Check if file exists
if (Test-Path $DashboardPath) {
    Write-Host "✅ Opening Service Dashboard..." -ForegroundColor Green
    Start-Process $DashboardPath
    
    Write-Host "`n📊 Quick Service Status:" -ForegroundColor Yellow
    docker ps --format "table {{.Names}}\t{{.Status}}" | Select-String -Pattern "bentley-|NAMES"
    
    Write-Host "`n💡 TIP: If services show errors in dashboard:" -ForegroundColor Cyan
    Write-Host "   Run: .\fix_services.ps1" -ForegroundColor White
    Write-Host "`n🌐 Direct Service Links:" -ForegroundColor Yellow
    Write-Host "   • Streamlit:  http://localhost:8501" -ForegroundColor White
    Write-Host "   • Airflow:    http://localhost:8080" -ForegroundColor White  
    Write-Host "   • MLflow:     http://localhost:5000" -ForegroundColor White
    Write-Host "   • Airbyte:    http://localhost:8000" -ForegroundColor White
} else {
    Write-Host "❌ Dashboard file not found at:" -ForegroundColor Red
    Write-Host "   $DashboardPath" -ForegroundColor White
}
