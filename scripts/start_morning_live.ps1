param(
    [double]$LiquidityBuffer = 0.20,
    [double]$DryPowderDeployPct = 0.25,
    [double]$MinTradeCash = 50,
    [int]$MaxTrades = 1,
    [switch]$SkipSignalBroadcast
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$mysqlScript = Join-Path $repoRoot "scripts/launchers/start_mysql_docker.ps1"
$apiScript = Join-Path $repoRoot "scripts/launchers/start_control_center_api.ps1"
$botModeScript = Join-Path $repoRoot "scripts/launchers/start_bot_mode.ps1"
$marketOpenScript = Join-Path $repoRoot "run_market_open_bots.ps1"
$signalScript = Join-Path $repoRoot "run_bot_signal_broadcast.ps1"

$requiredScripts = @(
    $mysqlScript,
    $apiScript,
    $botModeScript,
    $marketOpenScript,
    $signalScript
)

foreach ($script in $requiredScripts) {
    if (-not (Test-Path $script)) {
        Write-Error "Required script not found: $script"
        exit 1
    }
}

Write-Host "Starting MySQL Docker environment..." -ForegroundColor Cyan
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $mysqlScript
if ($LASTEXITCODE -ne 0) {
    Write-Error "MySQL startup failed."
    exit $LASTEXITCODE
}

Write-Host "Starting Control Center API in a new PowerShell window..." -ForegroundColor Cyan
Start-Process powershell.exe -WorkingDirectory $repoRoot -ArgumentList @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-File', $apiScript
)

$liveBots = @(
    @{ Bot = 'Titan'; Broker = 'ALPACA' },
    @{ Bot = 'Dogon'; Broker = 'ALPACA' },
    @{ Bot = 'Orion'; Broker = 'ALPACA' },
    @{ Bot = 'Rigel'; Broker = 'FTMO' },
    @{ Bot = 'Vega'; Broker = 'AXI' },
    @{ Bot = 'Hydra'; Broker = 'ALPACA' }
)

foreach ($entry in $liveBots) {
    Write-Host ("Setting {0} live mode via {1}..." -f $entry.Bot, $entry.Broker) -ForegroundColor Cyan
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $botModeScript -Bot $entry.Bot -Mode ON -Broker $entry.Broker -TradingMode live
    if ($LASTEXITCODE -ne 0) {
        Write-Error ("Failed to enable {0} in live mode." -f $entry.Bot)
        exit $LASTEXITCODE
    }
}

Write-Host "Running live market-open bot cycle..." -ForegroundColor Cyan
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $marketOpenScript -LiquidityBuffer $LiquidityBuffer -DryPowderDeployPct $DryPowderDeployPct -MinTradeCash $MinTradeCash -MaxTrades $MaxTrades
if ($LASTEXITCODE -ne 0) {
    Write-Error "Live market-open cycle failed."
    exit $LASTEXITCODE
}

if (-not $SkipSignalBroadcast.IsPresent) {
    Write-Host "Broadcasting live signals for active bots..." -ForegroundColor Cyan
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $signalScript -Mode live -Symbol SPY -ActiveOnly
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Live signal broadcast failed."
        exit $LASTEXITCODE
    }
}

Write-Host "Morning live startup completed." -ForegroundColor Green