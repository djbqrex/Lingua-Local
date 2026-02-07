"""Language-specific utilities and helpers."""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class LanguageHelper:
    """Helper class for language-specific operations."""

    # Language code to name mapping
    LANGUAGE_NAMES: Dict[str, str] = {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ja": "Japanese",
        "zh": "Chinese",
        "ko": "Korean",
        "ar": "Arabic",
        "nl": "Dutch",
        "ru": "Russian",
        "th": "Thai",
        "vi": "Vietnamese",
        "tr": "Turkish",
        "el": "Greek",
        "pl": "Polish",
        "hi": "Hindi",
    }

    # Whisper language codes (may differ from ISO 639-1)
    WHISPER_LANGUAGE_CODES: Dict[str, str] = {
        "en": "en",
        "es": "es",
        "fr": "fr",
        "de": "de",
        "it": "it",
        "pt": "pt",
        "ja": "ja",
        "zh": "zh",
        "ko": "ko",
        "ar": "ar",
        "nl": "nl",
        "ru": "ru",
        "th": "th",
        "vi": "vi",
        "tr": "tr",
        "el": "el",
        "pl": "pl",
        "hi": "hi",
    }

    # TTS voice mappings (language -> list of available voices)
    TTS_VOICES: Dict[str, List[str]] = {
        "en": ["en_US-lessac-medium", "en_US-amy-medium", "en_GB-alan-medium"],
        "es": ["es_ES-davefx-medium", "es_MX-ald-medium"],
        "fr": ["fr_FR-siwis-medium", "fr_FR-upmc-medium"],
        "de": ["de_DE-thorsten-medium", "de_DE-karlsson-low"],
        "it": ["it_IT-riccardo-medium"],
        "pt": ["pt_BR-faber-medium", "pt_PT-tugao-medium"],
        "ja": ["ja_JP-kokoro-medium"],
        "zh": ["zh_CN-huayan-medium"],
        "ko": ["ko_KR-keonhee-medium"],
        "ar": ["ar_JO-kareem-medium"],
        "nl": ["nl_NL-mls-medium"],
        "ru": ["ru_RU-dmitri-medium"],
        "th": ["th_TH-pongkul-medium"],
        "vi": ["vi_VN-vivos-medium"],
        "tr": ["tr_TR-dfki-medium"],
        "el": ["el_GR-rapunzelina-low"],
        "pl": ["pl_PL-mls-medium"],
    }

    # Conversation scenarios
    SCENARIOS: Dict[str, str] = {
        "greeting": "Practice basic greetings and introductions",
        "restaurant": "Ordering food at a restaurant",
        "directions": "Asking for and giving directions",
        "shopping": "Shopping and negotiating prices",
        "hotel": "Checking in/out of a hotel",
        "transportation": "Using public transportation",
        "emergency": "Handling emergency situations",
        "small_talk": "Making casual conversation with locals",
        "sightseeing": "Asking about tourist attractions",
    }

    @classmethod
    def get_language_name(cls, code: str) -> str:
        """Get language name from code."""
        return cls.LANGUAGE_NAMES.get(code.lower(), code.upper())

    @classmethod
    def get_whisper_code(cls, code: str) -> Optional[str]:
        """Get Whisper language code from standard code."""
        return cls.WHISPER_LANGUAGE_CODES.get(code.lower())

    @classmethod
    def get_tts_voice(cls, language: str, preference: Optional[str] = None) -> str:
        """
        Get TTS voice for language.

        Args:
            language: Language code
            preference: Preferred voice variant

        Returns:
            Voice model name
        """
        voices = cls.TTS_VOICES.get(language.lower(), [])
        
        if not voices:
            # Fallback to English
            logger.warning(f"No TTS voice found for {language}, using English")
            return "en_US-lessac-medium"
        
        if preference and preference in voices:
            return preference
        
        return voices[0]  # Return first available voice

    @classmethod
    def get_supported_languages(cls) -> List[str]:
        """Get list of supported language codes."""
        return list(cls.LANGUAGE_NAMES.keys())

    @classmethod
    def get_scenario_description(cls, scenario: str) -> str:
        """Get description for a conversation scenario."""
        return cls.SCENARIOS.get(scenario, "General conversation practice")

    @classmethod
    def get_available_scenarios(cls) -> List[str]:
        """Get list of available scenarios."""
        return list(cls.SCENARIOS.keys())

    @classmethod
    def format_system_prompt(
        cls,
        language: str,
        difficulty: str = "beginner",
        scenario: str = "greeting"
    ) -> str:
        """
        Format system prompt for language learning.

        Args:
            language: Target language code
            difficulty: Difficulty level (beginner, intermediate, advanced)
            scenario: Conversation scenario

        Returns:
            Formatted system prompt
        """
        language_name = cls.get_language_name(language)
        scenario_desc = cls.get_scenario_description(scenario)
        
        prompt = f"""You are a helpful language learning assistant. You are helping a user learn {language_name} for travel purposes.

Your role is to:
1. Have natural conversations in {language_name}
2. Keep responses concise and appropriate for {difficulty} level learners
3. Focus on practical phrases useful for travelers
4. Correct mistakes gently when the user makes them
5. Encourage and be supportive

Current scenario: {scenario_desc}

Beginner-friendly guidance:
- You may include brief English explanations or translations when it helps learning.
- If the user speaks English, acknowledge in English and then provide the {language_name} version.
- Keep responses to 1-3 sentences unless asked for more detail."""

        return prompt

    @classmethod
    def get_difficulty_guidelines(cls, difficulty: str) -> Dict[str, any]:
        """Get guidelines for different difficulty levels."""
        guidelines = {
            "beginner": {
                "max_sentence_length": 10,
                "vocabulary_level": "basic",
                "grammar_complexity": "simple",
                "speech_rate": "slow",
                "provide_translation": True
            },
            "intermediate": {
                "max_sentence_length": 20,
                "vocabulary_level": "intermediate",
                "grammar_complexity": "moderate",
                "speech_rate": "normal",
                "provide_translation": False
            },
            "advanced": {
                "max_sentence_length": None,
                "vocabulary_level": "advanced",
                "grammar_complexity": "complex",
                "speech_rate": "native",
                "provide_translation": False
            }
        }
        
        return guidelines.get(difficulty, guidelines["beginner"])
