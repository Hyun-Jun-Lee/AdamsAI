"""
Audio repository - Data access layer for Audio model.
Pure functional approach for database operations.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import Audio
from app.schemas import AudioCreate


# ============================================================================
# CREATE Operations
# ============================================================================

def create_audio(db: Session, audio_data: AudioCreate) -> Audio:
    """
    Create a new audio record.

    Args:
        db: Database session
        audio_data: Audio creation data

    Returns:
        Audio: Created audio instance
    """
    audio = Audio(**audio_data.model_dump())
    db.add(audio)
    db.commit()
    db.refresh(audio)
    return audio


# ============================================================================
# READ Operations
# ============================================================================

def get_audio_by_id(db: Session, audio_id: int) -> Optional[Audio]:
    """
    Retrieve audio by ID.

    Args:
        db: Database session
        audio_id: Audio ID

    Returns:
        Optional[Audio]: Audio instance or None if not found
    """
    return db.query(Audio).filter(Audio.id == audio_id).first()


def get_audio_by_filepath(db: Session, filepath: str) -> Optional[Audio]:
    """
    Retrieve audio by filepath.

    Args:
        db: Database session
        filepath: File path to search

    Returns:
        Optional[Audio]: Audio instance or None if not found
    """
    return db.query(Audio).filter(Audio.filepath == filepath).first()


def get_audios_by_video_id(db: Session, video_id: int) -> List[Audio]:
    """
    Retrieve all audios for a specific video.

    Args:
        db: Database session
        video_id: Video ID

    Returns:
        List[Audio]: List of audios for the video
    """
    return db.query(Audio).filter(Audio.video_id == video_id).order_by(Audio.created_at.desc()).all()


def get_all_audios(db: Session) -> List[Audio]:
    """
    Retrieve all audios.

    Args:
        db: Database session

    Returns:
        List[Audio]: List of all audios
    """
    return db.query(Audio).order_by(Audio.created_at.desc()).all()


def get_audios_by_status(db: Session, status: str) -> List[Audio]:
    """
    Retrieve audios filtered by status.

    Args:
        db: Database session
        status: Status to filter (e.g., 'extracted', 'processing')

    Returns:
        List[Audio]: List of audios with matching status
    """
    return db.query(Audio).filter(Audio.status == status).order_by(Audio.created_at.desc()).all()


def get_audios_paginated(db: Session, skip: int = 0, limit: int = 10) -> List[Audio]:
    """
    Retrieve audios with pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List[Audio]: Paginated list of audios
    """
    return db.query(Audio).order_by(Audio.created_at.desc()).offset(skip).limit(limit).all()


# ============================================================================
# UPDATE Operations
# ============================================================================

def update_audio_status(db: Session, audio_id: int, status: str) -> Optional[Audio]:
    """
    Update audio status.

    Args:
        db: Database session
        audio_id: Audio ID
        status: New status value

    Returns:
        Optional[Audio]: Updated audio or None if not found
    """
    audio = get_audio_by_id(db, audio_id)
    if not audio:
        return None

    audio.status = status
    db.commit()
    db.refresh(audio)
    return audio


def update_audio_metadata(db: Session, audio_id: int, updates: Dict[str, Any]) -> Optional[Audio]:
    """
    Update audio metadata fields.

    Args:
        db: Database session
        audio_id: Audio ID
        updates: Dictionary of fields to update

    Returns:
        Optional[Audio]: Updated audio or None if not found
    """
    audio = get_audio_by_id(db, audio_id)
    if not audio:
        return None

    for key, value in updates.items():
        if hasattr(audio, key):
            setattr(audio, key, value)

    db.commit()
    db.refresh(audio)
    return audio


# ============================================================================
# DELETE Operations
# ============================================================================

def delete_audio(db: Session, audio_id: int) -> bool:
    """
    Delete audio by ID.
    CASCADE delete will remove all related Transcript and Summary records.

    Args:
        db: Database session
        audio_id: Audio ID

    Returns:
        bool: True if deleted, False if not found
    """
    audio = get_audio_by_id(db, audio_id)
    if not audio:
        return False

    db.delete(audio)
    db.commit()
    return True


# ============================================================================
# COUNT Operations
# ============================================================================

def count_audios(db: Session) -> int:
    """
    Count total number of audios.

    Args:
        db: Database session

    Returns:
        int: Total audio count
    """
    return db.query(Audio).count()


def count_audios_by_status(db: Session, status: str) -> int:
    """
    Count audios by status.

    Args:
        db: Database session
        status: Status to filter

    Returns:
        int: Count of audios with matching status
    """
    return db.query(Audio).filter(Audio.status == status).count()
