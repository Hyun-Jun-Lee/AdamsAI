"""
File utility functions for handling uploads and file operations.
Pure functional approach for file management.
"""

import os
import uuid
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate UUID-based unique filename while preserving extension.

    Args:
        original_filename: Original file name with extension

    Returns:
        str: Unique filename in format "uuid-original_name.ext"

    Example:
        >>> generate_unique_filename("video.mp4")
        "a1b2c3d4-video.mp4"
    """
    file_stem = Path(original_filename).stem
    file_ext = Path(original_filename).suffix
    unique_id = uuid.uuid4().hex[:8]
    return f"{unique_id}-{file_stem}{file_ext}"


def get_file_size_mb(filepath: Path) -> float:
    """
    Get file size in megabytes.

    Args:
        filepath: Path to the file

    Returns:
        float: File size in MB

    Example:
        >>> get_file_size_mb(Path("video.mp4"))
        52.4
    """
    if not filepath.exists():
        return 0.0
    size_bytes = filepath.stat().st_size
    return size_bytes / (1024 * 1024)


def get_file_size_bytes(filepath: Path) -> int:
    """
    Get file size in bytes.

    Args:
        filepath: Path to the file

    Returns:
        int: File size in bytes
    """
    if not filepath.exists():
        return 0
    return filepath.stat().st_size


async def save_upload_file(file: UploadFile, destination: Path) -> Tuple[str, int]:
    """
    Save uploaded file to destination path.

    Args:
        file: FastAPI UploadFile object
        destination: Destination path including filename

    Returns:
        Tuple[str, int]: (filename, file_size_bytes)

    Example:
        >>> await save_upload_file(upload_file, Path("storage/videos/video.mp4"))
        ("video.mp4", 52428800)
    """
    # Ensure parent directory exists
    ensure_directory_exists(destination.parent)

    # Write file in chunks for memory efficiency
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks

    with open(destination, "wb") as f:
        while chunk := await file.read(chunk_size):
            f.write(chunk)
            file_size += len(chunk)

    return destination.name, file_size


def ensure_directory_exists(directory: Path) -> None:
    """
    Ensure directory exists, create if it doesn't.

    Args:
        directory: Path to directory

    Example:
        >>> ensure_directory_exists(Path("storage/videos"))
    """
    directory.mkdir(parents=True, exist_ok=True)


def delete_file_safe(filepath: Path) -> bool:
    """
    Safely delete file, return success status.

    Args:
        filepath: Path to file to delete

    Returns:
        bool: True if deleted successfully, False otherwise

    Example:
        >>> delete_file_safe(Path("temp.mp4"))
        True
    """
    try:
        if filepath.exists() and filepath.is_file():
            filepath.unlink()
            return True
        return False
    except Exception as e:
        print(f"Error deleting file {filepath}: {e}")
        return False


def get_file_extension(filename: str) -> str:
    """
    Extract file extension from filename.

    Args:
        filename: File name

    Returns:
        str: File extension (lowercase, without dot)

    Example:
        >>> get_file_extension("video.MP4")
        "mp4"
    """
    return Path(filename).suffix.lower().lstrip(".")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing unsafe characters.

    Args:
        filename: Original filename

    Returns:
        str: Sanitized filename

    Example:
        >>> sanitize_filename("my video/file?.mp4")
        "my_video_file.mp4"
    """
    # Replace unsafe characters with underscore
    unsafe_chars = '<>:"/\\|?*'
    sanitized = filename
    for char in unsafe_chars:
        sanitized = sanitized.replace(char, "_")

    # Remove multiple consecutive underscores
    while "__" in sanitized:
        sanitized = sanitized.replace("__", "_")

    return sanitized.strip("_")


def create_temp_filepath(directory: Path, prefix: str = "temp", suffix: str = "") -> Path:
    """
    Create unique temporary filepath.

    Args:
        directory: Directory for temp file
        prefix: Filename prefix
        suffix: File extension (with or without dot)

    Returns:
        Path: Unique temporary filepath

    Example:
        >>> create_temp_filepath(Path("storage/temp"), "download", ".mp4")
        Path("storage/temp/temp_a1b2c3d4.mp4")
    """
    ensure_directory_exists(directory)
    unique_id = uuid.uuid4().hex[:8]

    # Ensure suffix has dot
    if suffix and not suffix.startswith("."):
        suffix = f".{suffix}"

    return directory / f"{prefix}_{unique_id}{suffix}"
