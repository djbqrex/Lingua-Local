"""Conversation endpoints for language learning."""

import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ..config import settings
from ..utils.language import LanguageHelper

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/conversation", tags=["conversation"])


# Request/Response models
class ConversationMessage(BaseModel):
    """Single conversation message."""
    role: str  # 'user' or 'assistant'
    content: str
    language: Optional[str] = None


class ConversationRequest(BaseModel):
    """Request for text-based conversation."""
    message: str
    language: str = "en"
    difficulty: str = "beginner"
    teaching_intensity: str = settings.TEACHING_INTENSITY
    scenario: str = "greeting"
    history: List[ConversationMessage] = Field(default_factory=list)


class ConversationResponse(BaseModel):
    """Response from conversation."""
    response: str
    language: str
    detected_language: Optional[str] = None
    transcribed_text: Optional[str] = None
    speech_script: Optional[str] = None
    speech_segments: List[Dict[str, str]] = Field(default_factory=list)


class TranscriptionResponse(BaseModel):
    """Response from speech transcription."""
    text: str
    language: str
    language_probability: float
    segments: List[Dict]


# In-memory conversation storage (should use a database in production)
conversation_sessions: Dict[str, List[ConversationMessage]] = {}


def _resolve_default_speech_scale(difficulty: str, teaching_intensity: str) -> float:
    """Resolve default speech speed for learner comfort."""
    base_scale = {
        "beginner": settings.BEGINNER_SPEECH_RATE,
        "intermediate": settings.INTERMEDIATE_SPEECH_RATE,
        "advanced": settings.ADVANCED_SPEECH_RATE,
    }.get(difficulty.lower(), settings.BEGINNER_SPEECH_RATE)

    intensity = LanguageHelper.normalize_teaching_intensity(teaching_intensity)
    if intensity == "deep":
        return min(2.0, base_scale + 0.08)
    if intensity == "light":
        return max(0.95, base_scale - 0.08)
    return base_scale


def _prepare_speech_response(response_text: str, target_language: str) -> Dict[str, object]:
    """Prepare clean display text and language-tagged segments for TTS."""
    speech_script = response_text or ""
    clean_response = LanguageHelper.strip_speech_tags(speech_script) or speech_script
    speech_segments = LanguageHelper.split_speech_segments(
        text=speech_script,
        target_language=target_language,
        explanation_language=LanguageHelper.EXPLANATION_LANGUAGE_CODE,
    )
    if not speech_segments and clean_response:
        speech_segments = [{
            "text": clean_response,
            "language": target_language.lower(),
        }]
    return {
        "response": clean_response,
        "speech_script": speech_script,
        "speech_segments": speech_segments,
    }


@router.post("/text", response_model=ConversationResponse)
async def text_conversation(request: ConversationRequest):
    """
    Have a text-based conversation.
    
    Args:
        request: Conversation request with message and context
        
    Returns:
        Assistant's response
    """
    from ..main import app
    
    try:
        llm_handler = app.state.llm_handler
        if llm_handler is None:
            raise HTTPException(status_code=503, detail="LLM model is not available")
        teaching_intensity = LanguageHelper.normalize_teaching_intensity(request.teaching_intensity)
        
        # Build conversation history
        messages = []
        
        # Add system prompt
        system_prompt = LanguageHelper.format_system_prompt(
            language=request.language,
            difficulty=request.difficulty,
            scenario=request.scenario,
            teaching_intensity=teaching_intensity,
        )
        messages.append({"role": "system", "content": system_prompt})
        
        # Add history
        for msg in request.history[-10:]:  # Keep last 10 messages
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        # Generate response
        generation_settings = LanguageHelper.get_generation_settings(
            difficulty=request.difficulty,
            teaching_intensity=teaching_intensity,
        )
        response_text = llm_handler.generate(
            messages=messages,
            max_tokens=int(generation_settings["max_tokens"]),
            temperature=generation_settings["temperature"],
            top_p=generation_settings["top_p"],
        )
        
        prepared_response = _prepare_speech_response(response_text, request.language)
        return ConversationResponse(
            response=prepared_response["response"],
            language=request.language,
            speech_script=prepared_response["speech_script"],
            speech_segments=prepared_response["speech_segments"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text conversation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None)
):
    """
    Transcribe audio to text.
    
    Args:
        audio: Audio file (WAV, MP3, etc.)
        language: Target language code (optional, auto-detect if not provided)
        
    Returns:
        Transcription result
    """
    from ..main import app
    
    try:
        stt_handler = app.state.stt_handler
        if stt_handler is None:
            raise HTTPException(status_code=503, detail="STT model is not available")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Get Whisper language code if provided
            whisper_lang = None
            if language:
                whisper_lang = LanguageHelper.get_whisper_code(language)
            
            # Transcribe
            result = stt_handler.transcribe(
                audio_path=temp_path,
                language=whisper_lang
            )
            
            return TranscriptionResponse(
                text=result["text"],
                language=result["language"],
                language_probability=result["language_probability"],
                segments=result["segments"]
            )
            
        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize")
async def synthesize_speech(
    text: str = Form(...),
    language: str = Form("en"),
    voice: Optional[str] = Form(None),
    speech_rate: Optional[float] = Form(None),
    voice_style: Optional[str] = Form(settings.TTS_VOICE_STYLE),
    explanation_voice: Optional[str] = Form(None),
    explanation_language: str = Form(LanguageHelper.EXPLANATION_LANGUAGE_CODE),
    difficulty: str = Form("beginner"),
    teaching_intensity: str = Form(settings.TEACHING_INTENSITY),
):
    """
    Synthesize speech from text.
    
    Args:
        text: Text to synthesize
        language: Target language code
        voice: Target-language voice override (optional)
        speech_rate: Piper length_scale (higher = slower)
        voice_style: "female" or "male" voice profile preference
        explanation_voice: Explanation-language voice override (optional)
        explanation_language: Language used for explanatory text
        difficulty: Conversation difficulty for pace defaults
        teaching_intensity: light, standard, or deep teaching detail
        
    Returns:
        Audio file (WAV)
    """
    from ..main import app
    
    try:
        tts_handler = app.state.tts_handler
        if tts_handler is None:
            raise HTTPException(status_code=503, detail="TTS model is not available")
        normalized_teaching_intensity = LanguageHelper.normalize_teaching_intensity(teaching_intensity)

        selected_voices = LanguageHelper.get_bilingual_voices(
            target_language=language,
            voice_style=voice_style,
            target_preference=voice,
            explanation_preference=explanation_voice or settings.TTS_EXPLANATION_VOICE,
            explanation_language=explanation_language,
        )

        segments = LanguageHelper.split_speech_segments(
            text=text,
            target_language=language,
            explanation_language=selected_voices["explanation_language"],
        )
        if not segments:
            stripped_text = LanguageHelper.strip_speech_tags(text) or text
            segments = [{"text": stripped_text, "language": language.lower()}]

        speech_scale = speech_rate
        if speech_scale is None:
            speech_scale = _resolve_default_speech_scale(
                difficulty=difficulty,
                teaching_intensity=normalized_teaching_intensity,
            )

        voice_map = {
            selected_voices["target_language"]: selected_voices["target_voice"],
            selected_voices["explanation_language"]: selected_voices["explanation_voice"],
        }

        uses_multiple_languages = any(
            segment["language"] != selected_voices["target_language"]
            for segment in segments
        )
        if uses_multiple_languages or len(segments) > 1:
            audio_data = tts_handler.synthesize_segments(
                segments=segments,
                voice_for_language=voice_map,
                length_scale=speech_scale,
            )
        else:
            audio_data = tts_handler.synthesize(
                text=segments[0]["text"],
                voice=selected_voices["target_voice"],
                length_scale=speech_scale,
            )
        
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=speech.wav"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Speech synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/speak", response_model=ConversationResponse)
async def speak_and_respond(
    audio: UploadFile = File(...),
    language: str = Form("en"),
    difficulty: str = Form("beginner"),
    teaching_intensity: str = Form(settings.TEACHING_INTENSITY),
    scenario: str = Form("greeting"),
    session_id: Optional[str] = Form(None)
):
    """
    Complete conversation flow: transcribe audio, generate response, return text.
    Use /synthesize separately to get audio of the response.
    
    Args:
        audio: Audio file with user's speech
        language: Target language
        difficulty: Difficulty level
        teaching_intensity: light, standard, or deep teaching detail
        scenario: Conversation scenario
        session_id: Optional session ID for maintaining context
        
    Returns:
        Transcribed user text and assistant's response
    """
    from ..main import app
    
    try:
        stt_handler = app.state.stt_handler
        llm_handler = app.state.llm_handler
        if stt_handler is None:
            raise HTTPException(status_code=503, detail="STT model is not available")
        if llm_handler is None:
            raise HTTPException(status_code=503, detail="LLM model is not available")
        normalized_teaching_intensity = LanguageHelper.normalize_teaching_intensity(teaching_intensity)
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Transcribe user's speech (auto-detect input language to avoid forced translation)
            whisper_lang = None
            transcription = stt_handler.transcribe(
                audio_path=temp_path,
                language=whisper_lang
            )
            
            user_text = transcription["text"]
            detected_language = transcription["language"]
            
            logger.info(f"Transcribed: {user_text}")
            
            # Get or create session history
            if not session_id:
                session_id = "default"
            
            if session_id not in conversation_sessions:
                conversation_sessions[session_id] = []
            
            history = conversation_sessions[session_id]
            
            # Build messages for LLM
            messages = []
            
            # System prompt
            system_prompt = LanguageHelper.format_system_prompt(
                language=language,
                difficulty=difficulty,
                scenario=scenario,
                teaching_intensity=normalized_teaching_intensity,
            )
            messages.append({"role": "system", "content": system_prompt})
            
            # Add recent history
            for msg in history[-10:]:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_text
            })
            
            # Generate response
            generation_settings = LanguageHelper.get_generation_settings(
                difficulty=difficulty,
                teaching_intensity=normalized_teaching_intensity,
            )
            response_text = llm_handler.generate(
                messages=messages,
                max_tokens=int(generation_settings["max_tokens"]),
                temperature=generation_settings["temperature"],
                top_p=generation_settings["top_p"],
            )
            
            logger.info(f"Response: {response_text}")
            
            prepared_response = _prepare_speech_response(response_text, language)

            # Update session history
            history.append(ConversationMessage(
                role="user",
                content=user_text,
                language=detected_language
            ))
            history.append(ConversationMessage(
                role="assistant",
                content=prepared_response["response"],
                language=language
            ))
            
            # Keep only last 20 messages
            if len(history) > 20:
                conversation_sessions[session_id] = history[-20:]
            
            return ConversationResponse(
                response=prepared_response["response"],
                language=language,
                detected_language=detected_language,
                transcribed_text=user_text,
                speech_script=prepared_response["speech_script"],
                speech_segments=prepared_response["speech_segments"],
            )
            
        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Speak and respond failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session_history(session_id: str):
    """Get conversation history for a session."""
    if session_id not in conversation_sessions:
        return {"messages": []}
    
    return {
        "session_id": session_id,
        "messages": conversation_sessions[session_id]
    }


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation history for a session."""
    if session_id in conversation_sessions:
        del conversation_sessions[session_id]
    
    return {"status": "cleared", "session_id": session_id}


@router.get("/voices")
async def get_available_voices():
    """Get list of available TTS voices."""
    return {
        "voices": LanguageHelper.get_voice_catalog(),
        "voice_styles": sorted(LanguageHelper.VOICE_STYLE_OPTIONS),
        "default_voice_style": settings.TTS_VOICE_STYLE,
        "teaching_intensities": sorted(LanguageHelper.TEACHING_INTENSITY_OPTIONS),
        "default_teaching_intensity": settings.TEACHING_INTENSITY,
        "explanation_language": LanguageHelper.EXPLANATION_LANGUAGE_CODE,
    }
