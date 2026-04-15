#!/usr/bin/env pwsh
# Fix stuck/restarting services
# Handles MLflow and Airbyte startup issues

Write-Host "🔧 Service Recovery Script" -ForegroundColor Cyan
Write-Host "========================`n" -ForegroundColor Cyan

Write-Host "🔍 Checking service health..." -ForegroundColor Yellow

# Check for restarting containers
$RestartingContainers = docker ps --filter "status=restarting" --format "{{.Names}}"

if ($RestartingContainers) {
    Write-Host "⚠️  Found restarting containers:" -ForegroundColor Red
    $RestartingContainers | ForEach-Object {
        Write-Host "   - $_" -ForegroundColor White
    }
    
    Write-Host "`n🔄 Attempting recovery..." -ForegroundColor Yellow
    
    # Fix MLflow if restarting
    if ($RestartingContainers -match "mlflow") {
        Write-Host "`n📊 Restarting MLflow..." -ForegroundColor Cyan
        docker restart bentley-mlflow
        Start-Sleep -Seconds 5
    }
    
    # Fix Airbyte server if restarting
    if ($RestartingContainers -match "airbyte-server") {
        Write-Host "`n🔄 Restarting Airbyte services in correct order..." -ForegroundColor Cyan
        docker restart bentley-airbyte-temporal
        Start-Sleep -Seconds 10
        docker restart bentley-airbyte-server
        Start-Sleep -Seconds 5
        docker restart bentley-airbyte-worker
    }
    
    Write-Host "`n⏳ Waiting for services to stabilize (30s)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
} else {
    Write-Host "✅ No restarting containers found" -ForegroundColor Green
}

Write-Host "`n📊 Current Status:" -ForegroundColor Cyan
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String -Pattern "bentley-|NAMES"

Write-Host "`n💡 To open dashboard: .\open_dashboard.ps1" -ForegroundColor Yellow
