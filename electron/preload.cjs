const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Get available screen/window sources for capture
  getSources: () => ipcRenderer.invoke('get-sources'),

  // Send subtitle text to overlay
  showSubtitle: (text) => ipcRenderer.send('show-subtitle', text),

  // Clear subtitle from overlay
  clearSubtitle: () => ipcRenderer.send('clear-subtitle'),

  // Update overlay settings (font, colors, position, etc.)
  updateOverlaySettings: (settings) => ipcRenderer.send('update-overlay-settings', settings),

  // Toggle overlay visibility
  toggleOverlay: (visible) => ipcRenderer.send('toggle-overlay', visible),

  // Listen for subtitle updates (used by overlay window)
  onSubtitleUpdate: (callback) => {
    ipcRenderer.on('subtitle-update', (event, text) => callback(text));
  },

  // Listen for settings updates (used by overlay window)
  onSettingsUpdate: (callback) => {
    ipcRenderer.on('settings-update', (event, settings) => callback(settings));
  },
});
