"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import settings
from .models import STTHandler, TTSHandler, LLMHandler
from .routes import conversation_router, health_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the application."""
    logger.info("Starting Language Learning Assistant API")
    
    # Initialize model handlers
    try:
        logger.info("Initializing STT handler...")
        app.state.stt_handler = STTHandler(
            model_size=settings.STT_MODEL,
            device=settings.get_device(),
            compute_type=settings.COMPUTE_TYPE
        )
        logger.info("STT handler initialized")
    except Exception as e:
        logger.error(f"Failed to initialize STT handler: {e}")
        app.state.stt_handler = None
    
    try:
        logger.info("Initializing TTS handler...")
        app.state.tts_handler = TTSHandler(
            voice=settings.TTS_VOICE,
            model_dir=settings.TTS_MODEL_DIR
        )
        logger.info("TTS handler initialized")
    except Exception as e:
        logger.error(f"Failed to initialize TTS handler: {e}")
        app.state.tts_handler = None
    
    try:
        logger.info("Initializing LLM handler...")
        device = settings.get_device()
        n_gpu_layers = -1 if device == "cuda" else 0
        
        app.state.llm_handler = LLMHandler(
            model_name=settings.LLM_MODEL,
            model_dir=settings.LLM_MODEL_DIR,
            n_gpu_layers=n_gpu_layers
        )
        logger.info("LLM handler initialized")
    except Exception as e:
        logger.error(f"Failed to initialize LLM handler: {e}")
        app.state.llm_handler = None
    
    logger.info("API ready to serve requests")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Language Learning Assistant API")


# Create FastAPI app
app = FastAPI(
    title="Local Language Learning Assistant",
    description="AI-powered language learning through conversation",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(conversation_router)

# Mount static files (frontend)
frontend_dir = Path(__file__).parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


@app.get("/api")
async def api_root():
    """API root endpoint."""
    return {
        "message": "Local Language Learning Assistant API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
