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
    
    # Check if it's a file path (not a URL)
    if path.startswith(('http://', 'https://', 'ftp://')):
        return False
    
    # Check if file exists
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return False
    
    # Check if it's an audio file by extension
    audio_extensions = {'.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.wma', '.aiff', '.au'}
    return file_path.suffix.lower() in audio_extensions