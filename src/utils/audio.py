"""
Audio processing utilities for Open-Scribe
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List

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

def get_audio_duration(audio_path: str) -> float:
    """
    Get duration of audio file in seconds
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        float: Duration in seconds, or 0 if failed
    """
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception as e:
        print(f"[Audio] Error getting duration: {e}")
    return 0

def should_use_chunking(audio_path: str, max_size_mb: float = 25) -> bool:
    """
    Determine if chunking is needed for the audio file
    
    Args:
        audio_path: Path to audio file
        max_size_mb: Maximum file size in MB
        
    Returns:
        bool: True if chunking should be used
    """
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    
    # Try compression first
    if file_size_mb > max_size_mb:
        # Check if compression would be sufficient
        # Estimate: 64kbps compression reduces size by ~75%
        estimated_compressed_size = file_size_mb * 0.25
        if estimated_compressed_size > max_size_mb:
            return True  # Even compression won't be enough
    
    # Also use chunking for very long audio (>30 minutes)
    duration = get_audio_duration(audio_path)
    if duration > 1800:  # 30 minutes
        return True
    
    return False

def split_audio_into_chunks(audio_path: str, chunk_duration_seconds: int = 600, use_project_temp: bool = True) -> List[str]:
    """
    Split audio file into chunks of specified duration
    
    Args:
        audio_path: Path to audio file
        chunk_duration_seconds: Duration of each chunk in seconds (default 10 minutes)
        use_project_temp: Use project temp_audio directory instead of system temp
        
    Returns:
        list: Paths to chunk files
    """
    duration = get_audio_duration(audio_path)
    if duration == 0:
        print(f"[Audio] Could not determine duration, returning original file")
        return [audio_path]
    
    chunk_paths = []
    
    # Use project temp_audio directory for easier debugging
    if use_project_temp:
        from pathlib import Path
        project_root = Path(audio_path).parent
        temp_dir = project_root / "temp_audio"
        temp_dir.mkdir(exist_ok=True)
        temp_dir = str(temp_dir)
        print(f"[Audio] Using project temp directory: {temp_dir}")
    else:
        temp_dir = tempfile.mkdtemp(prefix="audio_chunks_")
    
    # Calculate number of chunks needed
    num_chunks = int(duration / chunk_duration_seconds) + (1 if duration % chunk_duration_seconds > 0 else 0)
    
    print(f"[Audio] Splitting {duration:.1f}s audio into {num_chunks} chunks of {chunk_duration_seconds}s each")
    
    for i in range(num_chunks):
        start_time = i * chunk_duration_seconds
        chunk_path = os.path.join(temp_dir, f"chunk_{i:03d}.mp3")
        
        cmd = [
            "ffmpeg", "-i", audio_path,
            "-ss", str(start_time),
            "-t", str(chunk_duration_seconds),
            "-c", "copy",  # Fast copy without re-encoding
            chunk_path,
            "-y",
            "-loglevel", "error"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Try with re-encoding if copy fails
            # Rebuild command explicitly to avoid index errors
            remaining = max(0, duration - start_time)
            target_duration = min(chunk_duration_seconds, remaining)
            reencode_cmd = [
                "ffmpeg",
                "-i", audio_path,
                "-ss", str(start_time),
                "-t", str(target_duration),
                "-c:a", "libmp3lame",
                "-b:a", "128k",
                chunk_path,
                "-y",
                "-loglevel", "error",
            ]
            result = subprocess.run(reencode_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"[Audio] Error creating chunk {i}: {result.stderr}")
                continue
        
        if os.path.exists(chunk_path):
            chunk_paths.append(chunk_path)
            print(f"[Audio] Created chunk {i+1}/{num_chunks}: {os.path.basename(chunk_path)}")
    
    if not chunk_paths:
        print(f"[Audio] Failed to create chunks, returning original file")
        return [audio_path]
    
    return chunk_paths

def cleanup_temp_chunks(chunk_paths: List[str], keep_for_debug: bool = False):
    """
    Clean up temporary chunk files
    
    Args:
        chunk_paths: List of paths to chunk files
        keep_for_debug: If True, preserve chunks for debugging
    """
    if keep_for_debug:
        print(f"[Audio] Keeping {len(chunk_paths)} chunk files for debugging")
        if chunk_paths:
            print(f"[Audio] Chunks location: {os.path.dirname(chunk_paths[0])}")
        return
    
    for path in chunk_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
    
    # Also try to remove the temp directory (but not if it's temp_audio)
    if chunk_paths:
        temp_dir = os.path.dirname(chunk_paths[0])
        if "audio_chunks_" in temp_dir:
            try:
                os.rmdir(temp_dir)
            except Exception:
                pass