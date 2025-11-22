"""
Video download utility functions supporting various formats including m3u8.
Refactored from download_m3u8.py into functional style.
"""

import os
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed


def normalize_url(url: str) -> str:
    """
    Remove whitespace, newlines, and escape characters from URL.

    Args:
        url: Raw URL string

    Returns:
        str: Normalized URL
    """
    normalized = ''.join(url.split())
    normalized = normalized.replace('\\', '')
    return normalized


def fetch_m3u8(url: str, headers: Dict[str, str]) -> str:
    """
    Fetch m3u8 playlist content.

    Args:
        url: M3U8 playlist URL
        headers: HTTP headers

    Returns:
        str: Playlist content
    """
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8')


def parse_master_playlist(content: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse master playlist and return best quality variant.

    Args:
        content: M3U8 master playlist content

    Returns:
        Tuple[Optional[str], Optional[str]]: (best_variant_path, resolution)
    """
    lines = content.strip().split('\n')
    best_bandwidth = 0
    best_variant = None
    best_resolution = None

    for i, line in enumerate(lines):
        if line.startswith('#EXT-X-STREAM-INF:'):
            params = {}
            for param in line.split(':')[1].split(','):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value

            bandwidth = int(params.get('BANDWIDTH', 0))
            resolution = params.get('RESOLUTION', 'unknown')

            if i + 1 < len(lines):
                variant_path = lines[i + 1].strip()
                if bandwidth > best_bandwidth:
                    best_bandwidth = bandwidth
                    best_variant = variant_path
                    best_resolution = resolution

    return best_variant, best_resolution


def parse_media_playlist(content: str) -> List[str]:
    """
    Parse media playlist and return list of segment filenames.

    Args:
        content: M3U8 media playlist content

    Returns:
        List[str]: List of segment paths
    """
    lines = content.strip().split('\n')
    segments = []

    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            segments.append(line)

    return segments


def download_segment(
    seg_url: str,
    headers: Dict[str, str],
    segment_num: int,
    total_segments: int
) -> Optional[bytes]:
    """
    Download a single TS segment.

    Args:
        seg_url: Segment URL
        headers: HTTP headers
        segment_num: Current segment number
        total_segments: Total number of segments

    Returns:
        Optional[bytes]: Segment data, None if failed
    """
    try:
        req = urllib.request.Request(seg_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = response.read()
            print(f"  [{segment_num}/{total_segments}] Downloaded {len(data)} bytes")
            return data
    except Exception as e:
        print(f"  ❌ Segment {segment_num} failed: {e}")
        return None


def download_m3u8_stream(
    url: str,
    output_path: Path,
    headers: Optional[Dict[str, str]] = None,
    threads: int = 8
) -> bool:
    """
    Download M3U8 HLS stream and convert to MP4.

    Args:
        url: M3U8 stream URL
        output_path: Output file path (will be .mp4)
        headers: Optional HTTP headers
        threads: Number of download threads

    Returns:
        bool: True if download successful

    Example:
        >>> download_m3u8_stream(
        ...     "https://example.com/video.m3u8",
        ...     Path("output.mp4"),
        ...     headers={"Referer": "https://example.com"}
        ... )
        True
    """
    # Normalize URL
    url = normalize_url(url)

    # Prepare default headers
    if headers is None:
        headers = {}

    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    headers = {**default_headers, **headers}

    try:
        # Step 1: Fetch master playlist
        print(f"📥 Fetching master playlist...")
        master_content = fetch_m3u8(url, headers)

        # Step 2: Parse and select best variant
        variant_path, resolution = parse_master_playlist(master_content)

        if not variant_path:
            print("❌ No variants found in master playlist")
            return False

        print(f"🎬 Selected quality: {resolution}")

        # Step 3: Build variant URL (preserve security parameters)
        parsed_url = urllib.parse.urlparse(url)
        base_url = url.rsplit('/', 1)[0]
        variant_url = f"{base_url}/{variant_path}"

        if parsed_url.query:
            variant_url = f"{variant_url}?{parsed_url.query}"

        # Step 4: Fetch media playlist
        print(f"📥 Fetching media playlist...")
        media_content = fetch_m3u8(variant_url, headers)

        # Step 5: Parse segments
        segments = parse_media_playlist(media_content)
        print(f"📦 Found {len(segments)} segments")

        # Step 6: Download segments
        print(f"⬇️  Downloading segments (using {threads} threads)...")

        segment_data = [None] * len(segments)
        variant_base_url = variant_url.rsplit('/', 1)[0]

        def download_task(idx: int, seg_path: str) -> Tuple[int, Optional[bytes]]:
            seg_url = f"{variant_base_url}/{seg_path}"
            if parsed_url.query:
                seg_url = f"{seg_url}?{parsed_url.query}"
            return idx, download_segment(seg_url, headers, idx + 1, len(segments))

        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(download_task, i, seg): i for i, seg in enumerate(segments)}

            for future in as_completed(futures):
                idx, data = future.result()
                segment_data[idx] = data

        # Step 7: Combine segments to temporary TS file
        print(f"🔨 Combining segments...")
        failed_count = sum(1 for d in segment_data if d is None)

        if failed_count > 0:
            print(f"⚠️  Warning: {failed_count} segments failed to download")

        # Create temporary TS file
        temp_ts = output_path.with_suffix('.ts')
        with open(temp_ts, 'wb') as f:
            for data in segment_data:
                if data:
                    f.write(data)

        file_size = temp_ts.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        print(f"✅ Download completed! ({file_size_mb:.2f} MB)")

        # Step 8: Convert to MP4 using ffmpeg
        print(f"\n🔄 Converting to MP4 format...")
        mp4_output = output_path.with_suffix('.mp4')

        try:
            result = subprocess.run(
                ['ffmpeg', '-i', str(temp_ts), '-c', 'copy', '-movflags', '+faststart', '-y', str(mp4_output)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                print(f"✅ Converted to: {mp4_output}")
                temp_ts.unlink()  # Remove temporary TS file
                print(f"📍 Saved to: {mp4_output.absolute()}")
                return True
            else:
                print(f"⚠️  Conversion failed. File saved as: {temp_ts}")
                return False

        except FileNotFoundError:
            print(f"⚠️  ffmpeg not found. File saved as raw TS: {temp_ts}")
            return False
        except subprocess.TimeoutExpired:
            print(f"⚠️  Conversion timeout. File saved as: {temp_ts}")
            return False

    except Exception as e:
        print(f"❌ Error downloading M3U8 stream: {e}")
        return False


def download_video_from_url(
    url: str,
    output_dir: Path,
    filename: Optional[str] = None,
    referer: Optional[str] = None,
    origin: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Download video from URL (supports m3u8 and direct downloads via yt-dlp).

    Args:
        url: Video URL (m3u8 or standard video URL)
        output_dir: Output directory path
        filename: Optional custom filename (without extension)
        referer: Optional Referer header
        origin: Optional Origin header

    Returns:
        Optional[Dict[str, Any]]: Download info including:
            - filepath: Path to downloaded file
            - title: Video title
            - duration: Duration in seconds
            - filesize: File size in bytes
        Returns None if download fails

    Example:
        >>> download_video_from_url(
        ...     "https://example.com/video.m3u8",
        ...     Path("storage/videos"),
        ...     filename="my_video"
        ... )
        {
            "filepath": Path("storage/videos/my_video.mp4"),
            "title": "my_video",
            "duration": 125.5,
            "filesize": 52428800
        }
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check if URL is m3u8
    if '.m3u8' in url.lower():
        # Use custom m3u8 downloader
        output_filename = filename if filename else "video"
        output_path = output_dir / f"{output_filename}.mp4"

        # Prepare headers
        headers = {}
        if referer:
            headers['Referer'] = referer
        if origin:
            headers['Origin'] = origin

        success = download_m3u8_stream(url, output_path, headers=headers)

        if success and output_path.exists():
            # Get video info
            from app.utils.video_utils import get_video_duration

            return {
                "filepath": output_path,
                "title": output_filename,
                "duration": get_video_duration(output_path),
                "filesize": output_path.stat().st_size
            }
        return None

    else:
        # Use yt-dlp for standard URLs
        return download_with_ytdlp(url, output_dir, filename)


def download_with_ytdlp(
    url: str,
    output_dir: Path,
    filename: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Download video using yt-dlp.

    Args:
        url: Video URL
        output_dir: Output directory
        filename: Optional custom filename

    Returns:
        Optional[Dict[str, Any]]: Download info or None if failed
    """
    try:
        import yt_dlp

        # Prepare output template
        if filename:
            output_template = str(output_dir / f"{filename}.%(ext)s")
        else:
            output_template = str(output_dir / "%(title)s.%(ext)s")

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'quiet': False,
            'no_warnings': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # Get the actual downloaded file path
            downloaded_file = ydl.prepare_filename(info)
            filepath = Path(downloaded_file)

            return {
                "filepath": filepath,
                "title": info.get('title', filename or 'video'),
                "duration": info.get('duration'),
                "filesize": filepath.stat().st_size if filepath.exists() else None
            }

    except Exception as e:
        print(f"❌ Error downloading with yt-dlp: {e}")
        return None


def get_video_info(url: str) -> Optional[Dict[str, Any]]:
    """
    Extract video information without downloading.

    Args:
        url: Video URL

    Returns:
        Optional[Dict[str, Any]]: Video metadata including:
            - title: str
            - duration: float (seconds)
            - thumbnail: str (URL)
            - description: str

    Example:
        >>> get_video_info("https://www.youtube.com/watch?v=...")
        {
            "title": "Video Title",
            "duration": 125.5,
            "thumbnail": "https://...",
            "description": "..."
        }
    """
    try:
        import yt_dlp

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            return {
                "title": info.get('title'),
                "duration": info.get('duration'),
                "thumbnail": info.get('thumbnail'),
                "description": info.get('description'),
                "uploader": info.get('uploader'),
                "upload_date": info.get('upload_date'),
            }

    except Exception as e:
        print(f"❌ Error extracting video info: {e}")
        return None
