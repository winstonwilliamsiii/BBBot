param(
    [string]$PythonPath,
    [string]$ScriptPath = "altair_main.py"
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

if (-not $PythonPath) {
    $candidates = @(
        (Join-Path $repoRoot ".venv\Scripts\python.exe"),
        (Join-Path $repoRoot "venv\Scripts\python.exe")
    )

    $PythonPath = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $PythonPath) {
    Write-Error "No project Python interpreter found. Expected .venv or venv under $repoRoot"
    exit 1
}

$resolvedScript = Join-Path $repoRoot $ScriptPath
if (-not (Test-Path $resolvedScript)) {
    Write-Error "Altair entrypoint not found: $resolvedScript"
    exit 1
}

Write-Host "Using Python: $PythonPath" -ForegroundColor Cyan
Write-Host "Launching: $resolvedScript" -ForegroundColor Cyan
& $PythonPath $resolvedScript
exit $LASTEXITCODE
