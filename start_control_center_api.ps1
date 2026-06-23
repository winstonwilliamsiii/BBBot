param(
    [string]$PythonPath,
    [string]$ApiHost = "0.0.0.0",
    [int]$Port = 5001,
    [switch]$Reload
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$apiEntry = Join-Path $repoRoot "Main.py"
$resolverScript = Join-Path $repoRoot "scripts\resolve_python_for_service.ps1"

if (-not (Test-Path $apiEntry)) {
    Write-Error "Control Center API entrypoint not found: $apiEntry"
    exit 1
}

if (-not $PythonPath) {
    if (-not (Test-Path $resolverScript)) {
        Write-Error "Python resolver script not found: $resolverScript"
        exit 1
    }

    $PythonPath = & $resolverScript -Service api -RepoRoot $repoRoot -AllowLegacyFallback
    if ($LASTEXITCODE -ne 0) {
        exit 1
    }
}

if (-not (Test-Path $PythonPath)) {
    Write-Error "Python executable not found: $PythonPath"
    Write-Host "Tip: create .venv-api or pass -PythonPath <path-to-python>." -ForegroundColor Yellow
    exit 1
}

# Kill any existing process holding the port before binding
$netstatOutput = netstat -ano | Select-String ":$Port\s.*LISTENING"
if ($netstatOutput) {
    $procId = ($netstatOutput -split '\s+')[-1]
    Write-Host "Stopping existing process on port $Port (PID $procId)..." -ForegroundColor Yellow
    taskkill /PID $procId /F 2>$null
    Start-Sleep -Milliseconds 800
}

Write-Host "Starting Bentley FastAPI Control Center on http://localhost:$Port ..." -ForegroundColor Cyan
$uvicornArgs = @("-m", "uvicorn", "Main:app", "--host", $ApiHost, "--port", $Port)
if ($Reload.IsPresent) {
    $uvicornArgs += "--reload"
}

& $PythonPath @uvicornArgs
