"""
STT (Speech-To-Text) service - Business logic for transcription operations.
Handles audio transcription using OpenAI Whisper API.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from pathlib import Path
import httpx

from app.config import get_settings
from app.models import Transcript
from app.schemas import TranscriptCreate
from app.repositories import transcript_repository, audio_repository


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
    settings = get_settings()

    # Prepare request
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}"
    }

    # Open audio file and send request
    with open(audio_filepath, "rb") as audio_file:
        files = {
            "file": audio_file,
            "model": (None, settings.default_whisper_model),
            "language": (None, language)
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, headers=headers, files=files)

    if response.status_code != 200:
        raise Exception(f"Whisper API error: {response.status_code} - {response.text}")

    result = response.json()
    return result.get("text", "")


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
    settings = get_settings()

    # Get audio record
    audio = audio_repository.get_audio_by_id(db, audio_id)
    if not audio:
        raise ValueError(f"Audio not found with id: {audio_id}")

    # Call Whisper API
    try:
        transcribed_text = await call_whisper_api(
            audio_filepath=audio.filepath,
            language=language
        )
    except Exception as e:
        raise ValueError(f"Transcription failed: {str(e)}")

    if not transcribed_text:
        raise ValueError("Transcription returned empty text")

    # Create transcript record
    transcript_data = TranscriptCreate(
        audio_id=audio_id,
        text=transcribed_text,
        language=language,
        model=settings.default_whisper_model
    )

    return transcript_repository.create_transcript(db, transcript_data)


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
    transcript = transcript_repository.get_transcript_by_id(db, transcript_id)
    if not transcript:
        raise ValueError(f"Transcript not found with id: {transcript_id}")

    return transcript


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
    transcripts = transcript_repository.search_transcripts_by_text(db, search_query)
    total = len(transcripts)
    items = transcripts[:limit]

    return {
        "total": total,
        "items": items
    }
