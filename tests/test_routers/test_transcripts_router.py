"""
Integration tests for transcripts router.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from app.routers import transcripts
from app.database import get_db


@pytest.fixture
def app():
    """Create FastAPI test application."""
    app = FastAPI()
    app.include_router(transcripts.router)
    return app


@pytest.fixture
def client(app, db_session):
    """Create test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def mock_transcript(transcript_factory, audio_factory, video_factory):
    """Mock transcript object using factory."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    return transcript_factory(
        audio_id=audio.id,
        text="This is a test transcript.",
        language="ko"
    )


class TestCreateTranscript:
    """Tests for POST /api/transcripts/create endpoint."""

    @patch('app.routers.transcripts.stt_service.handle_transcription', new_callable=AsyncMock)
    async def test_create_transcript_success(self, mock_transcribe, client, mock_transcript):
        """Test successful transcript creation."""
        mock_transcribe.return_value = mock_transcript

        response = client.post(
            "/api/transcripts/create",
            json={"audio_id": 1, "language": "ko"}
        )

        assert response.status_code == 202
        data = response.json()
        assert data["id"] == 1
        assert data["audio_id"] == 1
        assert data["language"] == "ko"
        assert "test transcript" in data["text"]

    @patch('app.routers.transcripts.stt_service.handle_transcription', new_callable=AsyncMock)
    async def test_create_transcript_default_language(self, mock_transcribe, client, mock_transcript):
        """Test transcript creation with default language."""
        mock_transcribe.return_value = mock_transcript

        response = client.post(
            "/api/transcripts/create",
            json={"audio_id": 1}
        )

        assert response.status_code == 202
        # Should use default language "ko"
        mock_transcribe.assert_called_once()
        call_args = mock_transcribe.call_args
        assert call_args.kwargs.get("language") == "ko"

    @patch('app.routers.transcripts.stt_service.handle_transcription', new_callable=AsyncMock)
    async def test_create_transcript_invalid_audio(self, mock_transcribe, client):
        """Test transcript creation with invalid audio ID."""
        mock_transcribe.side_effect = ValueError("Audio not found")

        response = client.post(
            "/api/transcripts/create",
            json={"audio_id": 999}
        )

        assert response.status_code == 400
        assert "Audio not found" in response.json()["detail"]

    @patch('app.routers.transcripts.stt_service.handle_transcription', new_callable=AsyncMock)
    async def test_create_transcript_server_error(self, mock_transcribe, client):
        """Test transcript creation with server error."""
        mock_transcribe.side_effect = Exception("API error")

        response = client.post(
            "/api/transcripts/create",
            json={"audio_id": 1}
        )

        assert response.status_code == 500
        assert "Transcription failed" in response.json()["detail"]


class TestListTranscripts:
    """Tests for GET /api/transcripts endpoint."""

    @patch('app.routers.transcripts.stt_service.get_transcript_list')
    def test_list_transcripts_success(self, mock_list, client, mock_transcript):
        """Test successful transcript listing."""
        mock_list.return_value = {
            "items": [mock_transcript],
            "total": 1
        }

        response = client.get("/api/transcripts")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == 1

    @patch('app.routers.transcripts.stt_service.get_transcript_list')
    def test_list_transcripts_with_audio_filter(self, mock_list, client, mock_transcript):
        """Test transcript listing with audio filter."""
        mock_list.return_value = {
            "items": [mock_transcript],
            "total": 1
        }

        response = client.get("/api/transcripts?audio_id=1&limit=10&offset=0")

        assert response.status_code == 200
        mock_list.assert_called_once()

    @patch('app.routers.transcripts.stt_service.get_transcript_list')
    def test_list_transcripts_server_error(self, mock_list, client):
        """Test listing with server error."""
        mock_list.side_effect = Exception("Database error")

        response = client.get("/api/transcripts")

        assert response.status_code == 500


class TestGetTranscript:
    """Tests for GET /api/transcripts/{transcript_id} endpoint."""

    @patch('app.routers.transcripts.stt_service.get_transcript_by_id')
    def test_get_transcript_success(self, mock_get, client, mock_transcript):
        """Test successful transcript retrieval."""
        mock_get.return_value = mock_transcript

        response = client.get("/api/transcripts/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["audio_id"] == 1

    @patch('app.routers.transcripts.stt_service.get_transcript_by_id')
    def test_get_transcript_not_found(self, mock_get, client):
        """Test transcript not found."""
        mock_get.side_effect = ValueError("Transcript not found")

        response = client.get("/api/transcripts/999")

        assert response.status_code == 404
        assert "Transcript not found" in response.json()["detail"]


class TestSearchTranscripts:
    """Tests for GET /api/transcripts/search endpoint."""

    @patch('app.routers.transcripts.stt_service.search_transcripts')
    def test_search_transcripts_success(self, mock_search, client, mock_transcript):
        """Test successful transcript search."""
        mock_search.return_value = {
            "items": [mock_transcript],
            "total": 1
        }

        response = client.get("/api/transcripts/search?q=test&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    @patch('app.routers.transcripts.stt_service.search_transcripts')
    def test_search_transcripts_empty_result(self, mock_search, client):
        """Test search with no results."""
        mock_search.return_value = {
            "items": [],
            "total": 0
        }

        response = client.get("/api/transcripts/search?q=nonexistent")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    @patch('app.routers.transcripts.stt_service.search_transcripts')
    def test_search_transcripts_server_error(self, mock_search, client):
        """Test search with server error."""
        mock_search.side_effect = Exception("Search error")

        response = client.get("/api/transcripts/search?q=test")

        assert response.status_code == 500
