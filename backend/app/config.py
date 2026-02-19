"""Configuration management for the application."""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings."""

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    MODELS_DIR: Path = BASE_DIR / "models"
    STT_MODEL_DIR: Path = MODELS_DIR / "stt"
    TTS_MODEL_DIR: Path = MODELS_DIR / "tts"
    LLM_MODEL_DIR: Path = MODELS_DIR / "llm"
    TEMP_DIR: Path = BASE_DIR / "tmp"

    # Hardware
    DEVICE: str = os.getenv("DEVICE", "auto")  # cuda, cpu, or auto
    COMPUTE_TYPE: str = os.getenv("COMPUTE_TYPE", "float16")  # float16, int8, float32

    # Model Configuration
    STT_MODEL: str = os.getenv("STT_MODEL", "small")  # tiny, base, small, medium, large-v3
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen2.5-1.5b-instruct")
    TTS_VOICE: str = os.getenv("TTS_VOICE", "en_US-lessac-medium")
    TTS_EXPLANATION_VOICE: str = os.getenv("TTS_EXPLANATION_VOICE", "en_US-amy-medium")
    TTS_VOICE_STYLE: str = os.getenv("TTS_VOICE_STYLE", "female")  # female, male

    # Supported Languages
    SUPPORTED_LANGUAGES: List[str] = os.getenv(
        "SUPPORTED_LANGUAGES", "en,es,fr,de,it,pt,ja,zh,ko,ar"
    ).split(",")

    # Performance
    MAX_AUDIO_LENGTH: int = int(os.getenv("MAX_AUDIO_LENGTH", "30"))  # seconds
    STREAM_AUDIO: bool = os.getenv("STREAM_AUDIO", "true").lower() == "true"
    CACHE_MODELS: bool = os.getenv("CACHE_MODELS", "true").lower() == "true"
    BEGINNER_SPEECH_RATE: float = float(os.getenv("BEGINNER_SPEECH_RATE", "1.45"))
    INTERMEDIATE_SPEECH_RATE: float = float(os.getenv("INTERMEDIATE_SPEECH_RATE", "1.20"))
    ADVANCED_SPEECH_RATE: float = float(os.getenv("ADVANCED_SPEECH_RATE", "1.00"))

    # API
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080"
    ).split(",")

    # Conversation
    MAX_CONTEXT_LENGTH: int = int(os.getenv("MAX_CONTEXT_LENGTH", "10"))
    SYSTEM_PROMPT_TEMPLATE: str = """You are a helpful language learning assistant. You are helping a user learn {language} for travel purposes. 

Your role is to:
1. Have natural conversations in {language}
2. Keep responses concise and appropriate for {difficulty} level learners
3. Focus on practical phrases useful for travelers
4. Correct mistakes gently when the user makes them
5. Encourage and be supportive

Current scenario: {scenario}

Beginner-friendly guidance:
- For beginners, respond mostly in English and include short {language} phrases with translations.
- For intermediate learners, balance {language} with English explanations.
- For advanced learners, respond primarily in {language}.
- If the user speaks English, acknowledge in English and then provide the {language} version.
- Keep responses to 1-3 sentences unless asked for more detail."""

    def __init__(self):
        """Initialize settings and create necessary directories."""
        self.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        self.STT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        self.TTS_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        self.LLM_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)

    def get_device(self) -> str:
        """Get the compute device based on availability."""
        if self.DEVICE == "auto":
            try:
                import torch
                return "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                return "cpu"
        return self.DEVICE


# Global settings instance
settings = Settings()
