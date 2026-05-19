# Airbyte Docker Startup Script for Bentley Budget Bot
# This script starts Airbyte in Docker containers

# Set encoding
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🔄 Bentley Budget Bot - Airbyte Docker Setup" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""

$scriptDir = $PSScriptRoot
$repoRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$composeCandidates = @(
    (Join-Path $repoRoot "docker\docker-compose-airbyte-fixed.yml"),
    (Join-Path $repoRoot "docker\docker-compose-airbyte-simple.yml"),
    (Join-Path $repoRoot "docker\docker-compose-airbyte.yml")
)
$composeFile = $composeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $composeFile) {
    throw "No Airbyte compose file found. Expected one of: docker-compose-airbyte-fixed.yml, docker-compose-airbyte-simple.yml, docker-compose-airbyte.yml"
}

# Check if Docker is running
Write-Host "🐳 Checking Docker status..." -ForegroundColor Cyan
$dockerStatus = docker info 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Stop existing Airbyte containers
Write-Host "🛑 Stopping existing Airbyte containers..." -ForegroundColor Yellow
docker-compose -f $composeFile down

# Pull latest Airbyte images
Write-Host "📦 Pulling latest Airbyte images (this may take a while)..." -ForegroundColor Cyan
docker-compose -f $composeFile pull

# Start Airbyte services
Write-Host "🚀 Starting Airbyte services..." -ForegroundColor Cyan
Write-Host "   - Compose file: $composeFile" -ForegroundColor White
Write-Host "   - PostgreSQL Database (internal)" -ForegroundColor White
Write-Host "   - Airbyte Server (API - port 8001)" -ForegroundColor White  
Write-Host "   - Airbyte Web UI (port 8000)" -ForegroundColor White
Write-Host "   - Airbyte Worker" -ForegroundColor White
Write-Host "   - Airbyte Scheduler" -ForegroundColor White

docker-compose -f $composeFile up -d

Write-Host ""
Write-Host "⏳ Waiting for Airbyte to initialize (this can take 2-3 minutes)..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

# Check status
Write-Host "📊 Checking Airbyte service status..." -ForegroundColor Cyan
docker-compose -f $composeFile ps

Write-Host ""
Write-Host "🎉 Airbyte Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access Points:" -ForegroundColor Yellow
Write-Host "   • Airbyte Web UI:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "   • Airbyte API:     http://localhost:8001" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔧 Integration with Airflow:" -ForegroundColor Yellow
Write-Host "   • Airflow should target the Airbyte API service on port 8001" -ForegroundColor White
Write-Host "   • When running in Docker, use http://airbyte-server:8001/api/v1" -ForegroundColor White
Write-Host ""
Write-Host "📝 Useful commands:" -ForegroundColor Cyan
Write-Host "   View logs:     docker-compose -f $composeFile logs -f" -ForegroundColor White
Write-Host "   Stop Airbyte:  docker-compose -f $composeFile down" -ForegroundColor White
Write-Host "   Restart:       .\start_airbyte_docker.ps1" -ForegroundColor White
Write-Host ""
Write-Host "🔄 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Visit http://localhost:8000 to configure data sources" -ForegroundColor White
Write-Host "   2. Create connections between your data sources and destinations" -ForegroundColor White
Write-Host "   3. Update the CONNECTION_ID in your Airflow DAG (.vscode/Airbyt_sync_DAG.py)" -ForegroundColor White
Write-Host "   4. Test the integration with your Airflow setup" -ForegroundColor White