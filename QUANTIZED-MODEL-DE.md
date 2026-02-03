# Quantisiertes Modell (ggml-base-q5_1.bin) 

## 🚀 Schnellstart mit quantisiertem Modell

Das quantisierte Modell **ggml-base-q5_1.bin** bietet eine bessere Performance bei vergleichbarer Qualität:

### Vorteile:
- ⚡ **Schneller**: Reduzierte Modellgröße (31 MB statt 74 MB)
- 💾 **Weniger Speicher**: Geringerer RAM-Verbrauch
- 🎯 **Gute Qualität**: Kaum merkbare Qualitätseinbußen gegenüber dem vollen Modell
- 🌍 **Mehrsprachig**: Unterstützt alle Sprachen wie das normale Base-Modell

### So verwendest du es:

#### Option 1: Mit dem Start-Skript (Empfohlen)
```powershell
.\start-with-quantized.ps1
```

Dieses Skript:
1. Prüft, ob das quantisierte Modell vorhanden ist
2. Startet den WebSocket-Server automatisch
3. Öffnet die Electron-App
4. Setzt das quantisierte Modell als Standard

#### Option 2: Manuelle Konfiguration

1. **Server starten:**
```powershell
cd subtitles-for-all
python run_server.py --port 9090 --model ..\models\ggml-base-q5_1.bin
```

2. **App starten:**
```powershell
npm run electron:dev
```

3. **Im Frontend:** Wähle **"⚡ Base Q5_1"** aus dem Modell-Dropdown

## 📊 Modell-Vergleich

| Modell | Größe | Performance | Qualität | Sprachen |
|--------|-------|-------------|----------|----------|
| **base-q5_1** | **31 MB** | **⚡⚡⚡** | **⭐⭐⭐⭐** | **✓** |
| base | 74 MB | ⚡⚡ | ⭐⭐⭐⭐ | ✓ |
| base.en | 74 MB | ⚡⚡ | ⭐⭐⭐⭐ | Nur EN |
| tiny | 39 MB | ⚡⚡⚡⚡ | ⭐⭐⭐ | ✓ |
| small | 244 MB | ⚡ | ⭐⭐⭐⭐⭐ | ✓ |

## 🔍 Was ist Quantisierung?

Quantisierung reduziert die Präzision der Modellgewichte (z.B. von 32-bit auf 5-bit), was zu:
- Kleineren Dateigrößen führt
- Schnellerer Inferenz (Verarbeitung)
- Geringerem Speicherbedarf

Die Q5_1-Quantisierung bietet einen guten Kompromiss zwischen Geschwindigkeit und Qualität.

## ✅ VAD (Voice Activity Detection)

**Ja, VAD ist bereits implementiert!** 

Die Anwendung nutzt automatisch VAD, um:
- Stille zu erkennen und zu überspringen
- Nur tatsächlich gesprochene Abschnitte zu transkribieren
- Die Performance zu verbessern
- Falsche Transkriptionen von Hintergrundgeräuschen zu reduzieren

VAD ist standardmäßig aktiviert (`use_vad: true` in App.tsx) und funktioniert mit allen Modellen.

## 🎯 Empfohlene Konfiguration

Für die beste Balance aus Geschwindigkeit und Qualität:
- **Modell**: base-q5_1 (quantisiert)
- **VAD**: Aktiviert (Standard)
- **Sprache**: Auto-Erkennung oder spezifisch (z.B. "de" für Deutsch)

## 📝 Technische Details

- **Quantisierungsmethode**: Q5_1 (5-bit integer mit 1-bit scale)
- **Original**: ggml-base.bin (~74 MB)
- **Quantisiert**: ggml-base-q5_1.bin (~31 MB)
- **Kompression**: ~58% Größenreduktion
- **Qualitätsverlust**: Minimal (<5% bei den meisten Anwendungen)
