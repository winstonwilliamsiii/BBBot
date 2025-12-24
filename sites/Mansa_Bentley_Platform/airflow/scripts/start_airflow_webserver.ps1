# Airflow Webserver Startup Script for Windows
# Handles encoding and compatibility issues

# Set UTF-8 encoding
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# Set Airflow environment
$env:AIRFLOW_HOME = "c:\Users\winst\BentleyBudgetBot\airflow_config"
$env:AIRFLOW__CORE__MP_START_METHOD = "spawn"
$env:AIRFLOW__CORE__EXECUTOR = "LocalExecutor"

Write-Host "🚀 Starting Airflow Webserver with Windows compatibility..." -ForegroundColor Green
Write-Host "📍 AIRFLOW_HOME: $env:AIRFLOW_HOME" -ForegroundColor Cyan
Write-Host "🌐 Webserver will be available at: http://localhost:8080" -ForegroundColor Yellow

# Change to project directory
Set-Location "c:\Users\winst\BentleyBudgetBot"

# Import the Windows compatibility wrapper and start webserver
python -c @"
import os
import sys
import warnings

# Windows compatibility patch
if not hasattr(os, 'register_at_fork'):
    def register_at_fork(**kwargs):
        pass
    os.register_at_fork = register_at_fork

# Set environment
os.environ.setdefault('AIRFLOW__CORE__MP_START_METHOD', 'spawn')
os.environ.setdefault('AIRFLOW__CORE__EXECUTOR', 'LocalExecutor')
warnings.filterwarnings('ignore', message='.*can be run on POSIX-compliant.*')

# Start webserver
try:
    from airflow.cli.commands.webserver_command import webserver
    print('✅ Starting Airflow webserver on port 8080...')
    webserver(['-p', '8080'])
except Exception as e:
    print(f'❌ Error starting webserver: {e}')
    sys.exit(1)
"@