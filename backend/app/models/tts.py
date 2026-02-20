"""Text-to-Speech handler using Piper TTS."""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import io

logger = logging.getLogger(__name__)


class TTSHandler:
    """Handler for text-to-speech conversion using Piper TTS."""
    DEFAULT_FALLBACK_VOICE = "en_US-lessac-medium"

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
        self.voice_models: Dict[str, Dict[str, object]] = {}
        self.voice_model = None
        self._load_model()

    def _load_model(self):
        """Load the Piper TTS model."""
        try:
            logger.info("Initializing Piper TTS with voice: %s", self.voice)
            self.voice_model = self._ensure_voice_model(self.voice)
            logger.info("Piper TTS handler initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Piper TTS: {e}")
            raise

    def _ensure_voice_model(self, voice: str) -> Dict[str, object]:
        """Ensure a voice model is available locally."""
        model_path = self.model_dir / f"{voice}.onnx"
        config_path = self.model_dir / f"{voice}.onnx.json"

        if not model_path.exists() or not config_path.exists():
            logger.info("Voice model %s not found. Attempting download...", voice)
            self._download_voice(voice)

        voice_model = {
            "model_path": model_path,
            "config_path": config_path,
            "voice": voice
        }
        self.voice_models[voice] = voice_model
        return voice_model

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
        length_scale: Optional[float] = None,
        voice: Optional[str] = None
    ) -> bytes:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize
            output_path: Optional path to save audio file
            length_scale: Optional Piper length scale (higher = slower)
            voice: Optional voice id override for this utterance

        Returns:
            Audio data as bytes (WAV format)
        """
        created_temp_file = False
        synth_output_path = output_path

        try:
            import subprocess
            import tempfile

            active_voice = voice or self.voice
            voice_model = self._ensure_voice_model(active_voice)

            # Use piper command line tool
            if synth_output_path is None:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                synth_output_path = temp_file.name
                temp_file.close()
                created_temp_file = True

            model_path = voice_model["model_path"]
            config_path = voice_model["config_path"]

            if not model_path.exists() or not config_path.exists():
                logger.warning("Voice model %s unavailable, using fallback audio", active_voice)
                return self._generate_fallback_audio(text)

            # Run piper
            cmd = [
                "piper",
                "--model", str(model_path),
                "--output_file", synth_output_path
            ]
            if length_scale and length_scale > 0:
                cmd.extend(["--length_scale", f"{length_scale:.2f}"])

            subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                capture_output=True,
                check=True
            )

            # Read the generated audio
            with open(synth_output_path, "rb") as f:
                audio_data = f.read()

            logger.info(
                "Synthesized %s characters with voice %s",
                len(text),
                active_voice,
            )
            return audio_data

        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode(errors="ignore") if e.stderr else ""
            logger.error("Piper synthesis failed: %s; stderr=%s", e, stderr)
            return self._generate_fallback_audio(text, length_scale)
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return self._generate_fallback_audio(text, length_scale)
        finally:
            if synth_output_path and created_temp_file:
                Path(synth_output_path).unlink(missing_ok=True)

    def synthesize_segments(
        self,
        segments: List[Dict[str, str]],
        voice_for_language: Dict[str, str],
        length_scale: Optional[float] = None,
    ) -> bytes:
        """
        Synthesize multiple segments with language-specific voices.

        Args:
            segments: List of {"text": str, "language": str}
            voice_for_language: Mapping from language code to Piper voice id
            length_scale: Optional Piper length scale (higher = slower)
        """
        import numpy as np
        from ..utils.audio import AudioProcessor

        if not segments:
            return self._generate_fallback_audio("")

        target_sample_rate = 22050
        pause = np.zeros(int(target_sample_rate * 0.16), dtype=np.float32)
        rendered_audio: List[np.ndarray] = []

        for segment in segments:
            segment_text = (segment.get("text") or "").strip()
            segment_language = (segment.get("language") or "").lower()
            if not segment_text:
                continue

            chosen_voice = voice_for_language.get(segment_language, self.voice)
            chunk_bytes = self.synthesize(
                text=segment_text,
                length_scale=length_scale,
                voice=chosen_voice,
            )
            chunk_audio = AudioProcessor.bytes_to_audio(
                audio_bytes=chunk_bytes,
                sample_rate=target_sample_rate,
            )
            if chunk_audio.size == 0:
                continue
            rendered_audio.append(chunk_audio.astype(np.float32))

        if not rendered_audio:
            return self._generate_fallback_audio("")

        merged_chunks: List[np.ndarray] = []
        for index, chunk in enumerate(rendered_audio):
            if index > 0:
                merged_chunks.append(pause)
            merged_chunks.append(chunk)

        combined = np.concatenate(merged_chunks)
        combined = AudioProcessor.normalize_audio(combined, target_level=0.9)
        return AudioProcessor.audio_to_bytes(combined, sample_rate=target_sample_rate, format="WAV")

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
        return voices or [self.DEFAULT_FALLBACK_VOICE]

    def set_voice(self, voice: str):
        """Change the active voice."""
        self.voice = voice
        self.voice_model = self._ensure_voice_model(voice)
