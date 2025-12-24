@echo off
REM Simple Airflow Webserver Starter
REM Sets up environment and starts webserver

echo Starting Bentley Budget Bot Airflow Webserver...
echo ================================================

REM Set environment
set AIRFLOW_HOME=%~dp0airflow_config
set AIRFLOW__CORE__MP_START_METHOD=spawn
set AIRFLOW__CORE__EXECUTOR=LocalExecutor
set PYTHONIOENCODING=utf-8

REM Show configuration
echo AIRFLOW_HOME: %AIRFLOW_HOME%
echo Access URL: http://localhost:8080
echo.

REM Start with compatibility patch
python -c "import os; os.register_at_fork=lambda **k:None if not hasattr(os,'register_at_fork') else None; import warnings; warnings.filterwarnings('ignore','.*POSIX.*'); import subprocess; subprocess.run(['python','-m','airflow','webserver','--port','8080'])"

pause