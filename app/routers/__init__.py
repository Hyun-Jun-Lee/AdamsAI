"""
Router layer - FastAPI route handlers.
Import routers here for easy access.
"""

from app.routers import videos, audios, transcripts, summaries

__all__ = ["videos", "audios", "transcripts", "summaries"]
