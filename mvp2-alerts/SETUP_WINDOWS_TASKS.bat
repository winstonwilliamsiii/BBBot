@echo off
REM Windows Task Scheduler Setup for TradingView Alerts
REM Run as Administrator

setlocal enabledelayedexpansion

echo.
echo ==========================================
echo  TradingView Alerts - Windows Task Setup
echo ==========================================
echo.

REM Get the path to this script directory
set SCRIPT_DIR=%~dp0
set NODE_PATH=C:\Program Files\nodejs\node.exe
set ALERT_SCRIPT=%SCRIPT_DIR%index.js

echo Checking Node.js installation...
if not exist "%NODE_PATH%" (
    echo ERROR: Node.js not found at %NODE_PATH%
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

echo OK: Found Node.js at %NODE_PATH%
echo Alert script: %ALERT_SCRIPT%
echo.

REM Create scheduled tasks
echo Creating scheduled tasks...
echo.

REM Task 1: 7:00 AM
echo [1/4] Creating task: TradingView-Alerts-7AM
schtasks /create /tn "TradingView-Alerts-7AM" /tr "\"%NODE_PATH%\" \"%ALERT_SCRIPT%\"" /sc daily /st 07:00 /d MON,TUE,WED,THU,FRI /f
if %ERRORLEVEL% EQU 0 echo   OK
if %ERRORLEVEL% NEQ 0 echo   FAILED

REM Task 2: 9:40 AM
echo [2/4] Creating task: TradingView-Alerts-9:40AM
schtasks /create /tn "TradingView-Alerts-9:40AM" /tr "\"%NODE_PATH%\" \"%ALERT_SCRIPT%\"" /sc daily /st 09:40 /d MON,TUE,WED,THU,FRI /f
if %ERRORLEVEL% EQU 0 echo   OK
if %ERRORLEVEL% NEQ 0 echo   FAILED

REM Task 3: 11:30 AM
echo [3/4] Creating task: TradingView-Alerts-11:30AM
schtasks /create /tn "TradingView-Alerts-11:30AM" /tr "\"%NODE_PATH%\" \"%ALERT_SCRIPT%\"" /sc daily /st 11:30 /d MON,TUE,WED,THU,FRI /f
if %ERRORLEVEL% EQU 0 echo   OK
if %ERRORLEVEL% NEQ 0 echo   FAILED

REM Task 4: 3:00 PM
echo [4/4] Creating task: TradingView-Alerts-3PM
schtasks /create /tn "TradingView-Alerts-3PM" /tr "\"%NODE_PATH%\" \"%ALERT_SCRIPT%\"" /sc daily /st 15:00 /d MON,TUE,WED,THU,FRI /f
if %ERRORLEVEL% EQU 0 echo   OK
if %ERRORLEVEL% NEQ 0 echo   FAILED

echo.
echo ==========================================
echo  Setup Complete!
echo ==========================================
echo.
echo Tasks scheduled for weekdays (Mon-Fri):
echo   - 7:00 AM
echo   - 9:40 AM
echo   - 11:30 AM
echo   - 3:00 PM (15:00)
echo.
echo To verify tasks were created:
echo   - Open Task Scheduler (taskschd.msc)
echo   - Look for "TradingView-Alerts-*" tasks
echo.
echo To view task logs:
echo   - Event Viewer ^> Windows Logs ^> System
echo   - Search for "TradingView-Alerts"
echo.
pause
