"""
Integration tests for videos router.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from io import BytesIO

from app.routers import videos
from app.database import get_db


@pytest.fixture
def app():
    """Create FastAPI test application."""
    app = FastAPI()
    app.include_router(videos.router)
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
def mock_video(video_factory):
    """Mock video object using factory."""
    return video_factory(
        filename="test_video.mp4",
        filepath="/storage/videos/test_video.mp4",
        file_size=1024000,
        duration=120.5,
        status="uploaded",
        source_type="upload"
    )


@pytest.fixture
def mock_upload_file():
    """Mock UploadFile."""
    mock_file = MagicMock()
    mock_file.filename = "test_video.mp4"
    mock_file.file = BytesIO(b"test video content")
    mock_file.size = 1024000
    return mock_file


class TestUploadVideo:
    """Tests for POST /api/videos/upload endpoint."""

    @patch('app.routers.videos.video_service.handle_video_upload', new_callable=AsyncMock)
    async def test_upload_video_success(self, mock_upload, client, mock_video):
        """Test successful video upload."""
        mock_upload.return_value = mock_video

        response = client.post(
            "/api/videos/upload",
            files={"file": ("test.mp4", BytesIO(b"content"), "video/mp4")}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["filename"] == "test_video.mp4"
        assert data["status"] == "uploaded"

    @patch('app.routers.videos.video_service.handle_video_upload', new_callable=AsyncMock)
    async def test_upload_video_invalid_format(self, mock_upload, client):
        """Test upload with invalid file format."""
        mock_upload.side_effect = ValueError("Unsupported file format")

        response = client.post(
            "/api/videos/upload",
            files={"file": ("test.txt", BytesIO(b"content"), "text/plain")}
        )

        assert response.status_code == 400
        assert "Unsupported file format" in response.json()["detail"]

    @patch('app.routers.videos.video_service.handle_video_upload', new_callable=AsyncMock)
    async def test_upload_video_server_error(self, mock_upload, client):
        """Test upload with server error."""
        mock_upload.side_effect = Exception("Server error")

        response = client.post(
            "/api/videos/upload",
            files={"file": ("test.mp4", BytesIO(b"content"), "video/mp4")}
        )

        assert response.status_code == 500
        assert "Upload failed" in response.json()["detail"]


class TestDownloadVideo:
    """Tests for POST /api/videos/download endpoint."""

    @patch('app.routers.videos.video_service.handle_video_download', new_callable=AsyncMock)
    async def test_download_video_success(self, mock_download, client, mock_video):
        """Test successful video download."""
        mock_download.return_value = mock_video

        response = client.post(
            "/api/videos/download",
            json={"url": "https://youtube.com/watch?v=test", "title": "Test Video"}
        )

        assert response.status_code == 202
        data = response.json()
        assert data["id"] == 1
        assert data["filename"] == "test_video.mp4"

    @patch('app.routers.videos.video_service.handle_video_download', new_callable=AsyncMock)
    async def test_download_video_invalid_url(self, mock_download, client):
        """Test download with invalid URL - Pydantic validation error."""
        # Pydantic validator raises ValueError which returns 422
        response = client.post(
            "/api/videos/download",
            json={"url": "invalid-url"}
        )

        assert response.status_code == 422  # Pydantic validation error
        response_data = response.json()
        assert "detail" in response_data


class TestListVideos:
    """Tests for GET /api/videos endpoint."""

    @patch('app.routers.videos.video_service.get_video_list')
    def test_list_videos_success(self, mock_list, client, mock_video):
        """Test successful video listing."""
        mock_list.return_value = {
            "items": [mock_video],
            "total": 1
        }

        response = client.get("/api/videos")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == 1

    @patch('app.routers.videos.video_service.get_video_list')
    def test_list_videos_with_filters(self, mock_list, client, mock_video):
        """Test video listing with filters."""
        mock_list.return_value = {
            "items": [mock_video],
            "total": 1
        }

        response = client.get("/api/videos?status=uploaded&limit=5&offset=0")

        assert response.status_code == 200
        mock_list.assert_called_once()


class TestGetVideo:
    """Tests for GET /api/videos/{video_id} endpoint."""

    @patch('app.routers.videos.video_service.get_video_by_id')
    def test_get_video_success(self, mock_get, client, mock_video):
        """Test successful video retrieval."""
        mock_get.return_value = mock_video

        response = client.get("/api/videos/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["filename"] == "test_video.mp4"

    @patch('app.routers.videos.video_service.get_video_by_id')
    def test_get_video_not_found(self, mock_get, client):
        """Test video not found."""
        mock_get.side_effect = ValueError("Video not found")

        response = client.get("/api/videos/999")

        assert response.status_code == 404
        assert "Video not found" in response.json()["detail"]


class TestDeleteVideo:
    """Tests for DELETE /api/videos/{video_id} endpoint."""

    @patch('app.routers.videos.video_service.delete_video')
    def test_delete_video_success(self, mock_delete, client):
        """Test successful video deletion."""
        mock_delete.return_value = True

        response = client.delete("/api/videos/1")

        assert response.status_code == 204

    @patch('app.routers.videos.video_service.delete_video')
    def test_delete_video_not_found(self, mock_delete, client):
        """Test video not found for deletion."""
        mock_delete.return_value = False

        response = client.delete("/api/videos/999")

        assert response.status_code == 404
        assert "Video not found" in response.json()["detail"]
