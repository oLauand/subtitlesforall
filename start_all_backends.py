#!/usr/bin/env python3
"""
🚀 Subtitles For All - Multi-Backend Launcher
=============================================

Startet alle 3 Backend-Server parallel:
- Port 9090: Whisper Python (OpenAI Whisper) - Baseline
- Port 9091: Moonshine ONNX - 5-15x schneller als Python
- Port 9092: Whisper.cpp - 2-4x schneller als Python

Verwendung:
    python start_all_backends.py           # Startet alle 3 Backends
    python start_all_backends.py --only whisper-python
    python start_all_backends.py --only moonshine
    python start_all_backends.py --only whisper-cpp
    python start_all_backends.py --no-whisper-python  # Ohne Python Whisper
"""

import subprocess
import sys
import os
import time
import signal
import argparse
from pathlib import Path
from typing import List, Optional

# Farben für Terminal-Ausgabe
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    """Zeigt ASCII-Banner an."""
    banner = f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   {Colors.BOLD}🎤 SUBTITLES FOR ALL - Multi-Backend Server 🎤{Colors.ENDC}{Colors.CYAN}                       ║
║                                                                          ║
║   {Colors.GREEN}Backend 1:{Colors.CYAN} Whisper Python (Port 9090) - Baseline Reference           ║
║   {Colors.YELLOW}Backend 2:{Colors.CYAN} Moonshine ONNX  (Port 9091) - 5-15x Faster              ║
║   {Colors.BLUE}Backend 3:{Colors.CYAN} Whisper.cpp     (Port 9092) - 2-4x Faster + Quantized   ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝{Colors.ENDC}
"""
    print(banner)

def check_dependencies():
    """Überprüft ob alle notwendigen Pakete installiert sind."""
    missing = []
    
    # Whisper Python
    try:
        import whisper
        print(f"{Colors.GREEN}✓{Colors.ENDC} OpenAI Whisper installiert")
    except ImportError:
        missing.append("openai-whisper")
        print(f"{Colors.RED}✗{Colors.ENDC} OpenAI Whisper nicht installiert")
    
    # Moonshine
    try:
        import moonshine_onnx
        print(f"{Colors.GREEN}✓{Colors.ENDC} Moonshine ONNX installiert")
    except ImportError:
        missing.append("moonshine-onnx")
        print(f"{Colors.RED}✗{Colors.ENDC} Moonshine ONNX nicht installiert")
    
    # Whisper.cpp (pywhispercpp)
    try:
        from pywhispercpp.model import Model
        print(f"{Colors.GREEN}✓{Colors.ENDC} pywhispercpp installiert")
    except ImportError:
        missing.append("pywhispercpp")
        print(f"{Colors.RED}✗{Colors.ENDC} pywhispercpp nicht installiert")
    
    # WebSocket
    try:
        import websockets
        print(f"{Colors.GREEN}✓{Colors.ENDC} websockets installiert")
    except ImportError:
        missing.append("websockets")
        print(f"{Colors.RED}✗{Colors.ENDC} websockets nicht installiert")
    
    if missing:
        print(f"\n{Colors.YELLOW}⚠ Fehlende Pakete: {', '.join(missing)}{Colors.ENDC}")
        print(f"  Installieren mit: pip install {' '.join(missing)}")
        return False
    
    return True

def start_backend(script_name: str, port: int, name: str, color: str) -> Optional[subprocess.Popen]:
    """Startet einen Backend-Server als Subprocess."""
    script_path = Path(__file__).parent / script_name
    
    if not script_path.exists():
        print(f"{Colors.RED}✗{Colors.ENDC} {script_name} nicht gefunden!")
        return None
    
    print(f"{color}▶{Colors.ENDC} Starte {name} auf Port {port}...")
    
    try:
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
            cwd=str(script_path.parent)
        )
        
        # Kurz warten um zu sehen ob der Server startet
        time.sleep(1)
        
        if process.poll() is None:
            print(f"{Colors.GREEN}✓{Colors.ENDC} {name} läuft auf Port {port}")
            return process
        else:
            print(f"{Colors.RED}✗{Colors.ENDC} {name} konnte nicht gestartet werden")
            return None
            
    except Exception as e:
        print(f"{Colors.RED}✗{Colors.ENDC} Fehler beim Starten von {name}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Startet alle Subtitles-for-All Backend-Server"
    )
    parser.add_argument(
        '--only', 
        choices=['whisper-python', 'moonshine', 'whisper-cpp'],
        help='Startet nur das angegebene Backend'
    )
    parser.add_argument(
        '--no-whisper-python',
        action='store_true',
        help='Startet ohne Whisper Python (langsamstes Backend)'
    )
    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='Überprüft nur die Abhängigkeiten'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    print(f"\n{Colors.BOLD}Überprüfe Abhängigkeiten...{Colors.ENDC}\n")
    deps_ok = check_dependencies()
    
    if args.check_deps:
        sys.exit(0 if deps_ok else 1)
    
    print()
    
    # Backend-Konfiguration
    backends = {
        'whisper-python': {
            'script': 'simple_server.py',
            'port': 9090,
            'name': 'Whisper Python',
            'color': Colors.GREEN
        },
        'moonshine': {
            'script': 'moonshine_server.py',
            'port': 9091,
            'name': 'Moonshine ONNX',
            'color': Colors.YELLOW
        },
        'whisper-cpp': {
            'script': 'whispercpp_server.py',
            'port': 9092,
            'name': 'Whisper.cpp',
            'color': Colors.BLUE
        }
    }
    
    # Bestimme welche Backends gestartet werden sollen
    if args.only:
        backends_to_start = [args.only]
    else:
        backends_to_start = list(backends.keys())
        if args.no_whisper_python:
            backends_to_start.remove('whisper-python')
    
    processes: List[subprocess.Popen] = []
    
    print(f"{Colors.BOLD}Starte Backend-Server...{Colors.ENDC}\n")
    
    for backend_id in backends_to_start:
        config = backends[backend_id]
        proc = start_backend(
            config['script'],
            config['port'],
            config['name'],
            config['color']
        )
        if proc:
            processes.append(proc)
    
    if not processes:
        print(f"\n{Colors.RED}Keine Server konnten gestartet werden!{Colors.ENDC}")
        sys.exit(1)
    
    # Zeige aktive Server
    print(f"\n{Colors.BOLD}═══════════════════════════════════════════════════════════════{Colors.ENDC}")
    print(f"{Colors.GREEN}✓ {len(processes)} Backend-Server aktiv{Colors.ENDC}")
    print()
    for backend_id in backends_to_start:
        config = backends[backend_id]
        print(f"  {config['color']}●{Colors.ENDC} {config['name']}: ws://localhost:{config['port']}")
    print()
    print(f"{Colors.CYAN}Frontend starten mit:{Colors.ENDC} npm run dev (Port 3000)")
    print(f"\n{Colors.YELLOW}Drücke Ctrl+C zum Beenden aller Server{Colors.ENDC}")
    print(f"{Colors.BOLD}═══════════════════════════════════════════════════════════════{Colors.ENDC}\n")
    
    # Warte auf Benutzer-Abbruch
    def signal_handler(sig, frame):
        print(f"\n\n{Colors.YELLOW}Beende alle Server...{Colors.ENDC}")
        for proc in processes:
            proc.terminate()
        time.sleep(1)
        for proc in processes:
            if proc.poll() is None:
                proc.kill()
        print(f"{Colors.GREEN}Alle Server beendet.{Colors.ENDC}")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Halte das Script am Laufen und zeige Server-Ausgaben
    try:
        while True:
            for proc in processes:
                if proc.poll() is not None:
                    print(f"{Colors.RED}Ein Server wurde beendet!{Colors.ENDC}")
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
