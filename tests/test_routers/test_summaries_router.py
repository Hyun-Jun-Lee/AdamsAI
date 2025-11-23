"""
Integration tests for summaries router.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from app.routers import summaries
from app.database import get_db


@pytest.fixture
def app():
    """Create FastAPI test application."""
    app = FastAPI()
    app.include_router(summaries.router)
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
def mock_summary(summary_factory, transcript_factory, audio_factory, video_factory):
    """Mock summary object using factory."""
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)
    return summary_factory(
        transcript_id=transcript.id,
        summary_text="This is a test summary.",
        ai_model_name="gpt-4"
    )


class TestCreateSummary:
    """Tests for POST /api/summaries/create endpoint."""

    @patch('app.routers.summaries.summary_service.handle_summary_generation', new_callable=AsyncMock)
    async def test_create_summary_success(self, mock_generate, client, mock_summary):
        """Test successful summary creation."""
        mock_generate.return_value = mock_summary

        response = client.post(
            "/api/summaries/create",
            json={"transcript_id": 1, "ai_model_name": "gpt-4"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["transcript_id"] == 1
        assert data["ai_model_name"] == "gpt-4"
        assert "test summary" in data["summary_text"]

    @patch('app.routers.summaries.summary_service.handle_summary_generation', new_callable=AsyncMock)
    async def test_create_summary_with_template_id(self, mock_generate, client, mock_summary):
        """Test summary creation with prompt template ID."""
        mock_generate.return_value = mock_summary

        response = client.post(
            "/api/summaries/create",
            json={
                "transcript_id": 1,
                "prompt_template_id": 1
            }
        )

        assert response.status_code == 201
        mock_generate.assert_called_once()

    @patch('app.routers.summaries.summary_service.handle_summary_generation', new_callable=AsyncMock)
    async def test_create_summary_with_template_name(self, mock_generate, client, mock_summary):
        """Test summary creation with prompt template name."""
        mock_generate.return_value = mock_summary

        response = client.post(
            "/api/summaries/create",
            json={
                "transcript_id": 1,
                "prompt_template_name": "default"
            }
        )

        assert response.status_code == 201
        mock_generate.assert_called_once()

    @patch('app.routers.summaries.summary_service.handle_summary_generation', new_callable=AsyncMock)
    async def test_create_summary_invalid_transcript(self, mock_generate, client):
        """Test summary creation with invalid transcript ID."""
        mock_generate.side_effect = ValueError("Transcript not found")

        response = client.post(
            "/api/summaries/create",
            json={"transcript_id": 999}
        )

        assert response.status_code == 400
        assert "Transcript not found" in response.json()["detail"]

    @patch('app.routers.summaries.summary_service.handle_summary_generation', new_callable=AsyncMock)
    async def test_create_summary_server_error(self, mock_generate, client):
        """Test summary creation with server error."""
        mock_generate.side_effect = Exception("API error")

        response = client.post(
            "/api/summaries/create",
            json={"transcript_id": 1}
        )

        assert response.status_code == 500
        assert "Summarization failed" in response.json()["detail"]


class TestListSummaries:
    """Tests for GET /api/summaries endpoint."""

    @patch('app.routers.summaries.summary_service.get_summary_list')
    def test_list_summaries_success(self, mock_list, client, mock_summary):
        """Test successful summary listing."""
        mock_list.return_value = {
            "items": [mock_summary],
            "total": 1
        }

        response = client.get("/api/summaries")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == 1

    @patch('app.routers.summaries.summary_service.get_summary_list')
    def test_list_summaries_with_transcript_filter(self, mock_list, client, mock_summary):
        """Test summary listing with transcript filter."""
        mock_list.return_value = {
            "items": [mock_summary],
            "total": 1
        }

        response = client.get("/api/summaries?transcript_id=1&limit=10&offset=0")

        assert response.status_code == 200
        mock_list.assert_called_once()

    @patch('app.routers.summaries.summary_service.get_summary_list')
    def test_list_summaries_server_error(self, mock_list, client):
        """Test listing with server error."""
        mock_list.side_effect = Exception("Database error")

        response = client.get("/api/summaries")

        assert response.status_code == 500


class TestGetSummary:
    """Tests for GET /api/summaries/{summary_id} endpoint."""

    @patch('app.routers.summaries.summary_service.get_summary_by_id')
    def test_get_summary_success(self, mock_get, client, mock_summary):
        """Test successful summary retrieval."""
        mock_get.return_value = mock_summary

        response = client.get("/api/summaries/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["transcript_id"] == 1

    @patch('app.routers.summaries.summary_service.get_summary_by_id')
    def test_get_summary_not_found(self, mock_get, client):
        """Test summary not found."""
        mock_get.side_effect = ValueError("Summary not found")

        response = client.get("/api/summaries/999")

        assert response.status_code == 404
        assert "Summary not found" in response.json()["detail"]


class TestSearchByModel:
    """Tests for GET /api/summaries/search/by-model endpoint."""

    @patch('app.routers.summaries.summary_service.get_summaries_by_model')
    def test_search_by_model_success(self, mock_search, client, mock_summary):
        """Test successful search by model."""
        mock_search.return_value = {
            "items": [mock_summary],
            "total": 1
        }

        response = client.get("/api/summaries/search/by-model?model=gpt&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert "gpt" in data["items"][0]["ai_model_name"]

    @patch('app.routers.summaries.summary_service.get_summaries_by_model')
    def test_search_by_model_partial_match(self, mock_search, client, mock_summary):
        """Test search with partial model name."""
        mock_search.return_value = {
            "items": [mock_summary],
            "total": 1
        }

        response = client.get("/api/summaries/search/by-model?model=gpt-4")

        assert response.status_code == 200
        # Service should use LIKE search
        mock_search.assert_called_once()

    @patch('app.routers.summaries.summary_service.get_summaries_by_model')
    def test_search_by_model_empty_result(self, mock_search, client):
        """Test search with no results."""
        mock_search.return_value = {
            "items": [],
            "total": 0
        }

        response = client.get("/api/summaries/search/by-model?model=nonexistent")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    @patch('app.routers.summaries.summary_service.get_summaries_by_model')
    def test_search_by_model_server_error(self, mock_search, client):
        """Test search with server error."""
        mock_search.side_effect = Exception("Search error")

        response = client.get("/api/summaries/search/by-model?model=gpt")

        assert response.status_code == 500
