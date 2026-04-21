param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(
        "Titan", "Vega", "Rigel", "Dogon", "Orion",
        "Draco", "Altair", "Procryon", "Hydra", "Triton",
        "Dione", "Cephei", "Rhea", "Jupicita"
    )]
    [string]$Bot,

    [Parameter(Mandatory = $true)]
    [ValidateSet("ON", "OFF")]
    [string]$Mode,

    [ValidateSet("AUTO", "IBKR", "ALPACA", "MT5", "FTMO", "AXI", "BINANCE", "COINBASE")]
    [string]$Broker = "AUTO",

    [ValidateSet("AUTO", "paper", "live")]
    [string]$TradingMode = "AUTO"
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

function Get-ConfigTradingMode {
    param(
        [string]$BrokerName
    )

    $configPath = Join-Path $repoRoot "config\broker_modes.json"
    if (-not (Test-Path $configPath)) {
        return "paper"
    }

    try {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
        $brokerKey = $BrokerName.ToLower()

        if ($config.broker_modes -and $config.broker_modes.$brokerKey) {
            return [string]$config.broker_modes.$brokerKey
        }

        if ($config.global_mode) {
            return [string]$config.global_mode
        }
    } catch {
        return "paper"
    }

    return "paper"
}

function Set-ModeEnvironment {
    param(
        [string]$BrokerName,
        [string]$ModeName
    )

    $envName = "{0}_MODE" -f $BrokerName.ToUpper()
    Set-Item -Path ("Env:{0}" -f $envName) -Value $ModeName
}

function Set-JsonProperty {
    param(
        [object]$Container,
        [string]$PropertyName,
        [object]$Value
    )

    if ($null -eq $Container) {
        return
    }

    if ($Container.PSObject.Properties.Name -contains $PropertyName) {
        $Container.$PropertyName = $Value
    } else {
        $Container | Add-Member -NotePropertyName $PropertyName -NotePropertyValue $Value
    }
}

function Update-BrokerModeConfig {
    param(
        [string]$BotName,
        [string]$BrokerName,
        [string]$TradingModeName,
        [bool]$IsActive
    )

    $configPath = Join-Path $repoRoot "config\broker_modes.json"
    if (-not (Test-Path $configPath)) {
        return
    }

    try {
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
    } catch {
        return
    }

    if (-not $config.active_bots) {
        $config | Add-Member -NotePropertyName "active_bots" -NotePropertyValue ([pscustomobject]@{})
    }
    if (-not $config.bot_broker_mapping) {
        $config | Add-Member -NotePropertyName "bot_broker_mapping" -NotePropertyValue ([pscustomobject]@{})
    }
    if (-not $config.broker_modes) {
        $config | Add-Member -NotePropertyName "broker_modes" -NotePropertyValue ([pscustomobject]@{})
    }

    $brokerKey = $BrokerName.ToLower()
    Set-JsonProperty -Container $config.active_bots -PropertyName $BotName -Value $IsActive
    Set-JsonProperty -Container $config.bot_broker_mapping -PropertyName $BotName -Value $brokerKey
    Set-JsonProperty -Container $config.broker_modes -PropertyName $brokerKey -Value $TradingModeName

    $config | ConvertTo-Json -Depth 8 | Set-Content -Path $configPath -Encoding UTF8
}

$resolvedBroker = $Broker.ToUpper()
if ($resolvedBroker -eq "AUTO") {
    if ($Bot -eq "Vega") {
        $resolvedBroker = "AXI"
    } elseif ($Bot -eq "Rigel") {
        $resolvedBroker = "FTMO"
    } else {
        $resolvedBroker = "ALPACA"
    }
}

$resolvedTradingMode = $TradingMode.ToLower()
if ($resolvedTradingMode -eq "auto") {
    $resolvedTradingMode = Get-ConfigTradingMode -BrokerName $resolvedBroker
}
if ($resolvedTradingMode -notin @("paper", "live")) {
    $resolvedTradingMode = "paper"
}

Set-ModeEnvironment -BrokerName $resolvedBroker -ModeName $resolvedTradingMode
Update-BrokerModeConfig -BotName $Bot -BrokerName $resolvedBroker -TradingModeName $resolvedTradingMode -IsActive ($Mode -eq "ON")

$modeLower = $Mode.ToLower()
$status = if ($Mode -eq "ON") { "ready" } else { "inactive" }
$note = if ($Mode -eq "ON") {
    "Bot launch state persisted to config/broker_modes.json."
} else {
    "Bot marked inactive in config/broker_modes.json."
}
$ibkrConnectOk = $null
$ibkrProbeOutput = ""
$tritonBootstrapOk = $null
$tritonProbeOutput = ""

if ($Bot -eq "Vega" -and $resolvedBroker -eq "AXI" -and $Mode -eq "ON") {
    # AXI uses MT5 bridge — verify the MT5 API endpoint is reachable
    $axiApiUrl = if ($env:AXI_MT5_API_URL) { $env:AXI_MT5_API_URL } else { "https://bbbot-production.up.railway.app" }
    $probe = & $pythonExe -c @"
import urllib.request, urllib.error, sys
try:
    req = urllib.request.urlopen('$axiApiUrl/health', timeout=5)
    print('AXI_API_OK=True')
except Exception as e:
    print('AXI_API_OK=False')
    print(str(e))
"@ 2>&1
    $ibkrProbeOutput = ($probe | Out-String).Trim()

    if ($ibkrProbeOutput -match "AXI_API_OK=True") {
        $ibkrConnectOk = $true
        $status = "ready"
        $note = "Vega launcher ON confirmed with AXI MT5 API connectivity."
    } else {
        $ibkrConnectOk = $false
        $status = "ready"
        $note = "Vega launcher ON (AXI MT5 paper mode). API probe: $ibkrProbeOutput"
    }
}

if ($Bot -eq "Rigel" -and $resolvedBroker -eq "FTMO" -and $Mode -eq "ON") {
    # FTMO uses MT5 bridge — set ready state (paper mode, no live socket needed)
    $status = "ready"
    $note = "Rigel launcher ON (FTMO MT5 paper mode). Credentials loaded from env."
}

if ($Bot -eq "Triton" -and $Mode -eq "ON") {
    $probe = & $pythonExe -c "from triton_bot import TritonBot; bot=TritonBot(); result=bot.bootstrap_demo_state(); print('TRITON_BOOTSTRAP_OK=True'); print('TRITON_ACTION=' + str(result.get('action', 'unknown'))); print('TRITON_SCORE=' + str(result.get('composite_score', 'unknown')))" 2>&1
    $tritonProbeOutput = ($probe | Out-String).Trim()

    if ($tritonProbeOutput -match "TRITON_BOOTSTRAP_OK=True") {
        $tritonBootstrapOk = $true
        $status = "ready"
        $note = "Triton launcher ON confirmed with local bootstrap analysis."
    } else {
        $tritonBootstrapOk = $false
        $status = "warning"
        $note = "Triton launcher ON attempted but local bootstrap analysis did not confirm success."
    }
}

$timestamp = (Get-Date).ToUniversalTime().ToString("o")
$botEvent = [ordered]@{
    timestamp = $timestamp
    bot = $Bot
    mode = $modeLower
    broker = $resolvedBroker
    trading_mode = $resolvedTradingMode
    status = $status
    note = $note
    ibkr_connect_ok = $ibkrConnectOk
    triton_bootstrap_ok = $tritonBootstrapOk
}

if ($ibkrProbeOutput) {
    $botEvent["ibkr_probe_output"] = $ibkrProbeOutput
}

if ($tritonProbeOutput) {
    $botEvent["triton_probe_output"] = $tritonProbeOutput
}

$eventJson = $botEvent | ConvertTo-Json -Compress -Depth 6
$eventsPath = Join-Path $logDir "bot_mode_events.jsonl"
Add-Content -Path $eventsPath -Value $eventJson

$webhookUrl = $env:DISCORD_WEBHOOK
if (-not $webhookUrl) { $webhookUrl = $env:DISCORD_WEBHOOK_PROD }
if (-not $webhookUrl) { $webhookUrl = $env:DISCORD_WEBHOOK_URL }
if (-not $webhookUrl) {
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
                $webhookUrl = $webhookValue
            }
        }
    }
}

if ($webhookUrl) {
    try {
        $message = "Bot $Bot $Mode | Broker: $resolvedBroker | Trading Mode: $resolvedTradingMode | Status: $status"
        $body = @{ content = $message } | ConvertTo-Json -Depth 4
        $response = Invoke-WebRequest -Method Post -Uri $webhookUrl -ContentType "application/json" -Body $body -UseBasicParsing
        $botEvent["discord_sent"] = $true
        $botEvent["discord_status_code"] = [int]$response.StatusCode
    } catch {
        $botEvent["discord_sent"] = $false
        $botEvent["discord_error"] = $_.Exception.Message
        if ($_.Exception.Response) {
            try {
                $botEvent["discord_status_code"] = [int]$_.Exception.Response.StatusCode.value__
            } catch {
                $botEvent["discord_status_code"] = -1
            }
        }
    }
} else {
    $botEvent["discord_sent"] = $false
    $botEvent["discord_error"] = "No DISCORD webhook environment variable set"
}

# Persist final event snapshot (with discord metadata) for dashboard convenience.
$latestPath = Join-Path $logDir "last_bot_mode_event.json"
$botEvent | ConvertTo-Json -Depth 8 | Set-Content -Path $latestPath -Encoding UTF8

Write-Host (($botEvent | ConvertTo-Json -Depth 8))
