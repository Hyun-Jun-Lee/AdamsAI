"""
Test suite for audio_repository.
Tests CRUD operations and query functions for Audio model.
"""

import pytest
from app.repositories import audio_repository
from app.models import Audio
from app.schemas import AudioCreate


# ============================================================================
# CREATE Tests
# ============================================================================

@pytest.mark.repository
def test_create_audio(db_session, video_factory):
    """Test creating a new audio record."""
    video = video_factory()

    audio_data = AudioCreate(
        video_id=video.id,
        filename="test_audio.mp3",
        filepath="/storage/audios/test_audio.mp3",
        file_size=512 * 1024,
        duration=120.0,
        status="extracted"
    )

    audio = audio_repository.create_audio(db_session, audio_data)

    assert audio.id is not None
    assert audio.video_id == video.id
    assert audio.filename == "test_audio.mp3"
    assert audio.filepath == "/storage/audios/test_audio.mp3"
    assert audio.file_size == 512 * 1024
    assert audio.duration == 120.0
    assert audio.status == "extracted"


# ============================================================================
# READ Tests
# ============================================================================

def test_get_audio_by_id(db_session, video_factory, audio_factory):
    """Test retrieving audio by ID."""
    video = video_factory()
    created_audio = audio_factory(video_id=video.id, filename="findme.mp3")

    found_audio = audio_repository.get_audio_by_id(db_session, created_audio.id)

    assert found_audio is not None
    assert found_audio.id == created_audio.id
    assert found_audio.filename == "findme.mp3"


def test_get_audio_by_id_not_found(db_session):
    """Test retrieving non-existent audio returns None."""
    audio = audio_repository.get_audio_by_id(db_session, 99999)
    assert audio is None


def test_get_audio_by_filepath(db_session, video_factory, audio_factory):
    """Test retrieving audio by filepath."""
    video = video_factory()
    created_audio = audio_factory(video_id=video.id, filepath="/unique/path/audio.mp3")

    found_audio = audio_repository.get_audio_by_filepath(db_session, "/unique/path/audio.mp3")

    assert found_audio is not None
    assert found_audio.filepath == "/unique/path/audio.mp3"


def test_get_audios_by_video_id(db_session, video_factory, audio_factory):
    """Test retrieving all audios for a specific video."""
    video = video_factory()
    audio1 = audio_factory(video_id=video.id, filename="audio1.mp3")
    audio2 = audio_factory(video_id=video.id, filename="audio2.mp3")

    # Create audio for different video (should not be returned)
    other_video = video_factory()
    audio_factory(video_id=other_video.id, filename="other.mp3")

    audios = audio_repository.get_audios_by_video_id(db_session, video.id)

    assert len(audios) == 2
    assert audio1 in audios
    assert audio2 in audios


def test_get_all_audios(db_session, video_factory, audio_factory):
    """Test retrieving all audios."""
    video = video_factory()
    audio_factory(video_id=video.id, filename="audio1.mp3")
    audio_factory(video_id=video.id, filename="audio2.mp3")
    audio_factory(video_id=video.id, filename="audio3.mp3")

    audios = audio_repository.get_all_audios(db_session)

    assert len(audios) == 3


def test_get_audios_by_status(db_session, video_factory, audio_factory):
    """Test filtering audios by status."""
    video = video_factory()
    audio_factory(video_id=video.id, filename="extracted1.mp3", status="extracted")
    audio_factory(video_id=video.id, filename="extracted2.mp3", status="extracted")
    audio_factory(video_id=video.id, filename="processing.mp3", status="processing")

    extracted_audios = audio_repository.get_audios_by_status(db_session, "extracted")
    processing_audios = audio_repository.get_audios_by_status(db_session, "processing")

    assert len(extracted_audios) == 2
    assert len(processing_audios) == 1


def test_get_audios_paginated(db_session, video_factory, audio_factory):
    """Test paginated audio retrieval."""
    video = video_factory()
    # Create 15 audios
    for i in range(15):
        audio_factory(video_id=video.id, filename=f"audio{i}.mp3")

    # Get first page (10 items)
    page1 = audio_repository.get_audios_paginated(db_session, skip=0, limit=10)
    assert len(page1) == 10

    # Get second page (5 items)
    page2 = audio_repository.get_audios_paginated(db_session, skip=10, limit=10)
    assert len(page2) == 5


# ============================================================================
# UPDATE Tests
# ============================================================================

def test_update_audio_status(db_session, video_factory, audio_factory):
    """Test updating audio status."""
    video = video_factory()
    audio = audio_factory(video_id=video.id, status="extracted")

    updated = audio_repository.update_audio_status(db_session, audio.id, "processing")

    assert updated.status == "processing"


def test_update_audio_metadata(db_session, video_factory, audio_factory):
    """Test updating audio metadata fields."""
    video = video_factory()
    audio = audio_factory(video_id=video.id, duration=None, file_size=None)

    updates = {
        "duration": 180.5,
        "file_size": 1024 * 1024
    }

    updated = audio_repository.update_audio_metadata(db_session, audio.id, updates)

    assert updated.duration == 180.5
    assert updated.file_size == 1024 * 1024


# ============================================================================
# DELETE Tests
# ============================================================================

def test_delete_audio(db_session, video_factory, audio_factory):
    """Test deleting an audio."""
    video = video_factory()
    audio = audio_factory(video_id=video.id, filename="to_delete.mp3")
    audio_id = audio.id

    result = audio_repository.delete_audio(db_session, audio_id)

    assert result is True

    # Verify deleted from database
    deleted_audio = audio_repository.get_audio_by_id(db_session, audio_id)
    assert deleted_audio is None


def test_delete_audio_cascades(db_session, video_factory, audio_factory, transcript_factory):
    """Test deleting audio cascades to transcripts."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)

    # Delete audio
    audio_repository.delete_audio(db_session, audio.id)

    # Verify cascade deletion
    from app.models import Transcript
    assert db_session.query(Transcript).filter_by(id=transcript.id).first() is None


# ============================================================================
# COUNT Tests
# ============================================================================

def test_count_audios(db_session, video_factory, audio_factory):
    """Test counting total audios."""
    video = video_factory()
    audio_factory(video_id=video.id)
    audio_factory(video_id=video.id)
    audio_factory(video_id=video.id)

    count = audio_repository.count_audios(db_session)
    assert count == 3


def test_count_audios_by_status(db_session, video_factory, audio_factory):
    """Test counting audios by status."""
    video = video_factory()
    audio_factory(video_id=video.id, status="extracted")
    audio_factory(video_id=video.id, status="extracted")
    audio_factory(video_id=video.id, status="processing")

    extracted_count = audio_repository.count_audios_by_status(db_session, "extracted")
    processing_count = audio_repository.count_audios_by_status(db_session, "processing")

    assert extracted_count == 2
    assert processing_count == 1


# ============================================================================
# Relationship Tests
# ============================================================================

def test_audio_video_relationship(db_session, video_factory, audio_factory):
    """Test Audio -> Video relationship."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)

    assert audio.video is not None
    assert audio.video.id == video.id


def test_audio_transcripts_relationship(db_session, video_factory, audio_factory, transcript_factory):
    """Test Audio -> Transcripts relationship."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript1 = transcript_factory(audio_id=audio.id)
    transcript2 = transcript_factory(audio_id=audio.id)

    db_session.refresh(audio)

    assert len(audio.transcripts) == 2
    assert transcript1 in audio.transcripts
    assert transcript2 in audio.transcripts
