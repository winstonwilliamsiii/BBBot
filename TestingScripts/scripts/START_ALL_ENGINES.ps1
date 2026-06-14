# Bentley Budget Bot - Master Engine Startup
# Starts the full local service stack: MySQL, Redis, Airflow, Airbyte, MLflow, Streamlit.

param(
    [switch]$NoPull,
    [switch]$NoBuild
)

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$SCRIPT_ROOT = $PSScriptRoot
$AIRFLOW_LAUNCHER = Join-Path $SCRIPT_ROOT "..\airflow\scripts\start_airflow_docker.ps1"
$AIRBYTE_LAUNCHER = Join-Path $SCRIPT_ROOT "..\airbyte\scripts\start_airbyte_docker.ps1"

function Test-DockerRunning {
    Write-Host "Checking Docker status..." -ForegroundColor Yellow
    $null = docker info 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Docker is not running. Start Docker/WSL Docker and try again." -ForegroundColor Red
        return $false
    }
    Write-Host "Docker is running." -ForegroundColor Green
    return $true
}

function Start-LauncherScript {
    param(
        [string]$Path,
        [string]$Label
    )

    if (-not (Test-Path $Path)) {
        Write-Host "$Label launcher not found: $Path" -ForegroundColor Yellow
        return
    }

    Write-Host "Starting $Label..." -ForegroundColor Cyan
    & $Path -NoPull:$NoPull -NoBuild:$NoBuild
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed to start."
    }
}

function Show-Summary {
    Write-Host ""
    Write-Host "Service endpoint summary:" -ForegroundColor Cyan
    Write-Host "  MySQL:      127.0.0.1:3307" -ForegroundColor White
    Write-Host "  Redis:      127.0.0.1:6379" -ForegroundColor White
    Write-Host "  Airflow UI: http://127.0.0.1:8080" -ForegroundColor White
    Write-Host "  MLflow UI:  http://127.0.0.1:5000" -ForegroundColor White
    Write-Host "  Airbyte UI: http://127.0.0.1:8000" -ForegroundColor White
    Write-Host "  Airbyte API: http://127.0.0.1:8001" -ForegroundColor White
    Write-Host "  Streamlit:  http://127.0.0.1:8501" -ForegroundColor White
    Write-Host ""
    Write-Host "Container snapshot:" -ForegroundColor Cyan
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String -Pattern "bentley-|NAMES"
    Write-Host ""
    Write-Host "Launch commands:" -ForegroundColor Cyan
    Write-Host "  Airflow stack: .\airflow\scripts\start_airflow_docker.ps1" -ForegroundColor Gray
    Write-Host "  Airbyte stack: .\airbyte\scripts\start_airbyte_docker.ps1" -ForegroundColor Gray
    Write-Host ""
}

try {
    Write-Host "Bentley Budget Bot - Full Stack Startup" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    if ($NoPull) {
        Write-Host "Mode: NO-PULL (offline/local images only)" -ForegroundColor Yellow
    }
    if ($NoBuild) {
        Write-Host "Mode: NO-BUILD (do not build missing images)" -ForegroundColor Yellow
    }

    if (-not (Test-DockerRunning)) {
        exit 1
    }

    Start-LauncherScript -Path $AIRFLOW_LAUNCHER -Label "Airflow/Streamlit/MySQL/Redis/MLflow stack"
    Start-LauncherScript -Path $AIRBYTE_LAUNCHER -Label "Airbyte stack"

    Show-Summary
    Write-Host "TIP: Keep this window open to review startup logs." -ForegroundColor Yellow
} catch {
    Write-Host ("ERROR: " + $_.Exception.Message) -ForegroundColor Red
    exit 1
}