# SubtitlesForAll 🎤📝

Real-time subtitle overlay for any audio source on Windows using Whisper AI. Capture system audio from any application and display live transcriptions as an always-on-top overlay.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Node](https://img.shields.io/badge/node-18+-green.svg)

## 🌟 Features

- 🎤 **System Audio Capture**: Capture audio from any application, screen, or window
- 📝 **Real-time Transcription**: Live subtitles using Whisper speech recognition (faster-whisper)
- 🖥️ **Always-on-top Overlay**: Subtitles appear over all windows, including fullscreen applications
- 🎨 **Customizable Appearance**: Adjust font size, colors, position, and styling
- 🌍 **Multi-language Support**: Supports all languages supported by Whisper
- 🚀 **Low Latency**: Optimized for real-time performance with faster-whisper
- 💻 **Modern UI**: Built with React 19 + Electron 33

## 📋 Based On

This project is built on top of:
- **[whisper.cpp](https://github.com/ggerganov/whisper.cpp)** - High-performance inference of OpenAI's Whisper model
- **[faster-whisper](https://github.com/SYSTRAN/faster-whisper)** - Fast Whisper transcription with CTranslate2
- **Electron** - Cross-platform desktop application framework
- **React 19** - Modern UI framework
- **Vite** - Fast build tool

## 🚀 Quick Start

### Prerequisites

1. **Node.js 18+** - [Download](https://nodejs.org/)
2. **Python 3.8+** - [Download](https://python.org/)
3. **Git** - [Download](https://git-scm.com/)

### Installation

```bash
# Clone the repository
git clone https://github.com/oLauand/subtitlesforall.git
cd subtitlesforall

# Install Node.js dependencies
npm install

# Install Python dependencies
pip install websockets numpy faster-whisper
```

### Starting the Application

#### Option 1: Quick Start (Recommended)

```powershell
# Start the WebSocket server (in one terminal)
python simple_server.py --port 9090 --model base

# Start the Electron app (in another terminal)
npm run electron:dev
```

#### Option 2: Using Start Scripts

```powershell
# Windows PowerShell - Full start with server
.\start-full.ps1

# Or just the app (start server separately)
.\start-quick.ps1
```

### First-Time Setup

1. **Server starts automatically** - The Python server downloads the Whisper model on first run
2. **Select Audio Source** - Click "Start Capture" and choose a screen or window to capture
3. **Configure Settings** - Adjust language, font size, colors, and overlay position
4. **Start Transcribing** - Speak into your microphone or play audio to see live subtitles

## 🛠️ What Was Fixed/Changed

This fork includes several critical fixes and improvements:

### Critical Bug Fixes ✅
1. **CSS Syntax Error** - Fixed duplicate CSS declarations in `src/styles/index.css` that caused 500 errors
2. **Content Security Policy** - Added proper CSP headers to eliminate Electron security warnings
3. **WebSocket Protocol Mismatch** - Fixed server-client communication protocol
   - Server now sends: `{"message": "SERVER_READY", "status": "ready"}`
   - Compatible with client expectations
4. **WebSocket Handler Signature** - Updated `handle_client()` to work with modern websockets library
   - Removed deprecated `path` parameter
   - Now compatible with websockets 11.0+

### Architecture Improvements 🏗️
- **Simplified Server** - `simple_server.py` using faster-whisper (no external dependencies on whisper.cpp)
- **Modern Stack** - React 19 + Electron 33 + Vite 6
- **Better Error Handling** - Improved connection management and error messages

## 📖 Usage Guide

### Basic Workflow

1. **Start Server**:
   ```bash
   python simple_server.py --port 9090 --model base
   ```
   
2. **Start App**:
   ```bash
   npm run electron:dev
   ```

3. **In the App**:
   - Click "Start Capture"
   - Select audio source (window/screen)
   - Subtitles appear at bottom of screen

### Configuration Options

#### Server Options
```bash
python simple_server.py --host 0.0.0.0 --port 9090 --model [tiny|base|small|medium|large]
```

- `--host` - Server host (default: 0.0.0.0)
- `--port` - Server port (default: 9090)
- `--model` - Whisper model size:
  - `tiny` - Fastest, least accurate (~75 MB)
  - `base` - Good balance (~150 MB) **[Recommended]**
  - `small` - Better accuracy (~500 MB)
  - `medium` - High accuracy (~1.5 GB)
  - `large` - Best accuracy (~3 GB)

#### App Settings
- **Server URL**: WebSocket server address (default: `ws://localhost:9090`)
- **Language**: Source language for transcription
- **Font Size**: 16-64px
- **Colors**: Text and background colors
- **Position**: Top or bottom of screen
- **Max Lines**: 1-3 lines of text

## 🎯 Future Optimizations & TODO

### High Priority 🔴
- [ ] **GPU Acceleration** - Add CUDA/DirectML support for faster transcription
- [ ] **Audio Format Handling** - Better audio preprocessing and format conversion
- [ ] **Buffer Management** - Optimize audio buffer size for lower latency
- [ ] **Error Recovery** - Auto-reconnect on server disconnect
- [ ] **Performance Optimization** - Reduce CPU usage during idle states

### Medium Priority 🟡
- [ ] **Model Management** - Built-in model downloader and manager
- [ ] **Multiple Languages** - Automatic language detection
- [ ] **Subtitle Export** - Save transcriptions to SRT/VTT files
- [ ] **Hotkeys** - Global keyboard shortcuts for control
- [ ] **System Tray** - Minimize to tray functionality
- [ ] **Audio Device Selection** - Choose specific input/output devices

### Nice to Have 🟢
- [ ] **Translation** - Real-time translation to other languages
- [ ] **Speaker Diarization** - Identify different speakers
- [ ] **Custom Styling** - More overlay customization options
- [ ] **Performance Metrics** - Display latency and accuracy stats
- [ ] **Settings Presets** - Save/load configuration presets
- [ ] **Dark/Light Themes** - UI theme support
- [ ] **Multi-Monitor Support** - Better handling of multiple displays

### Code Quality 🔧
- [ ] **TypeScript Strict Mode** - Enable strict type checking
- [ ] **Unit Tests** - Add Jest/Vitest tests
- [ ] **E2E Tests** - Add Playwright tests
- [ ] **Code Documentation** - Add JSDoc comments
- [ ] **CI/CD Pipeline** - Automated builds and releases
- [ ] **Linting** - ESLint + Prettier configuration

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Electron App (Frontend)               │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Settings   │  │  Audio        │  │  Overlay      │  │
│  │  Window     │──│  Capture      │──│  Window       │  │
│  │  (React)    │  │  (WebRTC)     │  │  (Transparent)│  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │ WebSocket
                         │ (Audio + JSON)
┌────────────────────────▼────────────────────────────────┐
│              Python WebSocket Server                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │  simple_server.py                                │   │
│  │  - WebSocket handler                             │   │
│  │  - Audio buffer management                       │   │
│  │  - Whisper transcription                         │   │
│  └───────────────────┬─────────────────────────────┘   │
└──────────────────────┼─────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────┐
│              faster-whisper                             │
│  - CTranslate2 optimized inference                      │
│  - CPU/GPU support                                      │
│  - Multiple model sizes                                 │
└─────────────────────────────────────────────────────────┘
```

## 🔧 Development

### Project Structure
```
subtitles-for-all/
├── electron/           # Electron main process
│   ├── main.cjs       # Main process entry
│   └── preload.cjs    # Preload script (IPC bridge)
├── src/               # React frontend
│   ├── App.tsx        # Main app component
│   ├── components/    # React components
│   │   ├── SourcePicker.tsx
│   │   └── SettingsPanel.tsx
│   ├── styles/        # CSS styles
│   │   └── index.css
│   └── types.ts       # TypeScript definitions
├── public/            # Static assets
│   ├── icon.svg
│   └── overlay.html   # Overlay window HTML
├── simple_server.py   # WebSocket transcription server
├── package.json       # Node.js dependencies
├── vite.config.ts     # Vite configuration
└── tsconfig.json      # TypeScript configuration
```

### Scripts

```bash
npm run dev          # Start Vite dev server only
npm run electron:dev # Start full app (Vite + Electron)
npm run build        # Build for production
npm run electron:build # Build distributable
```

### Building for Production

```bash
# Build the app
npm run build

# Package for Windows
npm run electron:build
```

The built application will be in the `release/` directory.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) by Georgi Gerganov
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) by SYSTRAN
- [OpenAI Whisper](https://github.com/openai/whisper) - Original model
- All contributors and users of this project

## 🐛 Known Issues

- WebSocket connection may fail if Python server is not started first
- Audio capture requires user permission on first run
- Large models (medium/large) may cause high CPU usage
- Some fullscreen applications may prevent overlay from displaying

## 🔍 Troubleshooting

### No audio captured
- Make sure you select a source that has audio playing
- Check that system audio is enabled for the selected source
- Try selecting "Entire Screen" instead of a specific window

### WebSocket connection fails
- Ensure the Python server is running: `python simple_server.py --port 9090 --model base`
- Check firewall settings
- Verify the server URL in the app settings matches the running server

### Transcription is slow
- Use a smaller model (tiny or base) for faster results
- Close other resource-intensive applications
- Consider upgrading to a machine with GPU support

### Overlay not visible
- Check if it's hidden behind fullscreen apps
- Toggle the overlay visibility from the main window
- Restart the application

## 📞 Support

For issues and questions, please use the [GitHub Issues](https://github.com/oLauand/subtitlesforall/issues) page.

---

**Made with ❤️ for accessibility and real-time transcription**
