param(
    [string]$PythonPath = "C:/Users/winst/BentleyBudgetBot/.venv/Scripts/python.exe"
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$apiEntry = Join-Path $repoRoot "backend/api/app.py"

if (-not (Test-Path $apiEntry)) {
    Write-Error "Control Center API entrypoint not found: $apiEntry"
    exit 1
}

if (-not (Test-Path $PythonPath)) {
    Write-Error "Python executable not found: $PythonPath"
    Write-Host "Tip: Activate your venv or pass -PythonPath <path-to-python>" -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting Control Center API on http://localhost:5001 ..." -ForegroundColor Cyan
& $PythonPath $apiEntry
