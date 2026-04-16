param(
    [string]$PythonPath = "C:/Users/winst/BentleyBudgetBot/.venv/Scripts/python.exe",
    [string]$ApiHost = "0.0.0.0",
    [int]$Port = 5001
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$apiEntry = Join-Path $repoRoot "Main.py"

if (-not (Test-Path $apiEntry)) {
    Write-Error "Control Center API entrypoint not found: $apiEntry"
    exit 1
}

if (-not (Test-Path $PythonPath)) {
    Write-Error "Python executable not found: $PythonPath"
    Write-Host "Tip: Activate your venv or pass -PythonPath <path-to-python>" -ForegroundColor Yellow
    exit 1
}

# Kill any existing process holding the port before binding
$netstatOutput = netstat -ano | Select-String ":5001\s.*LISTENING"
if ($netstatOutput) {
    $pid = ($netstatOutput -split '\s+')[-1]
    Write-Host "Stopping existing process on port $Port (PID $pid)..." -ForegroundColor Yellow
    taskkill /PID $pid /F 2>$null
    Start-Sleep -Milliseconds 800
}

Write-Host "Starting Bentley FastAPI Control Center on http://localhost:$Port ..." -ForegroundColor Cyan
& $PythonPath -m uvicorn Main:app --host $ApiHost --port $Port
