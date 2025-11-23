"""
Pytest configuration and shared fixtures for testing.
Provides database setup, session management, and test data factories.
"""

import pytest
import tempfile
import uuid
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.database import Base
from app.models import Video, Audio, Transcript, Summary, PromptTemplate


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """
    Setup test environment variables.
    Auto-used for all tests to ensure Settings can be initialized.
    """
    os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
    os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")
    yield
    # Cleanup after all tests
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("OPENROUTER_API_KEY", None)


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_engine():
    """
    Create a test database engine using SQLite in-memory.
    Session-scoped: created once for entire test session.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False  # Set to True for SQL debugging
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup: drop all tables
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """
    Create a new database session for each test.
    Function-scoped: fresh session for every test function.

    Yields:
        Session: SQLAlchemy database session

    Example:
        def test_create_video(db_session):
            video = Video(filename="test.mp4", ...)
            db_session.add(video)
            db_session.commit()
    """
    # Create connection and begin transaction
    connection = test_engine.connect()
    transaction = connection.begin()

    # Create session bound to connection
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    # Cleanup: rollback transaction (undoes all changes)
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def clean_db(test_engine):
    """
    Clean all tables before each test.
    Use this when you need a completely empty database.
    """
    # Clear all tables
    for table in reversed(Base.metadata.sorted_tables):
        test_engine.execute(table.delete())


# ============================================================================
# File System Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def temp_storage_dir():
    """
    Create temporary storage directory for file tests.
    Automatically cleaned up after test.

    Yields:
        Path: Temporary directory path
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        # Create subdirectories matching production structure
        (temp_path / "videos").mkdir()
        (temp_path / "audios").mkdir()
        (temp_path / "transcripts").mkdir()
        (temp_path / "summaries").mkdir()

        yield temp_path


@pytest.fixture(scope="function")
def sample_video_file(temp_storage_dir):
    """
    Create a sample video file for testing.

    Returns:
        Path: Path to sample video file
    """
    video_path = temp_storage_dir / "videos" / "test_video.mp4"
    # Create empty file (for testing file operations, not actual video processing)
    video_path.write_bytes(b"fake video content")
    return video_path


# ============================================================================
# Model Factories (Test Data Generators)
# ============================================================================

@pytest.fixture
def video_factory(db_session):
    """
    Factory for creating Video test instances.

    Returns:
        callable: Function to create Video with custom attributes

    Example:
        def test_video(video_factory):
            video = video_factory(filename="custom.mp4")
    """
    def _create_video(**kwargs):
        # Generate unique filepath if not provided
        unique_id = uuid.uuid4().hex[:8]
        defaults = {
            "filename": f"test_video_{unique_id}.mp4",
            "filepath": f"/storage/videos/test_video_{unique_id}.mp4",
            "source_type": "upload",
            "file_size": 1024 * 1024,  # 1MB
            "duration": 120.0,
            "status": "uploaded"
        }
        defaults.update(kwargs)

        video = Video(**defaults)
        db_session.add(video)
        db_session.commit()
        db_session.refresh(video)
        return video

    return _create_video


@pytest.fixture
def audio_factory(db_session):
    """Factory for creating Audio test instances."""
    def _create_audio(video_id, **kwargs):
        # Generate unique filepath if not provided
        unique_id = uuid.uuid4().hex[:8]
        defaults = {
            "video_id": video_id,
            "filename": f"test_audio_{unique_id}.mp3",
            "filepath": f"/storage/audios/test_audio_{unique_id}.mp3",
            "file_size": 512 * 1024,  # 512KB
            "duration": 120.0,
            "status": "extracted"
        }
        defaults.update(kwargs)

        audio = Audio(**defaults)
        db_session.add(audio)
        db_session.commit()
        db_session.refresh(audio)
        return audio

    return _create_audio


@pytest.fixture
def transcript_factory(db_session):
    """Factory for creating Transcript test instances."""
    def _create_transcript(audio_id, **kwargs):
        defaults = {
            "audio_id": audio_id,
            "text": "This is a test transcript text.",
            "language": "ko",
            "model": "whisper-1"
        }
        defaults.update(kwargs)

        transcript = Transcript(**defaults)
        db_session.add(transcript)
        db_session.commit()
        db_session.refresh(transcript)
        return transcript

    return _create_transcript


@pytest.fixture
def prompt_template_factory(db_session):
    """Factory for creating PromptTemplate test instances."""
    def _create_prompt_template(**kwargs):
        # Generate unique name if not provided
        unique_id = uuid.uuid4().hex[:8]
        defaults = {
            "name": f"test_template_{unique_id}",
            "description": "Test prompt template",
            "content": "Summarize the following: {transcript}",
            "is_active": True,
            "category": "general"
        }
        defaults.update(kwargs)

        template = PromptTemplate(**defaults)
        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)
        return template

    return _create_prompt_template


@pytest.fixture
def summary_factory(db_session):
    """Factory for creating Summary test instances."""
    def _create_summary(transcript_id, **kwargs):
        defaults = {
            "transcript_id": transcript_id,
            "summary_text": "This is a test summary.",
            "ai_model_name": "anthropic/claude-3.5-sonnet",
            "prompt_template_id": None
        }
        defaults.update(kwargs)

        summary = Summary(**defaults)
        db_session.add(summary)
        db_session.commit()
        db_session.refresh(summary)
        return summary

    return _create_summary


# ============================================================================
# Complete Data Chain Fixture
# ============================================================================

@pytest.fixture
def complete_data_chain(video_factory, audio_factory, transcript_factory, summary_factory):
    """
    Create complete data chain: Video → Audio → Transcript → Summary
    Useful for testing CASCADE deletes and relationships.

    Returns:
        dict: Contains video, audio, transcript, summary instances

    Example:
        def test_cascade_delete(complete_data_chain):
            video = complete_data_chain['video']
            # Delete video should cascade to all children
    """
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)
    summary = summary_factory(transcript_id=transcript.id)

    return {
        "video": video,
        "audio": audio,
        "transcript": transcript,
        "summary": summary
    }
