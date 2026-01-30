#!/usr/bin/env powershell
<#
.SYNOPSIS
    Deploy MT5 REST API on Windows VPS for production trading.

.DESCRIPTION
    Automated setup for running mt5_rest.py on a Windows server with:
    - Git repository cloning
    - Python environment setup
    - Dependency installation
    - MT5 credentials configuration
    - Windows Service creation (optional)
    - Firewall rules

.PARAMETER SourceDir
    Directory to clone repo into (default: C:\BentleyBot)

.PARAMETER MTUser
    MT5 account number (required)

.PARAMETER MTPassword
    MT5 password (required)

.PARAMETER MTHost
    MT5 broker host (required)

.PARAMETER Port
    API port (default: 8080)

.PARAMETER CreateService
    Create Windows Service for autostart (default: $false)

.EXAMPLE
    .\deploy_windows_vps.ps1 -MTUser "12345" -MTPassword "pass123" -MTHost "example.com"

.EXAMPLE
    .\deploy_windows_vps.ps1 -MTUser "12345" -MTPassword "pass123" -MTHost "example.com" -CreateService

#>

param(
    [string]$SourceDir = "C:\BentleyBot",
    [Parameter(Mandatory=$true)][string]$MTUser,
    [Parameter(Mandatory=$true)][string]$MTPassword,
    [Parameter(Mandatory=$true)][string]$MTHost,
    [int]$Port = 8080,
    [bool]$CreateService = $false
)

# Requires admin
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ERROR: Must run as Administrator" -ForegroundColor Red
    exit 1
}

Write-Host "=== MT5 REST API - Windows VPS Deployment ===" -ForegroundColor Cyan

# 1. Check prerequisites
Write-Host "`n[1/8] Checking prerequisites..." -ForegroundColor Yellow
$checks = @{
    "Git" = "git --version";
    "Python 3.11+" = "python --version";
    "MetaTrader 5" = "Get-Command 'MetaEditor64.exe' -ErrorAction SilentlyContinue"
}

foreach ($check in $checks.GetEnumerator()) {
    try {
        $result = Invoke-Expression $check.Value 2>&1
        Write-Host "  ✓ $($check.Key): $($result | Select-Object -First 1)" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ $($check.Key) not found" -ForegroundColor Red
    }
}

# 2. Clone repository
Write-Host "`n[2/8] Cloning repository..." -ForegroundColor Yellow
if (Test-Path $SourceDir) {
    Write-Host "  ! Directory exists: $SourceDir" -ForegroundColor Magenta
    $update = Read-Host "  Pull latest? (y/n)"
    if ($update -eq 'y') {
        Push-Location $SourceDir
        git pull origin main
        Pop-Location
    }
} else {
    Write-Host "  Cloning to: $SourceDir"
    git clone https://github.com/winstonwilliamsiii/BBBot $SourceDir
}
Write-Host "  ✓ Repository ready" -ForegroundColor Green

# 3. Create Python venv
Write-Host "`n[3/8] Creating Python virtual environment..." -ForegroundColor Yellow
$venvPath = Join-Path $SourceDir "venv"
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
    Write-Host "  ✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "  ✓ Virtual environment exists" -ForegroundColor Green
}

# 4. Activate venv and install dependencies
Write-Host "`n[4/8] Installing Python dependencies..." -ForegroundColor Yellow
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
& $activateScript

Push-Location $SourceDir
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
Pop-Location

# 5. Create environment file
Write-Host "`n[5/8] Creating .env configuration..." -ForegroundColor Yellow
$envFile = Join-Path $SourceDir ".env.vps"
$envContent = @"
# MT5 REST API Configuration
# Generated: $(Get-Date)

# API Server
HOST=0.0.0.0
PORT=$Port

# MT5 Credentials
MT5_USER=$MTUser
MT5_PASSWORD=$MTPassword
MT5_HOST=$MTHost

# Logging
LOG_LEVEL=INFO
LOG_FILE=$SourceDir\logs\mt5_rest.log
"@

Set-Content -Path $envFile -Value $envContent
Write-Host "  ✓ Configuration saved: $envFile" -ForegroundColor Green

# 6. Create logs directory
Write-Host "`n[6/8] Setting up logging..." -ForegroundColor Yellow
$logsDir = Join-Path $SourceDir "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}
Write-Host "  ✓ Logs directory: $logsDir" -ForegroundColor Green

# 7. Configure Firewall
Write-Host "`n[7/8] Configuring Windows Firewall..." -ForegroundColor Yellow
try {
    $ruleName = "MT5-REST-API-$Port"
    Remove-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue
    New-NetFirewallRule -Name $ruleName `
                        -DisplayName "MT5 REST API (Port $Port)" `
                        -Direction Inbound `
                        -Action Allow `
                        -Protocol TCP `
                        -LocalPort $Port | Out-Null
    Write-Host "  ✓ Firewall rule added: $ruleName" -ForegroundColor Green
} catch {
    Write-Host "  ! Firewall configuration skipped (may require manual setup)" -ForegroundColor Yellow
}

# 8. Create startup script
Write-Host "`n[8/8] Creating startup scripts..." -ForegroundColor Yellow

# Batch file for manual start
$batchFile = Join-Path $SourceDir "start_mt5_api.bat"
$batchContent = @"
@echo off
REM MT5 REST API Start Script
cd /d "$SourceDir"
call venv\Scripts\activate.bat
set /p MT5_USER=Enter MT5 Account: 
set /p MT5_PASSWORD=Enter MT5 Password: 
set /p MT5_HOST=Enter Broker Host (default: @echo off
REM MT5 REST API Start Script
cd /d "$SourceDir"
call venv\Scripts\activate.bat
set "MT5_HOST=mt5.example.com"
set "MT5_USER=$MTUser"
set "MT5_PASSWORD=$MTPassword"
set "HOST=0.0.0.0"
set "PORT=$Port"
echo Starting MT5 REST API on port $Port...
python mt5_rest.py
pause
"@
Set-Content -Path $batchFile -Value $batchContent
Write-Host "  ✓ Batch starter: $batchFile" -ForegroundColor Green

# PowerShell startup script
$psFile = Join-Path $SourceDir "start_mt5_api.ps1"
$psContent = @"
# MT5 REST API Start Script
`$SourceDir = "$SourceDir"
Push-Location `$SourceDir

# Activate venv
& ".\venv\Scripts\Activate.ps1"

# Set environment
`$env:MT5_USER = "$MTUser"
`$env:MT5_PASSWORD = "$MTPassword"
`$env:MT5_HOST = "$MTHost"
`$env:HOST = "0.0.0.0"
`$env:PORT = $Port

Write-Host "Starting MT5 REST API on port $Port..." -ForegroundColor Green
Write-Host "Access at: http://localhost:$Port/health" -ForegroundColor Cyan

# Run server
python mt5_rest.py
"@
Set-Content -Path $psFile -Value $psContent
Write-Host "  ✓ PowerShell starter: $psFile" -ForegroundColor Green

# Optional: Create Windows Service
if ($CreateService) {
    Write-Host "`n[BONUS] Creating Windows Service..." -ForegroundColor Yellow
    
    $serviceName = "MT5-REST-API"
    $serviceDisplayName = "MT5 REST API"
    $pythonExe = Join-Path $venvPath "Scripts\python.exe"
    $scriptPath = Join-Path $SourceDir "mt5_rest.py"
    
    # Remove existing service
    Stop-Service $serviceName -ErrorAction SilentlyContinue
    Remove-Service $serviceName -ErrorAction SilentlyContinue
    
    # Create service (requires NSSM or similar)
    Write-Host "  ! Windows Service requires NSSM tool" -ForegroundColor Yellow
    Write-Host "  ! Download: https://nssm.cc/download" -ForegroundColor Yellow
    Write-Host "  ! Then run: nssm install $serviceName `"$pythonExe`" `"$scriptPath`"" -ForegroundColor Cyan
} else {
    Write-Host "`n[BONUS] Skip Windows Service" -ForegroundColor Yellow
}

# Summary
Write-Host "`n" -ForegroundColor White
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Green

Write-Host "`n📍 Installation Directory: $SourceDir" -ForegroundColor Cyan
Write-Host "🔧 Environment File: $envFile" -ForegroundColor Cyan
Write-Host "📝 Logs Directory: $logsDir" -ForegroundColor Cyan
Write-Host "🚀 API Port: $Port" -ForegroundColor Cyan

Write-Host "`n▶ Start the server:" -ForegroundColor Yellow
Write-Host "   PowerShell: .\start_mt5_api.ps1" -ForegroundColor White
Write-Host "   Batch: start_mt5_api.bat" -ForegroundColor White
Write-Host "   Manual: cd $SourceDir; .\venv\Scripts\activate.ps1; python mt5_rest.py" -ForegroundColor White

Write-Host "`n✅ Test the API:" -ForegroundColor Yellow
Write-Host "   curl http://localhost:$Port/health" -ForegroundColor White

Write-Host "`n📖 Documentation:" -ForegroundColor Yellow
Write-Host "   RAILWAY_DEPLOYMENT.md - Full setup guide" -ForegroundColor White
Write-Host "   mt5_rest.py - API endpoints" -ForegroundColor White
Write-Host "   pages/api/mt5_bridge.py - MT5 bridge implementation" -ForegroundColor White

Write-Host "`n" -ForegroundColor White
