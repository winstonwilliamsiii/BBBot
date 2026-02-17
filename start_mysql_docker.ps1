# Bentley Budget Bot - Automatic Docker & MySQL Startup Script
# This script ensures Docker Desktop is running and starts MySQL containers

Write-Host "`n🚀 Bentley Bot - Starting Docker & MySQL Environment..." -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

# Function to check if Docker Desktop is running
function Test-DockerRunning {
    try {
        $null = docker info 2>&1
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

# Function to start Docker Desktop
function Start-DockerDesktop {
    Write-Host "`n⏳ Starting Docker Desktop..." -ForegroundColor Yellow
    
    # Common Docker Desktop paths
    $dockerPaths = @(
        "C:\Program Files\Docker\Docker\Docker Desktop.exe",
        "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
        "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
    )
    
    $dockerExe = $dockerPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
    
    if (-not $dockerExe) {
        Write-Host "❌ Docker Desktop not found. Please install Docker Desktop." -ForegroundColor Red
        Write-Host "   Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
        exit 1
    }
    
    Start-Process $dockerExe -WindowStyle Hidden
    
    # Wait for Docker to be ready (max 90 seconds)
    $maxWaitTime = 90
    $waited = 0
    
    while (-not (Test-DockerRunning) -and $waited -lt $maxWaitTime) {
        Start-Sleep -Seconds 3
        $waited += 3
        Write-Host "   Waiting for Docker... ($waited/$maxWaitTime seconds)" -ForegroundColor Gray
    }
    
    if (Test-DockerRunning) {
        Write-Host "✅ Docker Desktop is ready!" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ Docker Desktop failed to start within $maxWaitTime seconds" -ForegroundColor Red
        return $false
    }
}

# Step 1: Check if Docker is running
Write-Host "`n📋 Checking Docker status..." -ForegroundColor White

if (Test-DockerRunning) {
    Write-Host "✅ Docker is already running" -ForegroundColor Green
} else {
    Write-Host "⚠️  Docker is not running" -ForegroundColor Yellow
    if (-not (Start-DockerDesktop)) {
        exit 1
    }
}

# Step 2: Navigate to docker directory
Set-Location "$PSScriptRoot\docker"

# Step 3: Check which containers to start
Write-Host "`n📦 Starting MySQL containers..." -ForegroundColor White

# Check if containers already exist
$existingContainers = docker ps -a --format "{{.Names}}" 2>$null

# Start Airflow MySQL (bbbot1/mansa_bot database on port 3307)
if ($existingContainers -match "bentley-mysql") {
    Write-Host "   🔄 Starting existing bentley-mysql container..." -ForegroundColor Cyan
    docker start bentley-mysql 2>&1 | Out-Null
} else {
    Write-Host "   🆕 Creating bentley-mysql container (Airflow + Bbbot1)..." -ForegroundColor Cyan
    docker-compose -f docker-compose-airflow.yml up -d mysql 2>&1 | Out-Null
}

# Start MLflow MySQL (mlflow_db database on port 3307)
if ($existingContainers -match "bentley-mysql-mlflow") {
    Write-Host "   🔄 Starting existing bentley-mysql-mlflow container..." -ForegroundColor Cyan
    docker start bentley-mysql-mlflow 2>&1 | Out-Null
} else {
    Write-Host "   💡 MLflow MySQL not configured (run manually if needed)" -ForegroundColor Gray
}

# Wait a moment for containers to fully start
Start-Sleep -Seconds 3

# Step 4: Verify containers are running
Write-Host "`n🔍 Verifying container status..." -ForegroundColor White

$runningContainers = docker ps --filter "name=mysql" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>$null

if ($runningContainers) {
    Write-Host "`n$runningContainers" -ForegroundColor Green
} else {
    Write-Host "❌ No MySQL containers are running!" -ForegroundColor Red
    exit 1
}

# Step 5: Test MySQL connection
Write-Host "`n🔌 Testing MySQL connection..." -ForegroundColor White

$testResult = docker exec bentley-mysql mysqladmin ping -uroot -proot 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ MySQL is responding to connections!" -ForegroundColor Green
    
    # Show databases
    Write-Host "`n📊 Available databases:" -ForegroundColor White
    docker exec bentley-mysql mysql -uroot -proot -e "SHOW DATABASES;" 2>$null | ForEach-Object {
        if ($_ -notmatch "mysql|information_schema|performance_schema|sys|Database") {
            Write-Host "   📁 $_" -ForegroundColor Cyan
        }
    }
} else {
    Write-Host "⚠️  MySQL is starting up, may need a few more seconds..." -ForegroundColor Yellow
}

# Step 6: Display connection info
Write-Host "`n" -NoNewline
Write-Host "=" * 60 -ForegroundColor Gray
Write-Host "✅ MySQL Environment Ready!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Gray

Write-Host "`n📝 MySQL Workbench Connection Settings:" -ForegroundColor Cyan
Write-Host "   Connection Name: Demo_Bots (Bentley)" -ForegroundColor White
Write-Host "   Hostname: 127.0.0.1" -ForegroundColor White
Write-Host "   Port: 3307" -ForegroundColor White
Write-Host "   Username: root" -ForegroundColor White
Write-Host "   Password: root" -ForegroundColor White
Write-Host "   Default Schema: mansa_bot" -ForegroundColor White

Write-Host "`n📚 Available Databases:" -ForegroundColor Cyan
Write-Host "   • mansa_bot    - Main application database (Bbbot1, Tiingo, yfinance)" -ForegroundColor White
Write-Host "   • airflow      - Airflow metadata & DAG runs" -ForegroundColor White
Write-Host "   • mlflow_db    - MLflow experiments (if running)" -ForegroundColor White

Write-Host "`n💡 Quick Commands:" -ForegroundColor Cyan
Write-Host "   View logs:      docker logs bentley-mysql" -ForegroundColor Gray
Write-Host "   Stop MySQL:     docker stop bentley-mysql" -ForegroundColor Gray
Write-Host "   Restart MySQL:  docker restart bentley-mysql" -ForegroundColor Gray
Write-Host "   MySQL Shell:    docker exec -it bentley-mysql mysql -uroot -proot" -ForegroundColor Gray

Write-Host "`n"

# Return to original directory
Set-Location $PSScriptRoot
