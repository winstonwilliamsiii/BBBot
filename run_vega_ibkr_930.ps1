param(
    [int]$MaxTrades = 1,
    [ValidateSet("buy", "sell")]
    [string]$Side = "buy",
    [ValidateSet("AUTO", "paper", "live")]
    [string]$TradingMode = "AUTO"
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$launcher = Join-Path $repoRoot "start_bot_mode.ps1"
$vegaScript = Join-Path $repoRoot "scripts\vega_bot.py"
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
$logDir = Join-Path $repoRoot "logs"
$latestEventPath = Join-Path $logDir "last_bot_mode_event.json"
$runLogPath = Join-Path $logDir "vega_ibkr_930_last_run.log"

if (-not (Test-Path $launcher)) {
    Write-Error "Launcher not found: $launcher"
    exit 1
}

if (-not (Test-Path $vegaScript)) {
    Write-Error "Vega bot script not found: $vegaScript"
    exit 1
}

if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Get-ConfiguredIbkrMode {
    $configPath = Join-Path $repoRoot "config\broker_modes.json"
    if (-not (Test-Path $configPath)) {
        return "paper"
    }

    try {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
        if ($config.broker_modes -and $config.broker_modes.ibkr) {
            return [string]$config.broker_modes.ibkr
        }
        if ($config.global_mode) {
            return [string]$config.global_mode
        }
    } catch {
        return "paper"
    }

    return "paper"
}

$resolvedTradingMode = $TradingMode.ToLower()
if ($resolvedTradingMode -eq "auto") {
    $resolvedTradingMode = Get-ConfiguredIbkrMode
}
if ($resolvedTradingMode -notin @("paper", "live")) {
    $resolvedTradingMode = "paper"
}

$env:IBKR_MODE = $resolvedTradingMode
if (-not $env:IBKR_PORT) {
    if ($resolvedTradingMode -eq "paper") {
        $env:IBKR_PORT = "7497"
    } else {
        $env:IBKR_PORT = "7496"
    }
}

Write-Host "Running Vega IBKR 9:30 launcher..." -ForegroundColor Cyan
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $launcher -Bot Vega -Mode ON -Broker IBKR -TradingMode $resolvedTradingMode

if (-not (Test-Path $latestEventPath)) {
    Write-Error "Expected launcher event file missing: $latestEventPath"
    exit 1
}

$event = Get-Content $latestEventPath -Raw | ConvertFrom-Json
if (-not $event.ibkr_connect_ok) {
    Write-Error "IBKR connectivity was not confirmed. Vega_Bot run aborted."
    exit 1
}

$timestamp = (Get-Date).ToUniversalTime().ToString("o")
Add-Content -Path $runLogPath -Value ("[$timestamp] Vega IBKR 9:30 run started")

& $pythonExe $vegaScript --max-trades $MaxTrades --side $Side 2>&1 | Tee-Object -FilePath $runLogPath -Append

if ($LASTEXITCODE -ne 0) {
    Write-Error "Vega_Bot execution failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "Vega_Bot 9:30 run completed." -ForegroundColor Green