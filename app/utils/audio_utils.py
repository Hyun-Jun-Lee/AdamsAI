"""
Audio utility functions for extraction and processing.
Pure functional approach using moviepy and pydub.
"""

from pathlib import Path
from typing import Tuple, Optional
from moviepy.editor import VideoFileClip


def extract_audio_from_video(
    video_path: Path,
    output_path: Path,
    bitrate: str = "192k"
) -> Tuple[bool, Optional[float]]:
    """
    Extract audio from video file.

    Args:
        video_path: Path to source video file
        output_path: Path to save extracted audio
        bitrate: Audio bitrate (e.g., '192k', '256k')

    Returns:
        Tuple[bool, Optional[float]]: (success, duration_in_seconds)

    Example:
        >>> extract_audio_from_video(
        ...     Path("video.mp4"),
        ...     Path("audio.mp3"),
        ...     bitrate="192k"
        ... )
        (True, 125.5)
    """
    if not video_path.exists():
        print(f"Video file not found: {video_path}")
        return False, None

    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Extract audio using moviepy
        with VideoFileClip(str(video_path)) as video:
            if video.audio is None:
                print(f"No audio track found in video: {video_path}")
                return False, None

            duration = video.duration

            # Extract audio
            video.audio.write_audiofile(
                str(output_path),
                bitrate=bitrate,
                logger=None,  # Suppress verbose output
            )

        return True, duration

    except Exception as e:
        print(f"Error extracting audio: {e}")
        return False, None


def get_audio_duration(audio_path: Path) -> Optional[float]:
    """
    Get audio file duration in seconds.

    Args:
        audio_path: Path to audio file

    Returns:
        Optional[float]: Duration in seconds, None if extraction fails

    Example:
        >>> get_audio_duration(Path("audio.mp3"))
        125.5
    """
    if not audio_path.exists():
        return None

    try:
        from pydub import AudioSegment

        audio = AudioSegment.from_file(str(audio_path))
        return len(audio) / 1000.0  # Convert milliseconds to seconds

    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return None


def get_audio_info(audio_path: Path) -> Optional[dict]:
    """
    Extract comprehensive audio metadata.

    Args:
        audio_path: Path to audio file

    Returns:
        Optional[dict]: Audio metadata including:
            - duration: float (seconds)
            - channels: int
            - sample_rate: int (Hz)
            - file_size: int (bytes)

    Example:
        >>> get_audio_info(Path("audio.mp3"))
        {
            "duration": 125.5,
            "channels": 2,
            "sample_rate": 44100,
            "file_size": 3145728
        }
    """
    if not audio_path.exists():
        return None

    try:
        from pydub import AudioSegment

        audio = AudioSegment.from_file(str(audio_path))

        return {
            "duration": len(audio) / 1000.0,  # milliseconds to seconds
            "channels": audio.channels,
            "sample_rate": audio.frame_rate,
            "file_size": audio_path.stat().st_size,
        }

    except Exception as e:
        print(f"Error extracting audio info: {e}")
        return None


def convert_audio_format(
    input_path: Path,
    output_path: Path,
    output_format: str = "mp3",
    bitrate: str = "192k"
) -> bool:
    """
    Convert audio file to different format.

    Args:
        input_path: Path to source audio file
        output_path: Path to save converted audio
        output_format: Target format (mp3, wav, etc.)
        bitrate: Audio bitrate for compressed formats

    Returns:
        bool: True if conversion successful

    Example:
        >>> convert_audio_format(
        ...     Path("audio.wav"),
        ...     Path("audio.mp3"),
        ...     output_format="mp3",
        ...     bitrate="192k"
        ... )
        True
    """
    if not input_path.exists():
        print(f"Input audio file not found: {input_path}")
        return False

    try:
        from pydub import AudioSegment

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load and convert
        audio = AudioSegment.from_file(str(input_path))

        # Export with specified format and bitrate
        audio.export(
            str(output_path),
            format=output_format,
            bitrate=bitrate
        )

        return True

    except Exception as e:
        print(f"Error converting audio format: {e}")
        return False


def is_valid_audio_file(audio_path: Path) -> bool:
    """
    Validate if file is a readable audio file.

    Args:
        audio_path: Path to audio file

    Returns:
        bool: True if file can be read as audio

    Example:
        >>> is_valid_audio_file(Path("audio.mp3"))
        True
        >>> is_valid_audio_file(Path("corrupt.mp3"))
        False
    """
    if not audio_path.exists():
        return False

    try:
        from pydub import AudioSegment

        audio = AudioSegment.from_file(str(audio_path))
        # Try to access basic properties
        _ = audio.duration_seconds
        _ = audio.channels
        return True

    except Exception:
        return False


def normalize_audio_volume(
    input_path: Path,
    output_path: Path,
    target_dBFS: float = -20.0
) -> bool:
    """
    Normalize audio volume to target loudness.

    Args:
        input_path: Path to source audio file
        output_path: Path to save normalized audio
        target_dBFS: Target loudness in dBFS (default: -20.0)

    Returns:
        bool: True if normalization successful

    Example:
        >>> normalize_audio_volume(
        ...     Path("audio.mp3"),
        ...     Path("normalized.mp3"),
        ...     target_dBFS=-20.0
        ... )
        True
    """
    if not input_path.exists():
        print(f"Input audio file not found: {input_path}")
        return False

    try:
        from pydub import AudioSegment
        from pydub.effects import normalize

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load audio
        audio = AudioSegment.from_file(str(input_path))

        # Calculate gain change needed
        change_in_dBFS = target_dBFS - audio.dBFS

        # Apply gain
        normalized_audio = audio.apply_gain(change_in_dBFS)

        # Export
        normalized_audio.export(str(output_path), format=output_path.suffix[1:])

        return True

    except Exception as e:
        print(f"Error normalizing audio: {e}")
        return False
