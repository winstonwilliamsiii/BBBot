param(
    [ValidateSet("paper", "live")]
    [string]$Mode = "paper",
    [string]$Symbol = "SPY",
    [switch]$ActiveOnly
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot
$env:PYTHONPATH = $repoRoot

$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Error "Required interpreter not found: $pythonExe"
    Write-Host "Create or restore the project virtual environment at .venv before launching bots." -ForegroundColor Yellow
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
