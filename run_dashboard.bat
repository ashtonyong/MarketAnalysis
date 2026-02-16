@echo off
echo ================================================
echo Launching Volume Profile Dashboard...
echo ================================================
echo.

echo 1. Checking for Streamlit...
python -m streamlit --version
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Streamlit not found! Installing...
    pip install streamlit plotly
)

echo.
echo 2. Starting Dashboard...
echo    If the browser does not open, go to: http://localhost:8501
echo.

python -m streamlit run dashboard.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Dashboard crashed with code %ERRORLEVEL%
    echo.
)

echo.
echo Closing launcher...
pause
