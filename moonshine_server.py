"""
Moonshine WebSocket Server for SubtitlesForAll
This uses the Moonshine ONNX models for ultra-fast real-time transcription (5-15x faster than Whisper)
"""

import asyncio
import json
import sys
import os
from concurrent.futures import ThreadPoolExecutor
import time

# Fix Windows console encoding
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

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
    print("[OK] Moonshine ONNX loaded successfully!")
except ImportError:
    print("[WARN] Moonshine ONNX not available")
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
        self.executor = ThreadPoolExecutor(max_workers=1)
        
        if MOONSHINE_AVAILABLE:
            try:
                print(f"[Moonshine] Loading model: {model_name}")
                self.model = MoonshineOnnxModel(model_name=model_name)
                self.tokenizer = load_tokenizer()
                self._warmup()
                print(f"[OK] Model loaded: {model_name}")
            except Exception as e:
                print(f"[FAIL] Failed to load model: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("[WARN] Moonshine not available - demo mode")
    
    def _warmup(self):
        """Warm up the model with a dummy input."""
        if self.model and self.tokenizer:
            try:
                dummy_audio = np.zeros((1, 16000), dtype=np.float32)
                self.model.generate(dummy_audio)
                print("[OK] Model warmed up")
            except Exception as e:
                print(f"[WARN] Warmup failed: {e}")
    
    def _load_model_sync(self, model_name: str):
        """Load model synchronously (to be called in thread)."""
        try:
            print(f"[Moonshine] Loading model: {model_name}...")
            model = MoonshineOnnxModel(model_name=model_name)
            tokenizer = load_tokenizer()
            
            # Warmup
            dummy_audio = np.zeros((1, 16000), dtype=np.float32)
            model.generate(dummy_audio)
            
            print(f"[OK] Model {model_name} loaded successfully")
            return model, tokenizer, None
        except Exception as e:
            error_msg = f"Failed to load model {model_name}: {str(e)}"
            print(f"[FAIL] {error_msg}")
            import traceback
            traceback.print_exc()
            return None, None, error_msg
    
    async def switch_model_async(self, model_name: str):
        """Switch to a different Moonshine model asynchronously."""
        if not MOONSHINE_AVAILABLE:
            return False, "Moonshine ONNX not available"
        
        loop = asyncio.get_event_loop()
        model, tokenizer, error = await loop.run_in_executor(
            self.executor, 
            self._load_model_sync, 
            model_name
        )
        
        if model and tokenizer:
            self.model = model
            self.tokenizer = tokenizer
            self.model_name = model_name
            return True, None
        else:
            return False, error
    
    def transcribe(self, audio_data: np.ndarray) -> str:
        """Transcribe audio data to text."""
        if not self.model or not MOONSHINE_AVAILABLE:
            return ""
        
        try:
            # Check if audio has content (not silence)
            audio_power = np.sqrt(np.mean(audio_data ** 2))
            if audio_power < 0.001:  # Very quiet, likely silence
                return ""
            
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
                            
                            # Notify loading start
                            await websocket.send(json.dumps({
                                "type": "model_loading",
                                "model": model_name,
                                "progress": 0
                            }))
                            
                            # Send progress updates while loading
                            async def send_progress():
                                for progress in [10, 30, 50, 70, 90]:
                                    await asyncio.sleep(0.5)
                                    await websocket.send(json.dumps({
                                        "type": "model_loading",
                                        "model": model_name,
                                        "progress": progress
                                    }))
                            
                            # Start progress updates and model loading simultaneously
                            progress_task = asyncio.create_task(send_progress())
                            success, error = await self.transcriber.switch_model_async(model_name)
                            
                            # Cancel progress task if still running
                            try:
                                progress_task.cancel()
                                await progress_task
                            except asyncio.CancelledError:
                                pass
                            
                            if success:
                                await websocket.send(json.dumps({
                                    "type": "model_loaded",
                                    "model": model_name,
                                    "progress": 100
                                }))
                                print(f"[OK] Switched to {model_name}")
                            else:
                                await websocket.send(json.dumps({
                                    "type": "error",
                                    "message": error or f"Failed to load model {model_name}"
                                }))
                                print(f"[FAIL] Failed to switch to {model_name}: {error}")
                    except json.JSONDecodeError as e:
                        print(f"Invalid JSON: {e}")
                
                elif isinstance(message, bytes):
                    # Binary audio data
                    audio_chunk = np.frombuffer(message, dtype=np.float32)
                    audio_buffer = np.concatenate([audio_buffer, audio_chunk])
                    
                    # Limit buffer size to prevent memory issues
                    max_buffer = 16000 * 10  # 10 seconds max
                    if len(audio_buffer) > max_buffer:
                        audio_buffer = audio_buffer[-max_buffer:]
                    
                    # Transcribe when we have enough audio (2 seconds at 16kHz)
                    if len(audio_buffer) >= 32000:
                        # Transcribe
                        text = self.transcriber.transcribe(audio_buffer)
                        
                        # Keep last 0.5 seconds for context
                        audio_buffer = audio_buffer[-8000:]
                        
                        if text:
                            # Send transcription result
                            result = {
                                "segments": [{
                                    "text": text,
                                }],
                                "text": text,
                                "backend": "moonshine"
                            }
                            await websocket.send(json.dumps(result))
                            print(f"[Moonshine] >> {text[:60]}")
        
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
        print(f"  [MOON] SubtitlesForAll - Moonshine Server")
        print(f"{'='*55}")
        print(f"  Host:     {self.host}")
        print(f"  Port:     {self.port}")
        print(f"  Model:    {self.transcriber.model_name}")
        print(f"  Status:   {'Ready [OK]' if self.transcriber.model else 'Demo Mode (no transcription)'}")
        print(f"{'='*55}")
        print(f"\n  Moonshine is 5-15x FASTER than Whisper!")
        print(f"\n  Available models:")
        for name, info in MOONSHINE_MODELS.items():
            print(f"    - {name}: {info['size']} - {info['description']}")
        print(f"\n{'='*55}\n")
        
        async with websockets.serve(
            self.handle_client, 
            self.host, 
            self.port,
            ping_interval=30,
            ping_timeout=10,
            close_timeout=5
        ):
            print(f"[OK] Moonshine server running on ws://{self.host}:{self.port}")
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
