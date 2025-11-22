"""
SQLAlchemy ORM models for database tables.
Defines the database schema with relationships.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Video(Base):
    """Video table storing uploaded or downloaded video metadata."""

    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)  # 'upload' or 'download'
    source_url = Column(String(1024), nullable=True)  # Original URL if downloaded
    file_size = Column(Integer, nullable=True)  # Size in bytes
    duration = Column(Float, nullable=True)  # Duration in seconds
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(50), default="uploaded", nullable=False)  # uploaded, processing, completed, failed

    # Relationships
    audios = relationship("Audio", back_populates="video", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Video(id={self.id}, filename='{self.filename}', status='{self.status}')>"


class Audio(Base):
    """Audio table storing extracted audio files from videos."""

    __tablename__ = "audios"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False, unique=True)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    duration = Column(Float, nullable=True)  # Duration in seconds
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(50), default="extracted", nullable=False)  # extracted, processing, completed, failed

    # Relationships
    video = relationship("Video", back_populates="audios")
    transcripts = relationship("Transcript", back_populates="audio", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Audio(id={self.id}, video_id={self.video_id}, filename='{self.filename}')>"


class Transcript(Base):
    """Transcript table storing speech-to-text results."""

    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    audio_id = Column(Integer, ForeignKey("audios.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False)  # Transcribed text
    language = Column(String(10), default="ko", nullable=False)  # Language code (e.g., 'ko', 'en')
    model = Column(String(50), default="whisper-1", nullable=False)  # STT model used
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    audio = relationship("Audio", back_populates="transcripts")
    summaries = relationship("Summary", back_populates="transcript", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Transcript(id={self.id}, audio_id={self.audio_id}, language='{self.language}')>"


class Summary(Base):
    """Summary table storing AI-generated summaries of transcripts."""

    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False, index=True)
    summary_text = Column(Text, nullable=False)  # Generated summary
    model_name = Column(String(100), nullable=False)  # LLM model used (e.g., 'anthropic/claude-3.5-sonnet')
    prompt_template = Column(String(50), nullable=True)  # Template name used (e.g., 'default', 'detailed')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    transcript = relationship("Transcript", back_populates="summaries")

    def __repr__(self):
        return f"<Summary(id={self.id}, transcript_id={self.transcript_id}, model='{self.model_name}')>"
