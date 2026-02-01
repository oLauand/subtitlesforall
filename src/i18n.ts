// Language translations
export const translations = {
  en: {
    // Main App
    title: 'SubtitlesForAll',
    startCapture: 'Start Capture',
    stopCapture: 'Stop Capture',
    clearTranscript: 'Clear Transcript',
    
    // Status
    status: {
      idle: 'Idle',
      connecting: 'Connecting...',
      capturing: 'Capturing',
      error: 'Error',
      connected: 'Connected',
      disconnected: 'Disconnected',
    },
    
    // Settings
    settings: {
      title: 'Settings',
      language: 'Interface Language',
      serverUrl: 'Server URL',
      transcriptionLanguage: 'Transcription Language',
      overlaySettings: 'Overlay Settings',
      fontSize: 'Font Size',
      fontFamily: 'Font Family',
      textColor: 'Text Color',
      backgroundColor: 'Background Color',
      backgroundOpacity: 'Background Opacity',
      position: 'Position',
      positionTop: 'Top',
      positionBottom: 'Bottom',
      maxLines: 'Max Lines',
    },
    
    // Source Picker
    sourcePicker: {
      title: 'Select Audio Source',
      subtitle: 'Choose a screen or window to capture audio from',
      selectSource: 'Select Source',
      cancel: 'Cancel',
    },
    
    // Transcript
    transcript: {
      title: 'Live Transcript',
      empty: 'No transcription yet. Start capturing to see live subtitles.',
    },
  },
  
  de: {
    // Main App
    title: 'SubtitlesForAll',
    startCapture: 'Aufnahme starten',
    stopCapture: 'Aufnahme stoppen',
    clearTranscript: 'Transkript löschen',
    
    // Status
    status: {
      idle: 'Bereit',
      connecting: 'Verbinde...',
      capturing: 'Aufnahme läuft',
      error: 'Fehler',
      connected: 'Verbunden',
      disconnected: 'Getrennt',
    },
    
    // Settings
    settings: {
      title: 'Einstellungen',
      language: 'Menüsprache',
      serverUrl: 'Server-URL',
      transcriptionLanguage: 'Transkriptionssprache',
      overlaySettings: 'Overlay-Einstellungen',
      fontSize: 'Schriftgröße',
      fontFamily: 'Schriftart',
      textColor: 'Textfarbe',
      backgroundColor: 'Hintergrundfarbe',
      backgroundOpacity: 'Hintergrundtransparenz',
      position: 'Position',
      positionTop: 'Oben',
      positionBottom: 'Unten',
      maxLines: 'Max. Zeilen',
    },
    
    // Source Picker
    sourcePicker: {
      title: 'Audioquelle auswählen',
      subtitle: 'Wähle einen Bildschirm oder ein Fenster für die Audioaufnahme',
      selectSource: 'Quelle auswählen',
      cancel: 'Abbrechen',
    },
    
    // Transcript
    transcript: {
      title: 'Live-Transkript',
      empty: 'Noch keine Transkription. Starte die Aufnahme, um Live-Untertitel zu sehen.',
    },
  },
};

export type Language = keyof typeof translations;
export type TranslationKey = typeof translations.en;
