param(
    [double]$LiquidityBuffer = 0.20,
    [double]$DryPowderDeployPct = 0.25,
    [double]$MinTradeCash = 50,
    [int]$MaxTrades = 1,
    [switch]$ForceDryRun
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$logDir = Join-Path $repoRoot "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = Join-Path $logDir "market_open_bots_$stamp.log"

$env:TITAN_LIQUIDITY_BUFFER = $LiquidityBuffer.ToString("0.00")
$env:TITAN_DRY_POWDER_DEPLOY_PCT = $DryPowderDeployPct.ToString("0.00")
$env:TITAN_MIN_TRADE_CASH = $MinTradeCash.ToString("0.00")
$env:TITAN_MAX_TRADES = [string]$MaxTrades

if ($ForceDryRun.IsPresent) {
    $env:TITAN_DRY_RUN = "true"
    $env:TITAN_ENABLE_TRADING = "false"
} else {
    $env:TITAN_DRY_RUN = "false"
    $env:TITAN_ENABLE_TRADING = "true"
}

# Keep paper mode explicit for morning automation.
$env:ALPACA_PAPER = "true"

# Ensure Discord webhook is available for Titan notifications.
if (-not $env:DISCORD_WEBHOOK_URL) {
    if ($env:DISCORD_WEBHOOK) {
        $env:DISCORD_WEBHOOK_URL = $env:DISCORD_WEBHOOK
    } elseif ($env:DISCORD_WEBHOOK_PROD) {
        $env:DISCORD_WEBHOOK_URL = $env:DISCORD_WEBHOOK_PROD
    } else {
        $alertsEnvPath = Join-Path $repoRoot "mvp2-alerts\.env"
        if (Test-Path $alertsEnvPath) {
            $webhookLine = Get-Content $alertsEnvPath |
                Where-Object {
                    $_ -match '^DISCORD_WEBHOOK=' -and $_ -notmatch '^\s*#'
                } |
                Select-Object -First 1

            if ($webhookLine) {
                $webhookValue = ($webhookLine -split '=', 2)[1].Trim()
                if ($webhookValue) {
                    $env:DISCORD_WEBHOOK_URL = $webhookValue
                }
            }
        }
    }
}

$mysqlContainerName = "bentley-mysql"
$runningNames = docker ps --format "{{.Names}}"
if ($runningNames -notcontains $mysqlContainerName) {
    Write-Host "MySQL container not running, starting Docker stack..." -ForegroundColor Yellow
    $startScript = Join-Path $repoRoot "start_mysql_docker.ps1"
    if (Test-Path $startScript) {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $startScript | Out-Null
    }
}

Write-Host "Launching market-open bot cycle..." -ForegroundColor Cyan
Write-Host "Log file: $logFile" -ForegroundColor Gray

$cmdOutput = & $pythonExe -m scripts.run_market_open_bots 2>&1
$cmdOutput | Tee-Object -FilePath $logFile

if ($LASTEXITCODE -ne 0) {
    Write-Error "Market-open bot cycle failed. See $logFile"
    exit $LASTEXITCODE
}

Write-Host "Market-open bot cycle completed successfully." -ForegroundColor Green
