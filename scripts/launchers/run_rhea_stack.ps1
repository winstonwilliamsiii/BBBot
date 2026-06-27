param(
    [switch]$NoPull,
    [switch]$NoBuild
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

function Test-LoopbackPort {
    param(
        [int]$Port
    )

    try {
        $null = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 "http://127.0.0.1:$Port"
        return $true
    } catch {
        return $false
    }
}

$airflowLauncher = Join-Path $repoRoot "airflow\scripts\start_airflow_docker.ps1"
if (-not (Test-Path $airflowLauncher)) {
    Write-Error "Airflow launcher not found: $airflowLauncher"
    exit 1
}

if (-not (Test-LoopbackPort -Port 5000) -or -not (Test-LoopbackPort -Port 8080)) {
    Write-Host "MLflow/Airflow stack not reachable. Starting local engine stack..." -ForegroundColor Cyan
    if ($NoPull -and $NoBuild) {
        & $airflowLauncher -NoPull -NoBuild
    } elseif ($NoPull) {
        & $airflowLauncher -NoPull
    } elseif ($NoBuild) {
        & $airflowLauncher -NoBuild
    } else {
        & $airflowLauncher
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start MLflow/Airflow stack."
        exit $LASTEXITCODE
    }
} else {
    Write-Host "MLflow and Airflow are already reachable on 5000 and 8080." -ForegroundColor Green
}

if (Test-LoopbackPort -Port 7860) {
    Write-Host "Rhea Gradio is already reachable on 7860." -ForegroundColor Green
    exit 0
}

$gradioLauncher = Join-Path $repoRoot "run_rhea_main.ps1"
if (-not (Test-Path $gradioLauncher)) {
    Write-Error "Rhea launcher not found: $gradioLauncher"
    exit 1
}

Write-Host "Starting Rhea Gradio..." -ForegroundColor Cyan
& $gradioLauncher
exit $LASTEXITCODE
