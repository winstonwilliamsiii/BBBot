param(
    [ValidateSet("paper", "live")]
    [string]$Mode = "paper",
    [string]$Symbol = "SPY",
    [switch]$ActiveOnly
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot
$env:PYTHONPATH = $repoRoot

$resolverScript = Join-Path $repoRoot "scripts\resolve_python_for_service.ps1"
if (-not (Test-Path $resolverScript)) {
    Write-Error "Python resolver script not found: $resolverScript"
    exit 1
}

$pythonExe = & $resolverScript -Service bots -RepoRoot $repoRoot -AllowLegacyFallback
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $pythonExe)) {
    Write-Error "Required interpreter not found for bot signal broadcast."
    Write-Host "Create .venv-bots (preferred) or .venv." -ForegroundColor Yellow
    exit 1
}

$scriptPath = Join-Path $repoRoot "scripts\broadcast_all_bot_signals.py"
if (-not (Test-Path $scriptPath)) {
    Write-Error "Script not found: $scriptPath"
    exit 1
}

$argsList = @($scriptPath, "--mode", $Mode, "--symbol", $Symbol)
if ($ActiveOnly.IsPresent) {
    $argsList += "--active-only"
}

& $pythonExe @argsList
exit $LASTEXITCODE
