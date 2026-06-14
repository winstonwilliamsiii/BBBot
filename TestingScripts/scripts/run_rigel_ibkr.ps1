#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run Rigel Forex Bot - End-to-End with IBKR TWS Paper Trade + MLflow + Discord

.DESCRIPTION
    Starts Rigel against the IBKR Client Portal Gateway (TWS paper trading).
    MLflow benchmark runs are logged automatically per cycle.
    Discord trade notifications fire via DISCORD_BOT_TALK_WEBHOOK.

.PREREQUISITES
    1. IBKR TWS (or Client Portal Gateway) running on localhost:5000
       - Paper trading account logged in
       - Gateway port: 5000 (Client Portal) or configure IBKR_GATEWAY_URL
    2. MLflow server running: mlflow server --host 127.0.0.1 --port 5001
       (or set MLFLOW_TRACKING_URI to your server)
    3. DISCORD_BOT_TALK_WEBHOOK set in .env or environment
    4. venv activated with requirements-rigel.txt installed

.USAGE
    # Dry-run (observe signals, no orders):
    .\scripts\run_rigel_ibkr.ps1

    # Paper trade (real IBKR paper orders):
    .\scripts\run_rigel_ibkr.ps1 -EnableTrading

    # Custom gateway URL:
    .\scripts\run_rigel_ibkr.ps1 -GatewayUrl "https://localhost:5000"
#>

param(
    [string]$GatewayUrl    = $env:IBKR_GATEWAY_URL ?? "https://localhost:5000",
    [string]$AccountId     = $env:IBKR_ACCOUNT_ID  ?? "",
    [string]$MlflowUri     = $env:MLFLOW_TRACKING_URI ?? "http://127.0.0.1:5001",
    [string]$Interval      = "300",   # seconds between cycles
    [switch]$EnableTrading,           # pass to execute real IBKR paper orders
    [switch]$EnableML                 # pass to activate ML predictor
)

# ── Resolve workspace root ───────────────────────────────────────────────────
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  RIGEL FOREX BOT  -  IBKR TWS Paper Trade" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Workspace   : $Root"
Write-Host "  IBKR Gateway: $GatewayUrl"
Write-Host "  Account     : $(if ($AccountId) { $AccountId } else { 'auto-detect' })"
Write-Host "  MLflow URI  : $MlflowUri"
Write-Host "  Trading ON  : $($EnableTrading.IsPresent)"
Write-Host "  ML ON       : $($EnableML.IsPresent)"
Write-Host "  Interval    : ${Interval}s"
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ── Verify venv ──────────────────────────────────────────────────────────────
$PythonExe = "$Root\venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Warning "venv not found at $PythonExe. Falling back to system python."
    $PythonExe = "python"
}

# ── Confirm IBKR Gateway is reachable ────────────────────────────────────────
Write-Host "[PRE-CHECK] Testing IBKR Gateway at $GatewayUrl ..." -ForegroundColor Yellow
try {
    $resp = Invoke-WebRequest -Uri "$GatewayUrl/v1/api/iserver/auth/status" `
                              -SkipCertificateCheck `
                              -TimeoutSec 5 `
                              -ErrorAction Stop
    $body = $resp.Content | ConvertFrom-Json
    if ($body.authenticated) {
        Write-Host "[PRE-CHECK] IBKR Gateway: AUTHENTICATED ✓" -ForegroundColor Green
    } else {
        Write-Warning "[PRE-CHECK] IBKR Gateway reachable but NOT authenticated."
        Write-Warning "  Log in to TWS / Client Portal Gateway first, then re-run."
        exit 1
    }
} catch {
    Write-Warning "[PRE-CHECK] Cannot reach IBKR Gateway: $_"
    Write-Warning "  Make sure TWS or IB Gateway is running on $GatewayUrl"
    exit 1
}

# ── Confirm MLflow is reachable (non-fatal) ───────────────────────────────────
Write-Host "[PRE-CHECK] Testing MLflow at $MlflowUri ..." -ForegroundColor Yellow
try {
    $null = Invoke-WebRequest -Uri "$MlflowUri/health" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "[PRE-CHECK] MLflow server: REACHABLE ✓" -ForegroundColor Green
} catch {
    Write-Warning "[PRE-CHECK] MLflow not reachable at $MlflowUri (runs will be logged locally)."
}

# ── Build environment ─────────────────────────────────────────────────────────
$env:BROKER_PLATFORM        = "ibkr"
$env:IBKR_GATEWAY_URL       = $GatewayUrl
$env:IBKR_ACCOUNT_ID        = $AccountId
$env:MLFLOW_TRACKING_URI    = $MlflowUri
$env:DRY_RUN                = if ($EnableTrading) { "false" } else { "true" }
$env:ENABLE_TRADING         = if ($EnableTrading) { "true"  } else { "false" }
$env:ENABLE_ML              = if ($EnableML)       { "true"  } else { "false" }

Write-Host ""
Write-Host "[ENV] BROKER_PLATFORM  = $($env:BROKER_PLATFORM)"
Write-Host "[ENV] DRY_RUN          = $($env:DRY_RUN)"
Write-Host "[ENV] ENABLE_TRADING   = $($env:ENABLE_TRADING)"
Write-Host "[ENV] ENABLE_ML        = $($env:ENABLE_ML)"
Write-Host ""

# ── Ensure logs directory exists ──────────────────────────────────────────────
New-Item -ItemType Directory -Force -Path "$Root\logs" | Out-Null

# ── Run Rigel ─────────────────────────────────────────────────────────────────
Write-Host "Starting Rigel Forex Bot..." -ForegroundColor Green
Write-Host "Log file: $Root\logs\rigel_forex_bot.log"
Write-Host "(Ctrl+C to stop)"
Write-Host ""

& $PythonExe -m scripts.rigel_forex_bot
