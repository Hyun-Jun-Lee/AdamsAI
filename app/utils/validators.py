"""
Validation utility functions for file types, sizes, and URLs.
Pure functional approach for input validation.
"""

from typing import List
from urllib.parse import urlparse


# Supported file extensions
VIDEO_EXTENSIONS = ["mp4", "avi", "mov", "mkv", "flv", "wmv", "webm", "m4v", "mpg", "mpeg"]
AUDIO_EXTENSIONS = ["mp3", "wav", "aac", "flac", "m4a", "ogg", "wma"]
M3U8_EXTENSIONS = ["m3u8"]


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Validate if file has an allowed extension.

    Args:
        filename: File name to validate
        allowed_extensions: List of allowed extensions (without dots)

    Returns:
        bool: True if extension is allowed

    Example:
        >>> validate_file_extension("video.mp4", ["mp4", "avi"])
        True
        >>> validate_file_extension("video.xyz", ["mp4", "avi"])
        False
    """
    if not filename:
        return False

    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return extension in [ext.lower() for ext in allowed_extensions]


def validate_video_file(filename: str) -> bool:
    """
    Validate if file is a supported video format.

    Args:
        filename: Video file name

    Returns:
        bool: True if valid video file

    Example:
        >>> validate_video_file("movie.mp4")
        True
        >>> validate_video_file("audio.mp3")
        False
    """
    return validate_file_extension(filename, VIDEO_EXTENSIONS)


def validate_audio_file(filename: str) -> bool:
    """
    Validate if file is a supported audio format.

    Args:
        filename: Audio file name

    Returns:
        bool: True if valid audio file

    Example:
        >>> validate_audio_file("song.mp3")
        True
        >>> validate_audio_file("video.mp4")
        False
    """
    return validate_file_extension(filename, AUDIO_EXTENSIONS)


def validate_file_size(file_size_bytes: int, max_size_mb: int) -> bool:
    """
    Validate if file size is within allowed limit.

    Args:
        file_size_bytes: File size in bytes
        max_size_mb: Maximum allowed size in megabytes

    Returns:
        bool: True if file size is acceptable

    Example:
        >>> validate_file_size(10 * 1024 * 1024, 100)  # 10MB file, 100MB limit
        True
        >>> validate_file_size(200 * 1024 * 1024, 100)  # 200MB file, 100MB limit
        False
    """
    if file_size_bytes <= 0:
        return False

    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size_bytes <= max_size_bytes


def is_m3u8_url(url: str) -> bool:
    """
    Check if URL points to an m3u8 playlist.

    Args:
        url: URL to check

    Returns:
        bool: True if URL is m3u8 format

    Example:
        >>> is_m3u8_url("https://example.com/video.m3u8")
        True
        >>> is_m3u8_url("https://example.com/video.mp4")
        False
    """
    if not url:
        return False

    # Check file extension
    url_lower = url.lower()
    if ".m3u8" in url_lower:
        return True

    # Check URL path
    parsed = urlparse(url)
    path = parsed.path.lower()
    return path.endswith(".m3u8")


def is_valid_url(url: str) -> bool:
    """
    Validate if string is a valid URL.

    Args:
        url: URL string to validate

    Returns:
        bool: True if valid URL

    Example:
        >>> is_valid_url("https://example.com/video.mp4")
        True
        >>> is_valid_url("not a url")
        False
    """
    if not url or not isinstance(url, str):
        return False

    try:
        result = urlparse(url)
        return all([result.scheme in ["http", "https"], result.netloc])
    except Exception:
        return False


def is_youtube_url(url: str) -> bool:
    """
    Check if URL is a YouTube video URL.

    Args:
        url: URL to check

    Returns:
        bool: True if YouTube URL

    Example:
        >>> is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        True
        >>> is_youtube_url("https://youtu.be/dQw4w9WgXcQ")
        True
    """
    if not is_valid_url(url):
        return False

    parsed = urlparse(url)
    return parsed.netloc in [
        "www.youtube.com",
        "youtube.com",
        "youtu.be",
        "m.youtube.com",
    ]


def validate_language_code(language: str) -> bool:
    """
    Validate if language code is in supported format.

    Args:
        language: Language code (e.g., 'ko', 'en', 'ja')

    Returns:
        bool: True if valid language code format

    Example:
        >>> validate_language_code("ko")
        True
        >>> validate_language_code("en-US")
        True
        >>> validate_language_code("")
        False
    """
    if not language or not isinstance(language, str):
        return False

    language = language.strip()
    # ISO 639-1 (2 chars) or with region (e.g., en-US)
    return 2 <= len(language) <= 10 and language.replace("-", "").replace("_", "").isalnum()


def get_supported_video_extensions() -> List[str]:
    """
    Get list of supported video file extensions.

    Returns:
        List[str]: Supported video extensions
    """
    return VIDEO_EXTENSIONS.copy()


def get_supported_audio_extensions() -> List[str]:
    """
    Get list of supported audio file extensions.

    Returns:
        List[str]: Supported audio extensions
    """
    return AUDIO_EXTENSIONS.copy()
