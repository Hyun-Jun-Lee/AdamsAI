"""
Summary repository - Data access layer for Summary model.
Pure functional approach for database operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Summary
from app.schemas import SummaryCreate, SummaryUpdate


# ============================================================================
# CREATE Operations
# ============================================================================

def create_summary(db: Session, summary_data: SummaryCreate) -> Summary:
    """
    Create a new summary record.

    Args:
        db: Database session
        summary_data: Summary creation data

    Returns:
        Summary: Created summary instance
    """
    summary = Summary(**summary_data.model_dump())
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


# ============================================================================
# READ Operations
# ============================================================================

def get_summary_by_id(db: Session, summary_id: int) -> Optional[Summary]:
    """
    Retrieve summary by ID.

    Args:
        db: Database session
        summary_id: Summary ID

    Returns:
        Optional[Summary]: Summary instance or None if not found
    """
    return db.query(Summary).filter(Summary.id == summary_id).first()


def get_summaries_by_transcript_id(db: Session, transcript_id: int) -> List[Summary]:
    """
    Retrieve all summaries for a specific transcript.

    Args:
        db: Database session
        transcript_id: Transcript ID

    Returns:
        List[Summary]: List of summaries for the transcript
    """
    return db.query(Summary).filter(
        Summary.transcript_id == transcript_id
    ).order_by(Summary.created_at.desc()).all()


def get_summaries_by_ai_model(db: Session, ai_model_name: str) -> List[Summary]:
    """
    Retrieve summaries filtered by AI model name using partial match.

    Args:
        db: Database session
        ai_model_name: AI model name or partial name (e.g., 'claude', 'gpt-4')

    Returns:
        List[Summary]: List of summaries matching the model name pattern
    """
    search_pattern = f"%{ai_model_name}%"
    return db.query(Summary).filter(
        Summary.ai_model_name.ilike(search_pattern)
    ).order_by(Summary.created_at.desc()).all()


def get_summaries_by_template_id(db: Session, template_id: int) -> List[Summary]:
    """
    Retrieve summaries filtered by prompt template ID.

    Args:
        db: Database session
        template_id: Prompt template ID

    Returns:
        List[Summary]: List of summaries using the specified template
    """
    return db.query(Summary).filter(
        Summary.prompt_template_id == template_id
    ).order_by(Summary.created_at.desc()).all()


def get_all_summaries(db: Session) -> List[Summary]:
    """
    Retrieve all summaries.

    Args:
        db: Database session

    Returns:
        List[Summary]: List of all summaries
    """
    return db.query(Summary).order_by(Summary.created_at.desc()).all()


def get_summaries_paginated(db: Session, skip: int = 0, limit: int = 10) -> List[Summary]:
    """
    Retrieve summaries with pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List[Summary]: Paginated list of summaries
    """
    return db.query(Summary).order_by(
        Summary.created_at.desc()
    ).offset(skip).limit(limit).all()


# ============================================================================
# UPDATE Operations
# ============================================================================

def update_summary(
    db: Session,
    summary_id: int,
    updates: SummaryUpdate
) -> Optional[Summary]:
    """
    Update summary fields.

    Args:
        db: Database session
        summary_id: Summary ID
        updates: Fields to update

    Returns:
        Optional[Summary]: Updated summary or None if not found
    """
    summary = get_summary_by_id(db, summary_id)
    if not summary:
        return None

    # Update only provided fields
    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(summary, key, value)

    db.commit()
    db.refresh(summary)
    return summary


# ============================================================================
# DELETE Operations
# ============================================================================

def delete_summary(db: Session, summary_id: int) -> bool:
    """
    Delete summary by ID.

    Args:
        db: Database session
        summary_id: Summary ID

    Returns:
        bool: True if deleted, False if not found
    """
    summary = get_summary_by_id(db, summary_id)
    if not summary:
        return False

    db.delete(summary)
    db.commit()
    return True


# ============================================================================
# COUNT Operations
# ============================================================================

def count_summaries(db: Session) -> int:
    """
    Count total number of summaries.

    Args:
        db: Database session

    Returns:
        int: Total summary count
    """
    return db.query(Summary).count()


def count_summaries_by_model(db: Session, ai_model_name: str) -> int:
    """
    Count summaries by AI model name using partial match.

    Args:
        db: Database session
        ai_model_name: AI model name or partial name (e.g., 'claude', 'gpt-4')

    Returns:
        int: Count of summaries matching the model name pattern
    """
    search_pattern = f"%{ai_model_name}%"
    return db.query(Summary).filter(
        Summary.ai_model_name.ilike(search_pattern)
    ).count()
