"""
Summary service - Business logic for AI summarization operations.
Handles transcript summarization using LLM API (OpenRouter).
"""

import logging
import traceback
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import httpx

from app.config import get_settings
from app.models import Summary
from app.schemas import SummaryCreate
from app.repositories import summary_repository, transcript_repository, prompt_template_repository

logger = logging.getLogger(__name__)


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
    try:
        settings = get_settings()

        logger.info(f"Calling OpenRouter API with model: {model_name}")

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

        logger.info(f"Request payload: model={model_name}, prompt_length={len(prompt)}")

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=data)

        logger.info(f"OpenRouter API response status: {response.status_code}")

        if response.status_code != 200:
            error_detail = response.text
            logger.error(f"OpenRouter API error for model={model_name}: {response.status_code}")
            logger.error(f"Response body: {error_detail}")
            raise Exception(f"OpenRouter API error: {response.status_code} - {error_detail}")

        result = response.json()
        logger.info(f"OpenRouter API success for model={model_name}")

        if "choices" not in result or len(result["choices"]) == 0:
            logger.error(f"Invalid response structure: {result}")
            raise Exception("Invalid response structure from OpenRouter API")

        return result["choices"][0]["message"]["content"]
    except httpx.TimeoutException as e:
        logger.error(f"Timeout calling OpenRouter API for model={model_name}: {str(e)}")
        raise Exception(f"API request timeout after 120 seconds")
    except httpx.RequestError as e:
        logger.error(f"Request error calling OpenRouter API for model={model_name}: {str(e)}")
        raise Exception(f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in call_openrouter_api for model={model_name}: {str(e)}\n{traceback.format_exc()}")
        raise


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
    try:
        if template_id:
            template = prompt_template_repository.get_prompt_template_by_id(db, template_id)
        elif template_name:
            template = prompt_template_repository.get_prompt_template_by_name(db, template_name)
        else:
            # Get default template - first active template
            active_templates = prompt_template_repository.get_active_prompt_templates(db)
            template = active_templates[0] if active_templates else None

        if not template:
            logger.error(f"Prompt template not found: name={template_name}, id={template_id}")
            raise ValueError(f"Prompt template not found: {template_name or template_id}")

        if not template.is_active:
            logger.error(f"Template '{template.name}' is inactive")
            raise ValueError(f"Template '{template.name}' is inactive")

        return template.content, template.id
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error in get_prompt_template_content (name={template_name}, id={template_id}): {str(e)}\n{traceback.format_exc()}")
        raise


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
    try:
        settings = get_settings()

        logger.info(f"Starting summary generation for transcript_id={transcript_id}, model={model_name}, template_id={prompt_template_id}")

        # Get transcript record
        transcript = transcript_repository.get_transcript_by_id(db, transcript_id)
        if not transcript:
            logger.error(f"Transcript not found with id: {transcript_id}")
            raise ValueError(f"Transcript not found with id: {transcript_id}")

        logger.info(f"Found transcript with id={transcript_id}, text_length={len(transcript.text)}")

        # Get prompt template
        try:
            template_content, used_template_id = get_prompt_template_content(
                db,
                template_name=prompt_template_name,
                template_id=prompt_template_id
            )
            logger.info(f"Using prompt template id={used_template_id}")
        except ValueError as e:
            logger.error(f"Template error for transcript_id={transcript_id}: {str(e)}\n{traceback.format_exc()}")
            raise ValueError(f"Template error: {str(e)}")

        # Format prompt with transcript
        prompt = template_content.format(transcript=transcript.text)
        logger.info(f"Formatted prompt length: {len(prompt)}")

        # Use default model if not specified
        if not model_name:
            model_name = settings.default_llm_model
            logger.info(f"Using default model: {model_name}")

        # Call LLM API
        try:
            logger.info(f"Calling LLM API with model: {model_name}")
            summary_text = await call_openrouter_api(prompt, model_name)
            logger.info(f"Received summary text, length: {len(summary_text)}")
        except Exception as e:
            logger.error(f"Summarization failed for transcript_id={transcript_id}: {str(e)}\n{traceback.format_exc()}")
            raise ValueError(f"Summarization failed: {str(e)}")

        if not summary_text:
            logger.error(f"Summarization returned empty text for transcript_id={transcript_id}")
            raise ValueError("Summarization returned empty text")

        # Create summary record
        summary_data = SummaryCreate(
            transcript_id=transcript_id,
            summary_text=summary_text,
            ai_model_name=model_name,
            prompt_template_id=used_template_id
        )

        logger.info(f"Creating summary record for transcript_id={transcript_id}")
        summary = summary_repository.create_summary(db, summary_data)
        logger.info(f"Successfully created summary with id={summary.id}")

        return summary
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in handle_summary_generation for transcript_id={transcript_id}: {str(e)}\n{traceback.format_exc()}")
        raise


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
    try:
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
    except Exception as e:
        logger.error(f"Error in get_summary_list (transcript_id={transcript_id}, limit={limit}, offset={offset}): {str(e)}\n{traceback.format_exc()}")
        raise


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
    try:
        summary = summary_repository.get_summary_by_id(db, summary_id)
        if not summary:
            logger.error(f"Summary not found with id: {summary_id}")
            raise ValueError(f"Summary not found with id: {summary_id}")

        return summary
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error in get_summary_by_id for summary_id={summary_id}: {str(e)}\n{traceback.format_exc()}")
        raise


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
    try:
        summaries = summary_repository.get_summaries_by_ai_model(db, model_name)
        total = len(summaries)
        items = summaries[:limit]

        return {
            "total": total,
            "items": items
        }
    except Exception as e:
        logger.error(f"Error in get_summaries_by_model for model_name='{model_name}': {str(e)}\n{traceback.format_exc()}")
        raise


# ============================================================================
# Delete Operations
# ============================================================================

def delete_summary(db: Session, summary_id: int) -> None:
    """
    Delete summary by ID.

    Args:
        db: Database session
        summary_id: Summary ID

    Raises:
        ValueError: If summary not found
    """
    try:
        summary = summary_repository.get_summary_by_id(db, summary_id)
        if not summary:
            logger.error(f"Summary not found with id: {summary_id}")
            raise ValueError(f"Summary not found with id: {summary_id}")

        summary_repository.delete_summary(db, summary_id)
        logger.info(f"Successfully deleted summary with id: {summary_id}")
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error in delete_summary for summary_id={summary_id}: {str(e)}\n{traceback.format_exc()}")
        raise
