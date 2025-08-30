"""
YouTube downloader module for Open-Scribe
Handles video/audio downloading and metadata extraction
"""

import os
from pathlib import Path
from typing import Optional, Dict, List, Any
from yt_dlp import YoutubeDL

class YouTubeDownloader:
    """Handle YouTube video/audio downloading"""
    
    def __init__(self, audio_path: Path, video_path: Path, temp_path: Path):
        """
        Initialize downloader with paths
        
        Args:
            audio_path: Path for audio files
            video_path: Path for video files  
            temp_path: Path for temporary files
        """
        self.audio_path = audio_path
        self.video_path = video_path
        self.temp_path = temp_path
        
        # Ensure directories exist
        for path in [audio_path, video_path, temp_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def download_audio(self, url: str, keep_original: bool = False) -> Optional[str]:
        """
        Download audio from YouTube URL
        
        Args:
            url: YouTube video URL
            keep_original: Keep original audio file after download
            
        Returns:
            str: Path to downloaded audio file, or None if failed
        """
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(self.audio_path / '%(title)s [%(id)s].%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'keepvideo': keep_original,
        }
        
        print(f"Downloading audio from YouTube...")
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Get the output filename
                filename = ydl.prepare_filename(info)
                # Replace extension with mp3
                mp3_filename = os.path.splitext(filename)[0] + '.mp3'
                
                if os.path.exists(mp3_filename):
                    print(f"Audio downloaded: {os.path.basename(mp3_filename)}")
                    return mp3_filename
                else:
                    print("Error: Audio file not found after download")
                    return None
                    
        except Exception as e:
            print(f"Error downloading audio: {e}")
            return None
    
    def download_video(self, url: str) -> Optional[str]:
        """
        Download video from YouTube URL
        
        Args:
            url: YouTube video URL
            
        Returns:
            str: Path to downloaded video file, or None if failed
        """
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': str(self.video_path / '%(title)s [%(id)s].%(ext)s'),
            'quiet': False,
            'no_warnings': False,
        }
        
        print(f"Downloading video from YouTube...")
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Get the output filename
                filename = ydl.prepare_filename(info)
                
                if os.path.exists(filename):
                    print(f"Video downloaded: {os.path.basename(filename)}")
                    return filename
                else:
                    # Check with mp4 extension
                    mp4_filename = os.path.splitext(filename)[0] + '.mp4'
                    if os.path.exists(mp4_filename):
                        print(f"Video downloaded: {os.path.basename(mp4_filename)}")
                        return mp4_filename
                    
                    print("Error: Video file not found after download")
                    return None
                    
        except Exception as e:
            print(f"Error downloading video: {e}")
            return None
    
    def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract video metadata without downloading
        
        Args:
            url: YouTube video URL
            
        Returns:
            dict: Video metadata including title, duration, uploader, etc.
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                    'description': info.get('description'),
                    'thumbnail': info.get('thumbnail'),
                    'url': url
                }
                
        except Exception as e:
            print(f"Error extracting video info: {e}")
            return None
    
    def get_playlist_items(self, url: str) -> List[Dict[str, str]]:
        """
        Extract playlist video information
        
        Args:
            url: YouTube playlist URL
            
        Returns:
            list: List of video dictionaries with title and URL
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'playlist_items': '1-1000',  # Limit to 1000 items
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                playlist_info = ydl.extract_info(url, download=False)
                
                if 'entries' in playlist_info:
                    videos = []
                    for entry in playlist_info['entries']:
                        if entry:
                            videos.append({
                                'title': entry.get('title', 'Unknown'),
                                'url': f"https://www.youtube.com/watch?v={entry['id']}",
                                'id': entry['id'],
                                'duration': entry.get('duration', 0)
                            })
                    
                    return videos
                    
        except Exception as e:
            print(f"Error extracting playlist: {e}")
        
        return []
    
    def is_playlist(self, url: str) -> bool:
        """
        Check if URL is a playlist
        
        Args:
            url: YouTube URL
            
        Returns:
            bool: True if playlist, False otherwise
        """
        return 'playlist' in url.lower() or 'list=' in url