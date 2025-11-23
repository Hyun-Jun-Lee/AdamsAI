"""
Test suite for stt_service.
Tests business logic with mocked external dependencies.
"""

import pytest
from unittest.mock import patch, AsyncMock
from app.services import stt_service
from app.models import Transcript


# ============================================================================
# Query Tests
# ============================================================================

def test_get_transcript_list(db_session, video_factory, audio_factory, transcript_factory):
    """Test retrieving transcript list."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    for i in range(3):
        transcript_factory(audio_id=audio.id)

    result = stt_service.get_transcript_list(db_session, limit=10, offset=0)

    assert result["total"] == 3
    assert len(result["items"]) == 3


def test_get_transcript_by_id_success(db_session, video_factory, audio_factory, transcript_factory):
    """Test retrieving specific transcript."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id, text="Test transcript")

    result = stt_service.get_transcript_by_id(db_session, transcript.id)

    assert result is not None
    assert result.text == "Test transcript"


def test_get_transcript_by_id_not_found(db_session):
    """Test retrieving non-existent transcript."""
    with pytest.raises(ValueError, match="Transcript not found"):
        stt_service.get_transcript_by_id(db_session, 99999)


def test_search_transcripts(db_session, video_factory, audio_factory, transcript_factory):
    """Test searching transcripts by text."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript_factory(audio_id=audio.id, text="This is about real estate")
    transcript_factory(audio_id=audio.id, text="This is about technology")

    result = stt_service.search_transcripts(db_session, "real estate")

    assert result["total"] >= 1
    assert any("real estate" in t.text for t in result["items"])


# ============================================================================
# Transcription Tests (Mocked API)
# ============================================================================

@pytest.mark.asyncio
async def test_handle_transcription_success(db_session, video_factory, audio_factory):
    """Test successful transcription with mocked Whisper API."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)

    with patch("app.services.stt_service.call_whisper_api", new_callable=AsyncMock) as mock_whisper:
        mock_whisper.return_value = "This is the transcribed text from the audio."

        result = await stt_service.handle_transcription(db_session, audio.id, language="ko")

    assert result is not None
    assert result.audio_id == audio.id
    assert result.text == "This is the transcribed text from the audio."
    assert result.language == "ko"


@pytest.mark.asyncio
async def test_handle_transcription_audio_not_found(db_session):
    """Test transcription with non-existent audio."""
    with pytest.raises(ValueError, match="Audio not found"):
        await stt_service.handle_transcription(db_session, 99999)


@pytest.mark.asyncio
async def test_handle_transcription_api_failure(db_session, video_factory, audio_factory):
    """Test transcription API failure handling."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)

    with patch("app.services.stt_service.call_whisper_api", new_callable=AsyncMock) as mock_whisper:
        mock_whisper.side_effect = Exception("API error")

        with pytest.raises(ValueError, match="Transcription failed"):
            await stt_service.handle_transcription(db_session, audio.id)


@pytest.mark.asyncio
async def test_handle_transcription_empty_result(db_session, video_factory, audio_factory):
    """Test transcription returning empty text."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)

    with patch("app.services.stt_service.call_whisper_api", new_callable=AsyncMock) as mock_whisper:
        mock_whisper.return_value = ""

        with pytest.raises(ValueError, match="empty text"):
            await stt_service.handle_transcription(db_session, audio.id)
