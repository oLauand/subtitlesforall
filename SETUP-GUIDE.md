# SubtitlesForAll - Complete Setup Guide

## 🚀 Quick Start Options

### Option 1: Build Everything and Run (Recommended)

From the **whisper.cpp root directory**:

```powershell
.\build-and-run.ps1
```

This script will:
- Build whisper.cpp with CMake
- Download the base.en model if needed
- Start the WebSocket server
- Launch the SubtitlesForAll app

### Option 2: Manual Setup

#### Step 1: Build whisper.cpp

```powershell
# From whisper.cpp root
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
cd ..
```

#### Step 2: Download a Model

```powershell
cd models
.\download-ggml-model.cmd base.en
cd ..
```

#### Step 3: Start WebSocket Server

```powershell
cd subtitles-for-all
python run_server.py --port 9090 --model ..\models\ggml-base.en.bin
```

Keep this terminal open.

#### Step 4: Start the App (in a new terminal)

```powershell
cd subtitles-for-all
npm install  # First time only
npm run electron:dev
```

### Option 3: Test the App Without Server

```powershell
cd subtitles-for-all
.\start-quick.ps1
```

This opens the app so you can explore the UI. Configure a remote server URL in the settings.

## 🎮 How to Use

1. **Start Capture**: Click "Start Capture" in the main window
2. **Select Source**: Choose a screen or window from the picker
3. **Check Audio**: Make sure "Include system audio" is enabled
4. **Transcribe**: Audio will be captured and transcribed in real-time
5. **View Subtitles**: Subtitles appear in the overlay at the bottom of your screen
6. **Customize**: Adjust font, colors, and position in the settings panel

## ⚙️ Configuration

### Server Settings

Default: `ws://localhost:9090`

The app connects to a WebSocket server that processes audio. You can:
- Use the included Python server (run_server.py)
- Connect to a remote WhisperLive server
- Change the port in the app settings

### Overlay Settings

Customize the subtitle appearance:
- **Font Size**: 16-64px
- **Font Family**: Multiple options
- **Colors**: Text and background
- **Position**: Top or bottom
- **Max Lines**: 1-3 lines

## 🔧 Troubleshooting

### "Could not find whisper-server.exe"

The whisper.cpp project needs to be built first:

```powershell
cd c:\Users\49152\projects\whisper.cpp-1
mkdir build
cd build
cmake ..
cmake --build . --config Release
```

### "No audio captured"

1. Make sure you select a source that's playing audio
2. Enable "Include system audio" in the source picker
3. Try selecting "Entire Screen" instead of a window
4. Check Windows sound settings

### "WebSocket connection failed"

1. Ensure the Python server is running:
   ```powershell
   python run_server.py --port 9090 --model ..\models\ggml-base.en.bin
   ```

2. Check that Python and required packages are installed:
   ```powershell
   pip install websockets numpy
   ```

3. Verify the server URL in the app matches where the server is running

### "Transcription is slow"

1. Use a smaller model (tiny or base) for faster results:
   ```powershell
   python run_server.py --model ..\models\ggml-tiny.en.bin
   ```

2. Make sure whisper.cpp was built with GPU support (CUDA/Metal)

3. Close other resource-intensive applications

### TypeScript Errors During Development

The TypeScript errors you saw earlier are resolved. If you see them again:

```powershell
npm run build  # Should complete without errors
```

## 📁 Project Structure

```
whisper.cpp-1/
├── build/                    # Compiled whisper.cpp binaries
├── models/                   # Whisper models (.bin files)
├── subtitles-for-all/        # Frontend application
│   ├── electron/             # Electron main process
│   ├── src/                  # React source code
│   ├── public/               # Static assets
│   ├── run_server.py         # WebSocket bridge server
│   └── start-*.ps1           # Startup scripts
└── build-and-run.ps1         # All-in-one build script
```

## 🎯 Architecture

```
┌─────────────────────┐
│  Electron App       │
│  (React Frontend)   │
└──────────┬──────────┘
           │ WebSocket
           │ (Audio chunks)
           ▼
┌─────────────────────┐
│  Python Bridge      │
│  (run_server.py)    │
└──────────┬──────────┘
           │ HTTP API
           ▼
┌─────────────────────┐
│  whisper.cpp        │
│  (Speech-to-Text)   │
└─────────────────────┘
           │
           ▼
     [Transcription]
           │
           ▼
┌─────────────────────┐
│  Overlay Window     │
│  (Always-on-top)    │
└─────────────────────┘
```

## 🔄 Development Workflow

### Running in Dev Mode

```powershell
cd subtitles-for-all
npm run electron:dev
```

Features:
- Hot reload for React changes
- DevTools enabled
- Source maps
- Vite dev server on port 5173

### Building for Production

```powershell
npm run build              # Build React app
npm run electron:build     # Package Electron app
```

The packaged app will be in `subtitles-for-all/release/`.

## 🌍 Supported Languages

English, German, Spanish, French, Italian, Portuguese, Dutch, Japanese, Chinese, Korean, Russian, and more.

Change in the app settings before starting capture.

## 📝 Notes

- System audio capture requires the source to be actively playing sound
- The overlay appears over ALL windows, including fullscreen games
- Audio is automatically downsampled from 48kHz to 16kHz for Whisper
- Transcription latency depends on the model size and your hardware

## 🆘 Getting Help

If you encounter issues:

1. Check the terminal output for error messages
2. Verify all prerequisites are installed
3. Try with a smaller model (tiny.en)
4. Check Windows firewall settings
5. Make sure the WebSocket port (9090) is not blocked

## ✅ Success Checklist

- [ ] whisper.cpp built successfully
- [ ] Model downloaded (ggml-base.en.bin or similar)
- [ ] Python dependencies installed (websockets, numpy)
- [ ] npm dependencies installed
- [ ] WebSocket server running on port 9090
- [ ] Electron app opens without errors
- [ ] Source picker shows available screens/windows
- [ ] Overlay window appears on screen
- [ ] System audio is being captured
- [ ] Subtitles appear in real-time

Enjoy real-time subtitles! 🎉
