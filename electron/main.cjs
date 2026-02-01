const { app, BrowserWindow, ipcMain, desktopCapturer, screen } = require('electron');
const path = require('path');

let settingsWindow = null;
let overlayWindow = null;

const isDev = process.env.NODE_ENV === 'development';

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
  createSettingsWindow();
  createOverlayWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createSettingsWindow();
      createOverlayWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
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
