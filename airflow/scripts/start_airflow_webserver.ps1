# Airflow Webserver Startup Script for Windows
# Uses the dedicated .venv-airflow environment and the canonical wrapper.

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$pythonExe = Join-Path $repoRoot ".venv-airflow\Scripts\python.exe"
$wrapper = Join-Path $repoRoot "airflow\scripts\airflow_windows.py"

if (-not (Test-Path $pythonExe)) {
    Write-Host "❌ Missing Airflow environment: $pythonExe" -ForegroundColor Red
    exit 1
}

$env:AIRFLOW_HOME = Join-Path $repoRoot "airflow_config"
$env:AIRFLOW__CORE__MP_START_METHOD = "spawn"
$env:AIRFLOW__CORE__EXECUTOR = "LocalExecutor"

Write-Host "🚀 Starting Airflow Webserver with Windows compatibility..." -ForegroundColor Green
Write-Host "📍 AIRFLOW_HOME: $env:AIRFLOW_HOME" -ForegroundColor Cyan
Write-Host "🌐 Webserver will be available at: http://localhost:8080" -ForegroundColor Yellow

Push-Location $repoRoot
& $pythonExe $wrapper webserver
$exitCode = $LASTEXITCODE
Pop-Location
exit $exitCode