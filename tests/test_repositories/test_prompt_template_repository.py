"""
Test suite for prompt_template_repository.
Tests CRUD operations and query functions for PromptTemplate model.
"""

import pytest
from app.repositories import prompt_template_repository
from app.models import PromptTemplate
from app.schemas import PromptTemplateCreate, PromptTemplateUpdate


# ============================================================================
# CREATE Tests
# ============================================================================

@pytest.mark.repository
def test_create_prompt_template(db_session):
    """Test creating a new prompt template record."""
    template_data = PromptTemplateCreate(
        name="test_template",
        description="Test prompt template",
        content="Summarize the following: {transcript}",
        is_active=True,
        category="general"
    )

    template = prompt_template_repository.create_prompt_template(db_session, template_data)

    assert template.id is not None
    assert template.name == "test_template"
    assert template.description == "Test prompt template"
    assert template.content == "Summarize the following: {transcript}"
    assert template.is_active is True
    assert template.category == "general"


# ============================================================================
# READ Tests
# ============================================================================

def test_get_prompt_template_by_id(db_session, prompt_template_factory):
    """Test retrieving prompt template by ID."""
    created_template = prompt_template_factory(name="find_me")

    found_template = prompt_template_repository.get_prompt_template_by_id(db_session, created_template.id)

    assert found_template is not None
    assert found_template.id == created_template.id
    assert found_template.name == "find_me"


def test_get_prompt_template_by_id_not_found(db_session):
    """Test retrieving non-existent prompt template returns None."""
    template = prompt_template_repository.get_prompt_template_by_id(db_session, 99999)
    assert template is None


def test_get_prompt_template_by_name(db_session, prompt_template_factory):
    """Test retrieving prompt template by unique name."""
    created_template = prompt_template_factory(name="unique_name")

    found_template = prompt_template_repository.get_prompt_template_by_name(db_session, "unique_name")

    assert found_template is not None
    assert found_template.name == "unique_name"


def test_get_all_prompt_templates(db_session, prompt_template_factory):
    """Test retrieving all prompt templates."""
    prompt_template_factory(name="template1")
    prompt_template_factory(name="template2")
    prompt_template_factory(name="template3")

    templates = prompt_template_repository.get_all_prompt_templates(db_session)

    assert len(templates) == 3


def test_get_active_prompt_templates(db_session, prompt_template_factory):
    """Test filtering active prompt templates."""
    prompt_template_factory(name="active1", is_active=True)
    prompt_template_factory(name="active2", is_active=True)
    prompt_template_factory(name="inactive1", is_active=False)

    active_templates = prompt_template_repository.get_active_prompt_templates(db_session)

    assert len(active_templates) == 2
    assert all(t.is_active for t in active_templates)


def test_get_templates_by_category(db_session, prompt_template_factory):
    """Test filtering templates by category."""
    prompt_template_factory(name="real_estate1", category="real_estate")
    prompt_template_factory(name="real_estate2", category="real_estate")
    prompt_template_factory(name="news1", category="news")

    real_estate_templates = prompt_template_repository.get_templates_by_category(db_session, "real_estate")
    news_templates = prompt_template_repository.get_templates_by_category(db_session, "news")

    assert len(real_estate_templates) == 2
    assert len(news_templates) == 1


# ============================================================================
# UPDATE Tests
# ============================================================================

def test_update_prompt_template(db_session, prompt_template_factory):
    """Test updating prompt template fields."""
    template = prompt_template_factory(
        name="original",
        content="Original content",
        category="general"
    )

    updates = PromptTemplateUpdate(
        name="updated",
        content="Updated content",
        category="real_estate"
    )

    updated = prompt_template_repository.update_prompt_template(db_session, template.id, updates)

    assert updated.name == "updated"
    assert updated.content == "Updated content"
    assert updated.category == "real_estate"


def test_activate_template(db_session, prompt_template_factory):
    """Test activating a template."""
    template = prompt_template_factory(is_active=False)

    activated = prompt_template_repository.activate_template(db_session, template.id)

    assert activated.is_active is True


def test_deactivate_template(db_session, prompt_template_factory):
    """Test deactivating a template."""
    template = prompt_template_factory(is_active=True)

    deactivated = prompt_template_repository.deactivate_template(db_session, template.id)

    assert deactivated.is_active is False


# ============================================================================
# DELETE Tests
# ============================================================================

def test_delete_prompt_template(db_session, prompt_template_factory):
    """Test deleting a prompt template."""
    template = prompt_template_factory(name="to_delete")
    template_id = template.id

    result = prompt_template_repository.delete_prompt_template(db_session, template_id)

    assert result is True

    # Verify deleted from database
    deleted = prompt_template_repository.get_prompt_template_by_id(db_session, template_id)
    assert deleted is None


def test_delete_template_sets_null_in_summaries(db_session, prompt_template_factory, video_factory, audio_factory, transcript_factory, summary_factory):
    """Test deleting template sets prompt_template_id to NULL in summaries."""
    template = prompt_template_factory()

    # Create a summary with this template
    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)
    summary = summary_factory(transcript_id=transcript.id, prompt_template_id=template.id)
    summary_id = summary.id

    # Delete template
    prompt_template_repository.delete_prompt_template(db_session, template.id)

    # Query summary again and verify template_id is NULL
    from app.models import Summary
    updated_summary = db_session.query(Summary).filter_by(id=summary_id).first()
    assert updated_summary.prompt_template_id is None


# ============================================================================
# COUNT Tests
# ============================================================================

def test_count_prompt_templates(db_session, prompt_template_factory):
    """Test counting total prompt templates."""
    prompt_template_factory()
    prompt_template_factory()
    prompt_template_factory()

    count = prompt_template_repository.count_prompt_templates(db_session)
    assert count == 3


# ============================================================================
# Relationship Tests
# ============================================================================

def test_template_summaries_relationship(db_session, prompt_template_factory, video_factory, audio_factory, transcript_factory, summary_factory):
    """Test PromptTemplate -> Summaries relationship."""
    template = prompt_template_factory()

    video = video_factory()
    audio = audio_factory(video_id=video.id)
    transcript = transcript_factory(audio_id=audio.id)

    summary1 = summary_factory(transcript_id=transcript.id, prompt_template_id=template.id)
    summary2 = summary_factory(transcript_id=transcript.id, prompt_template_id=template.id)

    db_session.refresh(template)

    assert len(template.summaries) == 2
    assert summary1 in template.summaries
    assert summary2 in template.summaries
