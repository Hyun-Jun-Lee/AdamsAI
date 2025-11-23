"""
Summaries router - API endpoints for summarization operations.
Handles AI-powered text summarization.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.database import get_db
from app.schemas import SummaryResponse, SummaryCreateRequest
from app.services import summary_service

router = APIRouter(prefix="/api/summaries", tags=["summaries"])


@router.post("/create", response_model=SummaryResponse, status_code=201)
async def create_summary(
    request: SummaryCreateRequest,
    db: Session = Depends(get_db)
) -> SummaryResponse:
    """
    Create summary from transcript using LLM.

    - **transcript_id**: Transcript ID to summarize
    - **ai_model_name**: Optional AI model name (default from settings)
    - **prompt_template_id**: Optional prompt template ID
    - **prompt_template_name**: Optional prompt template name
    """
    try:
        summary = await summary_service.handle_summary_generation(
            db,
            transcript_id=request.transcript_id,
            model_name=request.ai_model_name,
            prompt_template_name=request.prompt_template_name,
            prompt_template_id=request.prompt_template_id
        )
        return SummaryResponse.model_validate(summary)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")


@router.get("", response_model=Dict[str, Any])
def list_summaries(
    transcript_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List summaries with pagination and optional transcript filter.

    - **transcript_id**: Optional transcript ID filter
    - **limit**: Maximum number of results (default: 10)
    - **offset**: Number of results to skip (default: 0)
    """
    try:
        result = summary_service.get_summary_list(db, transcript_id=transcript_id, limit=limit, offset=offset)

        # Convert ORM objects to response models
        items = [SummaryResponse.model_validate(summary) for summary in result["items"]]

        return {
            "total": result["total"],
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{summary_id}", response_model=SummaryResponse)
def get_summary(
    summary_id: int,
    db: Session = Depends(get_db)
) -> SummaryResponse:
    """
    Get specific summary by ID.

    - **summary_id**: Summary ID
    """
    try:
        summary = summary_service.get_summary_by_id(db, summary_id)
        return SummaryResponse.model_validate(summary)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/by-model", response_model=Dict[str, Any])
def search_by_model(
    model: str,
    limit: int = 10,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Search summaries by AI model name (supports partial match).

    - **model**: AI model name or partial name (e.g., 'claude', 'gpt-4')
    - **limit**: Maximum number of results (default: 10)
    """
    try:
        result = summary_service.get_summaries_by_model(db, model_name=model, limit=limit)

        # Convert ORM objects to response models
        items = [SummaryResponse.model_validate(summary) for summary in result["items"]]

        return {
            "total": result["total"],
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
