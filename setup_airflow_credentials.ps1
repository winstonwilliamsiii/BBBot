#!/usr/bin/env pwsh
# Setup Airflow Variables and Connections for Plaid Integration
# Run this script to securely configure credentials in Airflow

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Bentley Budget Bot - Airflow Credentials Setup" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if Airflow is running
Write-Host "Checking Airflow status..." -ForegroundColor Yellow
$airflowRunning = docker ps --filter "name=bentley-airflow-scheduler" --filter "status=running" -q
if (-not $airflowRunning) {
    Write-Host "❌ Airflow scheduler is not running!" -ForegroundColor Red
    Write-Host "   Start with: docker-compose -f docker-compose-airflow.yml up -d`n" -ForegroundColor Gray
    exit 1
}
Write-Host "✅ Airflow is running`n" -ForegroundColor Green

# Prompt for Plaid credentials
Write-Host "Enter Plaid Credentials:" -ForegroundColor Cyan
Write-Host "(Get from: https://dashboard.plaid.com/account/keys)`n" -ForegroundColor Gray

$clientId = Read-Host "Plaid Client ID"
if ([string]::IsNullOrWhiteSpace($clientId)) {
    Write-Host "❌ Client ID is required" -ForegroundColor Red
    exit 1
}

$secret = Read-Host "Plaid Secret (will be encrypted)" -MaskInput
if ([string]::IsNullOrWhiteSpace($secret)) {
    Write-Host "❌ Secret is required" -ForegroundColor Red
    exit 1
}

$accessToken = Read-Host "Plaid Access Token (will be encrypted)" -MaskInput
if ([string]::IsNullOrWhiteSpace($accessToken)) {
    Write-Host "❌ Access Token is required" -ForegroundColor Red
    exit 1
}

$env = Read-Host "Plaid Environment (sandbox/development/production) [default: sandbox]"
if ([string]::IsNullOrWhiteSpace($env)) {
    $env = "sandbox"
}

$startDate = Read-Host "Default Start Date [default: 2025-11-01]"
if ([string]::IsNullOrWhiteSpace($startDate)) {
    $startDate = "2025-11-01"
}

$endDate = Read-Host "Default End Date [default: 2025-11-23]"
if ([string]::IsNullOrWhiteSpace($endDate)) {
    $endDate = "2025-11-23"
}

# Set Airflow Variables
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setting Airflow Variables..." -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

$variables = @{
    "plaid_client_id" = $clientId
    "plaid_secret" = $secret
    "plaid_access_token" = $accessToken
    "plaid_env" = $env
    "plaid_start_date" = $startDate
    "plaid_end_date" = $endDate
}

foreach ($key in $variables.Keys) {
    $value = $variables[$key]
    Write-Host "  Setting: $key" -ForegroundColor Gray
    
    $result = docker exec bentley-airflow-scheduler airflow variables set $key $value 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $key set successfully" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Failed to set $key`: $result" -ForegroundColor Red
    }
}

# Set MySQL Connection
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setting MySQL Connection..." -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if connection already exists
$existingConn = docker exec bentley-airflow-scheduler airflow connections get mysql_default 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "⚠️  Connection 'mysql_default' already exists" -ForegroundColor Yellow
    $overwrite = Read-Host "Overwrite? (y/N)"
    if ($overwrite -eq "y" -or $overwrite -eq "Y") {
        docker exec bentley-airflow-scheduler airflow connections delete mysql_default 2>$null
        Write-Host "  Deleted existing connection" -ForegroundColor Gray
    } else {
        Write-Host "  Skipping MySQL connection setup" -ForegroundColor Gray
        $skipMysql = $true
    }
}

if (-not $skipMysql) {
    $mysqlResult = docker exec bentley-airflow-scheduler airflow connections add 'mysql_default' `
        --conn-type 'mysql' `
        --conn-host 'mysql' `
        --conn-schema 'mansa_bot' `
        --conn-login 'root' `
        --conn-password 'root' `
        --conn-port 3306 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ MySQL connection created successfully" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Failed to create MySQL connection: $mysqlResult" -ForegroundColor Red
    }
}

# Verify setup
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Verifying Setup..." -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Airflow Variables:" -ForegroundColor White
$varList = docker exec bentley-airflow-scheduler airflow variables list 2>&1 | Select-String "plaid_"
if ($varList) {
    $varList | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
} else {
    Write-Host "  (No plaid variables found)" -ForegroundColor Yellow
}

Write-Host "`nAirflow Connections:" -ForegroundColor White
$connList = docker exec bentley-airflow-scheduler airflow connections list 2>&1 | Select-String "mysql_default"
if ($connList) {
    $connList | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
} else {
    Write-Host "  (mysql_default not found)" -ForegroundColor Yellow
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next Steps:" -ForegroundColor White
Write-Host "  1. Verify credentials at: http://localhost:8080" -ForegroundColor Gray
Write-Host "     - Admin → Variables" -ForegroundColor Gray
Write-Host "     - Admin → Connections" -ForegroundColor Gray
Write-Host "`n  2. Test Plaid integration:" -ForegroundColor Gray
Write-Host "     docker exec bentley-airflow-scheduler airflow dags trigger plaid_sync_dag" -ForegroundColor Gray
Write-Host "`n  3. View logs:" -ForegroundColor Gray
Write-Host "     docker exec bentley-airflow-scheduler airflow tasks test plaid_sync_dag fetch_plaid_transactions 2025-11-23" -ForegroundColor Gray
Write-Host "`n  4. (Optional) Remove credentials from .env file" -ForegroundColor Gray
Write-Host ""

Write-Host "🔐 All sensitive values are encrypted by Airflow" -ForegroundColor Cyan
Write-Host "📋 See AIRFLOW_CREDENTIALS_GUIDE.md for more details`n" -ForegroundColor Cyan
