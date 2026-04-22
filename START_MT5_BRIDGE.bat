@echo off
REM ============================================================================
REM START_MT5_BRIDGE.bat
REM Launches the MT5 REST API Bridge Server on port 8080
REM Required: MetaTrader 5 desktop must be running and logged in
REM ============================================================================

setlocal enabledelayedexpansion

REM ──────────────────────────────────────────────────────────────────────────
REM Configuration
REM ──────────────────────────────────────────────────────────────────────────
set PORT=8080
set HOST=0.0.0.0
set SCRIPT_PATH=%~dp0scripts\mt5_rest.py
set LOG_DIR=%~dp0logs
set LOG_FILE=%LOG_DIR%\mt5_bridge.log

REM ──────────────────────────────────────────────────────────────────────────
REM Colors for output
REM ──────────────────────────────────────────────────────────────────────────
for /F %%A in ('copy /Z "%~f0" nul') do set "BS=%%A"

REM ──────────────────────────────────────────────────────────────────────────
REM Verify Python is available
REM ──────────────────────────────────────────────────────────────────────────
echo [*] Checking Python installation...
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Python not found. Ensure Python is installed and in PATH.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo [OK] Found: %%i

REM ──────────────────────────────────────────────────────────────────────────
REM Check if MT5 bridge script exists
REM ──────────────────────────────────────────────────────────────────────────
if not exist "%SCRIPT_PATH%" (
    echo [ERROR] MT5 bridge script not found: %SCRIPT_PATH%
    pause
    exit /b 1
)
echo [OK] Found MT5 bridge script: %SCRIPT_PATH%

REM ──────────────────────────────────────────────────────────────────────────
REM Verify FastAPI is installed
REM ──────────────────────────────────────────────────────────────────────────
echo [*] Checking for FastAPI...
python -c "import fastapi; print('[OK] FastAPI version:', fastapi.__version__)" 2>nul
if !errorlevel! neq 0 (
    echo [WARNING] FastAPI not found. Installing...
    python -m pip install --quiet fastapi[standard] uvicorn[standard]
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install FastAPI
        pause
        exit /b 1
    )
)

REM ──────────────────────────────────────────────────────────────────────────
REM Create logs directory
REM ──────────────────────────────────────────────────────────────────────────
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM ──────────────────────────────────────────────────────────────────────────
REM Check if MT5 is running
REM ──────────────────────────────────────────────────────────────────────────
echo [*] Checking for MetaTrader 5...
tasklist | find /i "terminal64.exe" >nul 2>&1
if !errorlevel! neq 0 (
    echo [WARNING] MetaTrader 5 (terminal64.exe) is not running!
    echo [INFO] Please start MetaTrader 5 and log in before continuing.
    echo.
    echo Once MT5 is running, press any key to continue...
    pause
)

REM ──────────────────────────────────────────────────────────────────────────
REM Set environment variables
REM ──────────────────────────────────────────────────────────────────────────
set PORT=%PORT%
set HOST=%HOST%
set PYTHONUNBUFFERED=1

REM ──────────────────────────────────────────────────────────────────────────
REM Display startup banner
REM ──────────────────────────────────────────────────────────────────────────
cls
echo.
echo ============================================================================
echo  MT5 REST API Bridge Server
echo ============================================================================
echo.
echo  Status: Starting...
echo  Port: %PORT%
echo  Host: %HOST%
echo  Script: %SCRIPT_PATH%
echo  Logs: %LOG_FILE%
echo.
echo  IMPORTANT: MetaTrader 5 must be running and logged in!
echo.
echo  Test the bridge with:
echo    curl http://localhost:%PORT%/health
echo.
echo  Stop the server: Ctrl+C
echo ============================================================================
echo.

REM ──────────────────────────────────────────────────────────────────────────
REM Start the MT5 bridge server
REM ──────────────────────────────────────────────────────────────────────────
python "%SCRIPT_PATH%" 2>&1

REM If we get here, the script exited
echo [ERROR] MT5 bridge exited unexpectedly
echo [INFO] Check logs at: %LOG_FILE%
pause
