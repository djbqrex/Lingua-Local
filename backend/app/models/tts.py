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
            
            if not model_path.exists() or not config_path.exists():
                logger.info(f"Model not found at {model_path}. Attempting to download...")
                # Try to download the voice model
                self._download_voice(self.voice)
                # Re-check after download attempt
                if not model_path.exists() or not config_path.exists():
                    logger.warning(f"Model still not found after download attempt. Will use fallback.")
            
            self.voice_model = {
                "model_path": model_path,
                "config_path": config_path,
                "voice": self.voice
            }
            
            logger.info("Piper TTS handler initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Piper TTS: {e}")
            raise
    
    def _download_voice(self, voice: str) -> bool:
        """Download a Piper TTS voice model."""
        try:
            from ..utils.model_downloader import ModelDownloader
            # self.model_dir is models/tts, so parent is models/
            models_dir = self.model_dir.parent
            downloader = ModelDownloader(models_dir)
            return downloader.download_piper_voice(voice)
        except Exception as e:
            logger.error(f"Failed to download voice {voice}: {e}")
            return False

    def synthesize(
        self,
        text: str,
        output_path: Optional[str] = None,
        length_scale: Optional[float] = None
    ) -> bytes:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize
            output_path: Optional path to save audio file
            length_scale: Optional Piper length scale (higher = slower)

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
            config_path = self.voice_model["config_path"]
            
            if not model_path.exists() or not config_path.exists():
                # Try to download the voice model first
                logger.info(f"Voice model {self.voice} not found. Attempting to download...")
                if self._download_voice(self.voice):
                    # Reload model info after download
                    model_path = self.model_dir / f"{self.voice}.onnx"
                    config_path = self.model_dir / f"{self.voice}.onnx.json"
                    self.voice_model["model_path"] = model_path
                    self.voice_model["config_path"] = config_path
                
                # If still not found after download attempt, use fallback
                if not model_path.exists() or not config_path.exists():
                    logger.warning("Piper model not found after download attempt. Using fallback audio generation.")
                    return self._generate_fallback_audio(text)
            
            # Run piper
            cmd = [
                "piper",
                "--model", str(model_path),
                "--output_file", output_path
            ]
            if length_scale and length_scale > 0:
                cmd.extend(["--length_scale", f"{length_scale:.2f}"])
            
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
            return self._generate_fallback_audio(text, length_scale)
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return self._generate_fallback_audio(text, length_scale)

    def _generate_fallback_audio(self, text: str, length_scale: Optional[float] = None) -> bytes:
        """Generate a simple fallback audio (silence) for testing."""
        import numpy as np
        import soundfile as sf
        
        # Generate an audible sine tone as fallback
        sample_rate = 22050
        scale = length_scale if length_scale and length_scale > 0 else 1.0
        duration = max(0.5, len(text) * 0.08 * scale)  # Approximate duration
        samples = int(sample_rate * duration)

        t = np.linspace(0, duration, samples, endpoint=False)
        frequency = 440.0  # A4 tone
        audio = 0.15 * np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
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
