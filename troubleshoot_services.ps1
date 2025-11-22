# Bentley Budget Bot - Service Troubleshooting Script
# Diagnoses common issues with Docker services

param(
    [switch]$Fix = $false  # Run with -Fix to attempt automatic fixes
)

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🔍 Bentley Budget Bot - Service Troubleshooting" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "1. Checking Docker status..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "   ✓ Docker is installed: $dockerVersion" -ForegroundColor Green
    
    docker ps | Out-Null
    Write-Host "   ✓ Docker daemon is running" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Docker is not running or not installed!" -ForegroundColor Red
    Write-Host "   → Please start Docker Desktop" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Check port availability
Write-Host "2. Checking port availability..." -ForegroundColor Yellow

$ports = @{
    "8501" = "Streamlit App"
    "8080" = "Airflow UI"
    "8000" = "Airbyte UI"
    "5000" = "MLflow UI"
    "3307" = "MySQL Database"
    "6379" = "Redis"
    "8001" = "Airbyte API"
}

$portsInUse = @()
foreach ($port in $ports.Keys) {
    $process = netstat -ano | Select-String ":$port " | Select-Object -First 1
    if ($process) {
        $processInfo = $process.ToString().Trim()
        if ($processInfo -match "LISTENING") {
            Write-Host "   ✓ Port $port ($($ports[$port])) is in use" -ForegroundColor Green
        } else {
            Write-Host "   ⚠ Port $port ($($ports[$port])) status: $processInfo" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ✗ Port $port ($($ports[$port])) is not in use" -ForegroundColor Red
        $portsInUse += $port
    }
}

Write-Host ""

# Check Docker containers
Write-Host "3. Checking Docker containers..." -ForegroundColor Yellow

$expectedContainers = @(
    "bentley-mysql",
    "bentley-redis",
    "bentley-airflow-webserver",
    "bentley-airflow-scheduler",
    "bentley-airflow-worker",
    "bentley-mlflow",
    "bentley-budget-bot",
    "bentley-airbyte-db",
    "bentley-airbyte-server",
    "bentley-airbyte-webapp",
    "bentley-airbyte-worker"
)

$runningContainers = docker ps --format "{{.Names}}"
$allContainers = docker ps -a --format "{{.Names}}"

foreach ($container in $expectedContainers) {
    if ($runningContainers -contains $container) {
        Write-Host "   ✓ $container is running" -ForegroundColor Green
    } elseif ($allContainers -contains $container) {
        Write-Host "   ⚠ $container exists but is not running" -ForegroundColor Yellow
        
        if ($Fix) {
            Write-Host "   → Attempting to start $container..." -ForegroundColor Cyan
            docker start $container | Out-Null
        }
    } else {
        Write-Host "   ✗ $container does not exist" -ForegroundColor Red
    }
}

Write-Host ""

# Check service health
Write-Host "4. Checking service health..." -ForegroundColor Yellow

$services = @{
    "http://localhost:8501/_stcore/health" = "Streamlit"
    "http://localhost:8080/health" = "Airflow"
    "http://localhost:5000/health" = "MLflow"
    "http://localhost:8000" = "Airbyte"
}

foreach ($url in $services.Keys) {
    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "   ✓ $($services[$url]) is healthy" -ForegroundColor Green
        } else {
            Write-Host "   ⚠ $($services[$url]) responded with status $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ✗ $($services[$url]) is not accessible" -ForegroundColor Red
        Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor DarkGray
    }
}

Write-Host ""

# Check Docker networks
Write-Host "5. Checking Docker networks..." -ForegroundColor Yellow

$networks = @("bentley-network", "airbyte-network")
$existingNetworks = docker network ls --format "{{.Name}}"

foreach ($network in $networks) {
    if ($existingNetworks -contains $network) {
        Write-Host "   ✓ $network exists" -ForegroundColor Green
    } else {
        Write-Host "   ✗ $network does not exist" -ForegroundColor Red
    }
}

Write-Host ""

# Check logs for common errors
Write-Host "6. Checking for common errors in logs..." -ForegroundColor Yellow

$criticalContainers = @(
    "bentley-airflow-webserver",
    "bentley-airbyte-webapp",
    "bentley-mlflow"
)

foreach ($container in $criticalContainers) {
    if ($runningContainers -contains $container) {
        $logs = docker logs $container --tail 50 2>&1
        
        if ($logs -match "error|exception|failed" -and $logs -notmatch "error_log") {
            Write-Host "   ⚠ Found errors in $container logs" -ForegroundColor Yellow
            Write-Host "     Run: docker logs $container" -ForegroundColor DarkGray
        } else {
            Write-Host "   ✓ No obvious errors in $container" -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan

# Summary and recommendations
Write-Host "`n📋 Summary & Recommendations:" -ForegroundColor Cyan

if ($portsInUse.Count -gt 0) {
    Write-Host "`n⚠ Services not listening on expected ports:" -ForegroundColor Yellow
    Write-Host "   This usually means services haven't started yet or failed to start." -ForegroundColor White
    Write-Host "   → Check container logs: docker logs <container-name>" -ForegroundColor Cyan
    Write-Host "   → Try restarting: .\manage_services.ps1 -Service all -Action stop" -ForegroundColor Cyan
    Write-Host "                     .\manage_services.ps1 -Service all -Action start" -ForegroundColor Cyan
}

Write-Host "`n🌐 Expected Access URLs:" -ForegroundColor Cyan
Write-Host "   • Streamlit:  http://localhost:8501" -ForegroundColor White
Write-Host "   • Airflow:    http://localhost:8080 (admin/admin)" -ForegroundColor White
Write-Host "   • Airbyte:    http://localhost:8000" -ForegroundColor White
Write-Host "   • MLflow:     http://localhost:5000" -ForegroundColor White

Write-Host "`n💡 Common Issues:" -ForegroundColor Cyan
Write-Host "   1. Services starting slowly: Wait 30-60 seconds after starting" -ForegroundColor White
Write-Host "   2. Port conflicts: Check if other apps are using ports 8000, 8080, 8501, 5000" -ForegroundColor White
Write-Host "   3. Docker memory: Ensure Docker has at least 8GB RAM allocated" -ForegroundColor White
Write-Host "   4. Windows Firewall: May need to allow Docker through firewall" -ForegroundColor White

Write-Host "`n🔧 Quick Fixes:" -ForegroundColor Cyan
Write-Host "   • View all logs:  .\manage_services.ps1 -Service all -Action logs" -ForegroundColor White
Write-Host "   • Restart all:    .\manage_services.ps1 -Service all -Action stop" -ForegroundColor White
Write-Host "                     .\manage_services.ps1 -Service all -Action start" -ForegroundColor White
Write-Host "   • Nuclear option: docker-compose -f docker-compose-airflow.yml down -v" -ForegroundColor White
Write-Host "                     docker-compose -f docker-compose-airbyte.yml down -v" -ForegroundColor White
Write-Host "                     (Warning: This deletes all data!)" -ForegroundColor Yellow

Write-Host ""
