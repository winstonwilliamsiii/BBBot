# Bentley Budget Bot - Airbyte Docker Startup
# Starts the Airbyte compose stack from the first available compose file.

param(
    [switch]$NoPull,
    [switch]$NoBuild
)

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = $PSScriptRoot
$repoRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$composeCandidates = @(
    (Join-Path $repoRoot "docker\docker-compose-airbyte-fixed.yml"),
    (Join-Path $repoRoot "docker\docker-compose-airbyte-simple.yml"),
    (Join-Path $repoRoot "docker\docker-compose-airbyte.yml")
)
$composeFile = $composeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $composeFile) {
    throw "No Airbyte compose file found."
}

Push-Location $repoRoot

try {
    Write-Host "Bentley Budget Bot - Airbyte Docker Setup" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "Compose file: $composeFile" -ForegroundColor Gray

    Write-Host "Stopping existing Airbyte containers..." -ForegroundColor Yellow
    docker compose -f $composeFile down

    if (-not $NoPull) {
        Write-Host "Pulling images..." -ForegroundColor Yellow
        docker compose -f $composeFile pull
    } else {
        Write-Host "No-pull mode enabled: skipping image pull." -ForegroundColor Yellow
    }

    Write-Host "Starting Airbyte services..." -ForegroundColor Yellow
    Write-Host "  Airbyte DB" -ForegroundColor White
    Write-Host "  Airbyte server (8001)" -ForegroundColor White
    Write-Host "  Airbyte web UI (8000)" -ForegroundColor White
    Write-Host "  Airbyte worker" -ForegroundColor White
    Write-Host "  Airbyte temporal" -ForegroundColor White
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
                "One or more local images are missing. " +
                "Run again without -NoPull/-NoBuild after registry connectivity is restored."
            )
        }
        throw "Compose start failed. Review docker compose output and retry."
    }

    Write-Host "Waiting for Airbyte to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30

    Write-Host "Service status:" -ForegroundColor Cyan
    docker compose -f $composeFile ps

    Write-Host "Access points:" -ForegroundColor Green
    Write-Host "  Airbyte UI:  http://127.0.0.1:8000" -ForegroundColor White
    Write-Host "  Airbyte API: http://127.0.0.1:8001" -ForegroundColor White
    Write-Host ""
    Write-Host "Use: docker compose -f $composeFile logs -f" -ForegroundColor Gray
    Write-Host "Use: docker compose -f $composeFile down" -ForegroundColor Gray
} finally {
    Pop-Location
}