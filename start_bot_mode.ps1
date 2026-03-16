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

    [ValidateSet("AUTO", "IBKR", "ALPACA", "MT5", "BINANCE", "COINBASE")]
    [string]$Broker = "AUTO"
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

$resolvedBroker = $Broker.ToUpper()
if ($resolvedBroker -eq "AUTO") {
    if ($Bot -eq "Vega") {
        $resolvedBroker = "IBKR"
    } else {
        $resolvedBroker = "ALPACA"
    }
}

$modeLower = $Mode.ToLower()
$status = "placeholder"
$note = "ON/OFF launcher contract is active for this bot. Runtime executor is not implemented yet."
$ibkrConnectOk = $null
$ibkrProbeOutput = ""

if ($Bot -eq "Vega" -and $resolvedBroker -eq "IBKR" -and $Mode -eq "ON") {
    if (-not $env:IBKR_HOST) { $env:IBKR_HOST = "127.0.0.1" }
    if (-not $env:IBKR_PORT) { $env:IBKR_PORT = "7496" }
    if (-not $env:IBKR_CLIENT_ID) { $env:IBKR_CLIENT_ID = "1" }

    $probe = & $pythonExe -c "from bbbot1_pipeline.broker_api import IBKRClient; c=IBKRClient(); ok=c.connect(); print('IBKR_SOCKET_CONNECT_OK='+str(ok))" 2>&1
    $ibkrProbeOutput = ($probe | Out-String).Trim()

    if ($ibkrProbeOutput -match "IBKR_SOCKET_CONNECT_OK=True") {
        $ibkrConnectOk = $true
        $status = "ready"
        $note = "Vega launcher ON confirmed with IBKR socket connectivity."
    } else {
        $ibkrConnectOk = $false
        $status = "warning"
        $note = "Vega launcher ON attempted but IBKR connectivity probe did not confirm success."
    }
}

$timestamp = (Get-Date).ToUniversalTime().ToString("o")
$event = [ordered]@{
    timestamp = $timestamp
    bot = $Bot
    mode = $modeLower
    broker = $resolvedBroker
    status = $status
    note = $note
    ibkr_connect_ok = $ibkrConnectOk
}

if ($ibkrProbeOutput) {
    $event["ibkr_probe_output"] = $ibkrProbeOutput
}

$eventJson = $event | ConvertTo-Json -Compress -Depth 6
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
        $message = "Bot $Bot $Mode | Broker: $resolvedBroker | Status: $status"
        $body = @{ content = $message } | ConvertTo-Json -Depth 4
        $response = Invoke-WebRequest -Method Post -Uri $webhookUrl -ContentType "application/json" -Body $body -UseBasicParsing
        $event["discord_sent"] = $true
        $event["discord_status_code"] = [int]$response.StatusCode
    } catch {
        $event["discord_sent"] = $false
        $event["discord_error"] = $_.Exception.Message
        if ($_.Exception.Response) {
            try {
                $event["discord_status_code"] = [int]$_.Exception.Response.StatusCode.value__
            } catch {
                $event["discord_status_code"] = -1
            }
        }
    }
} else {
    $event["discord_sent"] = $false
    $event["discord_error"] = "No DISCORD webhook environment variable set"
}

# Persist final event snapshot (with discord metadata) for dashboard convenience.
$latestPath = Join-Path $logDir "last_bot_mode_event.json"
$event | ConvertTo-Json -Depth 8 | Set-Content -Path $latestPath -Encoding UTF8

Write-Host (($event | ConvertTo-Json -Depth 8))
