@echo off
REM Airflow Windows Compatibility Script
REM Uses the dedicated .venv-airflow environment at the repo root.

set SCRIPT_DIR=%~dp0
for %%I in ("%SCRIPT_DIR%..\..") do set REPO_ROOT=%%~fI
set PYTHON_EXE=%REPO_ROOT%\.venv-airflow\Scripts\python.exe
set WRAPPER=%REPO_ROOT%\airflow\scripts\airflow_windows.py

if not exist "%PYTHON_EXE%" (
    echo Missing Airflow environment: %PYTHON_EXE%
    exit /b 1
)

set AIRFLOW_HOME=%REPO_ROOT%\airflow_config
set AIRFLOW__CORE__MP_START_METHOD=spawn
set AIRFLOW__CORE__EXECUTOR=LocalExecutor
set AIRFLOW__CORE__LOAD_EXAMPLES=False

pushd "%REPO_ROOT%"
"%PYTHON_EXE%" "%WRAPPER%" %*
set EXIT_CODE=%ERRORLEVEL%
popd
exit /b %EXIT_CODE%