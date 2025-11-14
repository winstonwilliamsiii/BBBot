@echo off
REM Airflow Windows Compatibility Script
REM Fixes "Register in fork" errors on Windows

set AIRFLOW_HOME=%~dp0airflow_config
set AIRFLOW__CORE__MP_START_METHOD=spawn
set AIRFLOW__CORE__EXECUTOR=LocalExecutor
set AIRFLOW__CORE__LOAD_EXAMPLES=False

echo Setting up Airflow environment...
echo AIRFLOW_HOME=%AIRFLOW_HOME%
echo MP_START_METHOD=spawn

REM Activate virtual environment
call %~dp0.venv\Scripts\activate.bat

REM Apply Windows compatibility patch and run command
python "%~dp0airflow_windows.py" %*

if "%1"=="webserver" (
    echo Starting Airflow webserver...
    python -c "import os; os.register_at_fork = lambda **kwargs: None; exec(open('airflow_windows.py').read()); from airflow.cli.commands.webserver_command import webserver; webserver(['--port', '8080'])"
) else if "%1"=="scheduler" (
    echo Starting Airflow scheduler...
    python -c "import os; os.register_at_fork = lambda **kwargs: None; exec(open('airflow_windows.py').read()); from airflow.cli.commands.scheduler_command import scheduler; scheduler([])"
) else if "%1"=="config" (
    python "%~dp0airflow_windows.py" config
) else if "%1"=="init" (
    python "%~dp0airflow_windows.py" init
) else (
    echo Available commands:
    echo   airflow.bat config     - Show configuration
    echo   airflow.bat init       - Initialize database
    echo   airflow.bat webserver  - Start web server
    echo   airflow.bat scheduler  - Start scheduler
)