# Bentley Budget Bot - Airflow Docker Startup
# Starts the core container stack from docker/docker-compose-airflow.yml.

param(
    [switch]$NoPull,
    [switch]$NoBuild
)

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$composeFile = Join-Path $repoRoot "docker\docker-compose-airflow.yml"

Push-Location $repoRoot

try {
    Write-Host "Bentley Budget Bot - Docker Airflow Setup" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "Compose file: $composeFile" -ForegroundColor Gray

    Write-Host "Stopping existing containers..." -ForegroundColor Yellow
    docker compose -f $composeFile down

    if (-not $NoPull) {
        Write-Host "Pulling images..." -ForegroundColor Yellow
        docker compose -f $composeFile pull
    } else {
        Write-Host "No-pull mode enabled: skipping image pull." -ForegroundColor Yellow
    }

    Write-Host "Starting services..." -ForegroundColor Yellow
    Write-Host "  MySQL (3307)" -ForegroundColor White
    Write-Host "  Redis (6379)" -ForegroundColor White
    Write-Host "  Airflow webserver (8080)" -ForegroundColor White
    Write-Host "  Airflow scheduler" -ForegroundColor White
    Write-Host "  Airflow worker" -ForegroundColor White
    Write-Host "  MLflow (5000)" -ForegroundColor White
    Write-Host "  Streamlit (8501)" -ForegroundColor White
    $upCmd = @("compose", "-f", $composeFile, "up", "-d")
    if ($NoBuild) {
        $upCmd += "--no-build"
        Write-Host "No-build mode enabled: skipping image builds." -ForegroundColor Yellow
    }
    & docker @upCmd
    if ($LASTEXITCODE -ne 0) {
        if ($NoPull -or $NoBuild) {
            throw (
                "Compose start failed in no-pull/no-build mode. " +
                "One or more local images are missing (for example bentley-airflow-mlflow:latest). " +
                "Run again without -NoPull/-NoBuild after registry connectivity is restored."
            )
        }
        throw "Compose start failed. Review docker compose output and retry."
    }

    Write-Host "Waiting for services to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 20

    Write-Host "Service status:" -ForegroundColor Cyan
    docker compose -f $composeFile ps

    Write-Host "Access points:" -ForegroundColor Green
    Write-Host "  Airflow:   http://127.0.0.1:8080" -ForegroundColor White
    Write-Host "  Streamlit: http://127.0.0.1:8501" -ForegroundColor White
    Write-Host "  MySQL:     127.0.0.1:3307" -ForegroundColor White
    Write-Host "  Redis:     127.0.0.1:6379" -ForegroundColor White
    Write-Host "  MLflow:    http://127.0.0.1:5000" -ForegroundColor White
    Write-Host ""
    Write-Host "Airflow login: admin / admin" -ForegroundColor Cyan
    Write-Host "Use: docker compose -f docker/docker-compose-airflow.yml logs -f" -ForegroundColor Gray
    Write-Host "Use: docker compose -f docker/docker-compose-airflow.yml down" -ForegroundColor Gray
} finally {
    Pop-Location
}