@echo off
echo Education System Backend Services Launcher
echo ==========================================

cd /d "%~dp0"
python run_all_services.py

echo.
echo Press any key to exit...
pause > nul