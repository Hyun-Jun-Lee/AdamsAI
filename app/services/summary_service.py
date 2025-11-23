"""
Summary service - Business logic for AI summarization operations.
Handles transcript summarization using LLM API (OpenRouter).
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import httpx

from app.config import get_settings
from app.models import Summary
from app.schemas import SummaryCreate
from app.repositories import summary_repository, transcript_repository, prompt_template_repository


# ============================================================================
# External API Operations
# ============================================================================

async def call_openrouter_api(prompt: str, model_name: str) -> str:
    """
    Call OpenRouter API for LLM completion.

    Args:
        prompt: Prompt text
        model_name: LLM model identifier (e.g., 'anthropic/claude-3.5-sonnet')

    Returns:
        str: Generated text

    Raises:
        Exception: If API call fails
    """
    settings = get_settings()

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, headers=headers, json=data)

    if response.status_code != 200:
        raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")

    result = response.json()
    return result["choices"][0]["message"]["content"]


# ============================================================================
# Template Operations
# ============================================================================

def get_prompt_template_content(
    db: Session,
    template_name: Optional[str] = None,
    template_id: Optional[int] = None
) -> tuple[str, Optional[int]]:
    """
    Get prompt template content by name or ID.

    Args:
        db: Database session
        template_name: Template name (e.g., 'default', 'detailed')
        template_id: Template ID

    Returns:
        tuple: (template_content, template_id)

    Raises:
        ValueError: If template not found
    """
    if template_id:
        template = prompt_template_repository.get_prompt_template_by_id(db, template_id)
    elif template_name:
        template = prompt_template_repository.get_prompt_template_by_name(db, template_name)
    else:
        # Get default template - first active template
        active_templates = prompt_template_repository.get_active_prompt_templates(db)
        template = active_templates[0] if active_templates else None

    if not template:
        raise ValueError(f"Prompt template not found: {template_name or template_id}")

    if not template.is_active:
        raise ValueError(f"Template '{template.name}' is inactive")

    return template.content, template.id


# ============================================================================
# Summarization Operations
# ============================================================================

async def handle_summary_generation(
    db: Session,
    transcript_id: int,
    model_name: Optional[str] = None,
    prompt_template_name: Optional[str] = None,
    prompt_template_id: Optional[int] = None
) -> Summary:
    """
    Handle transcript summarization using LLM API.

    Args:
        db: Database session
        transcript_id: Transcript ID to summarize
        model_name: Optional LLM model name (default from settings)
        prompt_template_name: Optional template name
        prompt_template_id: Optional template ID

    Returns:
        Summary: Created summary record

    Raises:
        ValueError: If transcript not found or summarization fails
    """
    settings = get_settings()

    # Get transcript record
    transcript = transcript_repository.get_transcript_by_id(db, transcript_id)
    if not transcript:
        raise ValueError(f"Transcript not found with id: {transcript_id}")

    # Get prompt template
    try:
        template_content, used_template_id = get_prompt_template_content(
            db,
            template_name=prompt_template_name,
            template_id=prompt_template_id
        )
    except ValueError as e:
        raise ValueError(f"Template error: {str(e)}")

    # Format prompt with transcript
    prompt = template_content.format(transcript=transcript.text)

    # Use default model if not specified
    if not model_name:
        model_name = settings.default_llm_model

    # Call LLM API
    try:
        summary_text = await call_openrouter_api(prompt, model_name)
    except Exception as e:
        raise ValueError(f"Summarization failed: {str(e)}")

    if not summary_text:
        raise ValueError("Summarization returned empty text")

    # Create summary record
    summary_data = SummaryCreate(
        transcript_id=transcript_id,
        summary_text=summary_text,
        ai_model_name=model_name,
        prompt_template_id=used_template_id
    )

    return summary_repository.create_summary(db, summary_data)


# ============================================================================
# Query Operations
# ============================================================================

def get_summary_list(
    db: Session,
    transcript_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Get paginated summary list with optional transcript filter.

    Args:
        db: Database session
        transcript_id: Optional transcript ID filter
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        Dict containing total count and summary items
    """
    if transcript_id:
        summaries = summary_repository.get_summaries_by_transcript_id(db, transcript_id)
        total = len(summaries)
        items = summaries[offset:offset + limit]
    else:
        total = summary_repository.count_summaries(db)
        items = summary_repository.get_summaries_paginated(db, skip=offset, limit=limit)

    return {
        "total": total,
        "items": items
    }


def get_summary_by_id(db: Session, summary_id: int) -> Summary:
    """
    Get specific summary by ID.

    Args:
        db: Database session
        summary_id: Summary ID

    Returns:
        Summary: Summary record

    Raises:
        ValueError: If summary not found
    """
    summary = summary_repository.get_summary_by_id(db, summary_id)
    if not summary:
        raise ValueError(f"Summary not found with id: {summary_id}")

    return summary


# ============================================================================
# Search Operations
# ============================================================================

def get_summaries_by_model(
    db: Session,
    model_name: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get summaries by AI model name (supports partial match).

    Args:
        db: Database session
        model_name: AI model name or partial name (e.g., 'claude', 'gpt-4')
        limit: Maximum number of results

    Returns:
        Dict containing total count and summary items
    """
    summaries = summary_repository.get_summaries_by_ai_model(db, model_name)
    total = len(summaries)
    items = summaries[:limit]

    return {
        "total": total,
        "items": items
    }
