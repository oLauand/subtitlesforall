@echo off
REM SubtitlesForAll - Start with Quantized Model (Base Q5_1)
REM This starts the app with the faster ggml-base-q5_1.bin quantized model

echo =============================================
echo    SubtitlesForAll - Quantized Model
echo    Using ggml-base-q5_1.bin (31 MB)
echo =============================================
echo.

cd /d "%~dp0"

REM Check if model exists
set MODEL_PATH=..\models\ggml-base-q5_1.bin
if not exist "%MODEL_PATH%" (
    echo ERROR: Quantized model not found at: %MODEL_PATH%
    echo Please make sure the model file exists in the models directory.
    pause
    exit /b 1
)

echo [OK] Found quantized model: %MODEL_PATH%
echo.

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo Failed to install dependencies!
        pause
        exit /b 1
    )
)

REM Start the WebSocket server with quantized model in a new window
echo Starting WebSocket server with quantized model...
start "Whisper Server (Q5_1)" cmd /k "python run_server.py --port 9090 --model %MODEL_PATH%"

timeout /t 3 /nobreak >nul

echo.
echo Starting Electron app...
echo.
echo TIP: Select 'base-q5_1' from the model dropdown for best performance!
echo.

REM Start the Electron app
call npm run electron:dev

echo.
echo Done!
pause
