"""
Simple Python WebSocket Server for SubtitlesForAll
This version uses faster-whisper for real-time transcription
"""

import asyncio
import json
import struct
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
    subprocess.check_call(["pip", "install", "websockets", "numpy", "faster-whisper"])
    import websockets
    import numpy as np

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    print("faster-whisper not available, transcription will be simulated")

class SimpleTranscriptionServer:
    def __init__(self, host="0.0.0.0", port=9090, model_size="base"):
        self.host = host
        self.port = port
        self.model_size = model_size
        self.model = None
        
        if FASTER_WHISPER_AVAILABLE:
            print(f"Loading Whisper model: {model_size}...")
            try:
                self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
                print("Model loaded successfully!")
            except Exception as e:
                print(f"Failed to load model: {e}")
                print("Transcription will be simulated")
        
    def transcribe_audio(self, audio_data, language="en"):
        """Transcribe audio data to text"""
        if not self.model or not FASTER_WHISPER_AVAILABLE:
            # Simulate transcription for demo
            return "This is a test subtitle. Please install faster-whisper for real transcription."
        
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
                
                # Write WAV file
                with wave.open(temp_path, 'wb') as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(16000)
                    wav.writeframes(audio_data.tobytes())
            
            # Transcribe
            segments, _ = self.model.transcribe(temp_path, language=language, beam_size=1)
            text = " ".join([segment.text for segment in segments])
            
            # Cleanup
            os.unlink(temp_path)
            
            return text.strip()
            
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""
    
    async def handle_client(self, websocket):
        """Handle WebSocket client connection"""
        print(f"Client connected from {websocket.remote_address}")
        
        # Send ready message (compatible with client expectations)
        ready_msg = json.dumps({"message": "SERVER_READY", "status": "ready"})
        await websocket.send(ready_msg)
        
        audio_buffer = np.array([], dtype=np.float32)
        config = {"language": "en"}
        
        try:
            async for message in websocket:
                if isinstance(message, str):
                    # JSON configuration message
                    try:
                        data = json.loads(message)
                        if "language" in data:
                            config["language"] = data["language"]
                        print(f"Config received: {config}")
                    except json.JSONDecodeError:
                        pass
                        
                elif isinstance(message, bytes):
                    # Binary audio data
                    print(f"Received audio chunk: {len(message)} bytes")
                    audio_chunk = np.frombuffer(message, dtype=np.float32)
                    audio_buffer = np.concatenate([audio_buffer, audio_chunk])
                    print(f"Buffer size: {len(audio_buffer)} samples ({len(audio_buffer)/16000:.2f} seconds)")
                    
                    # Transcribe when we have enough audio (2 seconds at 16kHz)
                    if len(audio_buffer) >= 32000:
                        print("Transcribing audio...")
                        # Convert to int16
                        audio_int16 = (audio_buffer * 32767).astype(np.int16)
                        
                        # Transcribe
                        text = self.transcribe_audio(audio_int16, config["language"])
                        print(f"Transcription result: '{text}'")
                        
                        if text:
                            # Send transcription result
                            result = {
                                "type": "TRANSCRIPTION",
                                "segments": [
                                    {
                                        "text": text,
                                        "start": 0,
                                        "end": len(audio_buffer) / 16000
                                    }
                                ]
                            }
                            await websocket.send(json.dumps(result))
                            print(f"Transcribed: {text}")
                        
                        # Keep last 0.5 seconds for context
                        audio_buffer = audio_buffer[-8000:]
                        
        except websockets.exceptions.ConnectionClosed:
            print(f"Client disconnected")
        except Exception as e:
            print(f"Error handling client: {e}")
    
    async def start(self):
        """Start the WebSocket server"""
        print(f"\n{'='*50}")
        print(f"SubtitlesForAll Transcription Server")
        print(f"{'='*50}")
        print(f"Host: {self.host}")
        print(f"Port: {self.port}")
        print(f"Model: {self.model_size}")
        print(f"Status: {'Ready' if self.model else 'Demo Mode (no transcription)'}")
        print(f"{'='*50}\n")
        
        async with websockets.serve(self.handle_client, self.host, self.port):
            print(f"✓ Server running on ws://{self.host}:{self.port}")
            print("Waiting for connections...\n")
            await asyncio.Future()  # Run forever

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Simple Transcription Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9090, help="Port to listen on")
    parser.add_argument("--model", default="base", 
                        help="Whisper model size (tiny, base, base-q5_1, small, medium, large)")
    
    args = parser.parse_args()
    
    # Handle quantized model names - map to corresponding base model for faster-whisper
    model_name = args.model
    if model_name == "tiny-q5_1":
        print("Note: Quantized tiny model uses tiny model with faster-whisper")
        model_name = "tiny"
    elif model_name == "base-q5_1":
        print("Note: Quantized base model uses base model with faster-whisper")
        model_name = "base"
    
    args.model = model_name
    
    server = SimpleTranscriptionServer(args.host, args.port, args.model)
    asyncio.run(server.start())

if __name__ == "__main__":
    main()
