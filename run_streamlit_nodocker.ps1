param(
    [string]$PythonPath,
    [string]$AppPath = "streamlit_app.py",
    [int]$Port = 8501,
    [string]$ServerHost = "127.0.0.1"
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$noDockerEnvScript = Join-Path $repoRoot "set_no_docker_env.ps1"
if (Test-Path $noDockerEnvScript) {
    . $noDockerEnvScript
}

if (-not $PythonPath) {
    $resolverScript = Join-Path $repoRoot "scripts\resolve_python_for_service.ps1"
    if (-not (Test-Path $resolverScript)) {
        Write-Error "Python resolver script not found: $resolverScript"
        exit 1
    }

    $PythonPath = & $resolverScript -Service streamlit -RepoRoot $repoRoot -AllowLegacyFallback
    if ($LASTEXITCODE -ne 0) {
        exit 1
    }
}

if (-not (Test-Path $PythonPath)) {
    Write-Error "Python executable not found: $PythonPath"
    Write-Host "Tip: create .venv-streamlit or pass -PythonPath <path-to-python>." -ForegroundColor Yellow
    exit 1
}

$resolvedApp = Join-Path $repoRoot $AppPath
if (-not (Test-Path $resolvedApp)) {
    Write-Error "Streamlit app not found: $resolvedApp"
    exit 1
}

Write-Host "Using Python: $PythonPath" -ForegroundColor Cyan
Write-Host "Launching Streamlit app: $resolvedApp" -ForegroundColor Cyan
Write-Host "Access URL: http://${ServerHost}:$Port" -ForegroundColor Cyan

& $PythonPath -m streamlit run $resolvedApp --server.address $ServerHost --server.port $Port
exit $LASTEXITCODE
