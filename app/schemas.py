"""
Pydantic schemas for request/response validation.
Provides type-safe data validation and serialization.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============================================================================
# Video Schemas
# ============================================================================

class VideoBase(BaseModel):
    """Base schema for video with common fields."""
    filename: str
    source_type: str
    source_url: Optional[str] = None


class VideoCreate(VideoBase):
    """Schema for creating a new video record."""
    filepath: str
    file_size: Optional[int] = None
    duration: Optional[float] = None
    status: str = "uploaded"


class VideoResponse(VideoBase):
    """Schema for video response with all fields."""
    id: int
    filepath: str
    file_size: Optional[int] = None
    duration: Optional[float] = None
    created_at: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)


class VideoDownloadRequest(BaseModel):
    """Schema for video download request."""
    url: str = Field(..., min_length=1, description="Video URL to download")
    title: Optional[str] = Field(None, description="Optional video title")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


# ============================================================================
# Audio Schemas
# ============================================================================

class AudioBase(BaseModel):
    """Base schema for audio with common fields."""
    video_id: int
    filename: str


class AudioCreate(AudioBase):
    """Schema for creating a new audio record."""
    filepath: str
    file_size: Optional[int] = None
    duration: Optional[float] = None
    status: str = "extracted"


class AudioResponse(AudioBase):
    """Schema for audio response with all fields."""
    id: int
    filepath: str
    file_size: Optional[int] = None
    duration: Optional[float] = None
    created_at: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)


class AudioExtractRequest(BaseModel):
    """Schema for audio extraction request."""
    video_id: int = Field(..., gt=0, description="Video ID to extract audio from")


# ============================================================================
# Transcript Schemas
# ============================================================================

class TranscriptBase(BaseModel):
    """Base schema for transcript with common fields."""
    audio_id: int
    text: str


class TranscriptCreate(TranscriptBase):
    """Schema for creating a new transcript record."""
    language: str = "ko"
    model: str = "whisper-1"


class TranscriptResponse(TranscriptBase):
    """Schema for transcript response with all fields."""
    id: int
    language: str
    model: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TranscriptCreateRequest(BaseModel):
    """Schema for transcript creation request."""
    audio_id: int = Field(..., gt=0, description="Audio ID to transcribe")
    language: str = Field(default="ko", description="Language code (e.g., 'ko', 'en')")

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language code."""
        v = v.lower().strip()
        if len(v) < 2 or len(v) > 10:
            raise ValueError("Language code must be between 2 and 10 characters")
        return v


# ============================================================================
# PromptTemplate Schemas
# ============================================================================

class PromptTemplateBase(BaseModel):
    """Base schema for prompt template with common fields."""
    name: str
    content: str


class PromptTemplateCreate(PromptTemplateBase):
    """Schema for creating a new prompt template."""
    description: Optional[str] = None
    is_active: bool = True
    category: str = "general"


class PromptTemplateUpdate(BaseModel):
    """Schema for updating a prompt template."""
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None
    category: Optional[str] = None


class PromptTemplateResponse(PromptTemplateBase):
    """Schema for prompt template response with all fields."""
    id: int
    description: Optional[str]
    is_active: bool
    category: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Summary Schemas
# ============================================================================

class SummaryBase(BaseModel):
    """Base schema for summary with common fields."""
    transcript_id: int
    summary_text: str


class SummaryCreate(SummaryBase):
    """Schema for creating a new summary record."""
    ai_model_name: str
    prompt_template_id: Optional[int] = None


class SummaryUpdate(BaseModel):
    """Schema for updating a summary."""
    summary_text: Optional[str] = None
    ai_model_name: Optional[str] = None
    prompt_template_id: Optional[int] = None


class SummaryResponse(SummaryBase):
    """Schema for summary response with all fields."""
    id: int
    ai_model_name: str
    prompt_template_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class SummaryCreateRequest(BaseModel):
    """Schema for summary creation request."""
    transcript_id: int = Field(..., gt=0, description="Transcript ID to summarize")
    ai_model_name: Optional[str] = Field(
        default=None,
        description="LLM model to use (e.g., 'anthropic/claude-3.5-sonnet')"
    )
    prompt_template_id: Optional[int] = Field(
        default=None,
        description="Prompt template ID to use (if None, uses default template)"
    )
    prompt_template_name: Optional[str] = Field(
        default=None,
        description="Prompt template name to use (alternative to ID, e.g., 'default', 'detailed')"
    )

    model_config = ConfigDict(protected_namespaces=())


# ============================================================================
# Pagination and List Response Schemas
# ============================================================================

class PaginatedResponse(BaseModel):
    """Generic paginated response schema."""
    total: int
    items: list

    model_config = ConfigDict(from_attributes=True)
