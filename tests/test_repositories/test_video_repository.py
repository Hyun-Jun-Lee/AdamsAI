"""
Test suite for video_repository.
Tests CRUD operations and query functions for Video model.
"""

import pytest
from app.repositories import video_repository
from app.models import Video
from app.schemas import VideoCreate


# ============================================================================
# CREATE Tests
# ============================================================================

@pytest.mark.repository
def test_create_video(db_session):
    """Test creating a new video record."""
    video_data = VideoCreate(
        filename="test_video.mp4",
        filepath="/storage/videos/test_video.mp4",
        source_type="upload",
        file_size=1024 * 1024,
        duration=120.0,
        status="uploaded"
    )

    video = video_repository.create_video(db_session, video_data)

    assert video.id is not None
    assert video.filename == "test_video.mp4"
    assert video.filepath == "/storage/videos/test_video.mp4"
    assert video.source_type == "upload"
    assert video.file_size == 1024 * 1024
    assert video.duration == 120.0
    assert video.status == "uploaded"
    assert video.created_at is not None


def test_create_video_with_url(db_session):
    """Test creating video record from URL download."""
    video_data = VideoCreate(
        filename="downloaded.mp4",
        filepath="/storage/videos/downloaded.mp4",
        source_type="download",
        source_url="https://example.com/video.mp4",
        file_size=2048 * 1024,
        status="uploaded"
    )

    video = video_repository.create_video(db_session, video_data)

    assert video.source_type == "download"
    assert video.source_url == "https://example.com/video.mp4"


# ============================================================================
# READ Tests
# ============================================================================

def test_get_video_by_id(db_session, video_factory):
    """Test retrieving video by ID."""
    created_video = video_factory(filename="findme.mp4")

    found_video = video_repository.get_video_by_id(db_session, created_video.id)

    assert found_video is not None
    assert found_video.id == created_video.id
    assert found_video.filename == "findme.mp4"


def test_get_video_by_id_not_found(db_session):
    """Test retrieving non-existent video returns None."""
    video = video_repository.get_video_by_id(db_session, 99999)
    assert video is None


def test_get_video_by_filepath(db_session, video_factory):
    """Test retrieving video by filepath."""
    created_video = video_factory(filepath="/unique/path/video.mp4")

    found_video = video_repository.get_video_by_filepath(db_session, "/unique/path/video.mp4")

    assert found_video is not None
    assert found_video.filepath == "/unique/path/video.mp4"


def test_get_all_videos(db_session, video_factory):
    """Test retrieving all videos."""
    video_factory(filename="video1.mp4")
    video_factory(filename="video2.mp4")
    video_factory(filename="video3.mp4")

    videos = video_repository.get_all_videos(db_session)

    assert len(videos) == 3


def test_get_all_videos_empty(db_session):
    """Test retrieving videos from empty database."""
    videos = video_repository.get_all_videos(db_session)
    assert videos == []


def test_get_videos_by_status(db_session, video_factory):
    """Test filtering videos by status."""
    video_factory(filename="uploaded1.mp4", status="uploaded")
    video_factory(filename="uploaded2.mp4", status="uploaded")
    video_factory(filename="completed.mp4", status="completed")
    video_factory(filename="failed.mp4", status="failed")

    uploaded_videos = video_repository.get_videos_by_status(db_session, "uploaded")
    completed_videos = video_repository.get_videos_by_status(db_session, "completed")

    assert len(uploaded_videos) == 2
    assert len(completed_videos) == 1
    assert all(v.status == "uploaded" for v in uploaded_videos)


def test_get_videos_by_source_type(db_session, video_factory):
    """Test filtering videos by source type."""
    video_factory(filename="upload1.mp4", source_type="upload")
    video_factory(filename="upload2.mp4", source_type="upload")
    video_factory(filename="download1.mp4", source_type="download")

    uploaded = video_repository.get_videos_by_source_type(db_session, "upload")
    downloaded = video_repository.get_videos_by_source_type(db_session, "download")

    assert len(uploaded) == 2
    assert len(downloaded) == 1


def test_get_videos_paginated(db_session, video_factory):
    """Test paginated video retrieval."""
    # Create 15 videos
    for i in range(15):
        video_factory(filename=f"video{i}.mp4")

    # Get first page (10 items)
    page1 = video_repository.get_videos_paginated(db_session, skip=0, limit=10)
    assert len(page1) == 10

    # Get second page (5 items)
    page2 = video_repository.get_videos_paginated(db_session, skip=10, limit=10)
    assert len(page2) == 5

    # Verify no overlap
    page1_ids = {v.id for v in page1}
    page2_ids = {v.id for v in page2}
    assert page1_ids.isdisjoint(page2_ids)


# ============================================================================
# UPDATE Tests
# ============================================================================

def test_update_video_status(db_session, video_factory):
    """Test updating video status."""
    video = video_factory(status="uploaded")

    updated = video_repository.update_video_status(db_session, video.id, "processing")

    assert updated.status == "processing"

    # Verify in database
    db_session.refresh(video)
    assert video.status == "processing"


def test_update_video_status_not_found(db_session):
    """Test updating non-existent video returns None."""
    result = video_repository.update_video_status(db_session, 99999, "completed")
    assert result is None


def test_update_video_metadata(db_session, video_factory):
    """Test updating video metadata fields."""
    video = video_factory(duration=None, file_size=None)

    updates = {
        "duration": 180.5,
        "file_size": 5 * 1024 * 1024
    }

    updated = video_repository.update_video_metadata(db_session, video.id, updates)

    assert updated.duration == 180.5
    assert updated.file_size == 5 * 1024 * 1024


# ============================================================================
# DELETE Tests
# ============================================================================

def test_delete_video(db_session, video_factory):
    """Test deleting a video."""
    video = video_factory(filename="to_delete.mp4")
    video_id = video.id

    result = video_repository.delete_video(db_session, video_id)

    assert result is True

    # Verify deleted from database
    deleted_video = video_repository.get_video_by_id(db_session, video_id)
    assert deleted_video is None


def test_delete_video_not_found(db_session):
    """Test deleting non-existent video returns False."""
    result = video_repository.delete_video(db_session, 99999)
    assert result is False


def test_delete_video_cascades(db_session, complete_data_chain):
    """Test deleting video cascades to related records."""
    video = complete_data_chain["video"]
    audio_id = complete_data_chain["audio"].id
    transcript_id = complete_data_chain["transcript"].id
    summary_id = complete_data_chain["summary"].id

    # Delete video
    video_repository.delete_video(db_session, video.id)

    # Verify cascade deletion
    from app.models import Audio, Transcript, Summary

    assert db_session.query(Audio).filter_by(id=audio_id).first() is None
    assert db_session.query(Transcript).filter_by(id=transcript_id).first() is None
    assert db_session.query(Summary).filter_by(id=summary_id).first() is None


# ============================================================================
# COUNT Tests
# ============================================================================

def test_count_videos(db_session, video_factory):
    """Test counting total videos."""
    video_factory()
    video_factory()
    video_factory()

    count = video_repository.count_videos(db_session)
    assert count == 3


def test_count_videos_by_status(db_session, video_factory):
    """Test counting videos by status."""
    video_factory(status="uploaded")
    video_factory(status="uploaded")
    video_factory(status="completed")

    uploaded_count = video_repository.count_videos_by_status(db_session, "uploaded")
    completed_count = video_repository.count_videos_by_status(db_session, "completed")

    assert uploaded_count == 2
    assert completed_count == 1


# ============================================================================
# Relationship Tests
# ============================================================================

def test_video_audios_relationship(db_session, video_factory, audio_factory):
    """Test Video -> Audio relationship."""
    video = video_factory()
    audio1 = audio_factory(video_id=video.id, filename="audio1.mp3")
    audio2 = audio_factory(video_id=video.id, filename="audio2.mp3")

    db_session.refresh(video)

    assert len(video.audios) == 2
    assert audio1 in video.audios
    assert audio2 in video.audios
