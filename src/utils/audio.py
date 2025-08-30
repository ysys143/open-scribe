"""
Audio processing utilities for Open-Scribe
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple

def compress_audio_if_needed(audio_path: str, max_size_mb: float = 25) -> Tuple[str, bool]:
    """
    Compress audio file if it exceeds max size
    
    Args:
        audio_path: Path to audio file
        max_size_mb: Maximum file size in MB (default 25MB for OpenAI)
    
    Returns:
        tuple: (path to processed file, True if compressed)
    """
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    
    if file_size_mb <= max_size_mb:
        return audio_path, False
    
    print(f"[Audio] File size ({file_size_mb:.1f}MB) exceeds limit ({max_size_mb}MB). Compressing...")
    
    # Create compressed version with lower bitrate
    compressed_path = audio_path.replace('.mp3', '_compressed.mp3')
    
    # Use progressively lower bitrates
    bitrates = ["64k", "48k", "32k", "24k"]
    
    for bitrate in bitrates:
        compress_cmd = [
            "ffmpeg", "-i", audio_path,
            "-b:a", bitrate,      # Lower bitrate
            "-ar", "16000",       # Lower sample rate
            "-ac", "1",           # Mono
            compressed_path,
            "-y",                 # Overwrite
            "-loglevel", "error"
        ]
        
        result = subprocess.run(compress_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[Audio] Error compressing at {bitrate}: {result.stderr}")
            continue
            
        compressed_size_mb = os.path.getsize(compressed_path) / (1024 * 1024)
        print(f"[Audio] Compressed to {compressed_size_mb:.1f}MB using {bitrate} bitrate")
        
        if compressed_size_mb <= max_size_mb:
            return compressed_path, True
    
    # If all attempts failed, return original
    print(f"[Audio] Warning: Could not compress below {max_size_mb}MB limit")
    return audio_path, False

def convert_to_wav(input_path: str, output_path: Optional[str] = None,
                   sample_rate: int = 16000, channels: int = 1) -> Optional[str]:
    """
    Convert audio file to WAV format
    
    Args:
        input_path: Input audio file path
        output_path: Output WAV file path (auto-generated if None)
        sample_rate: Sample rate in Hz (default 16000)
        channels: Number of channels (default 1 for mono)
    
    Returns:
        str: Path to converted WAV file, or None if failed
    """
    if output_path is None:
        output_path = Path(input_path).with_suffix('.wav')
    
    convert_cmd = [
        "ffmpeg", "-i", input_path,
        "-ar", str(sample_rate),
        "-ac", str(channels),
        "-c:a", "pcm_s16le",  # 16-bit PCM
        str(output_path),
        "-y",
        "-loglevel", "error"
    ]
    
    result = subprocess.run(convert_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[Audio] Error converting to WAV: {result.stderr}")
        return None
    
    return str(output_path)

def check_ffmpeg() -> bool:
    """
    Check if ffmpeg is available
    
    Returns:
        bool: True if ffmpeg is available
    """
    try:
        result = subprocess.run(["ffmpeg", "-version"], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def format_timestamp(seconds: float) -> str:
    """
    Convert seconds to MM:SS or HH:MM:SS format
    
    Args:
        seconds: Time in seconds
        
    Returns:
        str: Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def timestamp_to_seconds(timestamp_str: str) -> float:
    """
    Convert timestamp string (HH:MM:SS.mmm) to seconds
    
    Args:
        timestamp_str: Timestamp string
        
    Returns:
        float: Time in seconds
    """
    parts = timestamp_str.split(':')
    if len(parts) == 3:
        hours, minutes, seconds = parts
        seconds_parts = seconds.split('.')
        secs = float(seconds_parts[0])
        if len(seconds_parts) > 1:
            secs += float('0.' + seconds_parts[1])
        return int(hours) * 3600 + int(minutes) * 60 + secs
    elif len(parts) == 2:
        minutes, seconds = parts
        seconds_parts = seconds.split('.')
        secs = float(seconds_parts[0])
        if len(seconds_parts) > 1:
            secs += float('0.' + seconds_parts[1])
        return int(minutes) * 60 + secs
    return 0