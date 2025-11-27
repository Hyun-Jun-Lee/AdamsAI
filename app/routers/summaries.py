"""
Summaries router - API endpoints for summarization operations.
Handles AI-powered text summarization.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging

from app.database import get_db
from app.schemas import (
    SummaryResponse,
    SummaryCreateRequest,
    PromptTemplateResponse,
    PromptTemplateCreate,
    PromptTemplateUpdate
)
from app.services import summary_service, prompt_template_service

logger = logging.getLogger(__name__)
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
        logger.info(f"Received summary creation request: transcript_id={request.transcript_id}, model={request.ai_model_name}, template_id={request.prompt_template_id}")

        summary = await summary_service.handle_summary_generation(
            db,
            transcript_id=request.transcript_id,
            model_name=request.ai_model_name,
            prompt_template_name=request.prompt_template_name,
            prompt_template_id=request.prompt_template_id
        )

        logger.info(f"Summary created successfully with id={summary.id}")
        return SummaryResponse.model_validate(summary)
    except ValueError as e:
        logger.error(f"Validation error in summary creation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in summary creation: {str(e)}", exc_info=True)
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


# ============================================================================
# Template Endpoints (Must be BEFORE /{summary_id} to avoid path conflicts)
# ============================================================================

@router.get("/templates", response_model=Dict[str, Any])
def list_templates(
    is_active: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List prompt templates with pagination and optional active filter.

    - **is_active**: Optional active status filter
    - **limit**: Maximum number of results (default: 100)
    - **offset**: Number of results to skip (default: 0)
    """
    try:
        result = prompt_template_service.get_template_list(
            db,
            is_active=is_active,
            limit=limit,
            offset=offset
        )

        # Convert ORM objects to response models
        items = [PromptTemplateResponse.model_validate(template) for template in result["items"]]

        return {
            "total": result["total"],
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}", response_model=PromptTemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(get_db)
) -> PromptTemplateResponse:
    """
    Get specific template by ID.

    - **template_id**: Template ID
    """
    try:
        template = prompt_template_service.get_template_by_id(db, template_id)
        return PromptTemplateResponse.model_validate(template)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates", response_model=PromptTemplateResponse, status_code=201)
def create_template(
    template_data: PromptTemplateCreate,
    db: Session = Depends(get_db)
) -> PromptTemplateResponse:
    """
    Create new prompt template.

    - **name**: Template name (unique)
    - **content**: Template content with {transcript} placeholder
    - **description**: Optional description
    - **is_active**: Active status (default: true)
    - **category**: Category (default: 'general')
    """
    try:
        template = prompt_template_service.create_template(db, template_data)
        return PromptTemplateResponse.model_validate(template)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/templates/{template_id}", response_model=PromptTemplateResponse)
def update_template(
    template_id: int,
    updates: PromptTemplateUpdate,
    db: Session = Depends(get_db)
) -> PromptTemplateResponse:
    """
    Update existing template.

    - **template_id**: Template ID
    - **name**: Optional new name
    - **content**: Optional new content
    - **description**: Optional new description
    - **is_active**: Optional new active status
    - **category**: Optional new category
    """
    try:
        template = prompt_template_service.update_template(db, template_id, updates)
        return PromptTemplateResponse.model_validate(template)
    except ValueError as e:
        status_code = 404 if "not found" in str(e).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/templates/{template_id}", status_code=204)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db)
) -> None:
    """
    Delete prompt template.

    - **template_id**: Template ID
    """
    try:
        prompt_template_service.delete_template(db, template_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Summary by ID (Must be LAST to avoid catching specific paths)
# ============================================================================

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


@router.delete("/{summary_id}", status_code=204)
def delete_summary(
    summary_id: int,
    db: Session = Depends(get_db)
) -> None:
    """
    Delete summary by ID.

    - **summary_id**: Summary ID
    """
    try:
        summary_service.delete_summary(db, summary_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
