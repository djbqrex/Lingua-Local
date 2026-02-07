"""Health check endpoints."""

import logging
from fastapi import APIRouter
from typing import Any, Dict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "message": "Language Learning Assistant API is running"
    }


@router.get("/models")
async def models_status() -> Dict[str, Any]:
    """Check status of loaded models."""
    from ..main import app
    
    status = {
        "stt": "not_loaded",
        "tts": "not_loaded",
        "llm": "not_loaded"
    }
    
    try:
        if hasattr(app.state, "stt_handler") and app.state.stt_handler.model is not None:
            status["stt"] = "loaded"
    except:
        pass
    
    try:
        if hasattr(app.state, "tts_handler") and app.state.tts_handler.voice_model is not None:
            status["tts"] = "loaded"
    except:
        pass
    
    try:
        if hasattr(app.state, "llm_handler") and app.state.llm_handler.model is not None:
            status["llm"] = "loaded"
    except:
        pass
    
    return {
        "status": "ok",
        "models": status
    }


@router.get("/languages")
async def supported_languages() -> Dict[str, Any]:
    """Get list of supported languages."""
    from ..utils.language import LanguageHelper
    
    languages = {}
    for code in LanguageHelper.get_supported_languages():
        languages[code] = {
            "name": LanguageHelper.get_language_name(code),
            "tts_voices": LanguageHelper.TTS_VOICES.get(code, [])
        }
    
    return {
        "languages": languages,
        "count": len(languages)
    }


@router.get("/scenarios")
async def available_scenarios() -> Dict[str, Any]:
    """Get list of available conversation scenarios."""
    from ..utils.language import LanguageHelper
    
    scenarios = {}
    for scenario in LanguageHelper.get_available_scenarios():
        scenarios[scenario] = LanguageHelper.get_scenario_description(scenario)
    
    return {
        "scenarios": scenarios,
        "count": len(scenarios)
    }
