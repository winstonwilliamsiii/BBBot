param(
    [string]$PythonPath,
    [string]$ScriptPath = "rhea_main.py",
    [int]$Port = 7860
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

# Keep Rhea in local/no-Docker mode for fast Gradio testing.
$env:RHEA_NO_DOCKER_MODE = "true"
$env:RHEA_ENABLE_MLFLOW = "false"
$env:MLFLOW_TRACKING_URI = "http://127.0.0.1:5000"
$env:GRADIO_SERVER_PORT = "$Port"

# Reuse existing local DB helper for a consistent local MySQL profile.
$noDockerEnvScript = Join-Path $repoRoot "set_no_docker_env.ps1"
if (Test-Path $noDockerEnvScript) {
    . $noDockerEnvScript
}

if (-not $PythonPath) {
    $candidates = @(
        (Join-Path $repoRoot ".venv-rhea\Scripts\python.exe"),
        (Join-Path $repoRoot ".venv\Scripts\python.exe"),
        (Join-Path $repoRoot "venv\Scripts\python.exe")
    )

    $PythonPath = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $PythonPath) {
    Write-Error "No Python interpreter found. Create .venv-rhea or .venv first."
    exit 1
}

$resolvedScript = Join-Path $repoRoot $ScriptPath
if (-not (Test-Path $resolvedScript)) {
    Write-Error "Rhea entrypoint not found: $resolvedScript"
    exit 1
}

try {
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
} catch {
    $listener = $null
}

if ($listener) {
    Write-Error "Port $Port is already in use (PID $($listener.OwningProcess)). Stop that process or run with -Port <freePort>."
    exit 1
}

Write-Host "Using Python: $PythonPath" -ForegroundColor Cyan
Write-Host "No-Docker mode: RHEA_ENABLE_MLFLOW=$($env:RHEA_ENABLE_MLFLOW), GRADIO_SERVER_PORT=$Port" -ForegroundColor Cyan
Write-Host "Launching: $resolvedScript" -ForegroundColor Cyan

& $PythonPath $resolvedScript
exit $LASTEXITCODE
