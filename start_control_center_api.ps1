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

Write-Host "Starting Bentley FastAPI Control Center on http://localhost:$Port ..." -ForegroundColor Cyan
& $PythonPath -m uvicorn Main:app --host $ApiHost --port $Port
