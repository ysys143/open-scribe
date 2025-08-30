"""
File handling utilities for Open-Scribe
"""

import re
from pathlib import Path
from typing import Optional

def sanitize_filename(filename: str) -> str:
    """
    Create a safe filename for the file system
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename safe for filesystem
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*\[\]()]', '_', filename)
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
    # Replace multiple spaces/underscores with single underscore
    filename = re.sub(r'[\s_]+', '_', filename)
    # Strip leading/trailing special characters
    filename = filename.strip('._- ')
    # Limit length
    return filename[:200] if filename else "untitled"

def save_text_file(content: str, filepath: Path, encoding: str = 'utf-8') -> Path:
    """
    Save text content to a file
    
    Args:
        content: Text content to save
        filepath: Path where to save the file
        encoding: File encoding (default: utf-8)
        
    Returns:
        Path: The path where the file was saved
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding=encoding)
    return filepath

def copy_to_downloads(source_path: Path, downloads_path: Path) -> Optional[Path]:
    """
    Copy a file to the downloads folder
    
    Args:
        source_path: Source file path
        downloads_path: Downloads folder path
        
    Returns:
        Path: Destination path if successful, None otherwise
    """
    import shutil
    
    try:
        downloads_path.mkdir(parents=True, exist_ok=True)
        dest_path = downloads_path / source_path.name
        shutil.copy2(source_path, dest_path)
        return dest_path
    except Exception as e:
        print(f"Warning: Could not copy to Downloads: {e}")
        return None