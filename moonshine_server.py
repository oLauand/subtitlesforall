"""
Moonshine WebSocket Server for SubtitlesForAll
This uses the Moonshine ONNX models for ultra-fast real-time transcription (5-15x faster than Whisper)
"""

import asyncio
import json
import wave
import tempfile
import os
from pathlib import Path

try:
    import websockets
    import numpy as np
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call(["pip", "install", "websockets", "numpy"])
    import websockets
    import numpy as np

# Try to import Moonshine ONNX
MOONSHINE_AVAILABLE = False
try:
    from moonshine_onnx import MoonshineOnnxModel, load_tokenizer
    MOONSHINE_AVAILABLE = True
    print("✓ Moonshine ONNX loaded successfully!")
except ImportError:
    try:
        # Try alternative import path
        import sys
        moonshine_path = Path(__file__).parent.parent / "moonshine_backend" / "moonshine-main" / "moonshine-onnx" / "src"
        if moonshine_path.exists():
            sys.path.insert(0, str(moonshine_path))
            from model import MoonshineOnnxModel
            from transcribe import load_tokenizer
            MOONSHINE_AVAILABLE = True
            print(f"✓ Moonshine loaded from local path: {moonshine_path}")
    except ImportError as e:
        print(f"⚠ Moonshine ONNX not available: {e}")
        print("Install with: pip install useful-moonshine-onnx")
        print("Transcription will be simulated.")

# Available Moonshine models
MOONSHINE_MODELS = {
    "moonshine/tiny": {"size": "27M", "description": "Ultra-fast, English only"},
    "moonshine/base": {"size": "62M", "description": "Fast, best quality, English only"},
    "moonshine/tiny-ar": {"size": "27M", "description": "Ultra-fast, Arabic"},
    "moonshine/tiny-zh": {"size": "27M", "description": "Ultra-fast, Chinese"},
    "moonshine/tiny-ja": {"size": "27M", "description": "Ultra-fast, Japanese"},
    "moonshine/tiny-ko": {"size": "27M", "description": "Ultra-fast, Korean"},
    "moonshine/tiny-uk": {"size": "27M", "description": "Ultra-fast, Ukrainian"},
    "moonshine/tiny-vi": {"size": "27M", "description": "Ultra-fast, Vietnamese"},
    "moonshine/base-es": {"size": "62M", "description": "Fast, Spanish"},
}


class MoonshineTranscriber:
    """Handles audio transcription using Moonshine ONNX models."""
    
    def __init__(self, model_name="moonshine/base"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.rate = 16000
        
        if MOONSHINE_AVAILABLE:
            print(f"Loading Moonshine model: {model_name}...")
            try:
                self.model = MoonshineOnnxModel(model_name=model_name)
                self.tokenizer = load_tokenizer()
                # Warmup inference
                self._warmup()
                print(f"✓ Moonshine model '{model_name}' loaded successfully!")
            except Exception as e:
                print(f"✗ Failed to load Moonshine model: {e}")
                self.model = None
    
    def _warmup(self):
        """Warmup the model with a short inference."""
        if self.model:
            dummy_audio = np.zeros((1, self.rate), dtype=np.float32)
            try:
                self.model.generate(dummy_audio)
            except Exception as e:
                print(f"Warmup failed: {e}")
    
    def change_model(self, model_name: str) -> bool:
        """Change to a different Moonshine model."""
        if not MOONSHINE_AVAILABLE:
            return False
            
        if model_name == self.model_name and self.model is not None:
            return True
            
        try:
            print(f"Switching to Moonshine model: {model_name}...")
            self.model = MoonshineOnnxModel(model_name=model_name)
            self.model_name = model_name
            self._warmup()
            print(f"✓ Model switched to: {model_name}")
            return True
        except Exception as e:
            print(f"✗ Failed to switch model: {e}")
            return False
    
    def transcribe(self, audio_data: np.ndarray) -> str:
        """Transcribe audio data to text."""
        if not self.model or not MOONSHINE_AVAILABLE:
            return "[Moonshine not available - install with: pip install useful-moonshine-onnx]"
        
        try:
            # Ensure audio is in correct shape (1, num_samples)
            if audio_data.ndim == 1:
                audio_data = audio_data[np.newaxis, :]
            
            # Generate tokens
            tokens = self.model.generate(audio_data.astype(np.float32))
            
            # Decode tokens to text
            text = self.tokenizer.decode_batch(tokens)[0]
            
            return text.strip()
            
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""


class MoonshineWebSocketServer:
    """WebSocket server for Moonshine transcription."""
    
    def __init__(self, host="0.0.0.0", port=9091, model_name="moonshine/base"):
        self.host = host
        self.port = port
        self.transcriber = MoonshineTranscriber(model_name)
        self.clients = set()
        
    async def handle_client(self, websocket):
        """Handle a WebSocket client connection."""
        client_id = id(websocket)
        self.clients.add(websocket)
        print(f"Client {client_id} connected. Total clients: {len(self.clients)}")
        
        audio_buffer = np.array([], dtype=np.float32)
        config = {"model": "moonshine/base"}
        
        try:
            # Send ready message
            await websocket.send(json.dumps({
                "message": "SERVER_READY",
                "status": "ready",
                "backend": "moonshine",
                "model": self.transcriber.model_name,
                "available_models": list(MOONSHINE_MODELS.keys())
            }))
            
            async for message in websocket:
                if isinstance(message, str):
                    # JSON configuration message
                    try:
                        data = json.loads(message)
                        print(f"Client {client_id} config: {data}")
                        
                        # Handle model change
                        if 'model' in data and data['model'].startswith('moonshine/'):
                            model_name = data['model']
                            
                            # Notify loading
                            await websocket.send(json.dumps({
                                "type": "model_loading",
                                "model": model_name,
                                "progress": 0
                            }))
                            
                            # Change model
                            success = self.transcriber.change_model(model_name)
                            
                            if success:
                                await websocket.send(json.dumps({
                                    "type": "model_ready",
                                    "model": model_name
                                }))
                            else:
                                await websocket.send(json.dumps({
                                    "type": "model_error",
                                    "error": f"Failed to load {model_name}"
                                }))
                                
                    except json.JSONDecodeError:
                        pass
                        
                elif isinstance(message, bytes):
                    # Binary audio data
                    audio_chunk = np.frombuffer(message, dtype=np.float32)
                    audio_buffer = np.concatenate([audio_buffer, audio_chunk])
                    
                    # Transcribe when we have enough audio (1.5 seconds at 16kHz)
                    # Moonshine is fast enough to process smaller chunks
                    if len(audio_buffer) >= 24000:
                        # Transcribe
                        text = self.transcriber.transcribe(audio_buffer)
                        
                        if text:
                            # Send transcription result
                            result = {
                                "type": "TRANSCRIPTION",
                                "segments": [{
                                    "text": text,
                                    "start": 0,
                                    "end": len(audio_buffer) / 16000
                                }],
                                "backend": "moonshine"
                            }
                            await websocket.send(json.dumps(result))
                            print(f"[Moonshine] Transcribed: {text}")
                        
                        # Keep last 0.3 seconds for context (Moonshine is fast)
                        audio_buffer = audio_buffer[-4800:]
                        
        except websockets.exceptions.ConnectionClosed:
            print(f"Client {client_id} disconnected")
        except Exception as e:
            print(f"Error handling client {client_id}: {e}")
        finally:
            self.clients.discard(websocket)
            print(f"Client {client_id} removed. Remaining: {len(self.clients)}")
    
    async def start(self):
        """Start the WebSocket server."""
        print(f"\n{'='*55}")
        print(f"  🌙 SubtitlesForAll - Moonshine Server")
        print(f"{'='*55}")
        print(f"  Host:     {self.host}")
        print(f"  Port:     {self.port}")
        print(f"  Model:    {self.transcriber.model_name}")
        print(f"  Status:   {'Ready ✓' if self.transcriber.model else 'Demo Mode (no transcription)'}")
        print(f"{'='*55}")
        print(f"\n  Moonshine is 5-15x FASTER than Whisper!")
        print(f"\n  Available models:")
        for name, info in MOONSHINE_MODELS.items():
            print(f"    - {name}: {info['size']} - {info['description']}")
        print(f"\n{'='*55}\n")
        
        async with websockets.serve(self.handle_client, self.host, self.port):
            print(f"✓ Moonshine server running on ws://{self.host}:{self.port}")
            print("Waiting for connections...\n")
            await asyncio.Future()  # Run forever


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Moonshine WebSocket Server for SubtitlesForAll")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9091, help="Port to listen on (default: 9091)")
    parser.add_argument("--model", default="moonshine/base", 
                        choices=list(MOONSHINE_MODELS.keys()),
                        help="Moonshine model to use")
    
    args = parser.parse_args()
    
    server = MoonshineWebSocketServer(args.host, args.port, args.model)
    asyncio.run(server.start())


if __name__ == "__main__":
    main()
