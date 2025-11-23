"""
Test setup validation - verify test environment is working correctly.
Run this first to ensure fixtures and database setup work properly.
"""

import pytest
from app.models import Video, Audio, Transcript, Summary, PromptTemplate


def test_database_session_works(db_session):
    """Verify database session fixture works."""
    # Simple query should not raise error
    result = db_session.query(Video).all()
    assert result == []


def test_video_factory_creates_video(video_factory):
    """Verify video factory fixture works."""
    video = video_factory(filename="factory_test.mp4")

    assert video.id is not None
    assert video.filename == "factory_test.mp4"
    assert video.source_type == "upload"


def test_complete_data_chain_creates_all(complete_data_chain):
    """Verify complete data chain fixture creates all related records."""
    video = complete_data_chain["video"]
    audio = complete_data_chain["audio"]
    transcript = complete_data_chain["transcript"]
    summary = complete_data_chain["summary"]

    # Verify all IDs are set
    assert video.id is not None
    assert audio.id is not None
    assert transcript.id is not None
    assert summary.id is not None

    # Verify relationships
    assert audio.video_id == video.id
    assert transcript.audio_id == audio.id
    assert summary.transcript_id == transcript.id


def test_cascade_delete_video(db_session, complete_data_chain):
    """Verify CASCADE delete works from Video down."""
    video = complete_data_chain["video"]
    audio_id = complete_data_chain["audio"].id
    transcript_id = complete_data_chain["transcript"].id
    summary_id = complete_data_chain["summary"].id

    # Delete video
    db_session.delete(video)
    db_session.commit()

    # Verify all related records are deleted
    assert db_session.query(Video).filter_by(id=video.id).first() is None
    assert db_session.query(Audio).filter_by(id=audio_id).first() is None
    assert db_session.query(Transcript).filter_by(id=transcript_id).first() is None
    assert db_session.query(Summary).filter_by(id=summary_id).first() is None


def test_prompt_template_factory(prompt_template_factory):
    """Verify prompt template factory works."""
    template = prompt_template_factory(name="test_prompt", category="real_estate")

    assert template.id is not None
    assert template.name == "test_prompt"
    assert template.category == "real_estate"
    assert template.is_active is True


def test_temp_storage_dir_structure(temp_storage_dir):
    """Verify temporary storage directory has correct structure."""
    assert temp_storage_dir.exists()
    assert (temp_storage_dir / "videos").exists()
    assert (temp_storage_dir / "audios").exists()
    assert (temp_storage_dir / "transcripts").exists()
    assert (temp_storage_dir / "summaries").exists()


def test_sample_video_file_exists(sample_video_file):
    """Verify sample video file fixture creates file."""
    assert sample_video_file.exists()
    assert sample_video_file.suffix == ".mp4"
    assert sample_video_file.read_bytes() == b"fake video content"
