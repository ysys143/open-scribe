"""
YouTube downloader module for Open-Scribe
Handles video/audio downloading and metadata extraction
"""

import os
from pathlib import Path
from typing import Optional, Dict, List, Any
from yt_dlp import YoutubeDL

_AUTH_ERRORS = ('sign in', 'Sign in', 'login required', 'Login required')
_LIVE_ENDED = 'This live event has ended'

class YouTubeDownloader:
    """Handle YouTube video/audio downloading"""

    def __init__(self, audio_path: Path, video_path: Path, temp_path: Path, cookies_browser: str = ''):
        self.audio_path = audio_path
        self.video_path = video_path
        self.temp_path = temp_path
        self.cookies_browser = cookies_browser

        # Ensure directories exist
        for path in [audio_path, video_path, temp_path]:
            path.mkdir(parents=True, exist_ok=True)

    def _base_opts(self) -> dict:
        opts = {
            'remote_components': ['ejs:github'],
            'extractor_args': {'youtube': {'player_client': ['web_creator', 'android_creator', 'mweb']}},
            'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'},
            'ignoreerrors': False,
            'retries': 3,
        }
        proxy = os.getenv('PROXY_URL')
        if proxy:
            opts['proxy'] = proxy
        return opts

    def _apply_cookies(self, opts: dict) -> dict:
        opts.pop('extractor_args', None)
        opts.pop('http_headers', None)
        opts['cookiesfrombrowser'] = (self.cookies_browser,)
        return opts

    @staticmethod
    def _is_auth_error(error_msg: str) -> bool:
        return any(s in error_msg for s in _AUTH_ERRORS)

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
            **self._base_opts(),
            'format': 'bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio/best[height<=480]/best',
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
            'fragment_retries': 3,
        }

        print("Downloading audio from YouTube...")

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                mp3_filename = os.path.splitext(filename)[0] + '.mp3'

                if os.path.exists(mp3_filename):
                    print(f"Audio downloaded: {os.path.basename(mp3_filename)}")
                    return mp3_filename
                else:
                    print("Error: Audio file not found after download")
                    return None

        except Exception as e:
            error_msg = str(e)
            if _LIVE_ENDED in error_msg:
                print("Live stream ended, retrying with relaxed format check...")
                ydl_opts['ignore_no_formats_error'] = True
                try:
                    with YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        if info:
                            filename = ydl.prepare_filename(info)
                            mp3_filename = os.path.splitext(filename)[0] + '.mp3'
                            if os.path.exists(mp3_filename):
                                print(f"Audio downloaded: {os.path.basename(mp3_filename)}")
                                return mp3_filename
                except Exception:
                    pass
                print("Error: This live stream replay is not downloadable yet.")
                print("  Tip: Try again later, or use --engine youtube-transcript-api for subtitle-based transcription.")
                return None
            if self._is_auth_error(error_msg) and self.cookies_browser:
                print(f"Authentication required, retrying with {self.cookies_browser} cookies...")
                return self._download_audio_with_cookies(url, ydl_opts)
            if "Requested format is not available" in error_msg:
                print("Error: Video format not available. This could be due to:")
                print("  - Age-restricted content")
                print("  - Private/unavailable video")
                print("  - Geographic restrictions")
                print("  - Video format changes by YouTube")
                print(f"  Original error: {error_msg}")
            else:
                print(f"Error downloading audio: {error_msg}")
            return None

    def _download_audio_with_cookies(self, url: str, ydl_opts: dict) -> Optional[str]:
        self._apply_cookies(ydl_opts)
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                mp3_filename = os.path.splitext(filename)[0] + '.mp3'
                if os.path.exists(mp3_filename):
                    print(f"Audio downloaded: {os.path.basename(mp3_filename)}")
                    return mp3_filename
        except Exception as e:
            print(f"Error downloading audio (with cookies): {e}")
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
            **self._base_opts(),
            'format': 'best[ext=mp4][height<=1080]/best[height<=720]/best',
            'outtmpl': str(self.video_path / '%(title)s [%(id)s].%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'fragment_retries': 3,
        }

        print("Downloading video from YouTube...")

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

                if os.path.exists(filename):
                    print(f"Video downloaded: {os.path.basename(filename)}")
                    return filename
                else:
                    mp4_filename = os.path.splitext(filename)[0] + '.mp4'
                    if os.path.exists(mp4_filename):
                        print(f"Video downloaded: {os.path.basename(mp4_filename)}")
                        return mp4_filename
                    print("Error: Video file not found after download")
                    return None

        except Exception as e:
            error_msg = str(e)
            if _LIVE_ENDED in error_msg:
                print("Error: This live stream has ended and the replay may not be available yet.")
                print("  Tip: Try again later once YouTube finishes processing the replay.")
                return None
            if self._is_auth_error(error_msg) and self.cookies_browser:
                print(f"Authentication required, retrying with {self.cookies_browser} cookies...")
                return self._download_video_with_cookies(url, ydl_opts)
            if "Requested format is not available" in error_msg:
                print("Error: Video format not available. This could be due to:")
                print("  - Age-restricted content")
                print("  - Private/unavailable video")
                print("  - Geographic restrictions")
                print("  - Video format changes by YouTube")
                print(f"  Original error: {error_msg}")
            else:
                print(f"Error downloading video: {error_msg}")
            return None

    def _download_video_with_cookies(self, url: str, ydl_opts: dict) -> Optional[str]:
        self._apply_cookies(ydl_opts)
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if os.path.exists(filename):
                    print(f"Video downloaded: {os.path.basename(filename)}")
                    return filename
                mp4_filename = os.path.splitext(filename)[0] + '.mp4'
                if os.path.exists(mp4_filename):
                    print(f"Video downloaded: {os.path.basename(mp4_filename)}")
                    return mp4_filename
        except Exception as e:
            print(f"Error downloading video (with cookies): {e}")
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
            **self._base_opts(),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return self._parse_video_info(info, url)

        except Exception as e:
            error_msg = str(e)
            if _LIVE_ENDED in error_msg:
                print("Live stream ended, retrying with relaxed format check...")
                return self._get_video_info_no_formats(url)
            if self._is_auth_error(error_msg) and self.cookies_browser:
                print(f"Authentication required, retrying with {self.cookies_browser} cookies...")
                return self._get_video_info_with_cookies(url, ydl_opts)
            if "Requested format is not available" in error_msg:
                print("Error: Cannot access video information. This could be due to:")
                print("  - Age-restricted content")
                print("  - Private/unavailable video")
                print("  - Geographic restrictions")
                print("  - Invalid video ID")
                print("  - Video has been deleted")
                print(f"  Original error: {error_msg}")
            else:
                print(f"Error extracting video info: {error_msg}")
            return None

    def _get_video_info_no_formats(self, url: str) -> Optional[Dict[str, Any]]:
        """Retry video info extraction ignoring missing formats (e.g. ended live streams)."""
        ydl_opts = {
            **self._base_opts(),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'ignore_no_formats_error': True,
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    return self._parse_video_info(info, url)
        except Exception as e:
            print(f"Error extracting video info (live ended fallback): {e}")
        return None

    def _get_video_info_with_cookies(self, url: str, ydl_opts: dict) -> Optional[Dict[str, Any]]:
        self._apply_cookies(ydl_opts)
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return self._parse_video_info(info, url)
        except Exception as e:
            print(f"Error extracting video info (with cookies): {e}")
        return None

    @staticmethod
    def _parse_video_info(info: dict, url: str) -> Dict[str, Any]:
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
            'playlist_items': '1-1000',
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
