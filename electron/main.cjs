const { app, BrowserWindow, ipcMain, desktopCapturer, screen } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let settingsWindow = null;
let overlayWindow = null;
let backendProcesses = [];

const isDev = process.env.NODE_ENV === 'development';

// Get the correct app directory
function getAppDir() {
  // app.getAppPath() returns the path to the app's main file directory
  // In development this is the subtitles-for-all folder
  // In production this might be inside an asar archive
  let appDir = app.getAppPath();
  
  // If we're in an asar archive, get the unpacked directory
  if (appDir.includes('app.asar')) {
    appDir = path.dirname(appDir);
  }
  
  console.log('[Electron] App directory:', appDir);
  return appDir;
}

// Backend server configurations
const BACKENDS = [
  {
    name: 'Whisper.cpp',
    script: 'whispercpp_server.py',
    port: 9092,
    args: ['--model', 'base-q5_1'],
    enabled: true,
  },
  {
    name: 'Moonshine',
    script: 'moonshine_server.py', 
    port: 9091,
    args: [],
    enabled: true,
  },
  {
    name: 'Whisper Python',
    script: 'simple_server.py',
    port: 9090,
    args: ['--model', 'base'],
    enabled: true, // Enable all backends for testing
  },
];

function getServerPath() {
  const appDir = getAppDir();
  console.log('[Electron] Server path:', appDir);
  return appDir;
}

function startBackendServers() {
  const serverPath = getServerPath();
  console.log('[Electron] Starting backend servers from:', serverPath);
  
  BACKENDS.filter(b => b.enabled).forEach(backend => {
    const scriptPath = path.join(serverPath, backend.script);
    
    // Check if script exists
    if (!fs.existsSync(scriptPath)) {
      console.error(`[Electron] Script not found: ${scriptPath}`);
      return;
    }
    
    console.log(`[Electron] Starting ${backend.name} on port ${backend.port}...`);
    console.log(`[Electron] Script: ${scriptPath}`);
    
    try {
      // Use PYTHONIOENCODING to fix Unicode issues on Windows
      const env = { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUNBUFFERED: '1' };
      
      const proc = spawn('python', [scriptPath, ...backend.args], {
        cwd: serverPath,
        stdio: ['ignore', 'pipe', 'pipe'],
        detached: false,
        windowsHide: true,
        env: env,
      });
      
      proc.stdout.on('data', (data) => {
        const output = data.toString().trim();
        if (output) console.log(`[${backend.name}] ${output}`);
      });
      
      proc.stderr.on('data', (data) => {
        const output = data.toString().trim();
        if (output) console.error(`[${backend.name}] ${output}`);
      });
      
      proc.on('error', (err) => {
        console.error(`[${backend.name}] Failed to start:`, err.message);
      });
      
      proc.on('exit', (code) => {
        if (code !== 0 && code !== null) {
          console.log(`[${backend.name}] Exited with code ${code}`);
        }
      });
      
      backendProcesses.push({ name: backend.name, process: proc, port: backend.port });
      console.log(`[Electron] ${backend.name} started (PID: ${proc.pid})`);
    } catch (err) {
      console.error(`[Electron] Failed to start ${backend.name}:`, err.message);
    }
  });
}

function stopBackendServers() {
  console.log('[Electron] Stopping backend servers...');
  backendProcesses.forEach(({ name, process }) => {
    try {
      if (process && !process.killed) {
        process.kill('SIGTERM');
        console.log(`[Electron] Stopped ${name}`);
      }
    } catch (err) {
      console.error(`[Electron] Error stopping ${name}:`, err.message);
    }
  });
  backendProcesses = [];
}

function createSettingsWindow() {
  settingsWindow = new BrowserWindow({
    width: 900,
    height: 700,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.cjs'),
    },
    title: 'SubtitlesForAll - Settings',
    icon: path.join(__dirname, '../public/icon.png'),
    show: false,
  });

  if (isDev) {
    settingsWindow.loadURL('http://localhost:5173');
    settingsWindow.webContents.openDevTools();
  } else {
    settingsWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  settingsWindow.once('ready-to-show', () => {
    settingsWindow.show();
  });

  settingsWindow.on('closed', () => {
    settingsWindow = null;
    if (overlayWindow) {
      overlayWindow.close();
    }
    app.quit();
  });
}

function createOverlayWindow() {
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;

  overlayWindow = new BrowserWindow({
    width: width,
    height: 120,
    x: 0,
    y: height - 120,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    movable: false,
    focusable: false,
    hasShadow: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.cjs'),
    },
  });

  // Make window click-through
  overlayWindow.setIgnoreMouseEvents(true, { forward: true });

  // Set to appear above everything, including fullscreen apps
  overlayWindow.setAlwaysOnTop(true, 'screen-saver', 1);
  overlayWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });

  if (isDev) {
    overlayWindow.loadURL('http://localhost:5173/overlay.html');
  } else {
    overlayWindow.loadFile(path.join(__dirname, '../dist/overlay.html'));
  }

  overlayWindow.on('closed', () => {
    overlayWindow = null;
  });

  return overlayWindow;
}

app.commandLine.appendSwitch('enable-features', 'ScreenCaptureKitPicker');

app.whenReady().then(() => {
  // Start backend servers first
  startBackendServers();
  
  // Wait a bit for servers to initialize, then create windows
  setTimeout(() => {
    createSettingsWindow();
    createOverlayWindow();
  }, 2000);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createSettingsWindow();
      createOverlayWindow();
    }
  });
});

app.on('window-all-closed', () => {
  stopBackendServers();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackendServers();
});

// IPC Handlers

// Get available capture sources
ipcMain.handle('get-sources', async () => {
  try {
    const sources = await desktopCapturer.getSources({
      types: ['window', 'screen'],
      thumbnailSize: { width: 320, height: 180 },
      fetchWindowIcons: true,
    });

    return sources.map((source) => ({
      id: source.id,
      name: source.name,
      thumbnail: source.thumbnail.toDataURL(),
      appIcon: source.appIcon ? source.appIcon.toDataURL() : null,
    }));
  } catch (error) {
    console.error('Error getting sources:', error);
    return [];
  }
});

// Show subtitle in overlay
ipcMain.on('show-subtitle', (event, text) => {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.webContents.send('subtitle-update', text);
  }
});

// Update overlay settings
ipcMain.on('update-overlay-settings', (event, settings) => {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.webContents.send('settings-update', settings);

    // Update overlay position if needed
    if (settings.position) {
      const primaryDisplay = screen.getPrimaryDisplay();
      const { width, height } = primaryDisplay.workAreaSize;
      const overlayHeight = 120;

      if (settings.position === 'top') {
        overlayWindow.setPosition(0, 0);
      } else {
        overlayWindow.setPosition(0, height - overlayHeight);
      }
    }
  }
});

// Toggle overlay visibility
ipcMain.on('toggle-overlay', (event, visible) => {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    if (visible) {
      overlayWindow.show();
    } else {
      overlayWindow.hide();
    }
  }
});

// Clear subtitle
ipcMain.on('clear-subtitle', () => {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    overlayWindow.webContents.send('subtitle-update', '');
  }
});
