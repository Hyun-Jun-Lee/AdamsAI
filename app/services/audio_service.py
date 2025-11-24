"""
Audio service - Business logic for audio extraction operations.
Handles audio extraction from videos and audio management.
"""

import logging
import traceback
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from pathlib import Path

from app.config import get_settings
from app.models import Audio
from app.schemas import AudioCreate
from app.repositories import audio_repository, video_repository
from app.utils.audio_utils import extract_audio_from_video
from app.utils.file_utils import ensure_directory_exists, delete_file_safe

logger = logging.getLogger(__name__)

# Valid audio statuses
VALID_STATUSES = ["extracted", "processing", "completed", "failed"]


# ============================================================================
# Extraction Operations
# ============================================================================

async def handle_audio_extraction(db: Session, video_id: int) -> Audio:
    """
    Extract audio from video file.

    Args:
        db: Database session
        video_id: Video ID to extract audio from

    Returns:
        Audio: Created audio record

    Raises:
        ValueError: If video not found or extraction fails
    """
    try:
        settings = get_settings()

        # Get video record
        video = video_repository.get_video_by_id(db, video_id)
        if not video:
            logger.error(f"Video not found with id: {video_id}")
            raise ValueError(f"Video not found with id: {video_id}")

        # Ensure audios directory exists
        ensure_directory_exists(settings.audios_dir)

        # Generate output audio filename
        video_path = Path(video.filepath)
        audio_filename = video_path.stem + ".mp3"
        output_path = Path(settings.audios_dir) / audio_filename

        # Extract audio from video
        try:
            success, duration = extract_audio_from_video(
                video_path=video_path,
                output_path=output_path,
                bitrate=settings.default_audio_bitrate
            )

            if not success:
                logger.error(f"Audio extraction failed for video_id={video_id}")
                raise ValueError("Audio extraction failed")

        except Exception as e:
            logger.error(f"Audio extraction failed for video_id={video_id}: {str(e)}\n{traceback.format_exc()}")
            raise ValueError(f"Audio extraction failed: {str(e)}")

        # Get file size
        file_size = output_path.stat().st_size if output_path.exists() else None

        # Create audio record
        audio_data = AudioCreate(
            video_id=video_id,
            filename=audio_filename,
            filepath=str(output_path),
            file_size=file_size,
            duration=duration,
            status="extracted"
        )

        return audio_repository.create_audio(db, audio_data)

    except ValueError:
        # Re-raise ValueError as-is (already logged above)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in handle_audio_extraction for video_id={video_id}: {str(e)}\n{traceback.format_exc()}")
        raise


# ============================================================================
# Query Operations
# ============================================================================

def get_audio_list(
    db: Session,
    video_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Get paginated audio list with optional video filter.

    Args:
        db: Database session
        video_id: Optional video ID filter
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        Dict containing total count and audio items
    """
    try:
        if video_id:
            audios = audio_repository.get_audios_by_video_id(db, video_id)
            total = len(audios)
            items = audios[offset:offset + limit]
        else:
            total = audio_repository.count_audios(db)
            items = audio_repository.get_audios_paginated(db, skip=offset, limit=limit)

        return {
            "total": total,
            "items": items
        }
    except Exception as e:
        logger.error(f"Error in get_audio_list (video_id={video_id}, limit={limit}, offset={offset}): {str(e)}\n{traceback.format_exc()}")
        raise


def get_audio_by_id(db: Session, audio_id: int) -> Audio:
    """
    Get specific audio by ID.

    Args:
        db: Database session
        audio_id: Audio ID

    Returns:
        Audio: Audio record

    Raises:
        ValueError: If audio not found
    """
    try:
        audio = audio_repository.get_audio_by_id(db, audio_id)
        if not audio:
            logger.error(f"Audio not found with id: {audio_id}")
            raise ValueError(f"Audio not found with id: {audio_id}")

        return audio
    except ValueError:
        # Re-raise ValueError as-is (already logged above)
        raise
    except Exception as e:
        logger.error(f"Error in get_audio_by_id for audio_id={audio_id}: {str(e)}\n{traceback.format_exc()}")
        raise


# ============================================================================
# Update Operations
# ============================================================================

def update_audio_status(db: Session, audio_id: int, status: str) -> Audio:
    """
    Update audio status.

    Args:
        db: Database session
        audio_id: Audio ID
        status: New status

    Returns:
        Audio: Updated audio record

    Raises:
        ValueError: If status is invalid or audio not found
    """
    try:
        if status not in VALID_STATUSES:
            logger.error(f"Invalid status '{status}' for audio_id={audio_id}. Must be one of {VALID_STATUSES}")
            raise ValueError(f"Invalid status: {status}. Must be one of {VALID_STATUSES}")

        audio = audio_repository.update_audio_status(db, audio_id, status)
        if not audio:
            logger.error(f"Audio not found with id: {audio_id}")
            raise ValueError(f"Audio not found with id: {audio_id}")

        return audio
    except ValueError:
        # Re-raise ValueError as-is (already logged above)
        raise
    except Exception as e:
        logger.error(f"Error in update_audio_status for audio_id={audio_id}, status={status}: {str(e)}\n{traceback.format_exc()}")
        raise


# ============================================================================
# Delete Operations
# ============================================================================

def delete_audio(db: Session, audio_id: int) -> bool:
    """
    Delete audio and associated file.

    Args:
        db: Database session
        audio_id: Audio ID

    Returns:
        bool: True if deleted, False if not found
    """
    try:
        # Get audio to retrieve filepath
        audio = audio_repository.get_audio_by_id(db, audio_id)
        if not audio:
            logger.warning(f"Audio not found for deletion: audio_id={audio_id}")
            return False

        # Delete database record (will CASCADE delete related records)
        audio_repository.delete_audio(db, audio_id)

        # Delete physical file
        try:
            delete_file_safe(Path(audio.filepath))
        except Exception as e:
            # Log error but don't fail if file deletion fails
            logger.error(f"Failed to delete audio file {audio.filepath} for audio_id={audio_id}: {str(e)}\n{traceback.format_exc()}")

        return True
    except Exception as e:
        logger.error(f"Error in delete_audio for audio_id={audio_id}: {str(e)}\n{traceback.format_exc()}")
        raise
