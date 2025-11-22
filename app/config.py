"""
Configuration settings for AdamsAI video summarizer service.
Uses pydantic-settings for environment variable management.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""

    # API Keys
    openai_api_key: str
    openrouter_api_key: str

    # Database
    database_url: str = "sqlite:///./storage/app.db"

    # Storage paths
    storage_root: Path = Path("./storage")
    videos_dir: Path = Path("./storage/videos")
    audios_dir: Path = Path("./storage/audios")
    transcripts_dir: Path = Path("./storage/transcripts")
    summaries_dir: Path = Path("./storage/summaries")

    # File size limits (MB)
    max_video_size_mb: int = 500
    max_upload_size_mb: int = 500

    # Audio extraction settings
    default_audio_bitrate: str = "192k"

    # AI model settings
    default_llm_model: str = "anthropic/claude-3.5-sonnet"
    default_whisper_model: str = "whisper-1"
    default_language: str = "ko"

    # Download settings
    default_user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    download_threads: int = 8

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings instance (singleton pattern).

    Returns:
        Settings: Application configuration settings
    """
    global _settings
    if _settings is None:
        _settings = Settings()

        # Ensure storage directories exist
        for directory in [
            _settings.storage_root,
            _settings.videos_dir,
            _settings.audios_dir,
            _settings.transcripts_dir,
            _settings.summaries_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    return _settings
