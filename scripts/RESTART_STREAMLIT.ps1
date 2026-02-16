#!/usr/bin/env pwsh
"""
Clean Streamlit restart script - kills all processes and starts fresh
"""

Write-Host "=================================="
Write-Host "STREAMLIT CLEAN RESTART"
Write-Host "=================================="

# 1. Kill all Python processes related to this project
Write-Host "`n1. Stopping Streamlit and Python processes..."
Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*BentleyBudgetBot*" -or 
    $_.CommandLine -like "*streamlit*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

# Also try taskkill as fallback
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Streamlit*" 2>$null
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *streamlit*" 2>$null

Write-Host "   Processes stopped"

# 2. Clear Streamlit cache
Write-Host "`n2. Clearing Streamlit cache..."
$streamlit_cache = "$env:APPDATA\streamlit"
if (Test-Path $streamlit_cache) {
    Remove-Item "$streamlit_cache\cache" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "   Cache cleared"
}

# 3. Clear Python cache
Write-Host "`n3. Clearing Python cache files..."
Get-ChildItem -Path (Get-Location) -Recurse -Include "__pycache__" -Directory | 
    ForEach-Object { Remove-Item $_ -Recurse -Force -ErrorAction SilentlyContinue }
Write-Host "   Python cache cleared"

# 4. Wait a moment
Write-Host "`n4. Waiting for processes to terminate..."
Start-Sleep -Seconds 2

# 5. Start Streamlit fresh
Write-Host "`n5. Starting Streamlit (clean environment)..."
Write-Host "   URL: http://localhost:8501"
Write-Host "   Press Ctrl+C to stop`n"

# Activate virtual environment if it exists
$venv = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $venv) {
    & $venv
}

# Start Streamlit
streamlit run streamlit_app.py
