"""
WhisperLive-Compatible WebSocket Server for SubtitlesForAll

This server provides a WebSocket interface that's compatible with the WhisperLive protocol,
but uses whisper.cpp for transcription. It accepts audio chunks via WebSocket and returns
transcription results in real-time.

Usage:
    python run_server.py --port 9090 --model path/to/ggml-model.bin

Requirements:
    pip install websockets numpy

Make sure whisper.cpp is built and the whisper-server binary is available.
"""

import asyncio
import json
import struct
import subprocess
import tempfile
import wave
import os
import sys
import argparse
from pathlib import Path

try:
    import websockets
    import numpy as np
except ImportError:
    print("Please install required packages: pip install websockets numpy")
    sys.exit(1)

# Default configuration
DEFAULT_PORT = 9090
DEFAULT_HOST = "0.0.0.0"
DEFAULT_MODEL = "models/ggml-base.en.bin"

# Find whisper-server binary
def find_whisper_server():
    """Find the whisper-server binary in common locations."""
    possible_paths = [
        Path(__file__).parent.parent / "build" / "bin" / "whisper-server",
        Path(__file__).parent.parent / "build" / "bin" / "whisper-server.exe",
        Path(__file__).parent.parent / "build" / "Release" / "whisper-server.exe",
        Path(__file__).parent.parent / "main",
        Path(__file__).parent.parent / "main.exe",
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    return None


class WhisperTranscriber:
    """Handles audio transcription using whisper.cpp HTTP server or CLI."""
    
    def __init__(self, model_path: str, server_url: str = None):
        self.model_path = model_path
        self.server_url = server_url or "http://127.0.0.1:8080"
        self.audio_buffer = []
        self.sample_rate = 16000
        self.min_audio_length = 1.0  # Minimum seconds of audio before processing
        self.current_model_name = None
        
    def set_model(self, model_name: str) -> str:
        """Change the model and return the full path."""
        # Map model names to file paths
        base_path = Path(__file__).parent.parent / "models"
        
        # Handle quantized models with special naming
        if model_name == "tiny-q5_1":
            model_file = "ggml-tiny-q5_1.bin"
        elif model_name == "base-q5_1":
            model_file = "ggml-base-q5_1.bin"
        else:
            model_file = f"ggml-{model_name}.bin"
        
        model_path = base_path / model_file
        
        if model_path.exists():
            self.model_path = str(model_path)
            self.current_model_name = model_name
            print(f"✓ Model set to: {model_file}")
            return str(model_path)
        else:
            print(f"⚠ Model file not found: {model_path}, using default")
        
        # Fallback to default
        return self.model_path
        
    async def transcribe_audio(self, audio_data: np.ndarray) -> str:
        """Transcribe audio using whisper.cpp server."""
        try:
            # Save audio to temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
                
            # Write WAV file
            with wave.open(temp_path, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                
                # Convert float32 to int16
                audio_int16 = (audio_data * 32767).astype(np.int16)
                wav_file.writeframes(audio_int16.tobytes())
            
            # Try to use the HTTP server first
            try:
                import urllib.request
                import urllib.parse
                
                with open(temp_path, 'rb') as f:
                    audio_bytes = f.read()
                
                # Create multipart form data
                boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
                body = (
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="file"; filename="audio.wav"\r\n'
                    f"Content-Type: audio/wav\r\n\r\n"
                ).encode() + audio_bytes + (
                    f"\r\n--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="response_format"\r\n\r\n'
                    f"json\r\n"
                    f"--{boundary}--\r\n"
                ).encode()
                
                req = urllib.request.Request(
                    f"{self.server_url}/inference",
                    data=body,
                    headers={
                        "Content-Type": f"multipart/form-data; boundary={boundary}"
                    }
                )
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    result = json.loads(response.read().decode())
                    return result.get("text", "")
                    
            except Exception as e:
                print(f"HTTP server not available, using CLI: {e}")
                # Fallback to CLI
                return await self._transcribe_cli(temp_path)
                
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
    
    async def _transcribe_cli(self, audio_path: str) -> str:
        """Transcribe using whisper.cpp CLI."""
        whisper_bin = find_whisper_server()
        if not whisper_bin:
            # Try using main binary instead
            main_paths = [
                Path(__file__).parent.parent / "main",
                Path(__file__).parent.parent / "main.exe",
                Path(__file__).parent.parent / "build" / "bin" / "main",
                Path(__file__).parent.parent / "build" / "bin" / "main.exe",
            ]
            for p in main_paths:
                if p.exists():
                    whisper_bin = str(p)
                    break
        
        if not whisper_bin:
            return ""
        
        cmd = [
            whisper_bin,
            "-m", self.model_path,
            "-f", audio_path,
            "-nt",  # No timestamps
            "-np",  # No progress
        ]
        
        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            return stdout.decode().strip()
        except Exception as e:
            print(f"CLI transcription error: {e}")
            return ""


class WebSocketServer:
    """WebSocket server that accepts audio and returns transcriptions."""
    
    def __init__(self, host: str, port: int, model_path: str):
        self.host = host
        self.port = port
        self.transcriber = WhisperTranscriber(model_path)
        self.clients = set()
        
    async def handle_client(self, websocket):
        """Handle a WebSocket client connection."""
        client_id = id(websocket)
        self.clients.add(websocket)
        print(f"Client {client_id} connected. Total clients: {len(self.clients)}")
        
        audio_buffer = []
        config = {}
        current_model = None
        
        try:
            # Send server ready message
            await websocket.send(json.dumps({
                "message": "SERVER_READY",
                "status": "ready"
            }))
            
            async for message in websocket:
                if isinstance(message, str):
                    # JSON configuration message
                    try:
                        config = json.loads(message)
                        print(f"Client {client_id} config: {config}")
                        
                        # Handle model change request
                        if 'model' in config and config['model'] != current_model:
                            requested_model = config['model']
                            print(f"Client {client_id} requesting model change to: {requested_model}")
                            
                            # Notify client that model is loading
                            await websocket.send(json.dumps({
                                "type": "model_loading",
                                "model": requested_model,
                                "progress": 0
                            }))
                            
                            # Simulate loading progress (in real scenario, this would track actual model load)
                            for progress in [20, 40, 60, 80]:
                                await asyncio.sleep(0.2)
                                await websocket.send(json.dumps({
                                    "type": "model_loading",
                                    "model": requested_model,
                                    "progress": progress
                                }))
                            
                            # Change the model
                            new_model_path = self.transcriber.set_model(requested_model)
                            current_model = requested_model
                            print(f"Model changed to: {new_model_path}")
                            
                            # Notify client that model is ready
                            await websocket.send(json.dumps({
                                "type": "model_ready",
                                "model": requested_model,
                                "progress": 100
                            }))
                            
                    except json.JSONDecodeError:
                        pass
                        
                elif isinstance(message, bytes):
                    # Binary audio data (Float32Array)
                    try:
                        # Parse as float32 array
                        audio_chunk = np.frombuffer(message, dtype=np.float32)
                        audio_buffer.append(audio_chunk)
                        
                        # Process when we have enough audio
                        total_samples = sum(len(chunk) for chunk in audio_buffer)
                        duration = total_samples / 16000  # Assuming 16kHz
                        
                        if duration >= 2.0:  # Process every 2 seconds
                            # Combine all audio chunks
                            full_audio = np.concatenate(audio_buffer)
                            
                            # Transcribe
                            text = await self.transcriber.transcribe_audio(full_audio)
                            
                            if text.strip():
                                # Send transcription result
                                result = {
                                    "segments": [
                                        {
                                            "id": 0,
                                            "text": text.strip(),
                                            "start": 0,
                                            "end": duration
                                        }
                                    ]
                                }
                                await websocket.send(json.dumps(result))
                            
                            # Keep last 0.5 seconds for context overlap
                            keep_samples = int(16000 * 0.5)
                            if len(full_audio) > keep_samples:
                                audio_buffer = [full_audio[-keep_samples:]]
                            else:
                                audio_buffer = []
                                
                    except Exception as e:
                        print(f"Error processing audio: {e}")
                        
        except websockets.exceptions.ConnectionClosed:
            print(f"Client {client_id} disconnected")
        except Exception as e:
            print(f"Error with client {client_id}: {e}")
        finally:
            self.clients.discard(websocket)
            print(f"Client {client_id} removed. Total clients: {len(self.clients)}")
    
    async def start(self):
        """Start the WebSocket server."""
        print(f"Starting WhisperLive-compatible server on ws://{self.host}:{self.port}")
        print(f"Using model: {self.transcriber.model_path}")
        
        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10,
            max_size=10 * 1024 * 1024  # 10MB max message size
        ):
            print("Server started. Waiting for connections...")
            await asyncio.Future()  # Run forever


def main():
    parser = argparse.ArgumentParser(description="WhisperLive-compatible WebSocket server")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host to bind to")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen on")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL, help="Path to whisper.cpp model")
    parser.add_argument("--backend", default="whisper_cpp", help="Backend to use (ignored, always uses whisper.cpp)")
    
    args = parser.parse_args()
    
    # Check if model exists
    model_path = Path(args.model)
    if not model_path.is_absolute():
        model_path = Path(__file__).parent.parent / args.model
    
    if not model_path.exists():
        print(f"Warning: Model not found at {model_path}")
        print("Please download a model using: ./models/download-ggml-model.sh base.en")
    
    server = WebSocketServer(args.host, args.port, str(model_path))
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
