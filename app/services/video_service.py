"""
Video service - Business logic for video operations.
Handles video upload, download, and management.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile
from pathlib import Path

from app.config import get_settings
from app.models import Video
from app.schemas import VideoCreate
from app.repositories import video_repository
from app.utils.file_utils import save_upload_file, delete_file_safe, ensure_directory_exists, generate_unique_filename
from app.utils.video_utils import get_video_info
from app.utils.downloader import download_video_from_url
from app.utils.validators import is_valid_url, validate_video_file

# Valid video statuses
VALID_STATUSES = ["uploaded", "processing", "completed", "failed"]


# ============================================================================
# Upload Operations
# ============================================================================

async def handle_video_upload(db: Session, file: UploadFile) -> Video:
    """
    Handle video file upload process.

    Args:
        db: Database session
        file: Uploaded file from FastAPI

    Returns:
        Video: Created video record

    Raises:
        ValueError: If file format is invalid or size exceeds limit
    """
    settings = get_settings()

    # Validate file extension
    if not validate_video_file(file.filename):
        raise ValueError(f"Unsupported file format: {file.filename}")

    # Validate file size
    max_size = settings.max_upload_size_mb * 1024 * 1024  # Convert MB to bytes
    if hasattr(file, 'size') and file.size and file.size > max_size:
        raise ValueError(f"File size exceeds maximum allowed size of {settings.max_upload_size_mb}MB")

    # Ensure videos directory exists
    ensure_directory_exists(settings.videos_dir)

    # Generate unique filename and save uploaded file
    unique_filename = generate_unique_filename(file.filename)
    destination = Path(settings.videos_dir) / unique_filename
    _, file_size = await save_upload_file(file, destination)
    filepath = str(destination)

    # Extract video metadata
    try:
        metadata = get_video_info(Path(filepath))
        if not metadata:
            raise ValueError("Could not extract video metadata")
    except Exception as e:
        # If metadata extraction fails, delete the file and raise error
        delete_file_safe(Path(filepath))
        raise ValueError(f"Failed to process video file: {str(e)}")

    # Create video record
    video_data = VideoCreate(
        filename=unique_filename,
        filepath=filepath,
        source_type="upload",
        source_url=None,
        file_size=metadata.get("file_size"),
        duration=metadata.get("duration"),
        status="uploaded"
    )

    return video_repository.create_video(db, video_data)


# ============================================================================
# Download Operations
# ============================================================================

async def handle_video_download(
    db: Session,
    url: str,
    title: Optional[str] = None
) -> Video:
    """
    Handle video download from URL.

    Args:
        db: Database session
        url: Video URL (YouTube, etc.)
        title: Optional custom title

    Returns:
        Video: Created video record

    Raises:
        ValueError: If URL is invalid
        Exception: If download fails
    """
    settings = get_settings()

    # Validate URL
    if not is_valid_url(url):
        raise ValueError(f"Invalid URL: {url}")

    # Ensure videos directory exists
    ensure_directory_exists(settings.videos_dir)

    # Download video
    try:
        download_result = download_video_from_url(
            url=url,
            output_dir=str(settings.videos_dir),
            filename=title
        )
    except Exception as e:
        raise Exception(f"Download failed: {str(e)}")

    # Create video record
    video_data = VideoCreate(
        filename=download_result["filename"],
        filepath=download_result["filepath"],
        source_type="download",
        source_url=url,
        file_size=download_result.get("file_size"),
        duration=download_result.get("duration"),
        status="uploaded"
    )

    return video_repository.create_video(db, video_data)


# ============================================================================
# Query Operations
# ============================================================================

def get_video_list(
    db: Session,
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Get paginated video list with optional status filter.

    Args:
        db: Database session
        status: Optional status filter
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        Dict containing total count and video items
    """
    if status:
        videos = video_repository.get_videos_by_status(db, status)
        total = len(videos)
        items = videos[offset:offset + limit]
    else:
        total = video_repository.count_videos(db)
        items = video_repository.get_videos_paginated(db, skip=offset, limit=limit)

    return {
        "total": total,
        "items": items
    }


def get_video_by_id(db: Session, video_id: int) -> Video:
    """
    Get specific video by ID.

    Args:
        db: Database session
        video_id: Video ID

    Returns:
        Video: Video record

    Raises:
        ValueError: If video not found
    """
    video = video_repository.get_video_by_id(db, video_id)
    if not video:
        raise ValueError(f"Video not found with id: {video_id}")

    return video


# ============================================================================
# Update Operations
# ============================================================================

def update_video_status(db: Session, video_id: int, status: str) -> Video:
    """
    Update video status.

    Args:
        db: Database session
        video_id: Video ID
        status: New status

    Returns:
        Video: Updated video record

    Raises:
        ValueError: If status is invalid or video not found
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}. Must be one of {VALID_STATUSES}")

    video = video_repository.update_video_status(db, video_id, status)
    if not video:
        raise ValueError(f"Video not found with id: {video_id}")

    return video


# ============================================================================
# Delete Operations
# ============================================================================

def delete_video(db: Session, video_id: int) -> bool:
    """
    Delete video and associated file.

    Args:
        db: Database session
        video_id: Video ID

    Returns:
        bool: True if deleted, False if not found
    """
    # Get video to retrieve filepath
    video = video_repository.get_video_by_id(db, video_id)
    if not video:
        return False

    # Delete database record (will CASCADE delete related records)
    video_repository.delete_video(db, video_id)

    # Delete physical file
    try:
        delete_file_safe(Path(video.filepath))
    except Exception:
        # Log error but don't fail if file deletion fails
        pass

    return True
