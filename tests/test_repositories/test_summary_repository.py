"""
Test suite for summary_repository.
Tests CRUD operations and query functions for Summary model.
"""

import pytest
from app.repositories import summary_repository
from app.models import Summary
from app.schemas import SummaryCreate, SummaryUpdate


# ============================================================================
# CREATE Tests
# ============================================================================

@pytest.mark.repository
def test_create_summary(db_session, video_factory, audio_factory, transcript_factory):
    """Test creating a new summary record."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)

    summary_data = SummaryCreate(
        transcript_id=transcript.id,
        summary_text="This is a comprehensive summary of the video content.",
        ai_model_name="anthropic/claude-3.5-sonnet",
        prompt_template_id=None
    )

    summary = summary_repository.create_summary(db_session, summary_data)

    assert summary.id is not None
    assert summary.transcript_id == transcript.id
    assert summary.summary_text == "This is a comprehensive summary of the video content."
    assert summary.ai_model_name == "anthropic/claude-3.5-sonnet"
    assert summary.prompt_template_id is None


def test_create_summary_with_template(db_session, video_factory, audio_factory, transcript_factory, prompt_template_factory):
    """Test creating summary with associated prompt template."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)
    template = prompt_template_factory()

    summary_data = SummaryCreate(
        transcript_id=transcript.id,
        summary_text="Summary using template",
        ai_model_name="openai/gpt-4",
        prompt_template_id=template.id
    )

    summary = summary_repository.create_summary(db_session, summary_data)

    assert summary.prompt_template_id == template.id
    assert summary.prompt_template.name == template.name


# ============================================================================
# READ Tests
# ============================================================================

def test_get_summary_by_id(db_session, summary_factory, video_factory, audio_factory, transcript_factory):
    """Test retrieving summary by ID."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)
    created_summary = summary_factory(transcript_id=transcript.id)

    found_summary = summary_repository.get_summary_by_id(db_session, created_summary.id)

    assert found_summary is not None
    assert found_summary.id == created_summary.id
    assert found_summary.summary_text == created_summary.summary_text


def test_get_summary_by_id_not_found(db_session):
    """Test retrieving non-existent summary returns None."""
    summary = summary_repository.get_summary_by_id(db_session, 99999)
    assert summary is None


def test_get_summaries_by_transcript_id(db_session, video_factory, audio_factory, transcript_factory, summary_factory):
    """Test retrieving all summaries for a specific transcript."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)

    summary1 = summary_factory(transcript_id=transcript.id, ai_model_name="model1")
    summary2 = summary_factory(transcript_id=transcript.id, ai_model_name="model2")

    # Create another transcript with summary to verify filtering
    transcript2 = transcript_factory(audio_id=audio.id)
    summary_factory(transcript_id=transcript2.id)

    summaries = summary_repository.get_summaries_by_transcript_id(db_session, transcript.id)

    assert len(summaries) == 2
    assert summary1 in summaries
    assert summary2 in summaries


def test_get_summaries_by_ai_model(db_session, video_factory, audio_factory, transcript_factory, summary_factory):
    """Test filtering summaries by AI model name."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)

    summary1 = summary_factory(transcript_id=transcript.id, ai_model_name="anthropic/claude-3.5-sonnet")
    summary2 = summary_factory(transcript_id=transcript.id, ai_model_name="anthropic/claude-3.5-sonnet")
    summary_factory(transcript_id=transcript.id, ai_model_name="openai/gpt-4")

    claude_summaries = summary_repository.get_summaries_by_ai_model(db_session, "anthropic/claude-3.5-sonnet")

    assert len(claude_summaries) == 2
    assert all(s.ai_model_name == "anthropic/claude-3.5-sonnet" for s in claude_summaries)


def test_get_summaries_by_template_id(db_session, video_factory, audio_factory, transcript_factory, summary_factory, prompt_template_factory):
    """Test filtering summaries by prompt template."""
    template = prompt_template_factory()

    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)

    summary1 = summary_factory(transcript_id=transcript.id, prompt_template_id=template.id)
    summary2 = summary_factory(transcript_id=transcript.id, prompt_template_id=template.id)
    summary_factory(transcript_id=transcript.id, prompt_template_id=None)

    template_summaries = summary_repository.get_summaries_by_template_id(db_session, template.id)

    assert len(template_summaries) == 2
    assert all(s.prompt_template_id == template.id for s in template_summaries)


def test_get_all_summaries(db_session, video_factory, audio_factory, transcript_factory, summary_factory):
    """Test retrieving all summaries."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)

    summary_factory(transcript_id=transcript.id)
    summary_factory(transcript_id=transcript.id)
    summary_factory(transcript_id=transcript.id)

    summaries = summary_repository.get_all_summaries(db_session)

    assert len(summaries) == 3


def test_get_summaries_paginated(db_session, video_factory, audio_factory, transcript_factory, summary_factory):
    """Test pagination of summaries."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)

    for i in range(15):
        summary_factory(transcript_id=transcript.id)

    # Get first page
    page1 = summary_repository.get_summaries_paginated(db_session, skip=0, limit=10)
    assert len(page1) == 10

    # Get second page
    page2 = summary_repository.get_summaries_paginated(db_session, skip=10, limit=10)
    assert len(page2) == 5


# ============================================================================
# UPDATE Tests
# ============================================================================

def test_update_summary(db_session, video_factory, audio_factory, transcript_factory, summary_factory):
    """Test updating summary fields."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)
    summary = summary_factory(
        transcript_id=transcript.id,
        summary_text="Original summary",
        ai_model_name="original-model"
    )

    updates = SummaryUpdate(
        summary_text="Updated summary text",
        ai_model_name="updated-model"
    )

    updated = summary_repository.update_summary(db_session, summary.id, updates)

    assert updated.summary_text == "Updated summary text"
    assert updated.ai_model_name == "updated-model"


def test_update_summary_not_found(db_session):
    """Test updating non-existent summary returns None."""
    updates = SummaryUpdate(summary_text="New text")
    result = summary_repository.update_summary(db_session, 99999, updates)
    assert result is None


# ============================================================================
# DELETE Tests
# ============================================================================

def test_delete_summary(db_session, video_factory, audio_factory, transcript_factory, summary_factory):
    """Test deleting a summary."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)
    summary = summary_factory(transcript_id=transcript.id)
    summary_id = summary.id

    result = summary_repository.delete_summary(db_session, summary_id)

    assert result is True

    # Verify deleted from database
    deleted = summary_repository.get_summary_by_id(db_session, summary_id)
    assert deleted is None


def test_delete_summary_not_found(db_session):
    """Test deleting non-existent summary returns False."""
    result = summary_repository.delete_summary(db_session, 99999)
    assert result is False


# ============================================================================
# COUNT Tests
# ============================================================================

def test_count_summaries(db_session, video_factory, audio_factory, transcript_factory, summary_factory):
    """Test counting total summaries."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)

    summary_factory(transcript_id=transcript.id)
    summary_factory(transcript_id=transcript.id)
    summary_factory(transcript_id=transcript.id)

    count = summary_repository.count_summaries(db_session)
    assert count == 3


def test_count_summaries_by_model(db_session, video_factory, audio_factory, transcript_factory, summary_factory):
    """Test counting summaries by AI model."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)

    summary_factory(transcript_id=transcript.id, ai_model_name="anthropic/claude-3.5-sonnet")
    summary_factory(transcript_id=transcript.id, ai_model_name="anthropic/claude-3.5-sonnet")
    summary_factory(transcript_id=transcript.id, ai_model_name="openai/gpt-4")

    claude_count = summary_repository.count_summaries_by_model(db_session, "anthropic/claude-3.5-sonnet")
    assert claude_count == 2


# ============================================================================
# Relationship Tests
# ============================================================================

def test_summary_transcript_relationship(db_session, video_factory, audio_factory, transcript_factory, summary_factory):
    """Test Summary -> Transcript relationship."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id, text="Original transcript text")
    summary = summary_factory(transcript_id=transcript.id)

    db_session.refresh(summary)

    assert summary.transcript is not None
    assert summary.transcript.id == transcript.id
    assert summary.transcript.text == "Original transcript text"


def test_summary_template_relationship(db_session, video_factory, audio_factory, transcript_factory, summary_factory, prompt_template_factory):
    """Test Summary -> PromptTemplate relationship."""
    template = prompt_template_factory(name="test_template")

    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)
    summary = summary_factory(transcript_id=transcript.id, prompt_template_id=template.id)

    db_session.refresh(summary)

    assert summary.prompt_template is not None
    assert summary.prompt_template.id == template.id
    assert summary.prompt_template.name == "test_template"


def test_cascade_delete_transcript_deletes_summaries(db_session, video_factory, audio_factory, transcript_factory, summary_factory):
    """Test CASCADE delete: deleting transcript deletes summaries."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)

    summary1 = summary_factory(transcript_id=transcript.id)
    summary2 = summary_factory(transcript_id=transcript.id)
    summary1_id = summary1.id
    summary2_id = summary2.id

    # Delete transcript
    db_session.delete(transcript)
    db_session.commit()

    # Verify summaries were CASCADE deleted
    assert summary_repository.get_summary_by_id(db_session, summary1_id) is None
    assert summary_repository.get_summary_by_id(db_session, summary2_id) is None
