"""Speech-to-Text handler using Faster-Whisper."""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class STTHandler:
    """Handler for speech-to-text conversion using Faster-Whisper."""

    def __init__(self, model_size: str = "small", device: str = "auto", compute_type: str = "float16"):
        """
        Initialize the STT handler.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large-v3)
            device: Device to use (cuda, cpu, or auto)
            compute_type: Compute type (float16, int8, float32)
        """
        self.model_size = model_size
        self.device = self._get_device(device)
        self.compute_type = compute_type if self.device == "cuda" else "int8"
        self.model = None
        self._load_model()

    def _get_device(self, device: str) -> str:
        """Determine the device to use."""
        if device == "auto":
            try:
                import torch
                return "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                return "cpu"
        return device

    def _load_model(self):
        """Load the Faster-Whisper model."""
        try:
            from faster_whisper import WhisperModel
            
            logger.info(f"Loading Whisper model: {self.model_size} on {self.device}")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root=str(Path(__file__).parent.parent.parent.parent / "models" / "stt")
            )
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text.

        Args:
            audio_path: Path to audio file
            language: Target language code (e.g., 'en', 'es', 'fr')
            task: Task type ('transcribe' or 'translate')

        Returns:
            Dictionary containing transcription results
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")

        try:
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                task=task,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )

            # Collect all segments
            transcription = []
            full_text = []
            
            for segment in segments:
                transcription.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                })
                full_text.append(segment.text.strip())

            result = {
                "text": " ".join(full_text),
                "language": info.language,
                "language_probability": info.language_probability,
                "segments": transcription,
                "duration": info.duration
            }

            logger.info(f"Transcribed {len(transcription)} segments, detected language: {info.language}")
            return result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def transcribe_numpy(
        self,
        audio_array: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio from numpy array.

        Args:
            audio_array: Audio data as numpy array
            sample_rate: Sample rate of audio
            language: Target language code

        Returns:
            Dictionary containing transcription results
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")

        try:
            # Faster-Whisper expects audio as float32 normalized to [-1, 1]
            if audio_array.dtype != np.float32:
                audio_array = audio_array.astype(np.float32)
            
            # Normalize if needed
            if audio_array.max() > 1.0 or audio_array.min() < -1.0:
                audio_array = audio_array / np.abs(audio_array).max()

            segments, info = self.model.transcribe(
                audio_array,
                language=language,
                beam_size=5,
                vad_filter=True
            )

            transcription = []
            full_text = []
            
            for segment in segments:
                transcription.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                })
                full_text.append(segment.text.strip())

            result = {
                "text": " ".join(full_text),
                "language": info.language,
                "language_probability": info.language_probability,
                "segments": transcription
            }

            return result

        except Exception as e:
            logger.error(f"Transcription from numpy array failed: {e}")
            raise
