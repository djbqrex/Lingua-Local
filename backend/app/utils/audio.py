"""Audio processing utilities."""

import logging
import io
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Utility class for audio processing operations."""

    @staticmethod
    def load_audio(file_path: str, target_sr: int = 16000) -> Tuple[np.ndarray, int]:
        """
        Load audio file and resample if needed.

        Args:
            file_path: Path to audio file
            target_sr: Target sample rate

        Returns:
            Tuple of (audio_array, sample_rate)
        """
        try:
            audio, sr = sf.read(file_path)
            
            # Convert stereo to mono
            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)
            
            # Resample if needed
            if sr != target_sr:
                audio = AudioProcessor.resample(audio, sr, target_sr)
                sr = target_sr
            
            return audio, sr
            
        except Exception as e:
            logger.error(f"Failed to load audio: {e}")
            raise

    @staticmethod
    def resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """
        Resample audio to target sample rate.

        Args:
            audio: Audio array
            orig_sr: Original sample rate
            target_sr: Target sample rate

        Returns:
            Resampled audio array
        """
        if orig_sr == target_sr:
            return audio
        
        try:
            from scipy import signal
            
            # Calculate resampling ratio
            ratio = target_sr / orig_sr
            n_samples = int(len(audio) * ratio)
            
            # Resample
            resampled = signal.resample(audio, n_samples)
            return resampled.astype(np.float32)
            
        except ImportError:
            # Fallback to simple linear interpolation
            logger.warning("scipy not available, using simple resampling")
            return AudioProcessor._simple_resample(audio, orig_sr, target_sr)

    @staticmethod
    def _simple_resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Simple resampling using linear interpolation."""
        ratio = target_sr / orig_sr
        n_samples = int(len(audio) * ratio)
        
        old_indices = np.arange(len(audio))
        new_indices = np.linspace(0, len(audio) - 1, n_samples)
        
        resampled = np.interp(new_indices, old_indices, audio)
        return resampled.astype(np.float32)

    @staticmethod
    def save_audio(
        audio: np.ndarray,
        file_path: str,
        sample_rate: int = 22050,
        format: str = "WAV"
    ):
        """
        Save audio array to file.

        Args:
            audio: Audio array
            file_path: Output file path
            sample_rate: Sample rate
            format: Audio format
        """
        try:
            sf.write(file_path, audio, sample_rate, format=format)
            logger.info(f"Saved audio to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
            raise

    @staticmethod
    def bytes_to_audio(audio_bytes: bytes, sample_rate: int = 16000) -> np.ndarray:
        """
        Convert audio bytes to numpy array.

        Args:
            audio_bytes: Audio data as bytes
            sample_rate: Expected sample rate

        Returns:
            Audio as numpy array
        """
        try:
            buffer = io.BytesIO(audio_bytes)
            audio, sr = sf.read(buffer)
            
            # Convert stereo to mono
            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)
            
            # Resample if needed
            if sr != sample_rate:
                audio = AudioProcessor.resample(audio, sr, sample_rate)
            
            return audio.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Failed to convert bytes to audio: {e}")
            raise

    @staticmethod
    def audio_to_bytes(
        audio: np.ndarray,
        sample_rate: int = 22050,
        format: str = "WAV"
    ) -> bytes:
        """
        Convert audio array to bytes.

        Args:
            audio: Audio array
            sample_rate: Sample rate
            format: Audio format

        Returns:
            Audio as bytes
        """
        try:
            buffer = io.BytesIO()
            sf.write(buffer, audio, sample_rate, format=format)
            buffer.seek(0)
            return buffer.read()
        except Exception as e:
            logger.error(f"Failed to convert audio to bytes: {e}")
            raise

    @staticmethod
    def normalize_audio(audio: np.ndarray, target_level: float = 0.95) -> np.ndarray:
        """
        Normalize audio to target level.

        Args:
            audio: Audio array
            target_level: Target peak level (0-1)

        Returns:
            Normalized audio
        """
        max_val = np.abs(audio).max()
        if max_val > 0:
            audio = audio * (target_level / max_val)
        return audio

    @staticmethod
    def trim_silence(
        audio: np.ndarray,
        sample_rate: int,
        threshold: float = 0.01,
        min_silence_duration: float = 0.5
    ) -> np.ndarray:
        """
        Trim silence from beginning and end of audio.

        Args:
            audio: Audio array
            sample_rate: Sample rate
            threshold: Amplitude threshold for silence
            min_silence_duration: Minimum duration of silence to trim (seconds)

        Returns:
            Trimmed audio
        """
        # Find non-silent regions
        non_silent = np.abs(audio) > threshold
        
        # Find first and last non-silent sample
        non_silent_indices = np.where(non_silent)[0]
        
        if len(non_silent_indices) == 0:
            return audio  # All silence, return as is
        
        start_idx = non_silent_indices[0]
        end_idx = non_silent_indices[-1] + 1
        
        return audio[start_idx:end_idx]
