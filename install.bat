@echo off
echo ================================================
echo Volume Profile Tool - Installation & Setup
echo ================================================
echo.

:: Check Python version
echo 1. Checking Python version...
python --version
echo.

:: Install dependencies
echo 2. Installing dependencies...
pip install -r requirements.txt
echo.

:: Test installation
echo 3. Testing installation...
python -c "import pandas, numpy, yfinance, matplotlib; print('[OK] All packages installed successfully!')"
echo.

:: Run quick test
echo 4. Running quick test with SPY...
python volume_profile_cli.py quick SPY
echo.

echo ================================================
echo [OK] Setup Complete!
echo ================================================
echo.
echo Try these commands:
echo   python volume_profile_cli.py analyze AAPL
echo   python volume_profile_cli.py quick SPY
echo   python volume_profile_cli.py compare AAPL MSFT GOOGL
echo   python volume_profile_visualizer.py TSLA
echo.
echo For Antigravity integration, see:
echo   python example_antigravity_integration.py
echo.
echo Read README.md for full documentation
echo ================================================
