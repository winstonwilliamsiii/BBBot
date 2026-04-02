#!/usr/bin/env pwsh
# Quick launcher for the Streamlit-hosted Service Dashboard
# Opens the Streamlit app and points admins to the Services tab

Write-Host "🚀 Bentley Budget Bot - Service Dashboard Launcher" -ForegroundColor Cyan
Write-Host "==================================================`n" -ForegroundColor Cyan

$DashboardUrl = "http://localhost:8501"

Write-Host "✅ Opening Streamlit Service Dashboard..." -ForegroundColor Green
Start-Process $DashboardUrl

Write-Host "`n📍 Next step:" -ForegroundColor Yellow
Write-Host "   Open '🔧 Admin Control Center' and select the '🖥️ Services' tab." -ForegroundColor White

Write-Host "`n📊 Quick Service Status:" -ForegroundColor Yellow
docker ps --format "table {{.Names}}\t{{.Status}}" | Select-String -Pattern "bentley-|NAMES"

Write-Host "`n💡 TIP: If services show errors in dashboard:" -ForegroundColor Cyan
Write-Host "   Run: .\fix_services.ps1" -ForegroundColor White
Write-Host "`n🌐 Direct Service Links:" -ForegroundColor Yellow
Write-Host "   • Streamlit:  http://localhost:8501" -ForegroundColor White
Write-Host "   • Airflow:    http://localhost:8080" -ForegroundColor White
Write-Host "   • MLflow:     http://localhost:5000" -ForegroundColor White
Write-Host "   • Airbyte:    http://localhost:8000" -ForegroundColor White
