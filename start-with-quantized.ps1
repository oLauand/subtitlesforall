# SubtitlesForAll - Start with Quantized Model
# This starts the app with the faster ggml-base-q5_1.bin quantized model

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   SubtitlesForAll - Quantized Model" -ForegroundColor Cyan
Write-Host "   Using ggml-base-q5_1.bin (31 MB)" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check if model exists
$ModelPath = "..\models\ggml-base-q5_1.bin"
if (-not (Test-Path $ModelPath)) {
    Write-Host "ERROR: Quantized model not found at: $ModelPath" -ForegroundColor Red
    Write-Host "Please make sure the model file exists in the models directory." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✓ Found quantized model: $ModelPath" -ForegroundColor Green
Write-Host ""

# Stop existing processes
Write-Host "Stopping any existing processes..." -ForegroundColor Yellow
Get-Process -Name "electron", "node", "python" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

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

# Start the WebSocket server with quantized model
Write-Host "Starting WebSocket server with quantized model..." -ForegroundColor Cyan
$ServerJob = Start-Job -ScriptBlock {
    param($ScriptDir, $ModelPath)
    Set-Location $ScriptDir
    python run_server.py --port 9090 --model $ModelPath
} -ArgumentList $ScriptDir, $ModelPath

Start-Sleep -Seconds 2

# Check if server started successfully
if ($ServerJob.State -ne "Running") {
    Write-Host "ERROR: Failed to start server!" -ForegroundColor Red
    Write-Host "Make sure Python and required packages are installed:" -ForegroundColor Yellow
    Write-Host "  pip install websockets numpy" -ForegroundColor Gray
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✓ Server started successfully" -ForegroundColor Green
Write-Host ""

# Start the Electron app in development mode
Write-Host "Starting Electron app..." -ForegroundColor Cyan
Write-Host ""
Write-Host "TIP: Select 'base-q5_1' from the model dropdown for best performance!" -ForegroundColor Yellow
Write-Host ""

npm run electron:dev

# Cleanup on exit
Write-Host ""
Write-Host "Cleaning up..." -ForegroundColor Yellow
Stop-Job -Job $ServerJob -ErrorAction SilentlyContinue
Remove-Job -Job $ServerJob -ErrorAction SilentlyContinue

Write-Host "Done!" -ForegroundColor Green
