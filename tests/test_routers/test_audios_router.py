"""
Integration tests for audios router.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from app.routers import audios
from app.database import get_db


@pytest.fixture
def app():
    """Create FastAPI test application."""
    app = FastAPI()
    app.include_router(audios.router)
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
def mock_audio(audio_factory, video_factory):
    """Mock audio object using factory."""
    video = video_factory()
    return audio_factory(
        video_id=video.id,
        filename="test_audio.mp3",
        filepath="/storage/audios/test_audio.mp3",
        file_size=512000,
        duration=120.5
    )


class TestExtractAudio:
    """Tests for POST /api/audios/extract endpoint."""

    @patch('app.routers.audios.audio_service.handle_audio_extraction', new_callable=AsyncMock)
    async def test_extract_audio_success(self, mock_extract, client, mock_audio):
        """Test successful audio extraction."""
        mock_extract.return_value = mock_audio

        response = client.post(
            "/api/audios/extract",
            json={"video_id": 1}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["video_id"] == 1
        assert data["filename"] == "test_audio.mp3"

    @patch('app.routers.audios.audio_service.handle_audio_extraction', new_callable=AsyncMock)
    async def test_extract_audio_invalid_video(self, mock_extract, client):
        """Test extraction with invalid video ID."""
        mock_extract.side_effect = ValueError("Video not found")

        response = client.post(
            "/api/audios/extract",
            json={"video_id": 999}
        )

        assert response.status_code == 400
        assert "Video not found" in response.json()["detail"]

    @patch('app.routers.audios.audio_service.handle_audio_extraction', new_callable=AsyncMock)
    async def test_extract_audio_server_error(self, mock_extract, client):
        """Test extraction with server error."""
        mock_extract.side_effect = Exception("Extraction failed")

        response = client.post(
            "/api/audios/extract",
            json={"video_id": 1}
        )

        assert response.status_code == 500
        assert "Extraction failed" in response.json()["detail"]


class TestListAudios:
    """Tests for GET /api/audios endpoint."""

    @patch('app.routers.audios.audio_service.get_audio_list')
    def test_list_audios_success(self, mock_list, client, mock_audio):
        """Test successful audio listing."""
        mock_list.return_value = {
            "items": [mock_audio],
            "total": 1
        }

        response = client.get("/api/audios")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == 1

    @patch('app.routers.audios.audio_service.get_audio_list')
    def test_list_audios_with_video_filter(self, mock_list, client, mock_audio):
        """Test audio listing with video filter."""
        mock_list.return_value = {
            "items": [mock_audio],
            "total": 1
        }

        response = client.get("/api/audios?video_id=1&limit=10&offset=0")

        assert response.status_code == 200
        mock_list.assert_called_once()

    @patch('app.routers.audios.audio_service.get_audio_list')
    def test_list_audios_server_error(self, mock_list, client):
        """Test listing with server error."""
        mock_list.side_effect = Exception("Database error")

        response = client.get("/api/audios")

        assert response.status_code == 500


class TestGetAudio:
    """Tests for GET /api/audios/{audio_id} endpoint."""

    @patch('app.routers.audios.audio_service.get_audio_by_id')
    def test_get_audio_success(self, mock_get, client, mock_audio):
        """Test successful audio retrieval."""
        mock_get.return_value = mock_audio

        response = client.get("/api/audios/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["filename"] == "test_audio.mp3"

    @patch('app.routers.audios.audio_service.get_audio_by_id')
    def test_get_audio_not_found(self, mock_get, client):
        """Test audio not found."""
        mock_get.side_effect = ValueError("Audio not found")

        response = client.get("/api/audios/999")

        assert response.status_code == 404
        assert "Audio not found" in response.json()["detail"]


class TestDeleteAudio:
    """Tests for DELETE /api/audios/{audio_id} endpoint."""

    @patch('app.routers.audios.audio_service.delete_audio')
    def test_delete_audio_success(self, mock_delete, client):
        """Test successful audio deletion."""
        mock_delete.return_value = True

        response = client.delete("/api/audios/1")

        assert response.status_code == 204

    @patch('app.routers.audios.audio_service.delete_audio')
    def test_delete_audio_not_found(self, mock_delete, client):
        """Test audio not found for deletion."""
        mock_delete.return_value = False

        response = client.delete("/api/audios/999")

        assert response.status_code == 404
        assert "Audio not found" in response.json()["detail"]

    @patch('app.routers.audios.audio_service.delete_audio')
    def test_delete_audio_server_error(self, mock_delete, client):
        """Test deletion with server error."""
        mock_delete.side_effect = Exception("Deletion failed")

        response = client.delete("/api/audios/1")

        assert response.status_code == 500
