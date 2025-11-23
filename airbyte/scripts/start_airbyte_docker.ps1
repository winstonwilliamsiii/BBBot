# Airbyte Docker Startup Script for Bentley Budget Bot
# This script starts Airbyte in Docker containers

# Set encoding
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🔄 Bentley Budget Bot - Airbyte Docker Setup" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""

# Check if Docker is running
Write-Host "🐳 Checking Docker status..." -ForegroundColor Cyan
$dockerStatus = docker info 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Stop existing Airbyte containers
Write-Host "🛑 Stopping existing Airbyte containers..." -ForegroundColor Yellow
docker-compose -f docker-compose-airbyte.yml down

# Pull latest Airbyte images
Write-Host "📦 Pulling latest Airbyte images (this may take a while)..." -ForegroundColor Cyan
docker-compose -f docker-compose-airbyte.yml pull

# Start Airbyte services
Write-Host "🚀 Starting Airbyte services..." -ForegroundColor Cyan
Write-Host "   - PostgreSQL Database (internal)" -ForegroundColor White
Write-Host "   - Airbyte Server (API - port 8001)" -ForegroundColor White  
Write-Host "   - Airbyte Web UI (port 8000)" -ForegroundColor White
Write-Host "   - Airbyte Worker" -ForegroundColor White
Write-Host "   - Airbyte Scheduler" -ForegroundColor White

docker-compose -f docker-compose-airbyte.yml up -d

Write-Host ""
Write-Host "⏳ Waiting for Airbyte to initialize (this can take 2-3 minutes)..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

# Check status
Write-Host "📊 Checking Airbyte service status..." -ForegroundColor Cyan
docker-compose -f docker-compose-airbyte.yml ps

Write-Host ""
Write-Host "🎉 Airbyte Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access Points:" -ForegroundColor Yellow
Write-Host "   • Airbyte Web UI:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "   • Airbyte API:     http://localhost:8001" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔧 Integration with Airflow:" -ForegroundColor Yellow
Write-Host "   • Your Airflow DAG is configured to use: http://localhost:8001" -ForegroundColor White
Write-Host "   • No additional configuration needed!" -ForegroundColor White
Write-Host ""
Write-Host "📝 Useful commands:" -ForegroundColor Cyan
Write-Host "   View logs:     docker-compose -f docker-compose-airbyte.yml logs -f" -ForegroundColor White
Write-Host "   Stop Airbyte:  docker-compose -f docker-compose-airbyte.yml down" -ForegroundColor White
Write-Host "   Restart:       .\start_airbyte_docker.ps1" -ForegroundColor White
Write-Host ""
Write-Host "🔄 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Visit http://localhost:8000 to configure data sources" -ForegroundColor White
Write-Host "   2. Create connections between your data sources and destinations" -ForegroundColor White
Write-Host "   3. Update the CONNECTION_ID in your Airflow DAG (.vscode/Airbyt_sync_DAG.py)" -ForegroundColor White
Write-Host "   4. Test the integration with your Airflow setup" -ForegroundColor White