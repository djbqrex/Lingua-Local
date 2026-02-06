#!/usr/bin/env python3
"""
Test script to verify API structure without running the server.

Note: This script requires dependencies to be installed.
Run inside Docker container for full test:
    docker-compose run --rm language-assistant python3 scripts/test_api_structure.py

Or install dependencies first:
    pip install -r backend/requirements.txt
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing module imports...")
    
    try:
        from backend.app import config
        print("✓ Config module")
    except Exception as e:
        print(f"✗ Config module: {e}")
        return False

    try:
        from backend.app.utils.language import LanguageHelper
        print("✓ Language helper")
        print(f"  - Supported languages: {len(LanguageHelper.get_supported_languages())}")
        print(f"  - Available scenarios: {len(LanguageHelper.get_available_scenarios())}")
    except Exception as e:
        print(f"✗ Language helper: {e}")
        return False

    try:
        from backend.app.utils.audio import AudioProcessor
        print("✓ Audio processor")
    except Exception as e:
        print(f"✗ Audio processor: {e}")
        return False

    # Note: Model handlers require dependencies that may not be installed
    print("\n⚠ Model handlers require installed dependencies (faster-whisper, llama-cpp-python, piper-tts)")
    print("  These will be tested when Docker container runs")

    return True

def test_config():
    """Test configuration."""
    print("\nTesting configuration...")
    
    try:
        from backend.app.config import settings
        
        print(f"✓ Settings loaded")
        print(f"  - Device: {settings.DEVICE}")
        print(f"  - STT Model: {settings.STT_MODEL}")
        print(f"  - LLM Model: {settings.LLM_MODEL}")
        print(f"  - TTS Voice: {settings.TTS_VOICE}")
        print(f"  - Supported languages: {', '.join(settings.SUPPORTED_LANGUAGES[:5])}...")
        print(f"  - Models directory: {settings.MODELS_DIR}")
        
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def test_language_helper():
    """Test language helper functionality."""
    print("\nTesting language helper...")
    
    try:
        from backend.app.utils.language import LanguageHelper
        
        # Test language name lookup
        name = LanguageHelper.get_language_name("es")
        assert name == "Spanish", f"Expected 'Spanish', got '{name}'"
        print(f"✓ Language name lookup: es -> {name}")
        
        # Test TTS voice lookup
        voice = LanguageHelper.get_tts_voice("es")
        print(f"✓ TTS voice lookup: es -> {voice}")
        
        # Test system prompt generation
        prompt = LanguageHelper.format_system_prompt("es", "beginner", "restaurant")
        assert "Spanish" in prompt
        assert "beginner" in prompt
        print(f"✓ System prompt generation")
        
        # Test scenarios
        scenarios = LanguageHelper.get_available_scenarios()
        print(f"✓ Scenarios: {len(scenarios)} available")
        
        return True
    except Exception as e:
        print(f"✗ Language helper error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_audio_processor():
    """Test audio processor functionality."""
    print("\nTesting audio processor...")
    
    try:
        from backend.app.utils.audio import AudioProcessor
        import numpy as np
        
        # Test audio normalization
        audio = np.array([0.5, -0.5, 0.3, -0.3])
        normalized = AudioProcessor.normalize_audio(audio, target_level=0.95)
        assert normalized.max() <= 1.0
        print(f"✓ Audio normalization")
        
        # Test simple resampling
        audio = np.random.randn(16000).astype(np.float32)
        resampled = AudioProcessor._simple_resample(audio, 16000, 22050)
        expected_length = int(len(audio) * 22050 / 16000)
        assert len(resampled) == expected_length
        print(f"✓ Audio resampling")
        
        return True
    except Exception as e:
        print(f"✗ Audio processor error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("Language Learning Assistant - API Structure Test")
    print("=" * 60)
    print()

    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Language Helper", test_language_helper()))
    results.append(("Audio Processor", test_audio_processor()))

    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    
    if all(r for _, r in results):
        print("✓ All tests passed!")
        print()
        print("The API structure is valid. You can now:")
        print("1. Download models: python3 scripts/download_models.py")
        print("2. Start the application: docker-compose up")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
