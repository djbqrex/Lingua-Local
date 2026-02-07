"""Utility for downloading missing models during startup."""

import logging
import urllib.request
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ModelDownloader:
    """Handles downloading models from various sources."""

    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.stt_dir = models_dir / "stt"
        self.tts_dir = models_dir / "tts"
        self.llm_dir = models_dir / "llm"

        # Create directories
        self.stt_dir.mkdir(parents=True, exist_ok=True)
        self.tts_dir.mkdir(parents=True, exist_ok=True)
        self.llm_dir.mkdir(parents=True, exist_ok=True)

    def download_file(self, url: str, dest_path: Path, desc: str = "Downloading") -> bool:
        """Download a file with progress logging."""
        logger.info(f"Downloading {desc}...")
        logger.info(f"URL: {url}")
        logger.info(f"Destination: {dest_path}")

        try:
            # Create parent directory if it doesn't exist
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Download file
            def update_progress(block_count, block_size, total_size):
                if total_size > 0:
                    percent = min(100, (block_count * block_size * 100) // total_size)
                    if block_count % 100 == 0:  # Log every 100 blocks to avoid spam
                        logger.info(f"Download progress: {percent}%")

            urllib.request.urlretrieve(url, dest_path, reporthook=update_progress)
            logger.info(f"✓ Downloaded {desc}")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to download {desc}: {e}")
            return False

    def download_piper_voice(self, voice: str = "en_US-lessac-medium") -> bool:
        """Download Piper TTS voice model."""
        logger.info(f"📥 Checking Piper voice: {voice}...")

        # Piper voices are hosted on Hugging Face; GitHub releases are fallback
        hf_base = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
        github_bases = [
            "https://github.com/rhasspy/piper/releases/download/v1.2.0",
            "https://github.com/rhasspy/piper/releases/download/v1.1.1",
            "https://github.com/rhasspy/piper/releases/download/v1.1.0"
        ]

        model_file = f"{voice}.onnx"
        config_file = f"{voice}.onnx.json"

        # Check if model already exists
        model_path = self.tts_dir / model_file
        config_path = self.tts_dir / config_file
        
        if model_path.exists() and config_path.exists():
            logger.info(f"✓ Piper voice {voice} already exists")
            return True

        # Build Hugging Face URLs
        hf_urls = []
        try:
            parts = voice.split("-")
            if len(parts) < 3:
                raise ValueError("Invalid voice format")
            locale = parts[0]
            quality = parts[-1]
            voice_name = "-".join(parts[1:-1])
            language = locale.split("_")[0]
            hf_prefix = f"{hf_base}/{language}/{locale}/{voice_name}/{quality}"
            hf_urls = [
                f"{hf_prefix}/{model_file}",
                f"{hf_prefix}/{config_file}"
            ]
        except Exception as e:
            logger.warning(f"Could not parse voice '{voice}' for Hugging Face URLs: {e}")

        # Download model file - try Hugging Face, then GitHub
        model_downloaded = False
        if not model_path.exists():
            logger.info(f"Downloading Piper model {voice}...")
            url_candidates = []
            if hf_urls:
                url_candidates.append(hf_urls[0])
            url_candidates.extend([f"{base}/{model_file}" for base in github_bases])
            for model_url in url_candidates:
                logger.info(f"Trying URL: {model_url}")
                if self.download_file(model_url, model_path, f"Piper model {voice}"):
                    model_downloaded = True
                    break
            if not model_downloaded:
                logger.warning(f"⚠ Failed to download Piper model from all URLs. Will use fallback TTS.")
                return False
        else:
            logger.info(f"✓ Model already exists: {model_file}")
            model_downloaded = True

        # Download config file - try Hugging Face, then GitHub
        config_downloaded = False
        if not config_path.exists():
            logger.info(f"Downloading Piper config {voice}...")
            url_candidates = []
            if hf_urls:
                url_candidates.append(hf_urls[1])
            url_candidates.extend([f"{base}/{config_file}" for base in github_bases])
            for config_url in url_candidates:
                logger.info(f"Trying URL: {config_url}")
                if self.download_file(config_url, config_path, f"Piper config {voice}"):
                    config_downloaded = True
                    break
            if not config_downloaded:
                logger.warning(f"⚠ Failed to download Piper config from all URLs. Will use fallback TTS.")
                # Clean up partial download
                if model_path.exists() and not config_path.exists():
                    model_path.unlink(missing_ok=True)
                return False
        else:
            logger.info(f"✓ Config already exists: {config_file}")
            config_downloaded = True

        logger.info(f"✓ Piper voice {voice} ready")
        return True

    def download_llm_model(self, model_name: str = "qwen2.5-1.5b-instruct") -> bool:
        """Download LLM model in GGUF format."""
        logger.info(f"📥 Checking LLM model: {model_name}...")

        # Model URLs from Hugging Face
        model_urls = {
            "qwen2.5-0.5b-instruct": {
                "repo": "Qwen/Qwen2.5-0.5B-Instruct-GGUF",
                "file": "qwen2.5-0.5b-instruct-q4_k_m.gguf"
            },
            "qwen2.5-1.5b-instruct": {
                "repo": "Qwen/Qwen2.5-1.5B-Instruct-GGUF",
                "file": "qwen2.5-1.5b-instruct-q4_k_m.gguf"
            },
            "qwen2.5-3b-instruct": {
                "repo": "Qwen/Qwen2.5-3B-Instruct-GGUF",
                "file": "qwen2.5-3b-instruct-q4_k_m.gguf"
            }
        }

        if model_name not in model_urls:
            logger.warning(f"⚠ Unknown model: {model_name}")
            logger.info(f"Available models: {', '.join(model_urls.keys())}")
            logger.info("\nTo download models manually:")
            logger.info("1. Visit https://huggingface.co/models?library=gguf")
            logger.info("2. Search for your preferred model (e.g., Qwen, Llama)")
            logger.info(f"3. Download the GGUF file to: {self.llm_dir}")
            return False

        model_info = model_urls[model_name]
        repo = model_info["repo"]
        filename = model_info["file"]

        # Construct Hugging Face URL
        url = f"https://huggingface.co/{repo}/resolve/main/{filename}"
        dest_path = self.llm_dir / filename

        if dest_path.exists():
            logger.info(f"✓ LLM model {model_name} already exists")
            return True

        logger.info(f"\n⚠ Note: LLM models are large (1-4GB). This may take a while.")
        logger.info(f"You can also download manually from: https://huggingface.co/{repo}")
        
        success = self.download_file(url, dest_path, f"LLM {model_name}")
        
        if success:
            logger.info(f"✓ LLM model {model_name} ready")
        else:
            logger.warning(f"\n⚠ Automatic download failed. Please download manually:")
            logger.warning(f"1. Visit: https://huggingface.co/{repo}")
            logger.warning(f"2. Download: {filename}")
            logger.warning(f"3. Place in: {self.llm_dir}")

        return success

    def ensure_models(self, llm_model: str, tts_voice: str, download_all_tts: bool = False) -> dict:
        """
        Ensure required models are downloaded.
        Returns dict with download status for each model type.
        
        Args:
            llm_model: LLM model name to check/download
            tts_voice: Default TTS voice to check/download
            download_all_tts: If True, download TTS voices for all supported languages
        """
        results = {
            "llm": False,
            "tts": False,
            "tts_voices": {}
        }

        # Check and download LLM model
        logger.info("Checking LLM model...")
        llm_files = list(self.llm_dir.glob("*.gguf"))
        if not llm_files:
            logger.info("LLM model not found. Downloading...")
            results["llm"] = self.download_llm_model(llm_model)
        else:
            logger.info(f"✓ LLM model found: {llm_files[0].name}")
            results["llm"] = True

        # Check and download TTS models
        if download_all_tts:
            # Download voices for all supported languages
            from .language import LanguageHelper
            logger.info("Checking TTS voices for all supported languages...")
            for lang_code, voices in LanguageHelper.TTS_VOICES.items():
                if voices:
                    voice = voices[0]  # Use first voice for each language
                    model_path = self.tts_dir / f"{voice}.onnx"
                    config_path = self.tts_dir / f"{voice}.onnx.json"
                    if not (model_path.exists() and config_path.exists()):
                        logger.info(f"Downloading TTS voice for {lang_code}: {voice}...")
                        results["tts_voices"][voice] = self.download_piper_voice(voice)
                    else:
                        logger.info(f"✓ TTS voice found for {lang_code}: {voice}")
                        results["tts_voices"][voice] = True
        else:
            # Only check/download default voice
            logger.info("Checking default TTS model...")
            model_path = self.tts_dir / f"{tts_voice}.onnx"
            config_path = self.tts_dir / f"{tts_voice}.onnx.json"
            if not (model_path.exists() and config_path.exists()):
                logger.info("TTS model not found. Downloading...")
                results["tts"] = self.download_piper_voice(tts_voice)
            else:
                logger.info(f"✓ TTS model found: {tts_voice}")
                results["tts"] = True
            logger.info("Note: Other TTS voices will be downloaded on-demand when needed.")

        return results

