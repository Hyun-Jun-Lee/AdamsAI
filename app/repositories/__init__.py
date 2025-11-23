"""
Repository layer - Data access functions for all models.
Import repositories here for easy access.
"""

from app.repositories import (
    video_repository,
    audio_repository,
    transcript_repository,
    prompt_template_repository,
    summary_repository
)

__all__ = [
    "video_repository",
    "audio_repository",
    "transcript_repository",
    "prompt_template_repository",
    "summary_repository"
]
