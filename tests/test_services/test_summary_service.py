"""
Test suite for summary_service.
Tests business logic with mocked external dependencies.
"""

import pytest
from unittest.mock import patch, AsyncMock
from app.services import summary_service
from app.models import Summary


# ============================================================================
# Query Tests
# ============================================================================

def test_get_summary_list(db_session, video_factory, audio_factory, transcript_factory, summary_factory):
    """Test retrieving summary list."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)
    for i in range(3):
        summary_factory(transcript_id=transcript.id)

    result = summary_service.get_summary_list(db_session, limit=10, offset=0)

    assert result["total"] == 3
    assert len(result["items"]) == 3


def test_get_summary_by_id_success(db_session, video_factory, audio_factory, transcript_factory, summary_factory):
    """Test retrieving specific summary."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)
    summary = summary_factory(transcript_id=transcript.id, summary_text="Test summary")

    result = summary_service.get_summary_by_id(db_session, summary.id)

    assert result is not None
    assert result.summary_text == "Test summary"


def test_get_summary_by_id_not_found(db_session):
    """Test retrieving non-existent summary."""
    with pytest.raises(ValueError, match="Summary not found"):
        summary_service.get_summary_by_id(db_session, 99999)


def test_get_summaries_by_model(db_session, video_factory, audio_factory, transcript_factory, summary_factory):
    """Test filtering summaries by model name."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)
    summary_factory(transcript_id=transcript.id, ai_model_name="anthropic/claude-3.5-sonnet")
    summary_factory(transcript_id=transcript.id, ai_model_name="openai/gpt-4")

    result = summary_service.get_summaries_by_model(db_session, "claude")

    assert result["total"] >= 1
    assert all("claude" in s.ai_model_name.lower() for s in result["items"])


# ============================================================================
# Template Tests
# ============================================================================

def test_get_prompt_template_content_by_name(db_session, prompt_template_factory):
    """Test getting template content by name."""
    template = prompt_template_factory(
        name="test_template",
        content="Summarize: {transcript}",
        is_active=True
    )

    content, template_id = summary_service.get_prompt_template_content(
        db_session,
        template_name="test_template"
    )

    assert content == "Summarize: {transcript}"
    assert template_id == template.id


def test_get_prompt_template_content_inactive(db_session, prompt_template_factory):
    """Test getting inactive template raises error."""
    prompt_template_factory(name="inactive", is_active=False)

    with pytest.raises(ValueError, match="inactive"):
        summary_service.get_prompt_template_content(db_session, template_name="inactive")


def test_get_prompt_template_content_not_found(db_session):
    """Test getting non-existent template raises error."""
    with pytest.raises(ValueError, match="not found"):
        summary_service.get_prompt_template_content(db_session, template_name="nonexistent")


# ============================================================================
# Summarization Tests (Mocked API)
# ============================================================================

@pytest.mark.asyncio
async def test_handle_summary_generation_success(db_session, video_factory, audio_factory, transcript_factory, prompt_template_factory):
    """Test successful summary generation with mocked OpenRouter API."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id, text="Original transcript text")
    template = prompt_template_factory(
        name="default",
        content="Summarize: {transcript}",
        is_active=True
    )

    with patch("app.services.summary_service.call_openrouter_api", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "This is the AI-generated summary."

        result = await summary_service.handle_summary_generation(
            db_session,
            transcript.id,
            prompt_template_name="default"
        )

    assert result is not None
    assert result.transcript_id == transcript.id
    assert result.summary_text == "This is the AI-generated summary."
    assert result.prompt_template_id == template.id


@pytest.mark.asyncio
async def test_handle_summary_generation_transcript_not_found(db_session):
    """Test summarization with non-existent transcript."""
    with pytest.raises(ValueError, match="Transcript not found"):
        await summary_service.handle_summary_generation(db_session, 99999)


@pytest.mark.asyncio
async def test_handle_summary_generation_api_failure(db_session, video_factory, audio_factory, transcript_factory, prompt_template_factory):
    """Test summarization API failure handling."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)
    prompt_template_factory(name="default", is_active=True)

    with patch("app.services.summary_service.call_openrouter_api", new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = Exception("API error")

        with pytest.raises(ValueError, match="Summarization failed"):
            await summary_service.handle_summary_generation(
                db_session,
                transcript.id,
                prompt_template_name="default"
            )


@pytest.mark.asyncio
async def test_handle_summary_generation_empty_result(db_session, video_factory, audio_factory, transcript_factory, prompt_template_factory):
    """Test summarization returning empty text."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)
    prompt_template_factory(name="default", is_active=True)

    with patch("app.services.summary_service.call_openrouter_api", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = ""

        with pytest.raises(ValueError, match="empty text"):
            await summary_service.handle_summary_generation(
                db_session,
                transcript.id,
                prompt_template_name="default"
            )


@pytest.mark.asyncio
async def test_handle_summary_generation_with_custom_model(db_session, video_factory, audio_factory, transcript_factory, prompt_template_factory):
    """Test summarization with custom model name."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)
    prompt_template_factory(name="default", is_active=True)

    with patch("app.services.summary_service.call_openrouter_api", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Summary text"

        result = await summary_service.handle_summary_generation(
            db_session,
            transcript.id,
            model_name="openai/gpt-4",
            prompt_template_name="default"
        )

    assert result.ai_model_name == "openai/gpt-4"
