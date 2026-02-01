import { useState, useRef, useCallback, useEffect } from 'react';
import SourcePicker from './components/SourcePicker';
import SettingsPanel from './components/SettingsPanel';
import { OverlaySettings, CaptureState, ConnectionStatus } from './types';
import { translations, Language } from './i18n';

function App() {
  // State
  const [captureState, setCaptureState] = useState<CaptureState>('idle');
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [showSourcePicker, setShowSourcePicker] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [serverUrl] = useState('ws://localhost:9090'); // Fixed URL
  const [uiLanguage, setUiLanguage] = useState<Language>('en');
  const [transcriptionLanguage, setTranscriptionLanguage] = useState('auto');
  const [overlaySettings, setOverlaySettings] = useState<OverlaySettings>({
    fontSize: 32,
    fontFamily: 'Segoe UI',
    textColor: '#ffffff',
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    position: 'bottom',
    maxLines: 2,
  });

  // Translation function
  const t = translations[uiLanguage];

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const isCapturingRef = useRef(false);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      stopCapture();
    };
  }, []);

  // Update overlay settings when they change
  useEffect(() => {
    if (window.electronAPI) {
      window.electronAPI.updateOverlaySettings(overlaySettings);
    }
  }, [overlaySettings]);

  // Handle source selection and start capture
  const handleSourceSelected = useCallback(async (sourceId: string, _includeAudio: boolean) => {
    setShowSourcePicker(false);
    setCaptureState('connecting');
    setConnectionStatus('connecting');

    try {
      // Get the media stream with system audio
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          // @ts-ignore - Electron's desktopCapturer requires these constraints
          mandatory: {
            chromeMediaSource: 'desktop',
            chromeMediaSourceId: sourceId,
          },
        },
        video: {
          // @ts-ignore
          mandatory: {
            chromeMediaSource: 'desktop',
            chromeMediaSourceId: sourceId,
          },
        },
      });

      // We only need audio, stop video tracks
      stream.getVideoTracks().forEach((track) => track.stop());

      // Check if we have audio tracks
      const audioTracks = stream.getAudioTracks();
      if (audioTracks.length === 0) {
        throw new Error('No audio track available. Make sure system audio is enabled.');
      }

      mediaStreamRef.current = stream;

      // Set up WebSocket connection
      const ws = new WebSocket(serverUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');

        // Send initial configuration to WhisperLive server
        const config = {
          uid: `user_${Date.now()}`,
          language: transcriptionLanguage === 'auto' ? null : transcriptionLanguage,
          task: 'transcribe',
          model: 'small',
          use_vad: true,
        };
        ws.send(JSON.stringify(config));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Server message:', data);

          if (data.message === 'SERVER_READY' || data.status === 'ready') {
            console.log('Server is ready, starting audio capture...');
            startAudioCapture(stream);
            setCaptureState('capturing');
          }

          // Handle transcription segments
          if (data.segments && data.segments.length > 0) {
            const text = data.segments.map((s: { text: string }) => s.text).join(' ').trim();
            if (text) {
              setTranscript((prev) => {
                const newTranscript = prev + ' ' + text;
                // Keep only last 1000 characters for display
                return newTranscript.slice(-1000);
              });

              // Send to overlay
              if (window.electronAPI) {
                window.electronAPI.showSubtitle(text);
              }
            }
          }

          // Handle individual text updates
          if (data.text) {
            setTranscript((prev) => {
              const newTranscript = prev + ' ' + data.text;
              return newTranscript.slice(-1000);
            });

            if (window.electronAPI) {
              window.electronAPI.showSubtitle(data.text);
            }
          }
        } catch (err) {
          console.error('Error parsing message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('disconnected');
        setCaptureState('error');
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        setConnectionStatus('disconnected');
        if (captureState === 'capturing') {
          setCaptureState('idle');
        }
      };
    } catch (error) {
      console.error('Error starting capture:', error);
      setCaptureState('error');
      setConnectionStatus('disconnected');
      alert(`Failed to start capture: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, [serverUrl, transcriptionLanguage, captureState]);

  // Start audio capture and send to WebSocket
  const startAudioCapture = useCallback((stream: MediaStream) => {
    try {
      // Create audio context with 48kHz sample rate (what browsers typically capture at)
      const audioContext = new AudioContext({ sampleRate: 48000 });
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);

      // Create script processor for audio processing
      // Using 4096 buffer size for smooth processing
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      // Target sample rate for Whisper (16kHz)
      const targetSampleRate = 16000;
      const resampleRatio = audioContext.sampleRate / targetSampleRate;

      isCapturingRef.current = true;

      processor.onaudioprocess = (event) => {
        if (!isCapturingRef.current || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          return;
        }

        const inputData = event.inputBuffer.getChannelData(0);

        // Downsample from 48kHz to 16kHz
        const outputLength = Math.floor(inputData.length / resampleRatio);
        const outputData = new Float32Array(outputLength);

        for (let i = 0; i < outputLength; i++) {
          const srcIndex = Math.floor(i * resampleRatio);
          outputData[i] = inputData[srcIndex];
        }

        // Send audio data as binary (Float32Array)
        wsRef.current.send(outputData.buffer);
      };

      // Connect audio nodes
      source.connect(processor);
      processor.connect(audioContext.destination);

      console.log('Audio capture started with sample rate:', audioContext.sampleRate);
    } catch (error) {
      console.error('Error starting audio capture:', error);
      setCaptureState('error');
    }
  }, []);

  // Stop capture and clean up
  const stopCapture = useCallback(() => {
    isCapturingRef.current = false;

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Stop audio processing
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Stop media stream
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }

    setCaptureState('idle');
    setConnectionStatus('disconnected');

    // Clear overlay
    if (window.electronAPI) {
      window.electronAPI.clearSubtitle();
    }
  }, []);

  // Handle start capture button
  const handleStartCapture = () => {
    setShowSourcePicker(true);
  };

  // Handle settings change
  const handleSettingsChange = (newSettings: Partial<OverlaySettings>) => {
    setOverlaySettings((prev) => ({ ...prev, ...newSettings }));
  };

  // Get status text and color
  const getStatusInfo = () => {
    switch (captureState) {
      case 'idle':
        return { text: t.status.idle, color: 'var(--text-secondary)' };
      case 'connecting':
        return { text: t.status.connecting, color: 'var(--warning)' };
      case 'capturing':
        return { text: t.status.capturing, color: 'var(--success)' };
      case 'error':
        return { text: t.status.error, color: 'var(--error)' };
      default:
        return { text: t.status.idle, color: 'var(--text-secondary)' };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <img src="/icon.svg" alt="SubtitlesForAll" className="app-logo" />
        <div>
          <h1 className="app-title">{t.title}</h1>
          <p className="app-subtitle">{uiLanguage === 'en' ? 'Real-time subtitles for any audio' : 'Echtzeit-Untertitel für jedes Audio'}</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Status Panel */}
        <div className="panel status-panel">
          <h3 className="panel-title">📊 Status</h3>
          <div className="status-row">
            <span className="status-label">{uiLanguage === 'en' ? 'Capture Status' : 'Aufnahme-Status'}</span>
            <span className="status-value" style={{ color: statusInfo.color }}>
              <span className={`status-indicator ${connectionStatus}`} />
              {statusInfo.text}
            </span>
          </div>
          <div className="status-row">
            <span className="status-label">WebSocket</span>
            <span className="status-value">
              {connectionStatus === 'connected' ? (uiLanguage === 'en' ? '✅ Connected' : '✅ Verbunden') : (uiLanguage === 'en' ? '❌ Disconnected' : '❌ Getrennt')}
            </span>
          </div>
          <div className="status-row">
            <span className="status-label">{t.settings.language}</span>
            <select
              value={uiLanguage}
              onChange={(e) => setUiLanguage(e.target.value as Language)}
              style={{ padding: '4px 8px', borderRadius: '4px' }}
            >
              <option value="en">English</option>
              <option value="de">Deutsch</option>
            </select>
          </div>
        </div>

        {/* Transcription Language Settings */}
        <div className="panel">
          <h3 className="panel-title">🌍 {uiLanguage === 'en' ? 'Transcription Language' : 'Transkriptionssprache'}</h3>
          <div className="status-row">
            <span className="status-label">{t.settings.transcriptionLanguage}</span>
            <select
              value={transcriptionLanguage}
              onChange={(e) => setTranscriptionLanguage(e.target.value)}
              disabled={captureState === 'capturing'}
              style={{ padding: '4px 8px', borderRadius: '4px' }}
            >
              <option value="auto">{uiLanguage === 'en' ? 'Auto (Automatic Detection)' : 'Auto (Automatische Erkennung)'}</option>
              <option value="en">English</option>
              <option value="de">Deutsch (German)</option>
              <option value="es">Español (Spanish)</option>
              <option value="fr">Français (French)</option>
              <option value="it">Italiano (Italian)</option>
              <option value="pt">Português (Portuguese)</option>
            </select>
          </div>
        </div>

        {/* Capture Controls */}
        <div className="panel">
          <h3 className="panel-title">🎤 {uiLanguage === 'en' ? 'Audio Capture' : 'Audio-Aufnahme'}</h3>
          {captureState === 'idle' || captureState === 'error' ? (
            <button className="btn btn-primary btn-full" onClick={handleStartCapture}>
              🎬 {t.startCapture}
            </button>
          ) : (
            <button className="btn btn-danger btn-full" onClick={stopCapture}>
              ⏹️ {t.stopCapture}
            </button>
          )}
        </div>

        {/* Settings Panel */}
        <div className="panel">
          <h3 className="panel-title">⚙️ {t.settings.overlaySettings}</h3>
          <SettingsPanel settings={overlaySettings} onChange={handleSettingsChange} uiLanguage={uiLanguage} />
        </div>

        {/* Transcript Display */}
        <div className="panel transcript-panel">
          <h3 className="panel-title">📝 {t.transcript.title}</h3>
          <div className="transcript-content">
            {transcript ? (
              transcript.trim()
            ) : (
              <div className="transcript-placeholder">
                {t.transcript.empty}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Source Picker Modal */}
      {showSourcePicker && (
        <SourcePicker
          onSelect={handleSourceSelected}
          onClose={() => setShowSourcePicker(false)}
          uiLanguage={uiLanguage}
        />
      )}
    </div>
  );
}

export default App;
