"""
Videos router - API endpoints for video operations.
Handles video upload, download, and management.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.database import get_db
from app.schemas import VideoResponse, VideoDownloadRequest
from app.services import video_service

router = APIRouter(prefix="/api/videos", tags=["videos"])


@router.post("/upload", response_model=VideoResponse, status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> VideoResponse:
    """
    Upload video file.

    - **file**: Video file to upload
    """
    try:
        video = await video_service.handle_video_upload(db, file)
        return VideoResponse.model_validate(video)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/download", response_model=VideoResponse, status_code=202)
async def download_video(
    request: VideoDownloadRequest,
    db: Session = Depends(get_db)
) -> VideoResponse:
    """
    Download video from URL.

    - **url**: Video URL (YouTube, etc.)
    - **title**: Optional custom title
    """
    try:
        video = await video_service.handle_video_download(
            db,
            url=request.url,
            title=request.title
        )
        return VideoResponse.model_validate(video)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("", response_model=Dict[str, Any])
def list_videos(
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List videos with pagination and optional status filter.

    - **status**: Optional status filter (uploaded, processing, completed, failed)
    - **limit**: Maximum number of results (default: 10)
    - **offset**: Number of results to skip (default: 0)
    """
    try:
        result = video_service.get_video_list(db, status=status, limit=limit, offset=offset)

        # Convert ORM objects to response models
        items = [VideoResponse.model_validate(video) for video in result["items"]]

        return {
            "total": result["total"],
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: int,
    db: Session = Depends(get_db)
) -> VideoResponse:
    """
    Get specific video by ID.

    - **video_id**: Video ID
    """
    try:
        video = video_service.get_video_by_id(db, video_id)
        return VideoResponse.model_validate(video)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{video_id}", status_code=204)
def delete_video(
    video_id: int,
    db: Session = Depends(get_db)
) -> None:
    """
    Delete video and associated files.

    - **video_id**: Video ID
    """
    try:
        result = video_service.delete_video(db, video_id)
        if not result:
            raise HTTPException(status_code=404, detail="Video not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
