"""
PromptTemplate repository - Data access layer for PromptTemplate model.
Pure functional approach for database operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import PromptTemplate
from app.schemas import PromptTemplateCreate, PromptTemplateUpdate


# ============================================================================
# CREATE Operations
# ============================================================================

def create_prompt_template(db: Session, template_data: PromptTemplateCreate) -> PromptTemplate:
    """
    Create a new prompt template record.

    Args:
        db: Database session
        template_data: Template creation data

    Returns:
        PromptTemplate: Created template instance
    """
    template = PromptTemplate(**template_data.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


# ============================================================================
# READ Operations
# ============================================================================

def get_prompt_template_by_id(db: Session, template_id: int) -> Optional[PromptTemplate]:
    """
    Retrieve prompt template by ID.

    Args:
        db: Database session
        template_id: Template ID

    Returns:
        Optional[PromptTemplate]: Template instance or None if not found
    """
    return db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()


def get_prompt_template_by_name(db: Session, name: str) -> Optional[PromptTemplate]:
    """
    Retrieve prompt template by unique name.

    Args:
        db: Database session
        name: Template name

    Returns:
        Optional[PromptTemplate]: Template instance or None if not found
    """
    return db.query(PromptTemplate).filter(PromptTemplate.name == name).first()


def get_all_prompt_templates(db: Session) -> List[PromptTemplate]:
    """
    Retrieve all prompt templates.

    Args:
        db: Database session

    Returns:
        List[PromptTemplate]: List of all templates
    """
    return db.query(PromptTemplate).order_by(PromptTemplate.created_at.desc()).all()


def get_active_prompt_templates(db: Session) -> List[PromptTemplate]:
    """
    Retrieve only active prompt templates.

    Args:
        db: Database session

    Returns:
        List[PromptTemplate]: List of active templates
    """
    return db.query(PromptTemplate).filter(
        PromptTemplate.is_active == True
    ).order_by(PromptTemplate.created_at.desc()).all()


def get_templates_by_category(db: Session, category: str) -> List[PromptTemplate]:
    """
    Retrieve templates filtered by category.

    Args:
        db: Database session
        category: Category name (e.g., 'real_estate', 'news')

    Returns:
        List[PromptTemplate]: List of templates in category
    """
    return db.query(PromptTemplate).filter(
        PromptTemplate.category == category
    ).order_by(PromptTemplate.created_at.desc()).all()


# ============================================================================
# UPDATE Operations
# ============================================================================

def update_prompt_template(
    db: Session,
    template_id: int,
    updates: PromptTemplateUpdate
) -> Optional[PromptTemplate]:
    """
    Update prompt template fields.

    Args:
        db: Database session
        template_id: Template ID
        updates: Fields to update

    Returns:
        Optional[PromptTemplate]: Updated template or None if not found
    """
    template = get_prompt_template_by_id(db, template_id)
    if not template:
        return None

    # Update only provided fields
    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(template, key, value)

    db.commit()
    db.refresh(template)
    return template


def activate_template(db: Session, template_id: int) -> Optional[PromptTemplate]:
    """
    Activate a prompt template.

    Args:
        db: Database session
        template_id: Template ID

    Returns:
        Optional[PromptTemplate]: Updated template or None if not found
    """
    template = get_prompt_template_by_id(db, template_id)
    if not template:
        return None

    template.is_active = True
    db.commit()
    db.refresh(template)
    return template


def deactivate_template(db: Session, template_id: int) -> Optional[PromptTemplate]:
    """
    Deactivate a prompt template.

    Args:
        db: Database session
        template_id: Template ID

    Returns:
        Optional[PromptTemplate]: Updated template or None if not found
    """
    template = get_prompt_template_by_id(db, template_id)
    if not template:
        return None

    template.is_active = False
    db.commit()
    db.refresh(template)
    return template


# ============================================================================
# DELETE Operations
# ============================================================================

def delete_prompt_template(db: Session, template_id: int) -> bool:
    """
    Delete prompt template by ID.
    SET NULL in related summaries (ondelete='SET NULL').

    Args:
        db: Database session
        template_id: Template ID

    Returns:
        bool: True if deleted, False if not found
    """
    template = get_prompt_template_by_id(db, template_id)
    if not template:
        return False

    db.delete(template)
    db.commit()
    return True


# ============================================================================
# COUNT Operations
# ============================================================================

def count_prompt_templates(db: Session) -> int:
    """
    Count total number of prompt templates.

    Args:
        db: Database session

    Returns:
        int: Total template count
    """
    return db.query(PromptTemplate).count()
