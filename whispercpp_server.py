#!/usr/bin/env python3
"""
whisper.cpp Backend Server for SubtitlesForAll
Uses pywhispercpp for fast C++ based transcription
Port: 9092
"""

import asyncio
import websockets
import json
import numpy as np
import argparse
import re
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

# whisper.cpp Python bindings
from pywhispercpp.model import Model as WhisperCppModel

# Path to local whisper.cpp models directory
WHISPER_CPP_MODELS_DIR = Path(__file__).parent.parent / "models"

# Patterns to filter out (noise/silence markers)
FILTER_PATTERNS = [
    r'\[BLANK_AUDIO\]',
    r'\[Silence\]',
    r'\[silence\]',
    r'\[ Silence \]',
    r'\[ Silence\.\.\]',
    r'\[Music\]',
    r'\[music\]',
    r'\(music\)',
    r'\(Musik\)',
    r'^\s*\.\.\.\s*$',
    r'^\s*$',
]

def filter_transcription(text: str) -> str:
    """Filter out noise markers and clean up transcription"""
    if not text:
        return ""
    
    # Remove filter patterns
    for pattern in FILTER_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Clean up multiple spaces and trim
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


class WhisperCppTranscriber:
    def __init__(self, model_name: str = "base-q5_1"):
        self.model_name = model_name
        self.model = None
        self.load_model(model_name)
    
    def get_local_model_path(self, model_name: str):
        """Check if model exists locally in whisper.cpp models folder"""
        file_map = {
            "tiny": "ggml-tiny.bin",
            "tiny.en": "ggml-tiny.en.bin",
            "base": "ggml-base.bin",
            "base.en": "ggml-base.en.bin",
            "small": "ggml-small.bin",
            "small.en": "ggml-small.en.bin",
            "medium": "ggml-medium.bin",
            "medium.en": "ggml-medium.en.bin",
            "large-v3": "ggml-large-v3.bin",
            "large-v3-turbo": "ggml-large-v3-turbo.bin",
            "tiny-q5_1": "ggml-tiny-q5_1.bin",
            "base-q5_1": "ggml-base-q5_1.bin",
            "small-q5_1": "ggml-small-q5_1.bin",
            "medium-q5_1": "ggml-medium-q5_1.bin",
            "large-v3-q5_0": "ggml-large-v3-q5_0.bin",
            "large-v3-turbo-q5_0": "ggml-large-v3-turbo-q5_0.bin",
        }
        
        filename = file_map.get(model_name, f"ggml-{model_name}.bin")
        model_path = WHISPER_CPP_MODELS_DIR / filename
        
        if model_path.exists():
            file_size_mb = model_path.stat().st_size / (1024 * 1024)
            if file_size_mb > 1:
                return model_path
        return None
    
    def load_model(self, model_name: str):
        """Load a whisper.cpp model"""
        print(f"[whisper.cpp] Loading model: {model_name}")
        
        local_path = self.get_local_model_path(model_name)
        
        try:
            if local_path:
                print(f"[whisper.cpp] Using local model: {local_path}")
                self.model = WhisperCppModel(str(local_path))
            else:
                print(f"[whisper.cpp] Downloading model: {model_name}")
                self.model = WhisperCppModel(model_name)
            
            self.model_name = model_name
            print(f"[whisper.cpp] Model '{model_name}' loaded successfully!")
            return True
        except Exception as e:
            print(f"[whisper.cpp] Error loading model: {e}")
            # Try fallback models
            for fallback in ["base-q5_1", "tiny-q5_1", "base.en"]:
                if fallback != model_name:
                    fallback_path = self.get_local_model_path(fallback)
                    if fallback_path:
                        try:
                            print(f"[whisper.cpp] Trying fallback: {fallback}")
                            self.model = WhisperCppModel(str(fallback_path))
                            self.model_name = fallback
                            print(f"[whisper.cpp] Fallback model '{fallback}' loaded!")
                            return True
                        except:
                            continue
            print("[whisper.cpp] No working model found!")
            return False
    
    def transcribe(self, audio_data: np.ndarray) -> str:
        """Transcribe audio using whisper.cpp"""
        if self.model is None:
            return ""
        
        try:
            # Ensure audio is float32 and normalized
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Check if audio has content (not silence)
            audio_power = np.sqrt(np.mean(audio_data ** 2))
            if audio_power < 0.001:  # Very quiet, likely silence
                return ""
            
            # Normalize if needed
            max_val = np.max(np.abs(audio_data))
            if max_val > 1.0:
                audio_data = audio_data / max_val
            
            # Transcribe with whisper.cpp
            segments = self.model.transcribe(audio_data)
            
            # Extract text from segments
            text_parts = []
            for segment in segments:
                if hasattr(segment, 'text'):
                    text_parts.append(segment.text)
                elif isinstance(segment, dict) and 'text' in segment:
                    text_parts.append(segment['text'])
                elif isinstance(segment, str):
                    text_parts.append(segment)
            
            result = " ".join(text_parts).strip()
            
            # Filter out noise markers
            result = filter_transcription(result)
            
            return result
            
        except Exception as e:
            print(f"[whisper.cpp] Transcription error: {e}")
            return ""


class WhisperCppWebSocketServer:
    def __init__(self, host: str = "localhost", port: int = 9092, model: str = "base-q5_1"):
        self.host = host
        self.port = port
        self.transcriber = WhisperCppTranscriber(model)
        self.clients = set()
    
    async def handle_client(self, websocket, path=None):
        """Handle a WebSocket client connection"""
        client_id = id(websocket)
        self.clients.add(websocket)
        print(f"[whisper.cpp] Client connected. Total: {len(self.clients)}")
        
        # Send SERVER_READY immediately
        try:
            await websocket.send(json.dumps({
                "message": "SERVER_READY",
                "status": "ready",
                "backend": "whisper.cpp",
                "model": self.transcriber.model_name
            }))
        except Exception as e:
            print(f"[whisper.cpp] Error sending ready: {e}")
            return
        
        # Audio buffer for accumulating samples
        audio_buffer = np.array([], dtype=np.float32)
        min_audio_length = 16000 * 3  # 3 seconds at 16kHz
        max_audio_length = 16000 * 10  # 10 seconds max
        
        try:
            async for message in websocket:
                # Handle JSON config messages
                if isinstance(message, str):
                    try:
                        data = json.loads(message)
                        print(f"[whisper.cpp] Config: {data.get('model', 'default')}")
                        
                        # Handle model change
                        if "model" in data:
                            new_model = data["model"]
                            # Only change if different and it's a whisper.cpp compatible model
                            if new_model != self.transcriber.model_name:
                                if not new_model.startswith("moonshine"):
                                    self.transcriber.load_model(new_model)
                        
                        # Confirm ready
                        await websocket.send(json.dumps({
                            "message": "SERVER_READY",
                            "status": "ready",
                            "backend": "whisper.cpp",
                            "model": self.transcriber.model_name
                        }))
                    except json.JSONDecodeError:
                        pass
                    continue
                
                # Handle binary audio data
                if isinstance(message, bytes):
                    try:
                        audio_chunk = np.frombuffer(message, dtype=np.float32)
                        audio_buffer = np.concatenate([audio_buffer, audio_chunk])
                        
                        # Limit buffer size
                        if len(audio_buffer) > max_audio_length:
                            audio_buffer = audio_buffer[-max_audio_length:]
                        
                        # Process when we have enough audio
                        if len(audio_buffer) >= min_audio_length:
                            # Transcribe
                            text = self.transcriber.transcribe(audio_buffer)
                            
                            # Keep last 0.5 seconds for context
                            audio_buffer = audio_buffer[-8000:]
                            
                            if text:
                                response = {
                                    "segments": [{"text": text}],
                                    "text": text,
                                    "backend": "whisper.cpp"
                                }
                                await websocket.send(json.dumps(response))
                                print(f"[whisper.cpp] >> {text[:60]}")
                    except Exception as e:
                        print(f"[whisper.cpp] Audio error: {e}")
                        
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"[whisper.cpp] Error: {e}")
        finally:
            self.clients.discard(websocket)
            print(f"[whisper.cpp] Client disconnected. Total: {len(self.clients)}")
    
    async def start(self):
        """Start the WebSocket server"""
        print(f"\n{'='*60}")
        print(f"  whisper.cpp Backend Server")
        print(f"  Port: {self.port}")
        print(f"  Model: {self.transcriber.model_name}")
        print(f"  Backend: whisper.cpp (C++ optimized)")
        print(f"{'='*60}\n")
        
        async with websockets.serve(
            self.handle_client, 
            self.host, 
            self.port,
            ping_interval=30,
            ping_timeout=10,
            close_timeout=5
        ):
            print(f"[whisper.cpp] Server running on ws://{self.host}:{self.port}")
            print("[whisper.cpp] Waiting for connections...")
            await asyncio.Future()


def main():
    parser = argparse.ArgumentParser(description="whisper.cpp WebSocket Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9092, help="Port to listen on")
    parser.add_argument("--model", default="base-q5_1", help="Whisper model to use")
    
    args = parser.parse_args()
    
    server = WhisperCppWebSocketServer(
        host=args.host,
        port=args.port,
        model=args.model
    )
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\n[whisper.cpp] Server stopped by user")


if __name__ == "__main__":
    main()
