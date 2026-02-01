import { OverlaySettings } from '../types';
import { translations, Language } from '../i18n';

interface SettingsPanelProps {
  settings: OverlaySettings;
  onChange: (settings: Partial<OverlaySettings>) => void;
  uiLanguage: Language;
}

const fontFamilies = [
  'Segoe UI',
  'Arial',
  'Calibri',
  'Tahoma',
  'Verdana',
  'Georgia',
  'Times New Roman',
  'Consolas',
  'Courier New',
];

function SettingsPanel({ settings, onChange, uiLanguage }: SettingsPanelProps) {
  const t = translations[uiLanguage];
  
  // Convert hex + opacity to rgba
  const hexToRgba = (hex: string, opacity: number): string => {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  };

  // Extract hex and opacity from rgba
  const rgbaToHexOpacity = (rgba: string): { hex: string; opacity: number } => {
    const match = rgba.match(/rgba?\((\d+),\s*(\d+),\s*(\d+),?\s*([\d.]+)?\)/);
    if (match) {
      const r = parseInt(match[1]).toString(16).padStart(2, '0');
      const g = parseInt(match[2]).toString(16).padStart(2, '0');
      const b = parseInt(match[3]).toString(16).padStart(2, '0');
      const opacity = match[4] ? parseFloat(match[4]) : 1;
      return { hex: `#${r}${g}${b}`, opacity };
    }
    return { hex: '#000000', opacity: 0.75 };
  };

  const bgColorInfo = rgbaToHexOpacity(settings.backgroundColor);

  return (
    <div className="settings-content">
      <div className="settings-grid">
        {/* Font Size */}
        <div className="setting-group">
          <div className="setting-row">
            <span className="setting-label">{t.settings.fontSize}</span>
            <span className="setting-value">{settings.fontSize}px</span>
          </div>
          <input
            type="range"
            min="16"
            max="64"
            value={settings.fontSize}
            onChange={(e) => onChange({ fontSize: parseInt(e.target.value) })}
          />
        </div>

        {/* Font Family */}
        <div className="setting-group">
          <span className="setting-label">{t.settings.fontFamily}</span>
          <select
            value={settings.fontFamily}
            onChange={(e) => onChange({ fontFamily: e.target.value })}
          >
            {fontFamilies.map((font) => (
              <option key={font} value={font} style={{ fontFamily: font }}>
                {font}
              </option>
            ))}
          </select>
        </div>

        {/* Text Color */}
        <div className="setting-group">
          <span className="setting-label">{t.settings.textColor}</span>
          <input
            type="color"
            value={settings.textColor}
            onChange={(e) => onChange({ textColor: e.target.value })}
          />
        </div>

        {/* Background Color */}
        <div className="setting-group">
          <span className="setting-label">{t.settings.backgroundColor}</span>
          <input
            type="color"
            value={bgColorInfo.hex}
            onChange={(e) =>
              onChange({ backgroundColor: hexToRgba(e.target.value, bgColorInfo.opacity) })
            }
          />
        </div>

        {/* Background Opacity */}
        <div className="setting-group">
          <div className="setting-row">
            <span className="setting-label">{t.settings.backgroundOpacity}</span>
            <span className="setting-value">{Math.round(bgColorInfo.opacity * 100)}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={bgColorInfo.opacity * 100}
            onChange={(e) =>
              onChange({ backgroundColor: hexToRgba(bgColorInfo.hex, parseInt(e.target.value) / 100) })
            }
          />
        </div>

        {/* Position */}
        <div className="setting-group">
          <span className="setting-label">{t.settings.position}</span>
          <select
            value={settings.position}
            onChange={(e) => onChange({ position: e.target.value as 'top' | 'bottom' })}
          >
            <option value="bottom">{t.settings.positionBottom}</option>
            <option value="top">{t.settings.positionTop}</option>
          </select>
        </div>
      </div>

      {/* Preview - full width */}
      <div className="setting-group" style={{ marginTop: '8px' }}>
        <span className="setting-label">{uiLanguage === 'en' ? 'Preview' : 'Vorschau'}</span>
        <div
          style={{
            marginTop: '8px',
            padding: '12px 20px',
            borderRadius: '8px',
            textAlign: 'center',
            fontSize: `${Math.min(settings.fontSize, 24)}px`,
            fontFamily: settings.fontFamily,
            color: settings.textColor,
            backgroundColor: settings.backgroundColor,
          }}
        >
          {uiLanguage === 'en' ? 'Sample subtitle text' : 'Beispiel-Untertiteltext'}
        </div>
      </div>
    </div>
  );
}

export default SettingsPanel;
