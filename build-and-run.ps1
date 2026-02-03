# Build whisper.cpp and start everything
# Run this from the whisper.cpp root directory

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   Building whisper.cpp" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

$WhisperRoot = Get-Location

# Check if we're in whisper.cpp root
if (-not (Test-Path "CMakeLists.txt") -or -not (Test-Path "examples")) {
    Write-Host "Error: Run this script from the whisper.cpp root directory!" -ForegroundColor Red
    exit 1
}

# Build whisper.cpp
if (-not (Test-Path "build")) {
    Write-Host "Creating build directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "build" | Out-Null
}

Set-Location "build"

Write-Host "Configuring CMake..." -ForegroundColor Yellow
cmake .. -DCMAKE_BUILD_TYPE=Release

if ($LASTEXITCODE -ne 0) {
    Write-Host "CMake configuration failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Building (this may take a few minutes)..." -ForegroundColor Yellow
cmake --build . --config Release

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

Set-Location $WhisperRoot

Write-Host ""
Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host ""

# Check if model exists
$ModelPath = "models\ggml-base.en.bin"
if (-not (Test-Path $ModelPath)) {
    Write-Host "Model not found. Downloading base.en model..." -ForegroundColor Yellow
    Set-Location "models"
    .\download-ggml-model.cmd base.en
    Set-Location $WhisperRoot
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   Starting Services" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Find the whisper-server executable
$WhisperServer = Get-ChildItem -Path "build" -Filter "whisper-server.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1

if (-not $WhisperServer) {
    # Try to find main.exe as fallback
    $WhisperServer = Get-ChildItem -Path "build" -Filter "main.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    
    if ($WhisperServer) {
        Write-Host "Using main.exe (CLI mode)" -ForegroundColor Yellow
    } else {
        Write-Host "Could not find whisper executable!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Found executable: $($WhisperServer.FullName)" -ForegroundColor Green

# Start the app
Write-Host ""
Write-Host "Starting SubtitlesForAll..." -ForegroundColor Green
Write-Host "The WebSocket server will start automatically." -ForegroundColor Gray
Write-Host ""

Set-Location "subtitles-for-all"

# Install npm deps if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
    npm install
}

# Start WebSocket server in background
$PythonServer = Start-Job -ScriptBlock {
    param($WorkDir, $ModelPath)
    Set-Location $WorkDir
    python run_server.py --port 9090 --model $ModelPath
} -ArgumentList (Get-Location), "..\$ModelPath"

Write-Host "WebSocket server started (Job ID: $($PythonServer.Id))" -ForegroundColor Green

# Give server time to start
Start-Sleep -Seconds 3

# Start Electron app
try {
    npm run electron:dev
}
finally {
    Write-Host ""
    Write-Host "Stopping background services..." -ForegroundColor Yellow
    Stop-Job -Id $PythonServer.Id -ErrorAction SilentlyContinue
    Remove-Job -Id $PythonServer.Id -ErrorAction SilentlyContinue
    Write-Host "Done." -ForegroundColor Green
}
