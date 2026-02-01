@echo off
echo.
echo =========================================
echo  SubtitlesForAll - Quick Start
echo =========================================
echo.

cd /d "%~dp0"

:: Start the Python server in background
echo Starting transcription server...
start "Transcription Server" cmd /k "python simple_server.py"

timeout /t 3 >nul

:: Start the Electron app
echo Starting application...
call npm run electron:dev

pause
