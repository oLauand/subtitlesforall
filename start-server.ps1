#!/usr/bin/env pwsh
# Simple Server Starter for SubtitlesForAll
# This script compiles whisper.cpp with the server and starts everything

Write-Host "`n=== SubtitlesForAll Server Startup ===" -ForegroundColor Cyan
Write-Host "Starting servers...`n" -ForegroundColor Green

# Get paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$whisperRoot = Split-Path -Parent $scriptDir
$buildDir = Join-Path $whisperRoot "build"

# Check if already built
$serverExe = Join-Path $buildDir "bin\whisper-server.exe"
if (Test-Path $serverExe) {
    Write-Host "✓ whisper-server already built" -ForegroundColor Green
} else {
    Write-Host "Building whisper-server (this may take a few minutes)..." -ForegroundColor Yellow
    
    # Create build directory
    if (!(Test-Path $buildDir)) {
        New-Item -ItemType Directory -Path $buildDir | Out-Null
    }
    
    # Run CMake configuration
    Push-Location $buildDir
    Write-Host "Running CMake..." -ForegroundColor Yellow
    cmake .. -DWHISPER_BUILD_SERVER=ON 2>&1 | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ CMake configuration failed!" -ForegroundColor Red
        Write-Host "Please ensure CMake and Visual Studio Build Tools are installed." -ForegroundColor Yellow
        Pop-Location
        exit 1
    }
    
    # Build
    Write-Host "Building (this will take a few minutes)..." -ForegroundColor Yellow
    cmake --build . --config Release --target whisper-server 2>&1 | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Build failed!" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Pop-Location
    Write-Host "✓ Build complete!" -ForegroundColor Green
}

# Check for model
$modelPath = Join-Path $whisperRoot "models\ggml-base.en.bin"
if (!(Test-Path $modelPath)) {
    Write-Host "`nModel not found. Downloading base.en model..." -ForegroundColor Yellow
    Push-Location (Join-Path $whisperRoot "models")
    
    if (Test-Path "download-ggml-model.sh") {
        # Use bash if available
        if (Get-Command bash -ErrorAction SilentlyContinue) {
            bash download-ggml-model.sh base.en
        } else {
            # Manual download
            $url = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin"
            Write-Host "Downloading from $url..." -ForegroundColor Yellow
            Invoke-WebRequest -Uri $url -OutFile "ggml-base.en.bin"
        }
    }
    
    Pop-Location
    
    if (Test-Path $modelPath) {
        Write-Host "✓ Model downloaded!" -ForegroundColor Green
    } else {
        Write-Host "✗ Model download failed. Please download manually." -ForegroundColor Red
        Write-Host "Visit: https://huggingface.co/ggerganov/whisper.cpp/tree/main" -ForegroundColor Yellow
        exit 1
    }
}

# Start whisper-server in background
Write-Host "`nStarting whisper-server on port 8080..." -ForegroundColor Cyan
$whisperJob = Start-Job -ScriptBlock {
    param($exe, $model)
    & $exe -m $model --port 8080 --convert
} -ArgumentList $serverExe, $modelPath

Start-Sleep -Seconds 2

# Check if whisper-server started
$jobState = (Get-Job -Id $whisperJob.Id).State
if ($jobState -eq "Running") {
    Write-Host "✓ whisper-server started (Job ID: $($whisperJob.Id))" -ForegroundColor Green
} else {
    Write-Host "✗ whisper-server failed to start" -ForegroundColor Red
    Receive-Job -Job $whisperJob
    exit 1
}

# Start Python WebSocket bridge
Write-Host "Starting Python WebSocket bridge on port 9090..." -ForegroundColor Cyan
Push-Location $scriptDir

$pythonJob = Start-Job -ScriptBlock {
    param($dir)
    Set-Location $dir
    python run_server.py
} -ArgumentList $scriptDir

Start-Sleep -Seconds 2

# Check if Python server started
$jobState = (Get-Job -Id $pythonJob.Id).State
if ($jobState -eq "Running") {
    Write-Host "✓ Python bridge started (Job ID: $($pythonJob.Id))" -ForegroundColor Green
} else {
    Write-Host "✗ Python bridge failed to start" -ForegroundColor Red
    Receive-Job -Job $pythonJob
    Stop-Job -Job $whisperJob
    Remove-Job -Job $whisperJob
    exit 1
}

Pop-Location

Write-Host "`n=== Servers Running ===" -ForegroundColor Green
Write-Host "whisper-server: http://localhost:8080" -ForegroundColor Cyan
Write-Host "WebSocket bridge: ws://localhost:9090" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop all servers`n" -ForegroundColor Yellow

# Keep script running and monitor jobs
try {
    while ($true) {
        $whisperState = (Get-Job -Id $whisperJob.Id).State
        $pythonState = (Get-Job -Id $pythonJob.Id).State
        
        if ($whisperState -ne "Running") {
            Write-Host "`nwhisper-server stopped!" -ForegroundColor Red
            Receive-Job -Job $whisperJob
            break
        }
        
        if ($pythonState -ne "Running") {
            Write-Host "`nPython bridge stopped!" -ForegroundColor Red
            Receive-Job -Job $pythonJob
            break
        }
        
        Start-Sleep -Seconds 5
    }
} finally {
    Write-Host "`nStopping servers..." -ForegroundColor Yellow
    Stop-Job -Job $whisperJob, $pythonJob -ErrorAction SilentlyContinue
    Remove-Job -Job $whisperJob, $pythonJob -Force -ErrorAction SilentlyContinue
    Write-Host "✓ Servers stopped" -ForegroundColor Green
}
