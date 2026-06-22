param(
    [string]$PythonPath,
    [string]$ScriptPath = "altair_main.py"
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

if (-not $PythonPath) {
    $resolverScript = Join-Path $repoRoot "scripts\resolve_python_for_service.ps1"
    if (-not (Test-Path $resolverScript)) {
        Write-Error "Python resolver script not found: $resolverScript"
        exit 1
    }

    $PythonPath = & $resolverScript -Service altair -RepoRoot $repoRoot -AllowLegacyFallback
    if ($LASTEXITCODE -ne 0) {
        exit 1
    }
}

if (-not $PythonPath) {
    Write-Error "No Python interpreter found. Create .venv-altair (recommended) or .venv."
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
