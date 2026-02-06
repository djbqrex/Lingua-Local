"""Text-to-Speech handler using Piper TTS."""

import logging
from pathlib import Path
from typing import Optional
import wave
import io

logger = logging.getLogger(__name__)


class TTSHandler:
    """Handler for text-to-speech conversion using Piper TTS."""

    def __init__(self, voice: str = "en_US-lessac-medium", model_dir: Optional[Path] = None):
        """
        Initialize the TTS handler.

        Args:
            voice: Voice model to use (format: language_code-voice-quality)
            model_dir: Directory containing Piper models
        """
        self.voice = voice
        self.model_dir = model_dir or Path(__file__).parent.parent.parent.parent / "models" / "tts"
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.voice_model = None
        self._load_model()

    def _load_model(self):
        """Load the Piper TTS model."""
        try:
            # Import piper_tts
            import subprocess
            import sys
            
            # Check if piper is available as command (for now, we'll use a fallback)
            logger.info(f"Initializing Piper TTS with voice: {self.voice}")
            
            # Note: Piper TTS is typically used as a command-line tool
            # For Python integration, we'll check if the model exists
            model_path = self.model_dir / f"{self.voice}.onnx"
            config_path = self.model_dir / f"{self.voice}.onnx.json"
            
            if not model_path.exists():
                logger.warning(f"Model not found at {model_path}. Will need to download.")
                logger.info("Piper TTS models can be downloaded from: https://github.com/rhasspy/piper/releases")
            
            self.voice_model = {
                "model_path": model_path,
                "config_path": config_path,
                "voice": self.voice
            }
            
            logger.info("Piper TTS handler initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Piper TTS: {e}")
            raise

    def synthesize(self, text: str, output_path: Optional[str] = None) -> bytes:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize
            output_path: Optional path to save audio file

        Returns:
            Audio data as bytes (WAV format)
        """
        try:
            import subprocess
            import tempfile
            
            # Use piper command line tool
            if output_path is None:
                output_path = tempfile.mktemp(suffix=".wav")
            
            model_path = self.voice_model["model_path"]
            
            if not model_path.exists():
                # Fallback: generate simple tone for testing
                logger.warning("Piper model not found. Using fallback audio generation.")
                return self._generate_fallback_audio(text)
            
            # Run piper
            cmd = [
                "piper",
                "--model", str(model_path),
                "--output_file", output_path
            ]
            
            result = subprocess.run(
                cmd,
                input=text.encode(),
                capture_output=True,
                check=True
            )
            
            # Read the generated audio
            with open(output_path, "rb") as f:
                audio_data = f.read()
            
            logger.info(f"Synthesized {len(text)} characters to audio")
            return audio_data
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Piper synthesis failed: {e}")
            # Fallback to simple audio
            return self._generate_fallback_audio(text)
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return self._generate_fallback_audio(text)

    def _generate_fallback_audio(self, text: str) -> bytes:
        """Generate a simple fallback audio (silence) for testing."""
        import numpy as np
        import soundfile as sf
        
        # Generate 1 second of silence as fallback
        sample_rate = 22050
        duration = max(0.5, len(text) * 0.1)  # Approximate duration
        samples = int(sample_rate * duration)
        
        # Generate very quiet noise instead of complete silence
        audio = np.random.randn(samples).astype(np.float32) * 0.001
        
        # Write to WAV in memory
        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format='WAV')
        buffer.seek(0)
        
        logger.info(f"Generated fallback audio: {duration:.2f}s")
        return buffer.read()

    def get_available_voices(self) -> list:
        """Get list of available voice models."""
        voices = []
        if self.model_dir.exists():
            for model_file in self.model_dir.glob("*.onnx"):
                if not model_file.name.endswith(".json"):
                    voice_name = model_file.stem
                    voices.append(voice_name)
        return voices or ["en_US-lessac-medium"]  # Default voice

    def set_voice(self, voice: str):
        """Change the active voice."""
        self.voice = voice
        self._load_model()
