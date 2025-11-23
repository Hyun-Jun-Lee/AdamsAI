"""
Test suite for video_service.
Tests business logic with mocked external dependencies.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from fastapi import UploadFile
from app.services import video_service
from app.models import Video


# ============================================================================
# Query Tests (No mocking needed - pure business logic)
# ============================================================================

def test_get_video_list(db_session, video_factory):
    """Test retrieving video list with pagination."""
    for i in range(5):
        video_factory(filename=f"video_{i}.mp4", status="uploaded")

    result = video_service.get_video_list(db_session, limit=3, offset=0)

    assert result["total"] == 5
    assert len(result["items"]) == 3
    assert all(isinstance(v, Video) for v in result["items"])


def test_get_video_list_with_status_filter(db_session, video_factory):
    """Test video list filtering by status."""
    video_factory(status="uploaded")
    video_factory(status="uploaded")
    video_factory(status="processing")

    result = video_service.get_video_list(db_session, status="uploaded")

    assert result["total"] == 2
    assert all(v.status == "uploaded" for v in result["items"])


def test_get_video_list_pagination(db_session, video_factory):
    """Test video list pagination."""
    for i in range(10):
        video_factory()

    # First page
    page1 = video_service.get_video_list(db_session, limit=3, offset=0)
    assert len(page1["items"]) == 3

    # Second page
    page2 = video_service.get_video_list(db_session, limit=3, offset=3)
    assert len(page2["items"]) == 3

    # Third page
    page3 = video_service.get_video_list(db_session, limit=3, offset=6)
    assert len(page3["items"]) == 3


def test_get_video_by_id_success(db_session, video_factory):
    """Test retrieving specific video by ID."""
    video = video_factory(filename="test.mp4")

    result = video_service.get_video_by_id(db_session, video.id)

    assert result is not None
    assert result.id == video.id
    assert result.filename == "test.mp4"


def test_get_video_by_id_not_found(db_session):
    """Test retrieving non-existent video raises error."""
    with pytest.raises(ValueError, match="Video not found"):
        video_service.get_video_by_id(db_session, 99999)


# ============================================================================
# Status Update Tests
# ============================================================================

def test_update_video_status_success(db_session, video_factory):
    """Test updating video status."""
    video = video_factory(status="uploaded")

    result = video_service.update_video_status(db_session, video.id, "processing")

    assert result.status == "processing"


def test_update_video_status_invalid(db_session, video_factory):
    """Test updating with invalid status raises error."""
    video = video_factory()

    with pytest.raises(ValueError, match="Invalid status"):
        video_service.update_video_status(db_session, video.id, "invalid_status")


def test_update_video_status_not_found(db_session):
    """Test updating non-existent video raises error."""
    with pytest.raises(ValueError, match="Video not found"):
        video_service.update_video_status(db_session, 99999, "processing")


def test_update_video_status_all_valid_statuses(db_session, video_factory):
    """Test all valid status transitions."""
    valid_statuses = ["uploaded", "processing", "completed", "failed"]

    for status in valid_statuses:
        video = video_factory()
        result = video_service.update_video_status(db_session, video.id, status)
        assert result.status == status


# ============================================================================
# Delete Tests
# ============================================================================

def test_delete_video_success(db_session, video_factory):
    """Test video deletion from database."""
    video = video_factory()
    video_id = video.id

    with patch("app.services.video_service.delete_file_safe"):
        result = video_service.delete_video(db_session, video_id)

    assert result is True

    # Verify video deleted from database
    from app.repositories import video_repository
    deleted_video = video_repository.get_video_by_id(db_session, video_id)
    assert deleted_video is None


def test_delete_video_not_found(db_session):
    """Test deleting non-existent video."""
    result = video_service.delete_video(db_session, 99999)
    assert result is False


def test_delete_video_calls_file_deletion(db_session, video_factory):
    """Test that file deletion is attempted."""
    video = video_factory(filepath="/test/path/video.mp4")

    with patch("app.services.video_service.delete_file_safe") as mock_delete:
        video_service.delete_video(db_session, video.id)
        mock_delete.assert_called_once()


# ============================================================================
# Upload Tests (Mocked external dependencies)
# ============================================================================

@pytest.mark.asyncio
async def test_handle_video_upload_success(db_session, temp_storage_dir, monkeypatch):
    """Test successful video upload with mocked file operations."""
    from app import config
    settings = config.get_settings()
    monkeypatch.setattr(settings, "videos_dir", temp_storage_dir / "videos")
    monkeypatch.setattr(settings, "max_upload_size_mb", 500)

    # Create mock upload file
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test_video.mp4"
    mock_file.content_type = "video/mp4"
    mock_file.size = 1024 * 1024  # 1MB

    # Mock all external file operations
    with patch("app.services.video_service.ensure_directory_exists"), \
         patch("app.services.video_service.generate_unique_filename", return_value="unique_test.mp4"), \
         patch("app.services.video_service.save_upload_file", new_callable=AsyncMock) as mock_save, \
         patch("app.services.video_service.get_video_info") as mock_info:

        mock_save.return_value = ("unique_test.mp4", 1024 * 1024)
        mock_info.return_value = {
            "duration": 120.5,
            "file_size": 1024 * 1024,
            "resolution": (1920, 1080)
        }

        result = await video_service.handle_video_upload(db_session, mock_file)

    assert result is not None
    assert result.filename == "unique_test.mp4"
    assert result.source_type == "upload"
    assert result.status == "uploaded"
    assert result.duration == 120.5


@pytest.mark.asyncio
async def test_handle_video_upload_invalid_format(db_session, monkeypatch):
    """Test upload with invalid file format."""
    from app import config
    settings = config.get_settings()
    monkeypatch.setattr(settings, "max_upload_size_mb", 500)

    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.txt"
    mock_file.content_type = "text/plain"

    with pytest.raises(ValueError, match="Unsupported file format"):
        await video_service.handle_video_upload(db_session, mock_file)


@pytest.mark.asyncio
async def test_handle_video_upload_file_too_large(db_session, monkeypatch):
    """Test upload with file exceeding size limit."""
    from app import config
    settings = config.get_settings()
    monkeypatch.setattr(settings, "max_upload_size_mb", 10)

    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "large_video.mp4"
    mock_file.content_type = "video/mp4"
    mock_file.size = 20 * 1024 * 1024  # 20MB

    with pytest.raises(ValueError, match="File size exceeds maximum"):
        await video_service.handle_video_upload(db_session, mock_file)


@pytest.mark.asyncio
async def test_handle_video_upload_metadata_extraction_fails(db_session, temp_storage_dir, monkeypatch):
    """Test upload when video metadata extraction fails."""
    from app import config
    settings = config.get_settings()
    monkeypatch.setattr(settings, "videos_dir", temp_storage_dir / "videos")
    monkeypatch.setattr(settings, "max_upload_size_mb", 500)

    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "corrupted.mp4"

    with patch("app.services.video_service.ensure_directory_exists"), \
         patch("app.services.video_service.generate_unique_filename", return_value="unique.mp4"), \
         patch("app.services.video_service.save_upload_file", new_callable=AsyncMock) as mock_save, \
         patch("app.services.video_service.get_video_info", return_value=None), \
         patch("app.services.video_service.delete_file_safe") as mock_delete:

        mock_save.return_value = ("unique.mp4", 1024)

        with pytest.raises(ValueError, match="Failed to process video file"):
            await video_service.handle_video_upload(db_session, mock_file)

        # Verify file cleanup was attempted
        mock_delete.assert_called_once()


# ============================================================================
# Download Tests (Mocked external dependencies)
# ============================================================================

@pytest.mark.asyncio
async def test_handle_video_download_success(db_session, temp_storage_dir, monkeypatch):
    """Test successful video download with mocked downloader."""
    from app import config
    settings = config.get_settings()
    monkeypatch.setattr(settings, "videos_dir", temp_storage_dir / "videos")

    test_url = "https://youtube.com/watch?v=test123"
    test_title = "Test Video"

    with patch("app.services.video_service.ensure_directory_exists"), \
         patch("app.services.video_service.download_video_from_url") as mock_download:

        mock_download.return_value = {
            "filepath": str(temp_storage_dir / "videos" / "test_video.mp4"),
            "filename": "test_video.mp4",
            "file_size": 5 * 1024 * 1024,
            "duration": 180.0
        }

        result = await video_service.handle_video_download(db_session, test_url, test_title)

    assert result is not None
    assert result.source_type == "download"
    assert result.source_url == test_url
    assert result.status == "uploaded"
    assert result.duration == 180.0


@pytest.mark.asyncio
async def test_handle_video_download_invalid_url(db_session, monkeypatch):
    """Test download with invalid URL."""
    from app import config
    settings = config.get_settings()
    monkeypatch.setattr(settings, "videos_dir", Path("/tmp/videos"))

    invalid_url = "not-a-url"

    with pytest.raises(ValueError, match="Invalid URL"):
        await video_service.handle_video_download(db_session, invalid_url)


@pytest.mark.asyncio
async def test_handle_video_download_failure(db_session, temp_storage_dir, monkeypatch):
    """Test download failure handling."""
    from app import config
    settings = config.get_settings()
    monkeypatch.setattr(settings, "videos_dir", temp_storage_dir / "videos")

    test_url = "https://youtube.com/watch?v=fail"

    with patch("app.services.video_service.ensure_directory_exists"), \
         patch("app.services.video_service.download_video_from_url") as mock_download:

        mock_download.side_effect = Exception("Download failed")

        with pytest.raises(Exception, match="Download failed"):
            await video_service.handle_video_download(db_session, test_url)
