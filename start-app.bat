@echo off
echo === SubtitlesForAll Launcher ===
echo.

cd /d "%~dp0"

:: Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo Failed to install dependencies!
        pause
        exit /b 1
    )
)

:: Start the Electron app
echo Starting application...
npm run electron:dev

pause
