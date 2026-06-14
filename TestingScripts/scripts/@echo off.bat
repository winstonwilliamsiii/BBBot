@echo off
REM filepath: C:\Users\winst\BentleyBudgetBot\start.bat
echo Starting BentleyBudgetBot...
cd /d "C:\Users\winst\BentleyBudgetBot"
call venv\Scripts\activate.bat
streamlit run streamlit_app.py
pause