"""
PromptTemplate service - Business logic for prompt template operations.
Handles template CRUD operations and validation.
"""

import logging
import traceback
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models import PromptTemplate
from app.schemas import PromptTemplateCreate, PromptTemplateUpdate
from app.repositories import prompt_template_repository

logger = logging.getLogger(__name__)


# ============================================================================
# Query Operations
# ============================================================================

def get_template_list(
    db: Session,
    is_active: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Get paginated template list with optional active filter.

    Args:
        db: Database session
        is_active: Optional active status filter
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        Dict containing total count and template items
    """
    try:
        if is_active is not None:
            if is_active:
                templates = prompt_template_repository.get_active_prompt_templates(db)
            else:
                # Get all templates and filter inactive ones
                all_templates = prompt_template_repository.get_all_prompt_templates(db)
                templates = [t for t in all_templates if not t.is_active]

            total = len(templates)
            items = templates[offset:offset + limit]
        else:
            templates = prompt_template_repository.get_all_prompt_templates(db)
            total = len(templates)
            items = templates[offset:offset + limit]

        return {
            "total": total,
            "items": items
        }
    except Exception as e:
        logger.error(f"Error in get_template_list (is_active={is_active}, limit={limit}, offset={offset}): {str(e)}\n{traceback.format_exc()}")
        raise


def get_template_by_id(db: Session, template_id: int) -> PromptTemplate:
    """
    Get specific template by ID.

    Args:
        db: Database session
        template_id: Template ID

    Returns:
        PromptTemplate: Template record

    Raises:
        ValueError: If template not found
    """
    try:
        template = prompt_template_repository.get_prompt_template_by_id(db, template_id)
        if not template:
            logger.error(f"Template not found with id: {template_id}")
            raise ValueError(f"Template not found with id: {template_id}")

        return template
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error in get_template_by_id for template_id={template_id}: {str(e)}\n{traceback.format_exc()}")
        raise


def get_template_by_name(db: Session, name: str) -> PromptTemplate:
    """
    Get specific template by name.

    Args:
        db: Database session
        name: Template name

    Returns:
        PromptTemplate: Template record

    Raises:
        ValueError: If template not found
    """
    try:
        template = prompt_template_repository.get_prompt_template_by_name(db, name)
        if not template:
            logger.error(f"Template not found with name: {name}")
            raise ValueError(f"Template not found with name: {name}")

        return template
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error in get_template_by_name for name={name}: {str(e)}\n{traceback.format_exc()}")
        raise


# ============================================================================
# Create Operations
# ============================================================================

def create_template(
    db: Session,
    template_data: PromptTemplateCreate
) -> PromptTemplate:
    """
    Create new prompt template.

    Args:
        db: Database session
        template_data: Template creation data

    Returns:
        PromptTemplate: Created template record

    Raises:
        ValueError: If template with same name already exists
    """
    try:
        # Check for duplicate name
        existing = prompt_template_repository.get_prompt_template_by_name(db, template_data.name)
        if existing:
            logger.error(f"Template with name '{template_data.name}' already exists")
            raise ValueError(f"Template with name '{template_data.name}' already exists")

        return prompt_template_repository.create_prompt_template(db, template_data)
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error in create_template for name={template_data.name}: {str(e)}\n{traceback.format_exc()}")
        raise


# ============================================================================
# Update Operations
# ============================================================================

def update_template(
    db: Session,
    template_id: int,
    updates: PromptTemplateUpdate
) -> PromptTemplate:
    """
    Update existing template.

    Args:
        db: Database session
        template_id: Template ID
        updates: Fields to update

    Returns:
        PromptTemplate: Updated template record

    Raises:
        ValueError: If template not found or name conflict
    """
    try:
        # Check template exists
        template = prompt_template_repository.get_prompt_template_by_id(db, template_id)
        if not template:
            logger.error(f"Template not found with id: {template_id}")
            raise ValueError(f"Template not found with id: {template_id}")

        # Check for name conflict if name is being updated
        if updates.name and updates.name != template.name:
            existing = prompt_template_repository.get_prompt_template_by_name(db, updates.name)
            if existing:
                logger.error(f"Template with name '{updates.name}' already exists")
                raise ValueError(f"Template with name '{updates.name}' already exists")

        updated_template = prompt_template_repository.update_prompt_template(db, template_id, updates)
        if not updated_template:
            logger.error(f"Failed to update template with id: {template_id}")
            raise ValueError(f"Failed to update template with id: {template_id}")

        return updated_template
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error in update_template for template_id={template_id}: {str(e)}\n{traceback.format_exc()}")
        raise


def toggle_template_active(
    db: Session,
    template_id: int,
    is_active: bool
) -> PromptTemplate:
    """
    Toggle template active status.

    Args:
        db: Database session
        template_id: Template ID
        is_active: New active status

    Returns:
        PromptTemplate: Updated template record

    Raises:
        ValueError: If template not found
    """
    try:
        if is_active:
            template = prompt_template_repository.activate_template(db, template_id)
        else:
            template = prompt_template_repository.deactivate_template(db, template_id)

        if not template:
            logger.error(f"Template not found with id: {template_id}")
            raise ValueError(f"Template not found with id: {template_id}")

        return template
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error in toggle_template_active for template_id={template_id}, is_active={is_active}: {str(e)}\n{traceback.format_exc()}")
        raise


# ============================================================================
# Delete Operations
# ============================================================================

def delete_template(db: Session, template_id: int) -> bool:
    """
    Delete prompt template.

    Args:
        db: Database session
        template_id: Template ID

    Returns:
        bool: True if deleted successfully

    Raises:
        ValueError: If template not found
    """
    try:
        success = prompt_template_repository.delete_prompt_template(db, template_id)
        if not success:
            logger.error(f"Template not found with id: {template_id}")
            raise ValueError(f"Template not found with id: {template_id}")

        return True
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error in delete_template for template_id={template_id}: {str(e)}\n{traceback.format_exc()}")
        raise
