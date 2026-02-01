# SubtitlesForAll - Quick Start (No Server Required)
# This runs the app in test mode - you can configure the server URL in the app

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   SubtitlesForAll - Quick Start" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Stop existing processes
Write-Host "Stopping any existing processes..." -ForegroundColor Yellow
Get-Process -Name "electron", "node" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Install dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install dependencies!" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "IMPORTANT: Server Setup Required" -ForegroundColor Yellow
Write-Host "=============================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Before using SubtitlesForAll, you need to:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Option 1: Use whisper.cpp HTTP server (Recommended)" -ForegroundColor Green
Write-Host "  1. Build whisper.cpp:" -ForegroundColor Gray
Write-Host "     cd .." -ForegroundColor Gray
Write-Host "     mkdir build && cd build" -ForegroundColor Gray
Write-Host "     cmake .." -ForegroundColor Gray
Write-Host "     cmake --build . --config Release" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Download a model:" -ForegroundColor Gray
Write-Host "     .\models\download-ggml-model.cmd base.en" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Start whisper-server:" -ForegroundColor Gray
Write-Host "     .\build\bin\Release\whisper-server.exe -m models\ggml-base.en.bin" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. In another terminal, start the WebSocket bridge:" -ForegroundColor Gray
Write-Host "     cd subtitles-for-all" -ForegroundColor Gray
Write-Host "     python run_server.py --port 9090 --model ..\models\ggml-base.en.bin" -ForegroundColor Gray
Write-Host ""
Write-Host "Option 2: Use an external WhisperLive server" -ForegroundColor Green
Write-Host "  Point the app to an existing WhisperLive server at ws://yourserver:9090" -ForegroundColor Gray
Write-Host ""
Write-Host "=============================================" -ForegroundColor Yellow
Write-Host ""

$response = Read-Host "Continue to open the app anyway? (y/n)"
if ($response -ne "y" -and $response -ne "Y") {
    exit 0
}

Write-Host ""
Write-Host "Starting SubtitlesForAll..." -ForegroundColor Green
Write-Host "Configure the server URL in the app settings." -ForegroundColor Gray
Write-Host ""

npm run electron:dev
