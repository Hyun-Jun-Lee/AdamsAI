"""
Transcript repository - Data access layer for Transcript model.
Pure functional approach for database operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import Transcript
from app.schemas import TranscriptCreate


# ============================================================================
# CREATE Operations
# ============================================================================

def create_transcript(db: Session, transcript_data: TranscriptCreate) -> Transcript:
    """
    Create a new transcript record.

    Args:
        db: Database session
        transcript_data: Transcript creation data

    Returns:
        Transcript: Created transcript instance
    """
    transcript = Transcript(**transcript_data.model_dump())
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    return transcript


# ============================================================================
# READ Operations
# ============================================================================

def get_transcript_by_id(db: Session, transcript_id: int) -> Optional[Transcript]:
    """
    Retrieve transcript by ID.

    Args:
        db: Database session
        transcript_id: Transcript ID

    Returns:
        Optional[Transcript]: Transcript instance or None if not found
    """
    return db.query(Transcript).filter(Transcript.id == transcript_id).first()


def get_transcripts_by_audio_id(db: Session, audio_id: int) -> List[Transcript]:
    """
    Retrieve all transcripts for a specific audio.

    Args:
        db: Database session
        audio_id: Audio ID

    Returns:
        List[Transcript]: List of transcripts for the audio
    """
    return db.query(Transcript).filter(Transcript.audio_id == audio_id).order_by(Transcript.created_at.desc()).all()


def get_all_transcripts(db: Session) -> List[Transcript]:
    """
    Retrieve all transcripts.

    Args:
        db: Database session

    Returns:
        List[Transcript]: List of all transcripts
    """
    return db.query(Transcript).order_by(Transcript.created_at.desc()).all()


def get_transcripts_by_language(db: Session, language: str) -> List[Transcript]:
    """
    Retrieve transcripts filtered by language.

    Args:
        db: Database session
        language: Language code (e.g., 'ko', 'en')

    Returns:
        List[Transcript]: List of transcripts with matching language
    """
    return db.query(Transcript).filter(Transcript.language == language).order_by(Transcript.created_at.desc()).all()


def get_transcripts_paginated(db: Session, skip: int = 0, limit: int = 10) -> List[Transcript]:
    """
    Retrieve transcripts with pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List[Transcript]: Paginated list of transcripts
    """
    return db.query(Transcript).order_by(Transcript.created_at.desc()).offset(skip).limit(limit).all()


def search_transcripts_by_text(db: Session, search_query: str) -> List[Transcript]:
    """
    Search transcripts by text content (case-insensitive).

    Args:
        db: Database session
        search_query: Text to search for

    Returns:
        List[Transcript]: List of transcripts containing the search query

    Example:
        >>> results = search_transcripts_by_text(db, "real estate")
    """
    search_pattern = f"%{search_query}%"
    return db.query(Transcript).filter(
        Transcript.text.ilike(search_pattern)
    ).order_by(Transcript.created_at.desc()).all()


# ============================================================================
# UPDATE Operations
# ============================================================================

def update_transcript_text(db: Session, transcript_id: int, text: str) -> Optional[Transcript]:
    """
    Update transcript text.

    Args:
        db: Database session
        transcript_id: Transcript ID
        text: New transcript text

    Returns:
        Optional[Transcript]: Updated transcript or None if not found
    """
    transcript = get_transcript_by_id(db, transcript_id)
    if not transcript:
        return None

    transcript.text = text
    db.commit()
    db.refresh(transcript)
    return transcript


# ============================================================================
# DELETE Operations
# ============================================================================

def delete_transcript(db: Session, transcript_id: int) -> bool:
    """
    Delete transcript by ID.
    CASCADE delete will remove all related Summary records.

    Args:
        db: Database session
        transcript_id: Transcript ID

    Returns:
        bool: True if deleted, False if not found
    """
    transcript = get_transcript_by_id(db, transcript_id)
    if not transcript:
        return False

    db.delete(transcript)
    db.commit()
    return True


# ============================================================================
# COUNT Operations
# ============================================================================

def count_transcripts(db: Session) -> int:
    """
    Count total number of transcripts.

    Args:
        db: Database session

    Returns:
        int: Total transcript count
    """
    return db.query(Transcript).count()


def count_transcripts_by_language(db: Session, language: str) -> int:
    """
    Count transcripts by language.

    Args:
        db: Database session
        language: Language code to filter

    Returns:
        int: Count of transcripts with matching language
    """
    return db.query(Transcript).filter(Transcript.language == language).count()
