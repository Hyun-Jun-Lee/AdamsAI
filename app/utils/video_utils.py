"""
Video utility functions for metadata extraction and validation.
Pure functional approach using moviepy.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from moviepy.editor import VideoFileClip


def get_video_duration(video_path: Path) -> Optional[float]:
    """
    Extract video duration in seconds.

    Args:
        video_path: Path to video file

    Returns:
        Optional[float]: Duration in seconds, None if extraction fails

    Example:
        >>> get_video_duration(Path("video.mp4"))
        125.5
    """
    if not video_path.exists():
        return None

    try:
        with VideoFileClip(str(video_path)) as video:
            return video.duration
    except Exception as e:
        print(f"Error extracting video duration: {e}")
        return None


def has_audio_track(video_path: Path) -> bool:
    """
    Check if video file has an audio track.

    Args:
        video_path: Path to video file

    Returns:
        bool: True if video has audio track

    Example:
        >>> has_audio_track(Path("video.mp4"))
        True
    """
    if not video_path.exists():
        return False

    try:
        with VideoFileClip(str(video_path)) as video:
            return video.audio is not None
    except Exception as e:
        print(f"Error checking audio track: {e}")
        return False


def get_video_info(video_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract comprehensive video metadata.

    Args:
        video_path: Path to video file

    Returns:
        Optional[Dict[str, Any]]: Video metadata including:
            - duration: float (seconds)
            - fps: float (frames per second)
            - size: tuple (width, height)
            - has_audio: bool
            - file_size: int (bytes)

    Example:
        >>> get_video_info(Path("video.mp4"))
        {
            "duration": 125.5,
            "fps": 30.0,
            "size": (1920, 1080),
            "has_audio": True,
            "file_size": 52428800
        }
    """
    if not video_path.exists():
        return None

    try:
        with VideoFileClip(str(video_path)) as video:
            return {
                "duration": video.duration,
                "fps": video.fps,
                "size": video.size,
                "has_audio": video.audio is not None,
                "file_size": video_path.stat().st_size,
            }
    except Exception as e:
        print(f"Error extracting video info: {e}")
        return None


def get_video_resolution(video_path: Path) -> Optional[tuple]:
    """
    Get video resolution (width, height).

    Args:
        video_path: Path to video file

    Returns:
        Optional[tuple]: (width, height) or None if extraction fails

    Example:
        >>> get_video_resolution(Path("video.mp4"))
        (1920, 1080)
    """
    if not video_path.exists():
        return None

    try:
        with VideoFileClip(str(video_path)) as video:
            return video.size
    except Exception as e:
        print(f"Error extracting video resolution: {e}")
        return None


def get_video_fps(video_path: Path) -> Optional[float]:
    """
    Get video frames per second (FPS).

    Args:
        video_path: Path to video file

    Returns:
        Optional[float]: FPS value, None if extraction fails

    Example:
        >>> get_video_fps(Path("video.mp4"))
        30.0
    """
    if not video_path.exists():
        return None

    try:
        with VideoFileClip(str(video_path)) as video:
            return video.fps
    except Exception as e:
        print(f"Error extracting video FPS: {e}")
        return None


def is_valid_video_file(video_path: Path) -> bool:
    """
    Validate if file is a readable video file.

    Args:
        video_path: Path to video file

    Returns:
        bool: True if file can be read as video

    Example:
        >>> is_valid_video_file(Path("video.mp4"))
        True
        >>> is_valid_video_file(Path("corrupt.mp4"))
        False
    """
    if not video_path.exists():
        return False

    try:
        with VideoFileClip(str(video_path)) as video:
            # Try to access basic properties
            _ = video.duration
            _ = video.size
            return True
    except Exception:
        return False
