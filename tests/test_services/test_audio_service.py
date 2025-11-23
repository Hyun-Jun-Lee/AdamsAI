"""
Test suite for audio_service.
Tests business logic with mocked external dependencies.
"""

import pytest
from unittest.mock import patch, Mock
from pathlib import Path
from app.services import audio_service
from app.models import Audio


# ============================================================================
# Query Tests (No mocking needed - pure business logic)
# ============================================================================

def test_get_audio_list(db_session, video_factory, audio_factory):
    """Test retrieving audio list with pagination."""
    video = video_factory()
    for i in range(5):
        audio_factory(video_id=video.id, filename=f"audio_{i}.mp3")

    result = audio_service.get_audio_list(db_session, limit=3, offset=0)

    assert result["total"] == 5
    assert len(result["items"]) == 3
    assert all(isinstance(a, Audio) for a in result["items"])


def test_get_audio_list_with_video_filter(db_session, video_factory, audio_factory):
    """Test audio list filtering by video."""
    video1 = video_factory()
    video2 = video_factory()
    audio_factory(video_id=video1.id)
    audio_factory(video_id=video1.id)
    audio_factory(video_id=video2.id)

    result = audio_service.get_audio_list(db_session, video_id=video1.id)

    assert result["total"] == 2
    assert all(a.video_id == video1.id for a in result["items"])


def test_get_audio_by_id_success(db_session, video_factory, audio_factory):
    """Test retrieving specific audio by ID."""
    video = video_factory()
    audio = audio_factory(video_id=video.id, filename="test.mp3")

    result = audio_service.get_audio_by_id(db_session, audio.id)

    assert result is not None
    assert result.id == audio.id
    assert result.filename == "test.mp3"


def test_get_audio_by_id_not_found(db_session):
    """Test retrieving non-existent audio raises error."""
    with pytest.raises(ValueError, match="Audio not found"):
        audio_service.get_audio_by_id(db_session, 99999)


# ============================================================================
# Status Update Tests
# ============================================================================

def test_update_audio_status_success(db_session, video_factory, audio_factory):
    """Test updating audio status."""
    video = video_factory()
    audio = audio_factory(video_id=video.id, status="extracted")

    result = audio_service.update_audio_status(db_session, audio.id, "processing")

    assert result.status == "processing"


def test_update_audio_status_invalid(db_session, video_factory, audio_factory):
    """Test updating with invalid status raises error."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)

    with pytest.raises(ValueError, match="Invalid status"):
        audio_service.update_audio_status(db_session, audio.id, "invalid_status")


def test_update_audio_status_not_found(db_session):
    """Test updating non-existent audio raises error."""
    with pytest.raises(ValueError, match="Audio not found"):
        audio_service.update_audio_status(db_session, 99999, "processing")


# ============================================================================
# Delete Tests
# ============================================================================

def test_delete_audio_success(db_session, video_factory, audio_factory):
    """Test audio deletion from database."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    audio_id = audio.id

    with patch("app.services.audio_service.delete_file_safe"):
        result = audio_service.delete_audio(db_session, audio_id)

    assert result is True

    # Verify audio deleted from database
    from app.repositories import audio_repository
    deleted_audio = audio_repository.get_audio_by_id(db_session, audio_id)
    assert deleted_audio is None


def test_delete_audio_not_found(db_session):
    """Test deleting non-existent audio."""
    result = audio_service.delete_audio(db_session, 99999)
    assert result is False


# ============================================================================
# Extraction Tests (Mocked external dependencies)
# ============================================================================

@pytest.mark.asyncio
async def test_handle_audio_extraction_success(db_session, video_factory, temp_storage_dir, monkeypatch):
    """Test successful audio extraction with mocked operations."""
    from app import config
    settings = config.get_settings()
    monkeypatch.setattr(settings, "audios_dir", temp_storage_dir / "audios")
    monkeypatch.setattr(settings, "default_audio_bitrate", "192k")

    video = video_factory()

    with patch("app.services.audio_service.ensure_directory_exists"), \
         patch("app.services.audio_service.extract_audio_from_video") as mock_extract:

        mock_extract.return_value = {
            "filepath": str(temp_storage_dir / "audios" / "test_audio.mp3"),
            "filename": "test_audio.mp3",
            "file_size": 512 * 1024,
            "duration": 120.0
        }

        result = await audio_service.handle_audio_extraction(db_session, video.id)

    assert result is not None
    assert result.video_id == video.id
    assert result.filename == "test_audio.mp3"
    assert result.status == "extracted"
    assert result.duration == 120.0


@pytest.mark.asyncio
async def test_handle_audio_extraction_video_not_found(db_session):
    """Test extraction with non-existent video."""
    with pytest.raises(ValueError, match="Video not found"):
        await audio_service.handle_audio_extraction(db_session, 99999)


@pytest.mark.asyncio
async def test_handle_audio_extraction_failure(db_session, video_factory, temp_storage_dir, monkeypatch):
    """Test extraction failure handling."""
    from app import config
    settings = config.get_settings()
    monkeypatch.setattr(settings, "audios_dir", temp_storage_dir / "audios")

    video = video_factory()

    with patch("app.services.audio_service.ensure_directory_exists"), \
         patch("app.services.audio_service.extract_audio_from_video") as mock_extract:

        mock_extract.side_effect = Exception("Extraction failed")

        with pytest.raises(ValueError, match="Audio extraction failed"):
            await audio_service.handle_audio_extraction(db_session, video.id)
