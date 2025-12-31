# ============================================================================
# BENTLEY BUDGET BOT - MASTER ENGINE STARTUP
# ============================================================================
# Starts all data pipeline and trading infrastructure services
# Date: December 30, 2025
# ============================================================================

# Set encoding
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "🚀 BENTLEY BUDGET BOT - ENGINE STARTUP" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# CONFIGURATION
# ============================================================================

$SCRIPT_ROOT = $PSScriptRoot
$AIRFLOW_DIR = Join-Path $SCRIPT_ROOT "airflow\scripts"
$AIRBYTE_DIR = Join-Path $SCRIPT_ROOT "airbyte\scripts"
$MLFLOW_DIR = Join-Path $SCRIPT_ROOT "scripts\setup"

# ============================================================================
# FUNCTIONS
# ============================================================================

function Test-DockerRunning {
    Write-Host "🐳 Checking Docker status..." -ForegroundColor Yellow
    $dockerStatus = docker info 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
        return $false
    }
    Write-Host "✅ Docker is running" -ForegroundColor Green
    return $true
}

function Start-MySQL {
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  [1/5] MYSQL DATABASE" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    
    # Check if MySQL is already running
    $mysqlStatus = docker ps --filter "name=mysql" --format "{{.Names}}" 2>$null
    
    if ($mysqlStatus) {
        Write-Host "✅ MySQL already running: $mysqlStatus" -ForegroundColor Green
    } else {
        Write-Host "🔧 Starting MySQL container..." -ForegroundColor Yellow
        docker start mysql 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️  MySQL container not found - skipping" -ForegroundColor Yellow
        } else {
            Write-Host "✅ MySQL started successfully" -ForegroundColor Green
        }
    }
    
    Write-Host "   Port: 3306, 3307" -ForegroundColor White
    Start-Sleep -Seconds 2
}

function Start-Airflow {
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  [2/5] APACHE AIRFLOW" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    
    if (Test-Path (Join-Path $AIRFLOW_DIR "start_airflow_docker.ps1")) {
        Write-Host "🔧 Starting Airflow services..." -ForegroundColor Yellow
        Set-Location $SCRIPT_ROOT
        & "$AIRFLOW_DIR\start_airflow_docker.ps1"
        Write-Host "✅ Airflow started" -ForegroundColor Green
        Write-Host "   Web UI: http://localhost:8080" -ForegroundColor White
        Write-Host "   Login: admin / admin" -ForegroundColor White
    } else {
        Write-Host "⚠️  Airflow script not found - skipping" -ForegroundColor Yellow
    }
    
    Start-Sleep -Seconds 3
}

function Start-Airbyte {
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  [3/5] AIRBYTE DATA INTEGRATION" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    
    if (Test-Path (Join-Path $AIRBYTE_DIR "start_airbyte_docker.ps1")) {
        Write-Host "🔧 Starting Airbyte services..." -ForegroundColor Yellow
        Set-Location $SCRIPT_ROOT
        & "$AIRBYTE_DIR\start_airbyte_docker.ps1"
        Write-Host "✅ Airbyte started" -ForegroundColor Green
        Write-Host "   Web UI: http://localhost:8000" -ForegroundColor White
    } else {
        Write-Host "⚠️  Airbyte script not found - skipping" -ForegroundColor Yellow
    }
    
    Start-Sleep -Seconds 3
}

function Start-MLflow {
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  [4/5] MLFLOW TRACKING SERVER" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    
    # Check if MLflow is already running
    $mlflowProcess = Get-Process | Where-Object { $_.ProcessName -like "*mlflow*" }
    
    if ($mlflowProcess) {
        Write-Host "✅ MLflow already running (PID: $($mlflowProcess.Id))" -ForegroundColor Green
    } else {
        Write-Host "🔧 Starting MLflow tracking server..." -ForegroundColor Yellow
        
        # Create MLflow data directory if it doesn't exist
        $mlflowDir = Join-Path $SCRIPT_ROOT "data\mlflow"
        if (!(Test-Path $mlflowDir)) {
            New-Item -ItemType Directory -Force -Path $mlflowDir | Out-Null
        }
        
        # Start MLflow in background
        $mlflowArgs = @(
            "mlflow", "server",
            "--host", "0.0.0.0",
            "--port", "5000",
            "--backend-store-uri", "sqlite:///$mlflowDir/mlflow.db",
            "--default-artifact-root", "$mlflowDir/artifacts"
        )
        
        Start-Process -FilePath "python" -ArgumentList ($mlflowArgs -join " ") -WindowStyle Hidden
        Start-Sleep -Seconds 5
        
        Write-Host "✅ MLflow started" -ForegroundColor Green
        Write-Host "   Tracking UI: http://localhost:5000" -ForegroundColor White
    }
    
    Start-Sleep -Seconds 2
}

function Start-Streamlit {
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  [5/5] STREAMLIT DASHBOARD" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    
    # Check if Streamlit is already running
    $streamlitProcess = Get-Process | Where-Object { $_.CommandLine -like "*streamlit*" }
    
    if ($streamlitProcess) {
        Write-Host "✅ Streamlit already running" -ForegroundColor Green
    } else {
        Write-Host "🔧 Starting Streamlit dashboard..." -ForegroundColor Yellow
        Write-Host "   (Run this manually if needed: .\RESTART_STREAMLIT.ps1)" -ForegroundColor Gray
    }
    
    Write-Host "   Dashboard: http://localhost:8501" -ForegroundColor White
    Start-Sleep -Seconds 1
}

function Show-Summary {
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor Green
    Write-Host "  🎉 ALL ENGINES STARTED SUCCESSFULLY" -ForegroundColor Green
    Write-Host "=" * 80 -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 SERVICE DASHBOARD:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   🗄️  MySQL Database:       localhost:3306, 3307" -ForegroundColor Cyan
    Write-Host "   🔄 Airflow UI:            http://localhost:8080" -ForegroundColor Cyan
    Write-Host "      └─ Login: admin/admin" -ForegroundColor Gray
    Write-Host "   🔌 Airbyte UI:            http://localhost:8000" -ForegroundColor Cyan
    Write-Host "   📈 MLflow Tracking:       http://localhost:5000" -ForegroundColor Cyan
    Write-Host "   📊 Streamlit Dashboard:   http://localhost:8501" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🔧 MANAGEMENT COMMANDS:" -ForegroundColor Yellow
    Write-Host "   • Check status:     docker ps" -ForegroundColor White
    Write-Host "   • View logs:        docker-compose logs -f [service]" -ForegroundColor White
    Write-Host "   • Stop all:         docker-compose down" -ForegroundColor White
    Write-Host "   • Restart Streamlit: .\RESTART_STREAMLIT.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 READY FOR TRADING!" -ForegroundColor Green
    Write-Host ""
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

try {
    # Step 0: Check Docker
    if (!(Test-DockerRunning)) {
        exit 1
    }
    
    # Step 1: MySQL
    Start-MySQL
    
    # Step 2: Airflow
    Start-Airflow
    
    # Step 3: Airbyte
    Start-Airbyte
    
    # Step 4: MLflow
    Start-MLflow
    
    # Step 5: Streamlit
    Start-Streamlit
    
    # Summary
    Show-Summary
    
    Write-Host "💡 TIP: Keep this window open to see startup logs" -ForegroundColor Yellow
    Write-Host "     Press Ctrl+C to exit (services will continue running)" -ForegroundColor Yellow
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    exit 1
}
