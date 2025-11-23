"""
Video repository - Data access layer for Video model.
Pure functional approach for database operations.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import Video
from app.schemas import VideoCreate


# ============================================================================
# CREATE Operations
# ============================================================================

def create_video(db: Session, video_data: VideoCreate) -> Video:
    """
    Create a new video record.

    Args:
        db: Database session
        video_data: Video creation data

    Returns:
        Video: Created video instance

    Example:
        >>> video_data = VideoCreate(filename="test.mp4", filepath="/path/test.mp4", ...)
        >>> video = create_video(db, video_data)
    """
    video = Video(**video_data.model_dump())
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


# ============================================================================
# READ Operations
# ============================================================================

def get_video_by_id(db: Session, video_id: int) -> Optional[Video]:
    """
    Retrieve video by ID.

    Args:
        db: Database session
        video_id: Video ID

    Returns:
        Optional[Video]: Video instance or None if not found
    """
    return db.query(Video).filter(Video.id == video_id).first()


def get_video_by_filepath(db: Session, filepath: str) -> Optional[Video]:
    """
    Retrieve video by filepath.

    Args:
        db: Database session
        filepath: File path to search

    Returns:
        Optional[Video]: Video instance or None if not found
    """
    return db.query(Video).filter(Video.filepath == filepath).first()


def get_all_videos(db: Session) -> List[Video]:
    """
    Retrieve all videos.

    Args:
        db: Database session

    Returns:
        List[Video]: List of all videos
    """
    return db.query(Video).order_by(Video.created_at.desc()).all()


def get_videos_by_status(db: Session, status: str) -> List[Video]:
    """
    Retrieve videos filtered by status.

    Args:
        db: Database session
        status: Status to filter (e.g., 'uploaded', 'processing', 'completed')

    Returns:
        List[Video]: List of videos with matching status
    """
    return db.query(Video).filter(Video.status == status).order_by(Video.created_at.desc()).all()


def get_videos_by_source_type(db: Session, source_type: str) -> List[Video]:
    """
    Retrieve videos filtered by source type.

    Args:
        db: Database session
        source_type: Source type to filter ('upload' or 'download')

    Returns:
        List[Video]: List of videos with matching source type
    """
    return db.query(Video).filter(Video.source_type == source_type).order_by(Video.created_at.desc()).all()


def get_videos_paginated(db: Session, skip: int = 0, limit: int = 10) -> List[Video]:
    """
    Retrieve videos with pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List[Video]: Paginated list of videos

    Example:
        >>> page1 = get_videos_paginated(db, skip=0, limit=10)
        >>> page2 = get_videos_paginated(db, skip=10, limit=10)
    """
    return db.query(Video).order_by(Video.created_at.desc()).offset(skip).limit(limit).all()


# ============================================================================
# UPDATE Operations
# ============================================================================

def update_video_status(db: Session, video_id: int, status: str) -> Optional[Video]:
    """
    Update video status.

    Args:
        db: Database session
        video_id: Video ID
        status: New status value

    Returns:
        Optional[Video]: Updated video or None if not found
    """
    video = get_video_by_id(db, video_id)
    if not video:
        return None

    video.status = status
    db.commit()
    db.refresh(video)
    return video


def update_video_metadata(db: Session, video_id: int, updates: Dict[str, Any]) -> Optional[Video]:
    """
    Update video metadata fields.

    Args:
        db: Database session
        video_id: Video ID
        updates: Dictionary of fields to update

    Returns:
        Optional[Video]: Updated video or None if not found

    Example:
        >>> updates = {"duration": 120.5, "file_size": 1024000}
        >>> video = update_video_metadata(db, 1, updates)
    """
    video = get_video_by_id(db, video_id)
    if not video:
        return None

    for key, value in updates.items():
        if hasattr(video, key):
            setattr(video, key, value)

    db.commit()
    db.refresh(video)
    return video


# ============================================================================
# DELETE Operations
# ============================================================================

def delete_video(db: Session, video_id: int) -> bool:
    """
    Delete video by ID.
    CASCADE delete will remove all related Audio, Transcript, Summary records.

    Args:
        db: Database session
        video_id: Video ID

    Returns:
        bool: True if deleted, False if not found
    """
    video = get_video_by_id(db, video_id)
    if not video:
        return False

    db.delete(video)
    db.commit()
    return True


# ============================================================================
# COUNT Operations
# ============================================================================

def count_videos(db: Session) -> int:
    """
    Count total number of videos.

    Args:
        db: Database session

    Returns:
        int: Total video count
    """
    return db.query(Video).count()


def count_videos_by_status(db: Session, status: str) -> int:
    """
    Count videos by status.

    Args:
        db: Database session
        status: Status to filter

    Returns:
        int: Count of videos with matching status
    """
    return db.query(Video).filter(Video.status == status).count()
