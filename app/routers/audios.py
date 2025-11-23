"""
Audios router - API endpoints for audio operations.
Handles audio extraction and management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.database import get_db
from app.schemas import AudioResponse, AudioExtractRequest
from app.services import audio_service

router = APIRouter(prefix="/api/audios", tags=["audios"])


@router.post("/extract", response_model=AudioResponse, status_code=201)
async def extract_audio(
    request: AudioExtractRequest,
    db: Session = Depends(get_db)
) -> AudioResponse:
    """
    Extract audio from video.

    - **video_id**: Video ID to extract audio from
    """
    try:
        audio = await audio_service.handle_audio_extraction(db, request.video_id)
        return AudioResponse.model_validate(audio)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.get("", response_model=Dict[str, Any])
def list_audios(
    video_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List audios with pagination and optional video filter.

    - **video_id**: Optional video ID filter
    - **limit**: Maximum number of results (default: 10)
    - **offset**: Number of results to skip (default: 0)
    """
    try:
        result = audio_service.get_audio_list(db, video_id=video_id, limit=limit, offset=offset)

        # Convert ORM objects to response models
        items = [AudioResponse.model_validate(audio) for audio in result["items"]]

        return {
            "total": result["total"],
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{audio_id}", response_model=AudioResponse)
def get_audio(
    audio_id: int,
    db: Session = Depends(get_db)
) -> AudioResponse:
    """
    Get specific audio by ID.

    - **audio_id**: Audio ID
    """
    try:
        audio = audio_service.get_audio_by_id(db, audio_id)
        return AudioResponse.model_validate(audio)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{audio_id}", status_code=204)
def delete_audio(
    audio_id: int,
    db: Session = Depends(get_db)
) -> None:
    """
    Delete audio and associated files.

    - **audio_id**: Audio ID
    """
    try:
        result = audio_service.delete_audio(db, audio_id)
        if not result:
            raise HTTPException(status_code=404, detail="Audio not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
