"""Language-specific utilities and helpers."""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LanguageHelper:
    """Helper class for language-specific operations."""

    EXPLANATION_LANGUAGE_CODE = "en"
    DEFAULT_TTS_FALLBACK_VOICE = "en_US-lessac-medium"
    VOICE_STYLE_OPTIONS = {"female", "male"}
    SPEECH_TAG_PATTERN = re.compile(r"\[(EN|TL)\](.*?)\[/\1\]", re.IGNORECASE | re.DOTALL)
    ENGLISH_HINT_WORDS = {
        "a", "an", "and", "are", "do", "for", "from", "have", "how", "i", "in", "is",
        "it", "my", "of", "on", "please", "the", "this", "to", "we", "what", "where",
        "you", "your"
    }

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
        "en": ["en_US-amy-medium", "en_GB-alan-medium", "en_US-lessac-medium"],
        "es": ["es_MX-ald-medium", "es_ES-davefx-medium"],
        "fr": ["fr_FR-siwis-medium", "fr_FR-upmc-medium"],
        "de": ["de_DE-karlsson-low", "de_DE-thorsten-medium"],
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

    # Best-effort voice gender metadata for style selection.
    TTS_VOICE_GENDER: Dict[str, str] = {
        "en_US-amy-medium": "female",
        "en_GB-alan-medium": "male",
        "en_US-lessac-medium": "male",
        "es_MX-ald-medium": "female",
        "es_ES-davefx-medium": "male",
        "fr_FR-siwis-medium": "female",
        "fr_FR-upmc-medium": "male",
        "de_DE-karlsson-low": "female",
        "de_DE-thorsten-medium": "male",
        "it_IT-riccardo-medium": "male",
        "pt_BR-faber-medium": "female",
        "pt_PT-tugao-medium": "male",
        "ja_JP-kokoro-medium": "female",
        "zh_CN-huayan-medium": "female",
        "ko_KR-keonhee-medium": "male",
        "ar_JO-kareem-medium": "male",
        "nl_NL-mls-medium": "female",
        "ru_RU-dmitri-medium": "male",
        "th_TH-pongkul-medium": "male",
        "vi_VN-vivos-medium": "female",
        "tr_TR-dfki-medium": "male",
        "el_GR-rapunzelina-low": "female",
        "pl_PL-mls-medium": "female",
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
    def normalize_voice_style(cls, voice_style: Optional[str]) -> str:
        """Normalize voice style selection."""
        candidate = (voice_style or "female").lower()
        if candidate in cls.VOICE_STYLE_OPTIONS:
            return candidate
        return "female"

    @classmethod
    def get_language_name(cls, code: str) -> str:
        """Get language name from code."""
        return cls.LANGUAGE_NAMES.get(code.lower(), code.upper())

    @classmethod
    def get_whisper_code(cls, code: str) -> Optional[str]:
        """Get Whisper language code from standard code."""
        return cls.WHISPER_LANGUAGE_CODES.get(code.lower())

    @classmethod
    def get_voice_gender(cls, voice: str) -> str:
        """Get gender metadata for a voice id."""
        return cls.TTS_VOICE_GENDER.get(voice, "unknown")

    @classmethod
    def get_tts_voice(
        cls,
        language: str,
        preference: Optional[str] = None,
        voice_style: Optional[str] = None
    ) -> str:
        """
        Get TTS voice for language.

        Args:
            language: Language code
            preference: Explicit voice id to use
            voice_style: "male" or "female" when available

        Returns:
            Voice model name
        """
        voices = cls.TTS_VOICES.get(language.lower(), [])
        if not voices:
            logger.warning("No TTS voice found for %s, using fallback", language)
            return cls.DEFAULT_TTS_FALLBACK_VOICE

        if preference and preference in voices:
            return preference

        normalized_style = cls.normalize_voice_style(voice_style)
        for voice in voices:
            if cls.get_voice_gender(voice) == normalized_style:
                return voice

        return voices[0]

    @classmethod
    def get_bilingual_voices(
        cls,
        target_language: str,
        voice_style: Optional[str] = None,
        target_preference: Optional[str] = None,
        explanation_preference: Optional[str] = None,
        explanation_language: str = EXPLANATION_LANGUAGE_CODE,
    ) -> Dict[str, str]:
        """
        Get matching voices for explanation and target-language speech.

        Returns:
            Dict containing explanation_voice and target_voice.
        """
        normalized_style = cls.normalize_voice_style(voice_style)
        target_voice = cls.get_tts_voice(
            language=target_language,
            preference=target_preference,
            voice_style=normalized_style,
        )

        # If target language is English, keep a single consistent voice.
        if target_language.lower() == explanation_language.lower():
            explanation_voice = target_voice
        else:
            explanation_voice = cls.get_tts_voice(
                language=explanation_language,
                preference=explanation_preference,
                voice_style=normalized_style,
            )

        return {
            "voice_style": normalized_style,
            "explanation_language": explanation_language,
            "explanation_voice": explanation_voice,
            "target_language": target_language.lower(),
            "target_voice": target_voice,
        }

    @classmethod
    def get_voice_catalog(cls) -> Dict[str, List[Dict[str, str]]]:
        """Return voice metadata grouped by language."""
        catalog: Dict[str, List[Dict[str, str]]] = {}
        for language, voices in cls.TTS_VOICES.items():
            catalog[language] = [
                {"id": voice, "gender": cls.get_voice_gender(voice)}
                for voice in voices
            ]
        return catalog

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
    def _looks_like_english(cls, text: str) -> bool:
        """Simple heuristic used when LLM forgets EN/TL tags."""
        words = re.findall(r"[a-zA-Z']+", text.lower())
        if not words:
            return False
        hint_hits = sum(1 for word in words if word in cls.ENGLISH_HINT_WORDS)
        return hint_hits >= max(2, len(words) // 3)

    @classmethod
    def _clean_segment_text(cls, text: str) -> str:
        """Normalize whitespace while preserving punctuation."""
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def strip_speech_tags(cls, text: str) -> str:
        """Remove [EN]/[TL] markers from assistant output."""
        if not text:
            return ""
        without_tags = re.sub(r"\[/?(?:EN|TL)\]", "", text, flags=re.IGNORECASE)
        return cls._clean_segment_text(without_tags)

    @classmethod
    def split_speech_segments(
        cls,
        text: str,
        target_language: str,
        explanation_language: str = EXPLANATION_LANGUAGE_CODE,
    ) -> List[Dict[str, str]]:
        """
        Split response text into language-tagged speech segments.

        Expected format:
            [EN]English explanation[/EN] [TL]Target phrase[/TL]
        """
        if not text:
            return []

        segments: List[Dict[str, str]] = []
        matches = list(cls.SPEECH_TAG_PATTERN.finditer(text))
        target_language = target_language.lower()
        explanation_language = explanation_language.lower()

        if not matches:
            cleaned = cls._clean_segment_text(text)
            if not cleaned:
                return []
            guessed_language = (
                explanation_language
                if target_language != explanation_language and cls._looks_like_english(cleaned)
                else target_language
            )
            return [{"text": cleaned, "language": guessed_language}]

        cursor = 0
        for match in matches:
            if match.start() > cursor:
                between = cls._clean_segment_text(text[cursor:match.start()])
                if between:
                    guessed_language = (
                        explanation_language
                        if target_language != explanation_language and cls._looks_like_english(between)
                        else target_language
                    )
                    segments.append({"text": between, "language": guessed_language})

            tag = match.group(1).upper()
            content = cls._clean_segment_text(match.group(2))
            if content:
                segment_language = explanation_language if tag == "EN" else target_language
                segments.append({"text": content, "language": segment_language})
            cursor = match.end()

        if cursor < len(text):
            tail = cls._clean_segment_text(text[cursor:])
            if tail:
                guessed_language = (
                    explanation_language
                    if target_language != explanation_language and cls._looks_like_english(tail)
                    else target_language
                )
                segments.append({"text": tail, "language": guessed_language})

        return segments

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

        if difficulty == "beginner":
            balance_guidance = (
                "Use mostly English explanations (about 70-80%) plus short target-language examples. "
                "Break down new words into syllables, explain difficult vowels/consonants, and include "
                "a quick pronunciation tip (stress, mouth position, or sound comparison)."
            )
            length_guidance = "Keep each reply short: 2-4 compact teaching lines."
        elif difficulty == "intermediate":
            balance_guidance = (
                f"Use a balanced mix of English and {language_name}. "
                "Provide concise meaning and pronunciation support for new phrases."
            )
            length_guidance = "Keep each reply concise: 2-3 sentences."
        else:
            balance_guidance = (
                f"Respond mostly in {language_name}. "
                "Use brief English only for clarification or correction when helpful."
            )
            length_guidance = "Keep each reply concise unless asked for detail."

        prompt = f"""You are a patient language tutor helping a beginner learn {language_name} for travel.

Current scenario: {scenario_desc}

Teaching behavior:
1. Teach practical phrases that are immediately useful.
2. Correct mistakes gently and clearly.
3. {balance_guidance}
4. {length_guidance}
5. For pronunciation support, prefer simple readable hints (for example: "ho-la", "long a", "soft r").

Output formatting rules (mandatory for speech synthesis):
- Wrap ALL English explanation text in [EN]...[/EN]
- Wrap ALL target-language text in [TL]...[/TL]
- Do not use any other custom tags.
- Keep punctuation inside the tags.

Example format:
[EN]Say this when greeting someone politely:[/EN] [TL]Buenos dias.[/TL] [EN]Pronunciation: bweh-nos dee-as.[/EN]
"""
        return prompt

    @classmethod
    def get_difficulty_guidelines(cls, difficulty: str) -> Dict[str, Any]:
        """Get guidelines for different difficulty levels."""
        guidelines = {
            "beginner": {
                "max_sentence_length": 10,
                "vocabulary_level": "basic",
                "grammar_complexity": "simple",
                "speech_rate": "slow",
                "tts_length_scale": 1.45,
                "provide_translation": True
            },
            "intermediate": {
                "max_sentence_length": 20,
                "vocabulary_level": "intermediate",
                "grammar_complexity": "moderate",
                "speech_rate": "normal",
                "tts_length_scale": 1.20,
                "provide_translation": False
            },
            "advanced": {
                "max_sentence_length": None,
                "vocabulary_level": "advanced",
                "grammar_complexity": "complex",
                "speech_rate": "native",
                "tts_length_scale": 1.00,
                "provide_translation": False
            }
        }
        return guidelines.get(difficulty, guidelines["beginner"])
