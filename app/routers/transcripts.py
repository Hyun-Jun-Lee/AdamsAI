"""
Transcripts router - API endpoints for transcription operations.
Handles speech-to-text processing and transcript management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.database import get_db
from app.schemas import TranscriptResponse, TranscriptCreateRequest
from app.services import stt_service

router = APIRouter(prefix="/api/transcripts", tags=["transcripts"])


@router.post("/create", response_model=TranscriptResponse, status_code=202)
async def create_transcript(
    request: TranscriptCreateRequest,
    db: Session = Depends(get_db)
) -> TranscriptResponse:
    """
    Create transcript from audio using STT (Speech-To-Text).

    - **audio_id**: Audio ID to transcribe
    - **language**: Language code (default: 'ko')
    """
    try:
        transcript = await stt_service.handle_transcription(
            db,
            audio_id=request.audio_id,
            language=request.language or "ko"
        )
        return TranscriptResponse.model_validate(transcript)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.get("", response_model=Dict[str, Any])
def list_transcripts(
    audio_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List transcripts with pagination and optional audio filter.

    - **audio_id**: Optional audio ID filter
    - **limit**: Maximum number of results (default: 10)
    - **offset**: Number of results to skip (default: 0)
    """
    try:
        result = stt_service.get_transcript_list(db, audio_id=audio_id, limit=limit, offset=offset)

        # Convert ORM objects to response models
        items = [TranscriptResponse.model_validate(transcript) for transcript in result["items"]]

        return {
            "total": result["total"],
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=Dict[str, Any])
def search_transcripts(
    q: str,
    limit: int = 10,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Search transcripts by text content.

    - **q**: Search query
    - **limit**: Maximum number of results (default: 10)
    """
    try:
        result = stt_service.search_transcripts(db, search_query=q, limit=limit)

        # Convert ORM objects to response models
        items = [TranscriptResponse.model_validate(transcript) for transcript in result["items"]]

        return {
            "total": result["total"],
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{transcript_id}", response_model=TranscriptResponse)
def get_transcript(
    transcript_id: int,
    db: Session = Depends(get_db)
) -> TranscriptResponse:
    """
    Get specific transcript by ID.

    - **transcript_id**: Transcript ID
    """
    try:
        transcript = stt_service.get_transcript_by_id(db, transcript_id)
        return TranscriptResponse.model_validate(transcript)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
