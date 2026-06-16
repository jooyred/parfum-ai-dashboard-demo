@echo off
cd /d "%~dp0"
echo ========================================
echo AI Business Control Tower - Demo Parfum
echo ========================================
echo.

if not exist ".venv" (
    echo Membuat virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Install / update dependencies...
pip install -r requirements.txt

echo.
echo Menjalankan Streamlit...
streamlit run app.py

pause
