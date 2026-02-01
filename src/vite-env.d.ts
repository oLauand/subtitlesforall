/// <reference types="vite/client" />

export interface ElectronSourceInfo {
  id: string;
  name: string;
  thumbnail: string;
  appIcon: string | null;
}

export interface ElectronOverlaySettings {
  fontSize?: number;
  fontFamily?: string;
  textColor?: string;
  backgroundColor?: string;
  position?: 'top' | 'bottom';
  maxLines?: number;
}

export interface ElectronAPI {
  getSources: () => Promise<ElectronSourceInfo[]>;
  showSubtitle: (text: string) => void;
  clearSubtitle: () => void;
  updateOverlaySettings: (settings: ElectronOverlaySettings) => void;
  toggleOverlay: (visible: boolean) => void;
  onSubtitleUpdate: (callback: (text: string) => void) => void;
  onSettingsUpdate: (callback: (settings: ElectronOverlaySettings) => void) => void;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}

export {};
