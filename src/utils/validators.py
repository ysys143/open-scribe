"""
Validation utilities for Open-Scribe
"""

import re
import os
from pathlib import Path
from typing import Optional

def validate_youtube_url(url: str) -> bool:
    """
    Validate if the URL is a valid YouTube URL
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if valid YouTube URL, False otherwise
    """
    valid_patterns = [
        'youtube.com/watch',
        'youtu.be/',
        'youtube.com/playlist',
        'youtube.com/embed/',
        'youtube.com/live/',
        'm.youtube.com/'
    ]
    return any(pattern in url.lower() for pattern in valid_patterns)

def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from YouTube URL
    
    Args:
        url: YouTube URL
        
    Returns:
        str: Video ID if found, None otherwise
    """
    # Try different patterns
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        r'(?:live\/)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def is_playlist_url(url: str) -> bool:
    """
    Check if URL is a YouTube playlist
    
    Args:
        url: YouTube URL
        
    Returns:
        bool: True if playlist URL, False otherwise
    """
    return 'playlist' in url.lower() or 'list=' in url

def is_local_audio_file(path: str) -> bool:
    """
    Check if the input is a local audio file path
    
    Args:
        path: Input path to check
        
    Returns:
        bool: True if valid local audio file, False otherwise
    """
    if not path or not isinstance(path, str):
        return False
    
    # Normalize: strip quotes, expand env vars and user (~)
    normalized = path.strip().strip('"').strip("'")
    normalized = os.path.expandvars(os.path.expanduser(normalized))
    
    # Check if it's a file path (not a URL)
    if normalized.startswith(('http://', 'https://', 'ftp://')):
        return False
    
    # Determine by extension (and existence when possible)
    file_path = Path(normalized)
    audio_extensions = {'.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.wma', '.aiff', '.au'}
    suffix_ok = file_path.suffix.lower() in audio_extensions
    if file_path.exists() and file_path.is_file():
        return suffix_ok
    # If the path doesn't exist yet, still treat as local audio if extension matches
    return suffix_ok