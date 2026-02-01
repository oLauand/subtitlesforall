import { useState, useEffect } from 'react';
import { SourceInfo } from '../types';
import { translations, Language } from '../i18n';

interface SourcePickerProps {
  onSelect: (sourceId: string, includeAudio: boolean) => void;
  onClose: () => void;
  uiLanguage: Language;
}

function SourcePicker({ onSelect, onClose, uiLanguage }: SourcePickerProps) {
  const t = translations[uiLanguage];
  const [sources, setSources] = useState<SourceInfo[]>([]);
  const [selectedSource, setSelectedSource] = useState<string | null>(null);
  const [includeAudio, setIncludeAudio] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSources();
  }, []);

  const loadSources = async () => {
    setLoading(true);
    try {
      if (window.electronAPI) {
        const fetchedSources = await window.electronAPI.getSources();
        // Map to local type
        const mappedSources: SourceInfo[] = fetchedSources.map((s) => ({
          id: s.id,
          name: s.name,
          thumbnail: s.thumbnail,
          appIcon: s.appIcon,
        }));
        setSources(mappedSources);
        // Auto-select first screen source if available
        const screenSource = mappedSources.find((s) => s.id.startsWith('screen:'));
        if (screenSource) {
          setSelectedSource(screenSource.id);
        } else if (mappedSources.length > 0) {
          setSelectedSource(mappedSources[0].id);
        }
      }
    } catch (error) {
      console.error('Error loading sources:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = () => {
    if (selectedSource) {
      onSelect(selectedSource, includeAudio);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    } else if (e.key === 'Enter' && selectedSource) {
      handleSelect();
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} onKeyDown={handleKeyDown}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">{t.sourcePicker.title}</h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        {loading ? (
          <div className="transcript-placeholder">{uiLanguage === 'en' ? 'Loading available sources...' : 'Lade verfügbare Quellen...'}</div>
        ) : sources.length === 0 ? (
          <div className="transcript-placeholder">
            {uiLanguage === 'en' ? 'No sources available. Make sure screen sharing is enabled.' : 'Keine Quellen verfügbar. Stelle sicher, dass Bildschirmfreigabe aktiviert ist.'}
          </div>
        ) : (
          <>
            <div className="sources-grid">
              {sources.map((source) => (
                <div
                  key={source.id}
                  className={`source-item ${selectedSource === source.id ? 'selected' : ''}`}
                  onClick={() => setSelectedSource(source.id)}
                >
                  <img
                    src={source.thumbnail}
                    alt={source.name}
                    className="source-thumbnail"
                  />
                  <div className="source-name" title={source.name}>
                    {source.name}
                  </div>
                </div>
              ))}
            </div>

            <div className="checkbox-group">
              <input
                type="checkbox"
                id="include-audio"
                checked={includeAudio}
                onChange={(e) => setIncludeAudio(e.target.checked)}
              />
              <label htmlFor="include-audio">
                {uiLanguage === 'en' ? 'Include system audio (required for subtitles)' : 'Systemton einbeziehen (erforderlich für Untertitel)'}
              </label>
            </div>

            <div className="modal-actions">
              <button className="btn btn-primary" onClick={onClose} style={{ background: 'var(--bg-tertiary)' }}>
                {t.sourcePicker.cancel}
              </button>
              <button
                className="btn btn-primary"
                onClick={handleSelect}
                disabled={!selectedSource}
              >
                {t.sourcePicker.selectSource}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default SourcePicker;
