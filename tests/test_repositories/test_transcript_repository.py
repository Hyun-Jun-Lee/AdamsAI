"""
Test suite for transcript_repository.
Tests CRUD operations and query functions for Transcript model.
"""

import pytest
from app.repositories import transcript_repository
from app.models import Transcript
from app.schemas import TranscriptCreate


# ============================================================================
# CREATE Tests
# ============================================================================

@pytest.mark.repository
def test_create_transcript(db_session, video_factory, audio_factory):
    """Test creating a new transcript record."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)

    transcript_data = TranscriptCreate(
        audio_id=audio.id,
        text="This is a test transcript.",
        language="ko",
        model="whisper-1"
    )

    transcript = transcript_repository.create_transcript(db_session, transcript_data)

    assert transcript.id is not None
    assert transcript.audio_id == audio.id
    assert transcript.text == "This is a test transcript."
    assert transcript.language == "ko"
    assert transcript.model == "whisper-1"


# ============================================================================
# READ Tests
# ============================================================================

def test_get_transcript_by_id(db_session, video_factory, audio_factory, transcript_factory):
    """Test retrieving transcript by ID."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    created_transcript = transcript_factory(audio_id=audio.id, text="Find me")

    found_transcript = transcript_repository.get_transcript_by_id(db_session, created_transcript.id)

    assert found_transcript is not None
    assert found_transcript.id == created_transcript.id
    assert found_transcript.text == "Find me"


def test_get_transcript_by_id_not_found(db_session):
    """Test retrieving non-existent transcript returns None."""
    transcript = transcript_repository.get_transcript_by_id(db_session, 99999)
    assert transcript is None


def test_get_transcripts_by_audio_id(db_session, video_factory, audio_factory, transcript_factory):
    """Test retrieving all transcripts for a specific audio."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript1 = transcript_factory(audio_id=audio.id, text="First")
    transcript2 = transcript_factory(audio_id=audio.id, text="Second")

    # Create transcript for different audio (should not be returned)
    other_audio = audio_factory(video_id=video.id)
    transcript_factory(audio_id=other_audio.id, text="Other")

    transcripts = transcript_repository.get_transcripts_by_audio_id(db_session, audio.id)

    assert len(transcripts) == 2
    assert transcript1 in transcripts
    assert transcript2 in transcripts


def test_get_all_transcripts(db_session, video_factory, audio_factory, transcript_factory):
    """Test retrieving all transcripts."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript_factory(audio_id=audio.id, text="First")
    transcript_factory(audio_id=audio.id, text="Second")
    transcript_factory(audio_id=audio.id, text="Third")

    transcripts = transcript_repository.get_all_transcripts(db_session)

    assert len(transcripts) == 3


def test_get_transcripts_by_language(db_session, video_factory, audio_factory, transcript_factory):
    """Test filtering transcripts by language."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript_factory(audio_id=audio.id, text="Korean", language="ko")
    transcript_factory(audio_id=audio.id, text="Korean 2", language="ko")
    transcript_factory(audio_id=audio.id, text="English", language="en")

    ko_transcripts = transcript_repository.get_transcripts_by_language(db_session, "ko")
    en_transcripts = transcript_repository.get_transcripts_by_language(db_session, "en")

    assert len(ko_transcripts) == 2
    assert len(en_transcripts) == 1


def test_get_transcripts_paginated(db_session, video_factory, audio_factory, transcript_factory):
    """Test paginated transcript retrieval."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    # Create 15 transcripts
    for i in range(15):
        transcript_factory(audio_id=audio.id, text=f"Transcript {i}")

    # Get first page (10 items)
    page1 = transcript_repository.get_transcripts_paginated(db_session, skip=0, limit=10)
    assert len(page1) == 10

    # Get second page (5 items)
    page2 = transcript_repository.get_transcripts_paginated(db_session, skip=10, limit=10)
    assert len(page2) == 5


def test_search_transcripts_by_text(db_session, video_factory, audio_factory, transcript_factory):
    """Test searching transcripts by text content."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript_factory(audio_id=audio.id, text="This is about real estate investment")
    transcript_factory(audio_id=audio.id, text="Another video about stocks")
    transcript_factory(audio_id=audio.id, text="Real estate market analysis")

    results = transcript_repository.search_transcripts_by_text(db_session, "real estate")

    assert len(results) == 2
    assert all("real estate" in t.text.lower() for t in results)


# ============================================================================
# UPDATE Tests
# ============================================================================

def test_update_transcript_text(db_session, video_factory, audio_factory, transcript_factory):
    """Test updating transcript text."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id, text="Original text")

    updated = transcript_repository.update_transcript_text(
        db_session,
        transcript.id,
        "Updated text"
    )

    assert updated.text == "Updated text"


# ============================================================================
# DELETE Tests
# ============================================================================

def test_delete_transcript(db_session, video_factory, audio_factory, transcript_factory):
    """Test deleting a transcript."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id, text="To delete")
    transcript_id = transcript.id

    result = transcript_repository.delete_transcript(db_session, transcript_id)

    assert result is True

    # Verify deleted from database
    deleted = transcript_repository.get_transcript_by_id(db_session, transcript_id)
    assert deleted is None


def test_delete_transcript_cascades(db_session, complete_data_chain):
    """Test deleting transcript cascades to summaries."""
    transcript = complete_data_chain["transcript"]
    summary = complete_data_chain["summary"]

    # Delete transcript
    transcript_repository.delete_transcript(db_session, transcript.id)

    # Verify cascade deletion
    from app.models import Summary
    assert db_session.query(Summary).filter_by(id=summary.id).first() is None


# ============================================================================
# COUNT Tests
# ============================================================================

def test_count_transcripts(db_session, video_factory, audio_factory, transcript_factory):
    """Test counting total transcripts."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript_factory(audio_id=audio.id)
    transcript_factory(audio_id=audio.id)
    transcript_factory(audio_id=audio.id)

    count = transcript_repository.count_transcripts(db_session)
    assert count == 3


def test_count_transcripts_by_language(db_session, video_factory, audio_factory, transcript_factory):
    """Test counting transcripts by language."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript_factory(audio_id=audio.id, language="ko")
    transcript_factory(audio_id=audio.id, language="ko")
    transcript_factory(audio_id=audio.id, language="en")

    ko_count = transcript_repository.count_transcripts_by_language(db_session, "ko")
    en_count = transcript_repository.count_transcripts_by_language(db_session, "en")

    assert ko_count == 2
    assert en_count == 1


# ============================================================================
# Relationship Tests
# ============================================================================

def test_transcript_audio_relationship(db_session, video_factory, audio_factory, transcript_factory):
    """Test Transcript -> Audio relationship."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)

    assert transcript.audio is not None
    assert transcript.audio.id == audio.id


def test_transcript_summaries_relationship(db_session, video_factory, audio_factory, transcript_factory, summary_factory):
    """Test Transcript -> Summaries relationship."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)
    summary1 = summary_factory(transcript_id=transcript.id)
    summary2 = summary_factory(transcript_id=transcript.id)

    db_session.refresh(transcript)

    assert len(transcript.summaries) == 2
    assert summary1 in transcript.summaries
    assert summary2 in transcript.summaries
