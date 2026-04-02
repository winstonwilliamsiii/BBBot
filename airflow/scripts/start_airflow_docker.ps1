# Airflow Docker Startup Script for Bentley Budget Bot
# This script handles the complete Docker setup for Airflow + Streamlit app

# Set encoding
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$composeFile = Join-Path $repoRoot "docker\docker-compose-airflow.yml"

Push-Location $repoRoot

Write-Host "🚀 Bentley Budget Bot - Docker Airflow Setup" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green
Write-Host ""

# Stop any existing containers first
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
docker compose -f $composeFile down

# Pull latest images
Write-Host "📦 Pulling latest Docker images..." -ForegroundColor Cyan
docker compose -f $composeFile pull

# Start the services
Write-Host "🔧 Starting Docker services..." -ForegroundColor Cyan
Write-Host "   - MySQL Database (host port 3307)" -ForegroundColor White
Write-Host "   - Redis Cache (port 6379)" -ForegroundColor White
Write-Host "   - Airflow Webserver (port 8080)" -ForegroundColor White
Write-Host "   - Airflow Scheduler" -ForegroundColor White
Write-Host "   - Airflow Worker" -ForegroundColor White
Write-Host "   - Streamlit App (port 8501)" -ForegroundColor White

docker compose -f $composeFile up -d

Write-Host ""
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check status
Write-Host "📊 Checking service status..." -ForegroundColor Cyan
docker compose -f $composeFile ps

Write-Host ""
Write-Host "🎉 Setup Complete! Access your applications:" -ForegroundColor Green
Write-Host "   🌐 Airflow UI:     http://localhost:8080" -ForegroundColor Yellow
Write-Host "   📊 Streamlit App:  http://localhost:8501" -ForegroundColor Yellow
Write-Host "   🗄️  MySQL:         localhost:3306" -ForegroundColor Yellow
Write-Host ""
Write-Host "🔐 Airflow Login:" -ForegroundColor Cyan
Write-Host "   Username: admin" -ForegroundColor White
Write-Host "   Password: admin" -ForegroundColor White
Write-Host ""
Write-Host "📝 Useful commands:" -ForegroundColor Cyan
Write-Host "   View logs:  docker compose -f docker\docker-compose-airflow.yml logs -f" -ForegroundColor White
Write-Host "   Stop all:   docker compose -f docker\docker-compose-airflow.yml down" -ForegroundColor White
Write-Host "   Restart:    .\start_airflow_docker.ps1" -ForegroundColor White

Pop-Location