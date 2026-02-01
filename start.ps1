# SubtitlesForAll - Startup Script
# This script starts the WhisperLive server and the Electron frontend

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   SubtitlesForAll - Startup Script" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Kill any existing processes
Write-Host "Stopping any existing processes..." -ForegroundColor Yellow
Get-Process -Name "python", "electron", "node" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host ""
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install dependencies!" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "Starting SubtitlesForAll..." -ForegroundColor Green
Write-Host ""
Write-Host "NOTE: Make sure your WhisperLive server is running on ws://localhost:9090" -ForegroundColor Yellow
Write-Host "You can start it with: python run_server.py --port 9090 --backend faster_whisper" -ForegroundColor Yellow
Write-Host ""

# Start the Electron app
npm run electron:dev

Read-Host "Press Enter to exit"
