@echo off
echo =============================================
echo   SubtitlesForAll - Startup Script
echo =============================================
echo.

:: Kill any existing processes
echo Stopping any existing processes...
taskkill /F /IM electron.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1

:: Change to frontend directory
cd /d "%~dp0"

:: Check if node_modules exists
if not exist "node_modules" (
    echo.
    echo Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo Failed to install dependencies!
        pause
        exit /b 1
    )
)

echo.
echo Starting SubtitlesForAll...
echo.
echo NOTE: Make sure your WhisperLive server is running on ws://localhost:9090
echo You can start it with: python run_server.py --port 9090 --backend faster_whisper
echo.

:: Start the Electron app
call npm run electron:dev

pause
