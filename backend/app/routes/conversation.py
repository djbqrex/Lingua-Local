"""Conversation endpoints for language learning."""

import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

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
    scenario: str = "greeting"
    history: List[ConversationMessage] = []


class ConversationResponse(BaseModel):
    """Response from conversation."""
    response: str
    language: str
    detected_language: Optional[str] = None
    transcribed_text: Optional[str] = None


class TranscriptionResponse(BaseModel):
    """Response from speech transcription."""
    text: str
    language: str
    language_probability: float
    segments: List[Dict]


# In-memory conversation storage (should use a database in production)
conversation_sessions: Dict[str, List[ConversationMessage]] = {}


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
    from ..utils.language import LanguageHelper
    
    try:
        llm_handler = app.state.llm_handler
        
        # Build conversation history
        messages = []
        
        # Add system prompt
        system_prompt = LanguageHelper.format_system_prompt(
            language=request.language,
            difficulty=request.difficulty,
            scenario=request.scenario
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
        response_text = llm_handler.generate(
            messages=messages,
            max_tokens=256,
            temperature=0.7
        )
        
        return ConversationResponse(
            response=response_text,
            language=request.language
        )
        
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
    from ..utils.language import LanguageHelper
    
    try:
        stt_handler = app.state.stt_handler
        
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
            
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize")
async def synthesize_speech(
    text: str = Form(...),
    language: str = Form("en"),
    voice: Optional[str] = Form(None),
    speech_rate: Optional[float] = Form(None)
):
    """
    Synthesize speech from text.
    
    Args:
        text: Text to synthesize
        language: Target language code
        voice: Specific voice to use (optional)
        
    Returns:
        Audio file (WAV)
    """
    from ..main import app
    from ..utils.language import LanguageHelper
    
    try:
        tts_handler = app.state.tts_handler
        
        # Get appropriate voice for language
        if not voice:
            voice = LanguageHelper.get_tts_voice(language)
        
        # Set voice if different from current
        if voice != tts_handler.voice:
            tts_handler.set_voice(voice)
        
        # Synthesize
        audio_data = tts_handler.synthesize(text, length_scale=speech_rate)
        
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=speech.wav"
            }
        )
        
    except Exception as e:
        logger.error(f"Speech synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/speak", response_model=ConversationResponse)
async def speak_and_respond(
    audio: UploadFile = File(...),
    language: str = Form("en"),
    difficulty: str = Form("beginner"),
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
        scenario: Conversation scenario
        session_id: Optional session ID for maintaining context
        
    Returns:
        Transcribed user text and assistant's response
    """
    from ..main import app
    from ..utils.language import LanguageHelper
    
    try:
        stt_handler = app.state.stt_handler
        llm_handler = app.state.llm_handler
        
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
                scenario=scenario
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
            response_text = llm_handler.generate(
                messages=messages,
                max_tokens=256,
                temperature=0.7
            )
            
            logger.info(f"Response: {response_text}")
            
            # Update session history
            history.append(ConversationMessage(
                role="user",
                content=user_text,
                language=detected_language
            ))
            history.append(ConversationMessage(
                role="assistant",
                content=response_text,
                language=language
            ))
            
            # Keep only last 20 messages
            if len(history) > 20:
                conversation_sessions[session_id] = history[-20:]
            
            return ConversationResponse(
                response=response_text,
                language=language,
                detected_language=detected_language,
                transcribed_text=user_text
            )
            
        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
            
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
    from ..utils.language import LanguageHelper
    
    return {
        "voices": LanguageHelper.TTS_VOICES
    }
