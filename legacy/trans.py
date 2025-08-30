#!/usr/bin/env python3
"""
Open-Scribe: YouTube Video Transcription CLI Tool
MIT License - https://github.com/open-scribe/open-scribe
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional, List
import json
from yt_dlp import YoutubeDL
import tempfile
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter, TextFormatter
import signal
import time
import sqlite3
import threading
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

# Import transcription functions
from transcript import (
    transcribe_with_openai,
    transcribe_with_whisper_api,
    transcribe_with_whisper_cpp
)

# Import OpenAI for summary
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# Engine aliases
ENGINE_ALIASES = {
    'high': 'gpt-4o-transcribe',
    'medium': 'gpt-4o-mini-transcribe',
    'whisper-cloud': 'whisper-api',
    'whisper-local': 'whisper-cpp',
    'youtube': 'youtube-transcript-api'
}

# Available engines
AVAILABLE_ENGINES = [
    'gpt-4o-transcribe',
    'gpt-4o-mini-transcribe', 
    'whisper-api',
    'whisper-cpp',
    'youtube-transcript-api'
]

DEFAULT_ENGINE = 'gpt-4o-mini-transcribe'


class ProgressBar:
    """Progress bar for non-streaming mode"""
    def __init__(self, message="Processing"):
        self.message = message
        self.running = False
        self.thread = None
        
    def start(self):
        """Start the progress animation"""
        self.running = True
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()
        
    def _animate(self):
        """Animate progress bar or spinner"""
        spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        while self.running:
            sys.stdout.write(f'\r{self.message} {next(spinner)} ')
            sys.stdout.flush()
            time.sleep(0.1)
            
    def stop(self, final_message="Done"):
        """Stop the progress animation"""
        self.running = False
        if self.thread:
            self.thread.join()
        sys.stdout.write(f'\r{final_message}' + ' ' * 20 + '\n')
        sys.stdout.flush()


class TranscriptionTool:
    def __init__(self, preferred_languages: Optional[List[str]] = None, translate_to: Optional[str] = None, srt: bool = False, preserve_formatting: bool = False, force: bool = False, include_timestamps: bool = False):
        # Get base path from environment variable or use default
        base_path_str = os.getenv('OPEN_SCRIBE_BASE_PATH', str(Path.home() / "Documents" / "open-scribe"))
        self.base_path = Path(base_path_str)
        
        # Get individual paths from environment variables or use defaults
        self.audio_path = Path(os.getenv('OPEN_SCRIBE_AUDIO_PATH', str(self.base_path / "audio")))
        self.video_path = Path(os.getenv('OPEN_SCRIBE_VIDEO_PATH', str(self.base_path / "video")))
        self.transcript_path = Path(os.getenv('OPEN_SCRIBE_TRANSCRIPT_PATH', str(self.base_path / "transcript")))
        self.temp_audio_path = Path(os.getenv('OPEN_SCRIBE_TEMP_PATH', str(self.base_path / "temp_audio")))
        self.downloads_path = Path(os.getenv('OPEN_SCRIBE_DOWNLOADS_PATH', str(Path.home() / "Downloads")))
        self.db_path = Path(os.getenv('OPEN_SCRIBE_DB_PATH', str(self.base_path / "transcription_jobs.db")))
        
        # transcription preferences (used by youtube-transcript-api path)
        self.preferred_languages = preferred_languages if preferred_languages is not None else ["en"]
        self.translate_to = translate_to
        self.srt = srt
        self.preserve_formatting = preserve_formatting
        self.force = force  # Skip overwrite prompts
        self.include_timestamps = include_timestamps  # Include timestamps in regular transcriptions
        
        # Create directories if they don't exist
        self.audio_path.mkdir(parents=True, exist_ok=True)
        self.video_path.mkdir(parents=True, exist_ok=True)
        self.transcript_path.mkdir(parents=True, exist_ok=True)
        self.temp_audio_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database for job tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcription_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                engine TEXT NOT NULL,
                status TEXT NOT NULL,
                category TEXT,
                keywords TEXT,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                transcript_path TEXT,
                UNIQUE(video_id, engine)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def check_existing_job(self, url: str, engine: str) -> Optional[dict]:
        """Check if job already exists in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        video_id = self.extract_video_id(url)
        cursor.execute('''
            SELECT * FROM transcription_jobs 
            WHERE video_id = ? AND engine = ? AND status = 'completed'
        ''', (video_id, engine))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'engine': row[3],
                'status': row[4],
                'transcript_path': row[10]
            }
        return None
    
    def create_job(self, url: str, title: str, engine: str) -> int:
        """Create new job in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        video_id = self.extract_video_id(url)
        cursor.execute('''
            INSERT INTO transcription_jobs (url, title, engine, status, video_id)
            VALUES (?, ?, ?, 'in_progress', ?)
        ''', (url, title, engine, video_id))
        
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return job_id
    
    def update_job_status(self, job_id: int, status: str, transcript_path: str = None, summary: str = None):
        """Update job status in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status == 'completed':
            cursor.execute('''
                UPDATE transcription_jobs 
                SET status = ?, completed_at = CURRENT_TIMESTAMP, transcript_path = ?, summary = ?
                WHERE id = ?
            ''', (status, transcript_path, summary, job_id))
        else:
            cursor.execute('''
                UPDATE transcription_jobs 
                SET status = ?
                WHERE id = ?
            ''', (status, job_id))
        
        conn.commit()
        conn.close()
    
    def prompt_with_timeout(self, message: str, timeout: int = 20) -> Optional[str]:
        """Prompt user with a timeout. Returns None if timeout or 'n', 'y' for yes."""
        print(f"{message} (y/n) - Timeout in {timeout} seconds: ", end='', flush=True)
        
        # Platform-specific timeout implementation
        import platform
        if platform.system() == 'Windows':
            # Windows doesn't support SIGALRM, use threading instead
            import threading
            
            response_container = [None]
            
            def get_input():
                try:
                    response_container[0] = input().strip().lower()
                except KeyboardInterrupt:
                    response_container[0] = 'interrupted'
            
            input_thread = threading.Thread(target=get_input)
            input_thread.daemon = True
            input_thread.start()
            input_thread.join(timeout)
            
            if input_thread.is_alive():
                print("\nTimeout reached. Proceeding with default action.")
                return None
            elif response_container[0] == 'interrupted':
                print("\nOperation cancelled.")
                sys.exit(1)
            else:
                return response_container[0]
        else:
            # Unix-like systems (Linux, macOS)
            def timeout_handler(signum, frame):
                raise TimeoutError()
            
            # Set up the timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
            
            try:
                response = input().strip().lower()
                signal.alarm(0)  # Cancel the alarm
                return response
            except TimeoutError:
                signal.alarm(0)
                print("\nTimeout reached. Proceeding with default action.")
                return None
            except KeyboardInterrupt:
                signal.alarm(0)
                print("\nOperation cancelled.")
                sys.exit(1)
    
    def check_existing_file(self, file_path: Path, file_type: str = "file") -> bool:
        """Check if file exists and prompt for overwrite if not forced.
        Returns True if should proceed with download, False if should skip."""
        
        if not file_path.exists():
            return True
        
        if self.force:
            print(f"Overwriting existing {file_type}: {file_path.name}")
            return True
        
        response = self.prompt_with_timeout(
            f"\n{file_type.capitalize()} already exists: {file_path.name}\nOverwrite?"
        )
        
        if response == 'y':
            print(f"Overwriting {file_type}...")
            return True
        else:
            print(f"Skipping {file_type} download, using existing file.")
            return False
    
    def find_existing_file(self, output_path: Path, video_id: str, extensions: List[str]) -> Optional[Path]:
        """Find existing file with video ID and any of the given extensions."""
        for file in output_path.iterdir():
            if video_id in file.name and file.suffix in extensions:
                return file
        return None
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        import re
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def download_progress_hook(self, d):
        """Display download progress"""
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A')
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            print(f"\rDownloading: {percent} | Speed: {speed} | ETA: {eta}", end='', flush=True)
        elif d['status'] == 'finished':
            print("\nDownload completed, converting to MP3...")
    
    def is_playlist(self, url: str) -> bool:
        """Check if URL is a playlist"""
        return 'playlist' in url.lower() or 'list=' in url
    
    def get_playlist_items(self, url: str) -> List[dict]:
        """Extract playlist items"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info:
                    items = []
                    for entry in info['entries']:
                        items.append({
                            'id': entry.get('id'),
                            'title': entry.get('title'),
                            'url': f"https://www.youtube.com/watch?v={entry.get('id')}"
                        })
                    return items
            return []
        except Exception as e:
            print(f"Error extracting playlist: {e}")
            return []
    
    def get_video_info(self, url: str) -> Optional[dict]:
        """Extract video metadata without downloading"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
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
                    'categories': info.get('categories', []),
                    'tags': info.get('tags', []),
                }
        except Exception as e:
            print(f"Error extracting video info: {e}")
            return None
    
    def download_video(self, url: str, output_path: Path) -> Optional[Path]:
        """Download video from YouTube"""
        try:
            video_id = self.extract_video_id(url)
            if not video_id:
                print(f"Error: Could not extract video ID from URL: {url}")
                return None
            
            # Check for existing video file
            existing_video = self.find_existing_file(output_path, video_id, ['.mp4', '.webm', '.mkv', '.avi'])
            if existing_video:
                if not self.check_existing_file(existing_video, "video"):
                    return existing_video  # Use existing file
            
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': str(output_path / '%(title)s [%(id)s].%(ext)s'),
                'quiet': False,
                'no_warnings': True,
                'progress_hooks': [self.download_progress_hook],
            }
            
            print(f"Downloading video from YouTube...")
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Get the final filename
                filename = ydl.prepare_filename(info)
                video_path = Path(filename)
                
                if video_path.exists():
                    print(f"Video downloaded: {video_path.name}")
                    return video_path
                else:
                    # Fallback: search for the file
                    for file in output_path.iterdir():
                        if video_id in file.name and file.suffix in ['.mp4', '.webm', '.mkv']:
                            print(f"Video downloaded: {file.name}")
                            return file
                    
            print("Warning: Could not find downloaded video file")
            return None
            
        except Exception as e:
            print(f"Error downloading video: {e}")
            return None
    
    def download_audio(self, url: str, output_path: Path) -> Optional[Path]:
        """Download audio from YouTube using yt-dlp Python library"""
        try:
            video_id = self.extract_video_id(url)
            if not video_id:
                print(f"Error: Could not extract video ID from URL: {url}")
                return None
            
            # Check for existing audio file
            existing_audio = self.find_existing_file(output_path, video_id, ['.mp3', '.m4a', '.wav'])
            if existing_audio:
                if not self.check_existing_file(existing_audio, "audio"):
                    return existing_audio  # Use existing file
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': str(output_path / '%(title)s [%(id)s].%(ext)s'),
                'quiet': False,
                'no_warnings': True,
                'progress_hooks': [self.download_progress_hook],
            }
            
            print(f"Downloading audio from YouTube...")
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Get the final filename
                filename = ydl.prepare_filename(info)
                mp3_path = Path(filename).with_suffix('.mp3')
                
                if mp3_path.exists():
                    print(f"Audio downloaded: {mp3_path.name}")
                    return mp3_path
                else:
                    # Fallback: search for the file
                    for file in output_path.iterdir():
                        if video_id in file.name and file.suffix == '.mp3':
                            print(f"Audio downloaded: {file.name}")
                            return file
                    
            print("Warning: Could not find downloaded audio file")
            return None
            
        except Exception as e:
            print(f"Error downloading audio: {e}")
            return None
    
    def transcribe_youtube_api(self, url: str, languages: Optional[List[str]] = None, translate_to: Optional[str] = None, preserve_formatting: bool = False, as_srt: bool = False) -> Optional[str]:
        """Fetch transcript via youtube-transcript-api with language/translation/formatting support.

        Strategy:
        - Prefer manually created transcripts; fallback to generated ones.
        - If translate_to is provided and transcript is translatable, translate server-side.
        - Optionally output SRT via provided formatter.
        """
        try:
            video_id = self.extract_video_id(url)
            if not video_id:
                print(f"Error: Could not extract video ID from URL: {url}")
                return None

            api = YouTubeTranscriptApi()
            languages = languages if languages is not None else ["en"]

            # Try finding the best transcript
            try:
                transcript_list = api.list(video_id)
                # Prefer manually created transcript
                try:
                    transcript_obj = transcript_list.find_manually_created_transcript(languages)
                except Exception:
                    # Fallback to any transcript matching languages
                    try:
                        transcript_obj = transcript_list.find_transcript(languages)
                    except Exception:
                        # Fallback to generated transcripts
                        transcript_obj = transcript_list.find_generated_transcript(languages)

                # Handle optional translation
                if translate_to:
                    if getattr(transcript_obj, "is_translatable", False):
                        transcript_obj = transcript_obj.translate(translate_to)
                    else:
                        print("Warning: Selected transcript is not translatable; proceeding without translation.")

                fetched = transcript_obj.fetch()
            except Exception:
                # Direct fetch as last resort
                fetched = api.fetch(video_id, languages=languages, preserve_formatting=preserve_formatting)

            if as_srt:
                formatter = SRTFormatter()
                return formatter.format_transcript(fetched)
            else:
                # Check if timestamps should be included
                if self.include_timestamps:
                    # Format with timestamps
                    formatted_lines = []
                    for entry in fetched:
                        # Handle both dict and object formats
                        if hasattr(entry, 'start'):
                            start_time = entry.start
                            text = entry.text if hasattr(entry, 'text') else ''
                        else:
                            start_time = entry.get('start', 0)
                            text = entry.get('text', '')
                        
                        text = text.strip()
                        if text:
                            # Convert seconds to MM:SS or HH:MM:SS format
                            hours = int(start_time // 3600)
                            minutes = int((start_time % 3600) // 60)
                            secs = int(start_time % 60)
                            
                            if hours > 0:
                                timestamp = f"{hours:02d}:{minutes:02d}:{secs:02d}"
                            else:
                                timestamp = f"{minutes:02d}:{secs:02d}"
                            
                            formatted_lines.append(f"[{timestamp}] {text}")
                    return '\n'.join(formatted_lines)
                else:
                    # Plain text join
                    formatter = TextFormatter()
                    return formatter.format_transcript(fetched)

        except Exception as e:
            print(f"Error fetching YouTube transcript: {e}")
            return None
    
    def generate_srt(self, text: str, timestamps: List[dict] = None) -> str:
        """Generate SRT format subtitles from transcript with timestamps"""
        if not timestamps:
            # If no timestamps, create basic ones (fallback)
            lines = text.split('\n')
            timestamps = []
            duration_per_line = 3  # seconds
            for i, line in enumerate(lines):
                if line.strip():
                    timestamps.append({
                        'text': line.strip(),
                        'start': i * duration_per_line,
                        'duration': duration_per_line
                    })
        
        srt_content = []
        for i, entry in enumerate(timestamps, 1):
            start_time = self.seconds_to_srt_time(entry.get('start', 0))
            end_time = self.seconds_to_srt_time(entry.get('start', 0) + entry.get('duration', 3))
            text = entry.get('text', '')
            
            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(text)
            srt_content.append("")  # Empty line between entries
        
        return '\n'.join(srt_content)
    
    def seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def transcribe(self, url: str, engine: str, stream: bool = True) -> Optional[str]:
        """Main transcription function with comprehensive error handling"""
        try:
            print(f"Starting transcription with engine: {engine}")
            
            # Handle YouTube transcript API separately
            if engine == 'youtube-transcript-api':
                return self.transcribe_youtube_api(
                    url,
                    languages=self.preferred_languages,
                    translate_to=self.translate_to,
                    preserve_formatting=self.preserve_formatting,
                    as_srt=self.srt,
                )
            
            # For other engines, we need to download audio first
            print("Downloading audio...")
            audio_file = self.download_audio(url, self.audio_path)
            if not audio_file:
                raise Exception("Failed to download audio. Video might be private or deleted.")
            
            # Perform transcription based on engine
            transcription = None
            
            if engine == 'gpt-4o-transcribe':
                print("Using OpenAI GPT-4o for transcription...")
                try:
                    # GPT-4o also uses the Whisper API for transcription
                    transcription = transcribe_with_openai(str(audio_file), stream=stream, return_timestamps=self.include_timestamps)
                except Exception as e:
                    print(f"OpenAI API error: {e}")
                    print("Tip: Check your OPENAI_API_KEY in .env file")
                    return None
                
            elif engine == 'gpt-4o-mini-transcribe':
                print("Using OpenAI GPT-4o-mini for transcription...")
                try:
                    transcription = transcribe_with_openai(str(audio_file), stream=stream, return_timestamps=self.include_timestamps)
                except Exception as e:
                    print(f"OpenAI API error: {e}")
                    print("Tip: Check your OPENAI_API_KEY in .env file")
                    return None
                
            elif engine == 'whisper-api':
                print("Using OpenAI Whisper API for transcription...")
                try:
                    transcription = transcribe_with_whisper_api(str(audio_file))
                except Exception as e:
                    print(f"Whisper API error: {e}")
                    print("Tip: Check your OPENAI_API_KEY in .env file")
                    return None
                
            elif engine == 'whisper-cpp':
                print("Using whisper.cpp for local transcription...")
                try:
                    transcription = transcribe_with_whisper_cpp(str(audio_file), stream=stream, return_timestamps=self.include_timestamps)
                except FileNotFoundError:
                    print("Error: whisper.cpp not found")
                    print("Tip: Run 'make' in whisper.cpp directory to build it")
                    return None
                except Exception as e:
                    print(f"whisper.cpp error: {e}")
                    return None
                
            else:
                print(f"Error: Unknown engine: {engine}")
                return None
            
            return transcription
            
        except KeyboardInterrupt:
            print("\n\nTranscription cancelled by user")
            return None
        except Exception as e:
            print(f"\nUnexpected error during transcription: {e}")
            return None
    
    def generate_summary(self, text: str, verbose: bool = False) -> Optional[str]:
        """Generate AI summary of the transcription using configurable GPT model"""
        try:
            client = OpenAI()
            
            # Get model from environment variable or use default
            summary_model = os.getenv('OPENAI_SUMMARY_MODEL', 'gpt-4o-mini')
            
            if verbose:
                prompt = """Please provide a comprehensive summary of the following transcript in Korean:
                
1. 핵심 요약 (3줄 이내)
2. 시간대별 주요 내용 정리
3. 상세한 내용 분석 및 비판적 의견

Transcript:
{text}"""
            else:
                prompt = """Please provide a concise 3-line summary in Korean of the following transcript:

Transcript:
{text}"""
            
            response = client.chat.completions.create(
                model=summary_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes video transcripts in Korean."},
                    {"role": "user", "content": prompt.format(text=text[:8000])}  # Limit text to avoid token limits
                ],
                temperature=0.7,
                max_tokens=1000 if verbose else 200
            )
            
            summary = response.choices[0].message.content
            return summary
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return None
    
    def save_transcript(self, text: str, title: str, export_downloads: bool = True, ext: str = "txt") -> Path:
        """Save transcription to file. ext can be 'txt' or 'srt'."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{title}_{timestamp}.{ext}"
        
        # Save to transcript folder
        transcript_file = self.transcript_path / filename
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Transcript saved to: {transcript_file}")
        
        # Export to Downloads folder if requested
        if export_downloads:
            downloads_file = self.downloads_path / filename
            with open(downloads_file, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Transcript exported to: {downloads_file}")
        
        return transcript_file


def select_engine_interactive():
    """Interactive engine selection with arrow keys"""
    try:
        # Try to use simple_term_menu if available
        from simple_term_menu import TerminalMenu
        
        options = [
            "gpt-4o-transcribe (high) - OpenAI GPT-4o high quality",
            "gpt-4o-mini-transcribe (medium) - OpenAI GPT-4o-mini [DEFAULT]",
            "whisper-api (whisper-cloud) - OpenAI Whisper API",
            "whisper-cpp (whisper-local) - Local whisper.cpp",
            "youtube-transcript-api (youtube) - YouTube native transcripts"
        ]
        
        terminal_menu = TerminalMenu(
            options,
            title="Select transcription engine (↑↓ to move, Enter to select):",
            cursor_index=1  # Default to gpt-4o-mini
        )
        
        choice = terminal_menu.show()
        
        if choice is None:
            return DEFAULT_ENGINE
            
        engine_map = {
            0: 'gpt-4o-transcribe',
            1: 'gpt-4o-mini-transcribe',
            2: 'whisper-api',
            3: 'whisper-cpp',
            4: 'youtube-transcript-api'
        }
        
        return engine_map.get(choice, DEFAULT_ENGINE)
        
    except ImportError:
        # Fallback to numbered selection
        print("\nSelect transcription engine:")
        print("1. gpt-4o-transcribe (high) - OpenAI GPT-4o high quality")
        print("2. gpt-4o-mini-transcribe (medium) - OpenAI GPT-4o-mini [DEFAULT]")
        print("3. whisper-api (whisper-cloud) - OpenAI Whisper API")
        print("4. whisper-cpp (whisper-local) - Local whisper.cpp")
        print("5. youtube-transcript-api (youtube) - YouTube native transcripts")
        
        try:
            choice = input("\nEnter number (1-5) or press Enter for default: ").strip()
            
            if not choice:
                return DEFAULT_ENGINE
                
            choice_map = {
                '1': 'gpt-4o-transcribe',
                '2': 'gpt-4o-mini-transcribe',
                '3': 'whisper-api',
                '4': 'whisper-cpp',
                '5': 'youtube-transcript-api'
            }
            
            return choice_map.get(choice, DEFAULT_ENGINE)
            
        except (KeyboardInterrupt, EOFError):
            print("\nUsing default engine")
            return DEFAULT_ENGINE

def sanitize_filename(filename: str) -> str:
    """Create a safe filename for the file system"""
    import re
    # Replace special characters with underscore
    filename = re.sub(r'[<>:"/\\|?*\[\]()]', '_', filename)
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
    # Replace multiple spaces/underscores with single underscore
    filename = re.sub(r'[\s_]+', '_', filename)
    # Remove leading/trailing special characters
    filename = filename.strip('._- ')
    # Limit length (200 characters to leave room for timestamp)
    return filename[:200] if filename else "untitled"

def validate_youtube_url(url: str) -> bool:
    """Validate if URL is a valid YouTube URL"""
    valid_patterns = [
        'youtube.com/watch',
        'youtu.be/',
        'youtube.com/playlist',
        'youtube.com/embed/',
        'm.youtube.com/'
    ]
    return any(pattern in url.lower() for pattern in valid_patterns)

def process_single_video(url, args, tool, engine, playlist_index=None, playlist_total=None):
    """Process a single video with all the specified options
    
    Args:
        url: Video URL to process
        args: Command line arguments
        tool: YouTubeTranscriber instance
        engine: Selected transcription engine
        playlist_index: Current video index in playlist (optional)
        playlist_total: Total videos in playlist (optional)
    
    Returns:
        tuple: (success, video_title, error_message)
    """
    try:
        # Print header if part of playlist
        if playlist_index:
            print(f"\n{'='*60}")
            print(f"Video {playlist_index}/{playlist_total}")
            print(f"{'='*60}")
        
        # Handle video download if requested
        if args.video:
            print(f"\nDownloading video: {url}")
            video_file = tool.download_video(url, tool.video_path)
            if video_file:
                print(f"Video saved to: {video_file}")
            else:
                print("Failed to download video")
                if not args.force:
                    return (False, None, "Failed to download video")
        
        # Get video metadata
        print(f"\nExtracting video information...")
        video_info = tool.get_video_info(url)
        video_title = "Unknown"
        if video_info:
            video_title = video_info.get('title', 'Unknown')
            print(f"Title: {video_title}")
            print(f"Duration: {video_info.get('duration', 0)} seconds")
            print(f"Uploader: {video_info.get('uploader', 'Unknown')}")
        
        # Check for existing job in database
        existing_job = tool.check_existing_job(url, engine)
        if existing_job and not args.force:
            # In parallel mode, skip without prompting
            if playlist_index:
                print(f"Skipping: Transcription already exists for '{video_title}' with {engine}")
                return (True, video_title, None)
            else:
                response = tool.prompt_with_timeout(
                    f"\nTranscription already exists for this video with {engine}.\nRe-transcribe?"
                )
                if response != 'y':
                    print(f"Using existing transcription from: {existing_job['transcript_path']}")
                    return (True, video_title, None)
        
        # Create job in database
        job_id = tool.create_job(url, video_title, engine)
        
        # Perform transcription
        print(f"\nTranscribing: {url}")
        print(f"Engine: {engine}")
        print(f"Options: stream={args.stream}, downloads={args.downloads}")
        
        transcription = tool.transcribe(url, engine, args.stream)
        
        if transcription:
            # Use sanitized video title for filename
            video_id = tool.extract_video_id(url)
            safe_title = sanitize_filename(video_title)
            
            # Save transcript (respect SRT output for YouTube transcript API path)
            file_ext = 'srt' if args.srt and engine == 'youtube-transcript-api' else 'txt'
            transcript_path = tool.save_transcript(transcription, safe_title, args.downloads, ext=file_ext)
            
            # Generate summary if requested
            summary_text = None
            if args.summary:
                print("\nGenerating AI summary...")
                summary = tool.generate_summary(transcription, args.verbose)
                if summary:
                    print("\n" + "="*50)
                    print("📝 SUMMARY")
                    print("="*50)
                    print(summary)
                    print("="*50)
                    
                    # Save summary to file
                    summary_title = f"{safe_title}_summary"
                    tool.save_transcript(summary, summary_title, args.downloads, ext="txt")
                    summary_text = summary
                else:
                    print("Failed to generate summary")
            
            # Update job status to completed
            tool.update_job_status(job_id, 'completed', str(transcript_path), summary_text)
            
            print(f"\n✅ Transcription completed successfully for '{video_title}'!")
            return (True, video_title, None)
        else:
            # Update job status to failed
            tool.update_job_status(job_id, 'failed')
            error_msg = f"Transcription failed for '{video_title}'"
            print(f"\n❌ {error_msg}")
            return (False, video_title, error_msg)
            
    except Exception as e:
        error_msg = f"Error processing video: {str(e)}"
        print(f"\n❌ {error_msg}")
        return (False, None, error_msg)

def main():
    # Get defaults from environment variables
    default_engine = os.getenv('OPEN_SCRIBE_ENGINE', DEFAULT_ENGINE)
    default_stream = os.getenv('OPEN_SCRIBE_STREAM', 'true').lower() == 'true'
    default_downloads = os.getenv('OPEN_SCRIBE_DOWNLOADS', 'true').lower() == 'true'
    default_summary = os.getenv('OPEN_SCRIBE_SUMMARY', 'true').lower() == 'true'  # Default to True
    default_verbose = os.getenv('OPEN_SCRIBE_VERBOSE', 'true').lower() == 'true'  # Default to True
    default_audio = os.getenv('OPEN_SCRIBE_AUDIO', 'false').lower() == 'true'
    default_video = os.getenv('OPEN_SCRIBE_VIDEO', 'false').lower() == 'true'
    default_srt = os.getenv('OPEN_SCRIBE_SRT', 'false').lower() == 'true'
    default_translate = os.getenv('OPEN_SCRIBE_TRANSLATE', 'false').lower() == 'true'
    default_timestamp = os.getenv('OPEN_SCRIBE_TIMESTAMP', 'false').lower() == 'true'
    
    parser = argparse.ArgumentParser(
        prog='open-scribe',
        description='Open-Scribe: YouTube Video Transcription Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Available engines:
  gpt-4o-transcribe      (alias: high)       - OpenAI GPT-4o high quality
  gpt-4o-mini-transcribe (alias: medium)     - OpenAI GPT-4o-mini (default)
  whisper-api            (alias: whisper-cloud) - OpenAI Whisper API
  whisper-cpp            (alias: whisper-local) - Local whisper.cpp
  youtube-transcript-api (alias: youtube)     - YouTube native transcripts

Environment variables for defaults:
  OPEN_SCRIBE_ENGINE     - Default transcription engine
  OPEN_SCRIBE_STREAM     - Enable streaming (true/false)
  OPEN_SCRIBE_DOWNLOADS  - Export to Downloads (true/false)
  OPEN_SCRIBE_SUMMARY    - Generate summary (true/false)
  OPEN_SCRIBE_VERBOSE    - Verbose output (true/false)
  OPEN_SCRIBE_AUDIO      - Keep audio files (true/false)
  OPEN_SCRIBE_VIDEO      - Download video (true/false)
  OPEN_SCRIBE_SRT        - Generate SRT (true/false)
  OPEN_SCRIBE_TRANSLATE  - Translate to Korean (true/false)
  OPEN_SCRIBE_TIMESTAMP  - Include timestamps (true/false)
        '''
    )
    
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument(
        '--engine', '-e',
        default=default_engine,
        help=f'Transcription engine (default: {default_engine})'
    )
    parser.add_argument(
        '--stream', '-s',
        action='store_true',
        default=default_stream,
        help=f'Stream transcription output (default: {default_stream})'
    )
    parser.add_argument(
        '--no-stream', '-ns',
        action='store_false',
        dest='stream',
        help='Disable streaming output'
    )
    parser.add_argument(
        '--downloads', '-d',
        action='store_true',
        default=default_downloads,
        help=f'Export to Downloads folder (default: {default_downloads})'
    )
    parser.add_argument(
        '--no-downloads', '-nd',
        action='store_false',
        dest='downloads',
        help='Do not export to Downloads folder'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        default=default_summary,
        help=f'Generate AI summary of transcription (default: {default_summary})'
    )
    parser.add_argument(
        '--no-summary',
        action='store_false',
        dest='summary',
        help='Disable AI summary generation'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        default=default_verbose,
        help=f'Verbose summary output (default: {default_verbose})'
    )
    parser.add_argument(
        '--no-verbose',
        action='store_false',
        dest='verbose',
        help='Disable verbose output'
    )
    parser.add_argument(
        '--audio',
        action='store_true',
        default=default_audio,
        help=f'Keep downloaded audio file (default: {default_audio})'
    )
    parser.add_argument(
        '--video',
        action='store_true',
        default=default_video,
        help=f'Download video file (default: {default_video})'
    )
    parser.add_argument(
        '--srt',
        action='store_true',
        default=default_srt,
        help=f'Generate SRT subtitle file (default: {default_srt})'
    )
    parser.add_argument(
        '--translate',
        action='store_true',
        default=default_translate,
        help=f'Translate to Korean (default: {default_translate})'
    )
    parser.add_argument(
        '--timestamp', '-t',
        action='store_true',
        default=default_timestamp,
        help=f'Include timestamps in transcription (default: {default_timestamp})'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force re-transcription even if already exists'
    )
    parser.add_argument(
        '--parallel', '-p',
        type=int,
        metavar='N',
        help='Process playlist videos in parallel (N workers, default: sequential)'
    )
    parser.add_argument(
        '--filename',
        type=str,
        help='Custom filename for the transcript (without extension)'
    )
    
    args = parser.parse_args()
    
    # Validate YouTube URL
    if not validate_youtube_url(args.url):
        print(f"Error: Invalid YouTube URL: {args.url}")
        print("Please provide a valid YouTube video or playlist URL")
        print("Examples:")
        print("  https://www.youtube.com/watch?v=VIDEO_ID")
        print("  https://youtu.be/VIDEO_ID")
        print("  https://www.youtube.com/playlist?list=PLAYLIST_ID")
        sys.exit(1)
    
    # Resolve engine aliases
    engine = ENGINE_ALIASES.get(args.engine, args.engine)
    
    # Validate engine
    if engine not in AVAILABLE_ENGINES:
        print(f"Error: Invalid engine '{args.engine}'")
        print(f"Available engines: {', '.join(AVAILABLE_ENGINES)}")
        print(f"Aliases: {', '.join([f'{k}={v}' for k, v in ENGINE_ALIASES.items()])}")
        sys.exit(1)
    
    # Force audio download for non-YouTube API engines
    if engine != 'youtube-transcript-api':
        args.audio = True
    
    # Auto-enable translate for SRT unless Korean detected
    if args.srt:
        args.translate = True  # Will be disabled later if Korean detected
    
    # Create transcription tool instance (configure preferences for youtube-transcript-api)
    tool = TranscriptionTool(
        preferred_languages=["ko", "en"],
        translate_to=("ko" if args.translate else None),
        srt=args.srt,
        preserve_formatting=False,
        force=args.force,
        include_timestamps=args.timestamp
    )
    
    # Check if URL is a playlist
    if tool.is_playlist(args.url):
        print(f"\n🎵 Playlist detected!")
        playlist_items = tool.get_playlist_items(args.url)
        
        if playlist_items:
            print(f"Found {len(playlist_items)} videos in playlist")
            
            # Determine parallel processing
            parallel_workers = args.parallel if args.parallel else None
            if parallel_workers:
                print(f"Parallel processing enabled with {parallel_workers} workers")
            
            response = tool.prompt_with_timeout(
                f"\nProcess all {len(playlist_items)} videos in the playlist?",
                timeout=20
            )
            
            if response != 'y':
                print("Playlist processing cancelled.")
                sys.exit(0)
            
            print(f"\nProcessing {len(playlist_items)} videos...")
            
            # Parallel processing
            if parallel_workers:
                # Limit workers to min(num_videos, num_cores, specified_workers)
                max_workers = min(
                    len(playlist_items),
                    multiprocessing.cpu_count(),
                    parallel_workers
                )
                print(f"Using {max_workers} parallel workers")
                
                successful = []
                failed = []
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all tasks
                    futures = {}
                    for i, item in enumerate(playlist_items, 1):
                        future = executor.submit(
                            process_single_video,
                            item['url'],
                            args,
                            tool,
                            engine,
                            i,
                            len(playlist_items)
                        )
                        futures[future] = item
                    
                    # Process results as they complete
                    for future in as_completed(futures):
                        item = futures[future]
                        try:
                            success, title, error = future.result()
                            if success:
                                successful.append(title or item['title'])
                            else:
                                failed.append((title or item['title'], error))
                        except Exception as e:
                            failed.append((item['title'], str(e)))
                
                # Print summary
                print("\n" + "="*60)
                print("PLAYLIST PROCESSING COMPLETE")
                print("="*60)
                print(f"✅ Successful: {len(successful)} videos")
                if successful:
                    for title in successful[:10]:  # Show first 10
                        print(f"  • {title}")
                    if len(successful) > 10:
                        print(f"  ... and {len(successful) - 10} more")
                
                if failed:
                    print(f"\n❌ Failed: {len(failed)} videos")
                    for title, error in failed[:5]:  # Show first 5 errors
                        print(f"  • {title}: {error}")
                    if len(failed) > 5:
                        print(f"  ... and {len(failed) - 5} more")
                
                print("="*60)
                sys.exit(0 if not failed else 1)
            
            # Sequential processing (existing code)
            else:
                for i, item in enumerate(playlist_items, 1):
                    success, title, error = process_single_video(
                        item['url'],
                        args,
                        tool,
                        engine,
                        i,
                        len(playlist_items)
                    )
                    if not success and not args.force:
                        print(f"Stopping playlist processing due to error: {error}")
                        sys.exit(1)
                
                print("\n" + "="*60)
                print("✅ PLAYLIST PROCESSING COMPLETE")
                print("="*60)
                sys.exit(0)
        else:
            print("Could not extract playlist items")
            sys.exit(1)
    
    # Process single video (not a playlist)
    else:
        success, title, error = process_single_video(args.url, args, tool, engine)
        if not success:
            sys.exit(1)
        sys.exit(0)


if __name__ == "__main__":
    main()