#!/usr/bin/env python3
"""
Model download script for Language Learning Assistant.

This script downloads the required models for STT, TTS, and LLM.
"""

import os
import sys
import argparse
from pathlib import Path
import urllib.request
import json
from tqdm import tqdm


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

    def download_file(self, url: str, dest_path: Path, desc: str = "Downloading"):
        """Download a file with progress bar."""
        print(f"Downloading {desc}...")
        print(f"URL: {url}")
        print(f"Destination: {dest_path}")

        try:
            # Create parent directory if it doesn't exist
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Download with progress bar
            with tqdm(unit='B', unit_scale=True, unit_divisor=1024) as pbar:
                def update_progress(block_count, block_size, total_size):
                    if pbar.total is None and total_size > 0:
                        pbar.total = total_size
                    pbar.update(block_size)

                urllib.request.urlretrieve(url, dest_path, reporthook=update_progress)

            print(f"✓ Downloaded {desc}")
            return True

        except Exception as e:
            print(f"✗ Failed to download {desc}: {e}")
            return False

    def download_whisper_models(self, model_size: str = "small"):
        """
        Download Faster-Whisper models.
        Note: Faster-Whisper downloads models automatically on first use.
        """
        print(f"\n📥 Preparing Whisper model ({model_size})...")
        print("Faster-Whisper will download the model automatically on first use.")
        print(f"Model will be cached in: {self.stt_dir}")
        
        # Create a marker file
        marker = self.stt_dir / f".{model_size}_ready"
        marker.write_text(f"Whisper {model_size} model will be downloaded on first use")
        
        print(f"✓ Whisper {model_size} configured")
        return True

    def download_piper_voice(self, voice: str = "en_US-lessac-medium"):
        """Download Piper TTS voice model."""
        print(f"\n📥 Downloading Piper voice: {voice}...")

        # Piper voices are hosted on Hugging Face; GitHub releases are fallback
        hf_base = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
        github_bases = [
            "https://github.com/rhasspy/piper/releases/download/v1.2.0",
            "https://github.com/rhasspy/piper/releases/download/v1.1.1",
            "https://github.com/rhasspy/piper/releases/download/v1.1.0"
        ]

        model_file = f"{voice}.onnx"
        config_file = f"{voice}.onnx.json"

        # Build Hugging Face URLs
        hf_model_url = None
        hf_config_url = None
        try:
            parts = voice.split("-")
            if len(parts) < 3:
                raise ValueError("Invalid voice format")
            locale = parts[0]
            quality = parts[-1]
            voice_name = "-".join(parts[1:-1])
            language = locale.split("_")[0]
            hf_prefix = f"{hf_base}/{language}/{locale}/{voice_name}/{quality}"
            hf_model_url = f"{hf_prefix}/{model_file}"
            hf_config_url = f"{hf_prefix}/{config_file}"
        except Exception as e:
            print(f"⚠ Could not parse voice for Hugging Face URLs: {e}")

        # Download model file
        model_urls = []
        if hf_model_url:
            model_urls.append(hf_model_url)
        model_urls.extend([f"{base}/{model_file}" for base in github_bases])
        model_path = self.tts_dir / model_file
        
        if not model_path.exists():
            success = False
            for model_url in model_urls:
                print(f"Trying URL: {model_url}")
                if self.download_file(model_url, model_path, f"Piper model {voice}"):
                    success = True
                    break
            if not success:
                print(f"⚠ Failed to download Piper model. Will use fallback TTS.")
                return False
        else:
            print(f"✓ Model already exists: {model_file}")

        # Download config file
        config_urls = []
        if hf_config_url:
            config_urls.append(hf_config_url)
        config_urls.extend([f"{base}/{config_file}" for base in github_bases])
        config_path = self.tts_dir / config_file
        
        if not config_path.exists():
            success = False
            for config_url in config_urls:
                print(f"Trying URL: {config_url}")
                if self.download_file(config_url, config_path, f"Piper config {voice}"):
                    success = True
                    break
            if not success:
                print(f"⚠ Failed to download Piper config. Will use fallback TTS.")
                return False
        else:
            print(f"✓ Config already exists: {config_file}")

        print(f"✓ Piper voice {voice} ready")
        return True

    def download_llm_model(self, model_name: str = "qwen2.5-1.5b-instruct"):
        """Download LLM model in GGUF format."""
        print(f"\n📥 Downloading LLM model: {model_name}...")

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
            print(f"⚠ Unknown model: {model_name}")
            print(f"Available models: {', '.join(model_urls.keys())}")
            print("\nTo download models manually:")
            print("1. Visit https://huggingface.co/models?library=gguf")
            print("2. Search for your preferred model (e.g., Qwen, Llama)")
            print(f"3. Download the GGUF file to: {self.llm_dir}")
            return False

        model_info = model_urls[model_name]
        repo = model_info["repo"]
        filename = model_info["file"]

        # Construct Hugging Face URL
        url = f"https://huggingface.co/{repo}/resolve/main/{filename}"
        dest_path = self.llm_dir / filename

        if dest_path.exists():
            print(f"✓ Model already exists: {filename}")
            return True

        print(f"\n⚠ Note: LLM models are large (1-4GB). This may take a while.")
        print(f"You can also download manually from: https://huggingface.co/{repo}")
        
        success = self.download_file(url, dest_path, f"LLM {model_name}")
        
        if success:
            print(f"✓ LLM model {model_name} ready")
        else:
            print(f"\n⚠ Automatic download failed. Please download manually:")
            print(f"1. Visit: https://huggingface.co/{repo}")
            print(f"2. Download: {filename}")
            print(f"3. Place in: {self.llm_dir}")

        return success

    def download_all(self, stt_model="small", tts_voice="en_US-lessac-medium", 
                    llm_model="qwen2.5-1.5b-instruct"):
        """Download all required models."""
        print("=" * 60)
        print("Language Learning Assistant - Model Downloader")
        print("=" * 60)

        results = {
            "stt": self.download_whisper_models(stt_model),
            "tts": self.download_piper_voice(tts_voice),
            "llm": self.download_llm_model(llm_model)
        }

        print("\n" + "=" * 60)
        print("Download Summary")
        print("=" * 60)
        print(f"STT (Whisper): {'✓' if results['stt'] else '✗'}")
        print(f"TTS (Piper): {'✓' if results['tts'] else '✗'}")
        print(f"LLM: {'✓' if results['llm'] else '✗'}")
        print()

        if all(results.values()):
            print("✓ All models ready!")
            print("\nYou can now start the application with:")
            print("  docker-compose up")
        else:
            print("⚠ Some models failed to download.")
            print("The application will still work with fallback functionality.")
            print("See messages above for manual download instructions.")

        return all(results.values())


def main():
    parser = argparse.ArgumentParser(
        description="Download models for Language Learning Assistant"
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=Path(__file__).parent.parent / "models",
        help="Directory to store models (default: ../models)"
    )
    parser.add_argument(
        "--stt-model",
        default="small",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="Whisper model size (default: small)"
    )
    parser.add_argument(
        "--tts-voice",
        default="en_US-lessac-medium",
        help="Piper TTS voice (default: en_US-lessac-medium)"
    )
    parser.add_argument(
        "--llm-model",
        default="qwen2.5-1.5b-instruct",
        help="LLM model name (default: qwen2.5-1.5b-instruct)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all models (default)"
    )

    args = parser.parse_args()

    downloader = ModelDownloader(args.models_dir)

    if args.all or len(sys.argv) == 1:
        downloader.download_all(
            stt_model=args.stt_model,
            tts_voice=args.tts_voice,
            llm_model=args.llm_model
        )
    else:
        if args.stt_model:
            downloader.download_whisper_models(args.stt_model)
        if args.tts_voice:
            downloader.download_piper_voice(args.tts_voice)
        if args.llm_model:
            downloader.download_llm_model(args.llm_model)


if __name__ == "__main__":
    main()
