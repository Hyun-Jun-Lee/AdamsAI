"""
SQLAlchemy ORM models for database tables.
Defines the database schema with relationships.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class Video(BaseModel):
    """Video table storing uploaded or downloaded video metadata."""

    __tablename__ = "videos"

    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)  # 'upload' or 'download'
    source_url = Column(String(1024), nullable=True)  # Original URL if downloaded
    file_size = Column(Integer, nullable=True)  # Size in bytes
    duration = Column(Float, nullable=True)  # Duration in seconds
    status = Column(String(50), default="uploaded", nullable=False)  # uploaded, processing, completed, failed

    # Relationships
    audios = relationship("Audio", back_populates="video", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Video(id={self.id}, filename='{self.filename}', status='{self.status}')>"


class Audio(BaseModel):
    """Audio table storing extracted audio files from videos."""

    __tablename__ = "audios"

    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False, unique=True)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    duration = Column(Float, nullable=True)  # Duration in seconds
    status = Column(String(50), default="extracted", nullable=False)  # extracted, processing, completed, failed

    # Relationships
    video = relationship("Video", back_populates="audios")
    transcripts = relationship("Transcript", back_populates="audio", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Audio(id={self.id}, video_id={self.video_id}, filename='{self.filename}')>"


class Transcript(BaseModel):
    """Transcript table storing speech-to-text results."""

    __tablename__ = "transcripts"

    audio_id = Column(Integer, ForeignKey("audios.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False)  # Transcribed text
    language = Column(String(10), default="ko", nullable=False)  # Language code (e.g., 'ko', 'en')
    model = Column(String(50), default="whisper-1", nullable=False)  # STT model used

    # Relationships
    audio = relationship("Audio", back_populates="transcripts")
    summaries = relationship("Summary", back_populates="transcript", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Transcript(id={self.id}, audio_id={self.audio_id}, language='{self.language}')>"


class PromptTemplate(BaseModel):
    """Prompt template table for managing reusable summarization prompts."""

    __tablename__ = "prompt_templates"

    name = Column(String(100), nullable=False, unique=True, index=True)  # Template identifier (e.g., 'default', 'detailed', 'brief')
    description = Column(String(500), nullable=True)  # Human-readable description
    content = Column(Text, nullable=False)  # Actual prompt text with placeholders
    is_active = Column(Boolean, default=True, nullable=False)  # Enable/disable template
    category = Column(String(50), default="general", nullable=False)  # Template category (e.g., 'real_estate', 'news', 'educational')

    # Relationships
    summaries = relationship("Summary", back_populates="prompt_template")

    def __repr__(self):
        return f"<PromptTemplate(id={self.id}, name='{self.name}', category='{self.category}')>"


class Summary(BaseModel):
    """Summary table storing AI-generated summaries of transcripts."""

    __tablename__ = "summaries"

    transcript_id = Column(Integer, ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id", ondelete="SET NULL"), nullable=True, index=True)
    summary_text = Column(Text, nullable=False)  # Generated summary
    ai_model_name = Column(String(100), nullable=False)  # LLM model used (e.g., 'anthropic/claude-3.5-sonnet')

    # Relationships
    transcript = relationship("Transcript", back_populates="summaries")
    prompt_template = relationship("PromptTemplate", back_populates="summaries")

    def __repr__(self):
        return f"<Summary(id={self.id}, transcript_id={self.transcript_id}, model='{self.ai_model_name}')>"
