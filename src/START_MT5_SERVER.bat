@echo off
REM ================================================
REM MT5 REST API Server Startup Script
REM ================================================
REM This script starts the MetaTrader 5 REST API server
REM Required: MT5 desktop terminal must be running
REM ================================================

echo.
echo ================================================
echo  Starting MT5 REST API Server
echo ================================================
echo.
echo Requirements:
echo  [1] MetaTrader 5 terminal is running
echo  [2] MT5 is logged into your account
echo  [3] Python virtual environment is activated
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if MT5 is running
tasklist /FI "IMAGENAME eq terminal64.exe" 2>NUL | find /I /N "terminal64.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] MetaTrader 5 terminal is running
) else (
    echo [WARNING] MetaTrader 5 terminal not detected!
    echo           Please start MT5 terminal first
    echo.
    pause
    exit /b 1
)

echo.
echo Starting MT5 REST API server on port 8002...
echo Server will be accessible at: http://localhost:8002
echo.
echo Available endpoints:
echo   GET  /Health           - Health check
echo   GET  /Connect          - Connect to MT5 account  
echo   GET  /AccountInfo      - Get account info
echo   GET  /Positions        - Get open positions
echo   POST /PlaceTrade       - Place order
echo.
echo Press CTRL+C to stop the server
echo ================================================
echo.

REM Set port to 8002 (8000 is used by Airbyte)
set PORT=8002
set HOST=0.0.0.0

REM Start the MT5 REST API server
python src\mt5_rest_api_server.py

pause
