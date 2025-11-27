"""
PromptTemplate router - API endpoints for prompt template operations.
Handles CRUD operations for summarization prompt templates.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.database import get_db
from app.schemas import PromptTemplateResponse, PromptTemplateCreate, PromptTemplateUpdate
from app.services import prompt_template_service

router = APIRouter(prefix="/api/prompt-templates", tags=["prompt-templates"])


@router.get("", response_model=Dict[str, Any])
def list_prompt_templates(
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


@router.get("/{template_id}", response_model=PromptTemplateResponse)
def get_prompt_template(
    template_id: int,
    db: Session = Depends(get_db)
) -> PromptTemplateResponse:
    """
    Get specific prompt template by ID.

    - **template_id**: Prompt template ID
    """
    try:
        template = prompt_template_service.get_template_by_id(db, template_id)
        return PromptTemplateResponse.model_validate(template)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/name/{name}", response_model=PromptTemplateResponse)
def get_prompt_template_by_name(
    name: str,
    db: Session = Depends(get_db)
) -> PromptTemplateResponse:
    """
    Get specific prompt template by name.

    - **name**: Prompt template name
    """
    try:
        template = prompt_template_service.get_template_by_name(db, name)
        return PromptTemplateResponse.model_validate(template)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=PromptTemplateResponse, status_code=201)
def create_prompt_template(
    template_data: PromptTemplateCreate,
    db: Session = Depends(get_db)
) -> PromptTemplateResponse:
    """
    Create new prompt template.

    - **name**: Template name (must be unique)
    - **content**: Template content with {transcript} placeholder
    - **description**: Optional description
    - **is_active**: Active status (default: true)
    - **category**: Template category (default: "general")
    """
    try:
        template = prompt_template_service.create_template(db, template_data)
        return PromptTemplateResponse.model_validate(template)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{template_id}", response_model=PromptTemplateResponse)
def update_prompt_template(
    template_id: int,
    updates: PromptTemplateUpdate,
    db: Session = Depends(get_db)
) -> PromptTemplateResponse:
    """
    Update existing prompt template.

    - **template_id**: Template ID to update
    - **name**: Optional new name
    - **content**: Optional new content
    - **description**: Optional new description
    - **is_active**: Optional active status
    - **category**: Optional category
    """
    try:
        template = prompt_template_service.update_template(db, template_id, updates)
        return PromptTemplateResponse.model_validate(template)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{template_id}/toggle", response_model=PromptTemplateResponse)
def toggle_template_active(
    template_id: int,
    is_active: bool,
    db: Session = Depends(get_db)
) -> PromptTemplateResponse:
    """
    Toggle template active status.

    - **template_id**: Template ID
    - **is_active**: New active status
    """
    try:
        template = prompt_template_service.toggle_template_active(db, template_id, is_active)
        return PromptTemplateResponse.model_validate(template)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}", status_code=204)
def delete_prompt_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete prompt template.

    - **template_id**: Template ID to delete
    """
    try:
        prompt_template_service.delete_template(db, template_id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
