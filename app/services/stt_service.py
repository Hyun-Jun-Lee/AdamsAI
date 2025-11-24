"""
STT (Speech-To-Text) service - Business logic for transcription operations.
Handles audio transcription using OpenAI Whisper API.
"""

import logging
import traceback
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from pathlib import Path
import httpx

from app.config import get_settings
from app.models import Transcript
from app.schemas import TranscriptCreate
from app.repositories import transcript_repository, audio_repository

logger = logging.getLogger(__name__)


# ============================================================================
# External API Operations
# ============================================================================

async def call_whisper_api(audio_filepath: str, language: str = "ko") -> str:
    """
    Call OpenAI Whisper API for speech-to-text transcription.

    Args:
        audio_filepath: Path to audio file
        language: Language code (e.g., 'ko', 'en')

    Returns:
        str: Transcribed text

    Raises:
        Exception: If API call fails
    """
    try:
        settings = get_settings()

        # Prepare request
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}"
        }

        # Open audio file and send request
        with open(audio_filepath, "rb") as audio_file:
            files = {
                "file": (Path(audio_filepath).name, audio_file, "audio/mpeg"),
            }
            data = {
                "model": settings.default_whisper_model,
                "language": language
            }

            # Use longer timeout and larger limits for file uploads
            timeout = httpx.Timeout(
                connect=30.0,  # Connection timeout
                read=300.0,    # Read timeout (5 minutes)
                write=300.0,   # Write timeout (5 minutes)
                pool=30.0      # Pool timeout
            )

            limits = httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
                keepalive_expiry=30.0
            )

            async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    files=files,
                    data=data
                )

        if response.status_code != 200:
            logger.error(f"Whisper API error for {audio_filepath}: {response.status_code} - {response.text}")
            raise Exception(f"Whisper API error: {response.status_code} - {response.text}")

        result = response.json()
        return result.get("text", "")
    except httpx.RemoteProtocolError as e:
        logger.error(f"Connection error in call_whisper_api for {audio_filepath}: {str(e)}\n{traceback.format_exc()}")
        raise Exception(f"Network connection error during transcription. Please try again. Error: {str(e)}")
    except httpx.TimeoutException as e:
        logger.error(f"Timeout error in call_whisper_api for {audio_filepath}: {str(e)}\n{traceback.format_exc()}")
        raise Exception(f"Transcription timed out. The audio file may be too large. Error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in call_whisper_api for {audio_filepath}: {str(e)}\n{traceback.format_exc()}")
        raise


# ============================================================================
# Transcription Operations
# ============================================================================

async def handle_transcription(
    db: Session,
    audio_id: int,
    language: str = "ko"
) -> Transcript:
    """
    Handle audio transcription using Whisper API.

    Args:
        db: Database session
        audio_id: Audio ID to transcribe
        language: Language code (default: "ko")

    Returns:
        Transcript: Created transcript record

    Raises:
        ValueError: If audio not found or transcription fails
    """
    try:
        settings = get_settings()

        # Get audio record
        audio = audio_repository.get_audio_by_id(db, audio_id)
        if not audio:
            logger.error(f"Audio not found with id: {audio_id}")
            raise ValueError(f"Audio not found with id: {audio_id}")

        # Call Whisper API
        try:
            transcribed_text = await call_whisper_api(
                audio_filepath=audio.filepath,
                language=language
            )
        except Exception as e:
            logger.error(f"Transcription failed for audio_id={audio_id}: {str(e)}\n{traceback.format_exc()}")
            raise ValueError(f"Transcription failed: {str(e)}")

        if not transcribed_text:
            logger.error(f"Transcription returned empty text for audio_id={audio_id}")
            raise ValueError("Transcription returned empty text")

        # Create transcript record
        transcript_data = TranscriptCreate(
            audio_id=audio_id,
            text=transcribed_text,
            language=language,
            model=settings.default_whisper_model
        )

        return transcript_repository.create_transcript(db, transcript_data)
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in handle_transcription for audio_id={audio_id}: {str(e)}\n{traceback.format_exc()}")
        raise


# ============================================================================
# Query Operations
# ============================================================================

def get_transcript_list(
    db: Session,
    audio_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Get paginated transcript list with optional audio filter.

    Args:
        db: Database session
        audio_id: Optional audio ID filter
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        Dict containing total count and transcript items
    """
    try:
        if audio_id:
            transcripts = transcript_repository.get_transcripts_by_audio_id(db, audio_id)
            total = len(transcripts)
            items = transcripts[offset:offset + limit]
        else:
            total = transcript_repository.count_transcripts(db)
            items = transcript_repository.get_transcripts_paginated(db, skip=offset, limit=limit)

        return {
            "total": total,
            "items": items
        }
    except Exception as e:
        logger.error(f"Error in get_transcript_list (audio_id={audio_id}, limit={limit}, offset={offset}): {str(e)}\n{traceback.format_exc()}")
        raise


def get_transcript_by_id(db: Session, transcript_id: int) -> Transcript:
    """
    Get specific transcript by ID.

    Args:
        db: Database session
        transcript_id: Transcript ID

    Returns:
        Transcript: Transcript record

    Raises:
        ValueError: If transcript not found
    """
    try:
        transcript = transcript_repository.get_transcript_by_id(db, transcript_id)
        if not transcript:
            logger.error(f"Transcript not found with id: {transcript_id}")
            raise ValueError(f"Transcript not found with id: {transcript_id}")

        return transcript
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error in get_transcript_by_id for transcript_id={transcript_id}: {str(e)}\n{traceback.format_exc()}")
        raise


# ============================================================================
# Search Operations
# ============================================================================

def search_transcripts(
    db: Session,
    search_query: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search transcripts by text content.

    Args:
        db: Database session
        search_query: Text to search for
        limit: Maximum number of results

    Returns:
        Dict containing total count and transcript items
    """
    try:
        transcripts = transcript_repository.search_transcripts_by_text(db, search_query)
        total = len(transcripts)
        items = transcripts[:limit]

        return {
            "total": total,
            "items": items
        }
    except Exception as e:
        logger.error(f"Error in search_transcripts for query='{search_query}': {str(e)}\n{traceback.format_exc()}")
        raise
