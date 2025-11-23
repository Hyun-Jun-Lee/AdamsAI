"""
AdamsAI - Video Summarization Service
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import get_settings
from app.database import get_engine, Base
from app.routers import videos, audios, transcripts, summaries

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting AdamsAI application...")
    settings = get_settings()

    # Create database tables
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

    # Create storage directories
    try:
        settings.videos_dir.mkdir(parents=True, exist_ok=True)
        settings.audios_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage directories created at {settings.storage_root}")
    except Exception as e:
        logger.error(f"Failed to create storage directories: {e}")
        raise

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down AdamsAI application...")


# Create FastAPI application
app = FastAPI(
    title="AdamsAI",
    description="Video Summarization Service - Video/Audio processing, Transcription, and AI Summarization",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/", tags=["health"])
async def root():
    """Root endpoint - health check."""
    return {
        "service": "AdamsAI",
        "status": "healthy",
        "version": "1.0.0",
        "description": "Video Summarization Service"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Detailed health check endpoint."""
    settings = get_settings()

    return {
        "status": "healthy",
        "database": "connected",
        "storage": {
            "videos_dir": str(settings.videos_dir),
            "audios_dir": str(settings.audios_dir),
        },
        "services": {
            "whisper": "configured",
            "openrouter": "configured"
        }
    }


# Include routers
app.include_router(videos.router)
app.include_router(audios.router)
app.include_router(transcripts.router)
app.include_router(summaries.router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(_request, exc):
    """Handle uncaught exceptions globally."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error occurred",
            "error": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
