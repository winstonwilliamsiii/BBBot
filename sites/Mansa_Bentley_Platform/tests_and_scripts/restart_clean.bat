@echo off
echo ================================
echo BBBot Complete Restart Procedure
echo ================================
echo.

echo [1/5] Stopping Streamlit processes...
taskkill /F /IM streamlit.exe 2>nul
timeout /t 2 >nul

echo [2/5] Testing Plaid credentials...
python test_plaid_credentials.py
if errorlevel 1 (
    echo ERROR: Plaid credentials test failed!
    echo Check your .env file
    pause
    exit /b 1
)

echo.
echo [3/5] Testing database connection...
python test_budget_database.py
if errorlevel 1 (
    echo ERROR: Database test failed!
    echo Check MySQL is running on port 3306
    pause
    exit /b 1
)

echo.
echo [4/5] Clearing Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo.
echo [5/5] Starting Streamlit...
echo.
echo ========================================
echo   LOGIN CREDENTIALS:
echo   Username: admin
echo   Password: admin123
echo ========================================
echo.
echo Opening browser in 3 seconds...
timeout /t 3 >nul
start http://localhost:8501/💰_Personal_Budget

streamlit run streamlit_app.py
