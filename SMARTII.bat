@echo off
REM SMARTII One-Click Launcher (Windows Batch)
REM Double-click this to start SMARTII!

title SMARTII AI Assistant
color 0B

echo.
echo ================================================================
echo   ███████╗███╗   ███╗ █████╗ ██████╗ ████████╗██╗██╗
echo   ██╔════╝████╗ ████║██╔══██╗██╔══██╗╚══██╔══╝██║██║
echo   ███████╗██╔████╔██║███████║██████╔╝   ██║   ██║██║
echo   ╚════██║██║╚██╔╝██║██╔══██║██╔══██╗   ██║   ██║██║
echo   ███████║██║ ╚═╝ ██║██║  ██║██║  ██║   ██║   ██║██║
echo   ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝╚═╝
echo ================================================================
echo   Your Intelligent AI Assistant - Starting...
echo.

cd /d "%~dp0desktop"
python smartii_launcher.py

pause
