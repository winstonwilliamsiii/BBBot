param(
    [double]$LiquidityBuffer = 0.20,
    [double]$DryPowderDeployPct = 0.25,
    [double]$MinTradeCash = 50,
    [int]$MaxTrades = 1,
    [int]$StartupRetryCount = 3,
    [int]$StartupRetryDelaySeconds = 10,
    [switch]$SkipSignalBroadcast
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$mysqlScript = Join-Path $repoRoot "start_mysql_docker.ps1"
$airflowScript = Join-Path $repoRoot "airflow\scripts\start_airflow_docker.ps1"
$apiScript = Join-Path $repoRoot "start_control_center_api.ps1"
$botModeScript = Join-Path $repoRoot "start_bot_mode.ps1"
$marketOpenScript = Join-Path $repoRoot "run_market_open_bots.ps1"
$signalScript = Join-Path $repoRoot "run_bot_signal_broadcast.ps1"

$requiredScripts = @(
    $mysqlScript,
    $airflowScript,
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

function Invoke-WithRetry {
    param(
        [scriptblock]$ScriptBlock,
        [string]$Name,
        [int]$MaxAttempts = 3,
        [int]$DelaySeconds = 10
    )

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        & $ScriptBlock
        if ($LASTEXITCODE -eq 0) {
            return $true
        }

        if ($attempt -lt $MaxAttempts) {
            Write-Host ("{0} attempt {1}/{2} failed. Retrying in {3}s..." -f $Name, $attempt, $MaxAttempts, $DelaySeconds) -ForegroundColor Yellow
            Start-Sleep -Seconds $DelaySeconds
        }
    }

    return $false
}

function Test-HttpHealth {
    param(
        [string[]]$Urls,
        [int]$TimeoutSeconds = 120,
        [int]$PollSeconds = 5
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        foreach ($url in $Urls) {
            try {
                $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
                if ($response.StatusCode -lt 500) {
                    return $true
                }
            } catch {
                continue
            }
        }

        Start-Sleep -Seconds $PollSeconds
    }

    return $false
}

function Start-ServiceStack {
    param(
        [string]$Name,
        [string]$Command,
        [string[]]$Args,
        [string[]]$HealthUrls,
        [int]$MaxAttempts = 3,
        [int]$DelaySeconds = 10
    )

    $started = Invoke-WithRetry -Name $Name -MaxAttempts $MaxAttempts -DelaySeconds $DelaySeconds -ScriptBlock {
        & $Command @Args
    }

    if (-not $started) {
        Write-Error ("{0} startup failed after {1} attempts." -f $Name, $MaxAttempts)
        exit 1
    }

    if ($HealthUrls -and -not (Test-HttpHealth -Urls $HealthUrls)) {
        Write-Error ("{0} did not become healthy within the timeout window." -f $Name)
        exit 1
    }
}

Write-Host "Starting MySQL Docker environment..." -ForegroundColor Cyan
Start-ServiceStack -Name "MySQL Docker" -Command "powershell.exe" -Args @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-File', $mysqlScript
) -HealthUrls @()

Write-Host "Starting Airflow stack..." -ForegroundColor Cyan
Start-ServiceStack -Name "Airflow" -Command "powershell.exe" -Args @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-File', $airflowScript
) -HealthUrls @(
    'http://127.0.0.1:8080/health',
    'http://127.0.0.1:8080/',
    'http://127.0.0.1:5000/health',
    'http://127.0.0.1:5000/'
) -MaxAttempts $StartupRetryCount -DelaySeconds $StartupRetryDelaySeconds

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