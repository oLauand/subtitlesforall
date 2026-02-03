@echo off
title SubtitlesForAll - Desktop App
cd /d "%~dp0"

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║     🎤 SubtitlesForAll - Desktop Application                 ║
echo ║                                                              ║
echo ║     Backend-Server werden automatisch gestartet:             ║
echo ║       • Whisper.cpp (Port 9092) - Schnell + Quantisiert     ║
echo ║       • Moonshine   (Port 9091) - Ultra-schnell             ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Prüfe ob node_modules existiert
if not exist "node_modules" (
    echo [Setup] Installiere npm Dependencies...
    call npm install
    if errorlevel 1 (
        echo [Error] npm install fehlgeschlagen!
        pause
        exit /b 1
    )
)

REM Prüfe ob dist existiert, wenn nicht bauen
if not exist "dist" (
    echo [Build] Erstelle Produktions-Build...
    call npm run build
    if errorlevel 1 (
        echo [Error] Build fehlgeschlagen!
        pause
        exit /b 1
    )
)

echo [Start] Starte SubtitlesForAll Desktop App...
echo.
echo   Die Backend-Server starten automatisch mit der App.
echo   Schließe dieses Fenster NICHT während die App läuft!
echo.

REM Starte Electron mit den gebauten Dateien
call npx electron .

echo.
echo [Exit] SubtitlesForAll beendet.
pause
