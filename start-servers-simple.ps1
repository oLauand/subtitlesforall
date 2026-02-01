Write-Host "`n=== Starting SubtitlesForAll Servers ===" -ForegroundColor Cyan

$scriptDir = $PSScriptRoot
$whisperRoot = Split-Path -Parent $scriptDir
$buildDir = Join-Path $whisperRoot "build"

# Build whisper-server if not exists
$serverExe = Join-Path $buildDir "bin\Release\whisper-server.exe"
if (-not (Test-Path $serverExe)) {
    Write-Host "Building whisper-server..." -ForegroundColor Yellow
    
    if (-not (Test-Path $buildDir)) {
        New-Item -ItemType Directory -Path $buildDir | Out-Null
    }
    
    Push-Location $buildDir
    cmake .. -DWHISPER_BUILD_SERVER=ON
    cmake --build . --config Release --target whisper-server
    Pop-Location
    
    if (-not (Test-Path $serverExe)) {
        Write-Host "Build failed!" -ForegroundColor Red
        exit 1
    }
}

# Download model if not exists
$modelPath = Join-Path $whisperRoot "models\ggml-base.en.bin"
if (-not (Test-Path $modelPath)) {
    Write-Host "Downloading model..." -ForegroundColor Yellow
    $url = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin"
    Invoke-WebRequest -Uri $url -OutFile $modelPath
}

# Start whisper-server
Write-Host "Starting whisper-server..." -ForegroundColor Green
$whisperProcess = Start-Process -FilePath $serverExe -ArgumentList "-m", $modelPath, "--port", "8080", "--convert" -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 3

# Start Python bridge
Write-Host "Starting Python bridge..." -ForegroundColor Green
$pythonProcess = Start-Process -FilePath "python" -ArgumentList "run_server.py" -WorkingDirectory $scriptDir -PassThru -WindowStyle Hidden

Write-Host "`n=== Servers Running ===" -ForegroundColor Green
Write-Host "whisper-server PID: $($whisperProcess.Id)" -ForegroundColor Cyan
Write-Host "Python bridge PID: $($pythonProcess.Id)" -ForegroundColor Cyan
Write-Host "`nTo stop servers, close this window or press Ctrl+C" -ForegroundColor Yellow

Wait-Process -Id $whisperProcess.Id, $pythonProcess.Id
