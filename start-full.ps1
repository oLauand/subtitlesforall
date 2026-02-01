# SubtitlesForAll - Full Stack Startup
# This script starts both the whisper.cpp server and the Electron frontend

param(
    [string]$Model = "..\models\ggml-base.en.bin",
    [int]$WhisperPort = 8080,
    [int]$WsPort = 9090
)

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   SubtitlesForAll - Full Stack Startup" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Get paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WhisperDir = Split-Path -Parent $ScriptDir

# Stop existing processes
Write-Host "Stopping any existing processes..." -ForegroundColor Yellow
Get-Process -Name "whisper-server", "python", "electron", "node" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Check for whisper-server
$WhisperServer = Join-Path $WhisperDir "build\bin\whisper-server.exe"
if (-not (Test-Path $WhisperServer)) {
    $WhisperServer = Join-Path $WhisperDir "build\Release\whisper-server.exe"
}

if (-not (Test-Path $WhisperServer)) {
    Write-Host "whisper-server not found!" -ForegroundColor Red
    Write-Host "Please build whisper.cpp first:" -ForegroundColor Yellow
    Write-Host "  mkdir build && cd build && cmake .. && cmake --build . --config Release" -ForegroundColor Gray
    Read-Host "Press Enter to exit"
    exit 1
}

# Check for model
$ModelPath = if ([System.IO.Path]::IsPathRooted($Model)) { $Model } else { Join-Path $ScriptDir $Model }
if (-not (Test-Path $ModelPath)) {
    Write-Host "Model not found at: $ModelPath" -ForegroundColor Red
    Write-Host "Please download a model:" -ForegroundColor Yellow
    Write-Host "  .\models\download-ggml-model.cmd base.en" -ForegroundColor Gray
    Read-Host "Press Enter to exit"
    exit 1
}

# Install npm dependencies if needed
Set-Location $ScriptDir
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
    npm install
}

# Start whisper-server in background
Write-Host ""
Write-Host "Starting whisper-server on port $WhisperPort..." -ForegroundColor Green
$whisperProcess = Start-Process -FilePath $WhisperServer -ArgumentList "-m", $ModelPath, "--port", $WhisperPort -PassThru -WindowStyle Minimized

Write-Host "Waiting for whisper-server to initialize..."
Start-Sleep -Seconds 5

# Start WebSocket bridge
Write-Host "Starting WebSocket bridge on port $WsPort..." -ForegroundColor Green
$pythonProcess = Start-Process -FilePath "python" -ArgumentList "run_server.py", "--port", $WsPort, "--model", $ModelPath -PassThru -WindowStyle Minimized

Write-Host "Waiting for WebSocket server to initialize..."
Start-Sleep -Seconds 3

# Start Electron app
Write-Host ""
Write-Host "Starting SubtitlesForAll..." -ForegroundColor Green
Write-Host ""
Write-Host "The application should open shortly." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop all services." -ForegroundColor Gray
Write-Host ""

try {
    npm run electron:dev
}
finally {
    Write-Host ""
    Write-Host "Stopping services..." -ForegroundColor Yellow
    Stop-Process -Id $whisperProcess.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $pythonProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Host "Done." -ForegroundColor Green
}
