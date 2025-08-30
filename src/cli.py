"""
Command-line interface for Open-Scribe
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .config import Config
from .database import TranscriptionDatabase
from .downloader import YouTubeDownloader
from .transcribers.openai import WhisperAPITranscriber, GPT4OTranscriber, GPT4OMiniTranscriber
from .utils.validators import validate_youtube_url, extract_video_id
from .utils.file import sanitize_filename, save_text_file, copy_to_downloads
from .utils.progress import ProgressBar

def create_argument_parser():
    """Create and configure argument parser"""
    
    parser = argparse.ArgumentParser(
        prog='open-scribe',
        description='🎥 Open-Scribe: YouTube Video Transcription Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s "https://www.youtube.com/watch?v=VIDEO_ID"
  %(prog)s "URL" --engine whisper-api --summary
  %(prog)s "URL" --parallel 4  # For playlists

Environment variables for defaults:
  OPEN_SCRIBE_ENGINE     - Default transcription engine
  OPEN_SCRIBE_STREAM     - Enable streaming (true/false)
  OPEN_SCRIBE_DOWNLOADS  - Export to Downloads (true/false)
  OPEN_SCRIBE_SUMMARY    - Generate summary (true/false)
        '''
    )
    
    parser.add_argument('url', help='YouTube video or playlist URL')
    
    parser.add_argument(
        '--engine', '-e',
        default=Config.DEFAULT_ENGINE,
        choices=Config.AVAILABLE_ENGINES,
        help=f'Transcription engine (default: {Config.DEFAULT_ENGINE})'
    )
    
    parser.add_argument(
        '--stream', '-s',
        action='store_true',
        default=Config.DEFAULT_STREAM,
        help=f'Stream transcription output (default: {Config.DEFAULT_STREAM})'
    )
    
    parser.add_argument(
        '--no-stream',
        action='store_false',
        dest='stream',
        help='Disable streaming output'
    )
    
    parser.add_argument(
        '--downloads', '-d',
        action='store_true',
        default=Config.DEFAULT_DOWNLOADS,
        help=f'Copy to Downloads folder (default: {Config.DEFAULT_DOWNLOADS})'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        default=Config.DEFAULT_SUMMARY,
        help=f'Generate AI summary (default: {Config.DEFAULT_SUMMARY})'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        default=Config.DEFAULT_VERBOSE,
        help=f'Verbose output (default: {Config.DEFAULT_VERBOSE})'
    )
    
    parser.add_argument(
        '--timestamp', '-t',
        action='store_true',
        default=Config.DEFAULT_TIMESTAMP,
        help=f'Include timestamps (default: {Config.DEFAULT_TIMESTAMP})'
    )
    
    parser.add_argument(
        '--audio',
        action='store_true',
        default=Config.DEFAULT_AUDIO,
        help=f'Keep audio file (default: {Config.DEFAULT_AUDIO})'
    )
    
    parser.add_argument(
        '--video',
        action='store_true',
        default=Config.DEFAULT_VIDEO,
        help=f'Download video (default: {Config.DEFAULT_VIDEO})'
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force re-transcription even if exists'
    )
    
    parser.add_argument(
        '--parallel', '-p',
        type=int,
        metavar='N',
        help='Process playlist videos in parallel (N workers)'
    )
    
    return parser

def get_transcriber(engine: str, config: Config):
    """
    Get appropriate transcriber based on engine name
    
    Args:
        engine: Engine name
        config: Configuration object
        
    Returns:
        BaseTranscriber: Transcriber instance
    """
    # Resolve aliases
    engine = config.ENGINE_ALIASES.get(engine, engine)
    
    transcribers = {
        'whisper-api': WhisperAPITranscriber,
        'gpt-4o-transcribe': GPT4OTranscriber,
        'gpt-4o-mini-transcribe': GPT4OMiniTranscriber,
    }
    
    transcriber_class = transcribers.get(engine)
    if not transcriber_class:
        raise ValueError(f"Unknown engine: {engine}")
    
    return transcriber_class(config)

def process_single_video(url: str, args, config: Config) -> bool:
    """
    Process a single video
    
    Args:
        url: Video URL
        args: Command line arguments
        config: Configuration object
        
    Returns:
        bool: True if successful
    """
    # Validate URL
    if not validate_youtube_url(url):
        print(f"Error: Invalid YouTube URL: {url}")
        return False
    
    # Initialize components
    db = TranscriptionDatabase(config.DB_PATH)
    downloader = YouTubeDownloader(config.AUDIO_PATH, config.VIDEO_PATH, config.TEMP_PATH)
    
    # Get video info
    print("\nExtracting video information...")
    video_info = downloader.get_video_info(url)
    if not video_info:
        print("Error: Could not extract video information")
        return False
    
    video_id = video_info['id']
    video_title = video_info['title']
    print(f"Title: {video_title}")
    print(f"Duration: {video_info['duration']} seconds")
    print(f"Uploader: {video_info['uploader']}")
    
    # Check for existing transcription
    if not args.force:
        existing = db.check_existing_job(video_id, args.engine)
        if existing:
            print(f"\nTranscription already exists: {existing['transcript_path']}")
            return True
    
    # Download video if requested
    if args.video:
        print("\nDownloading video...")
        video_file = downloader.download_video(url)
        if video_file:
            print(f"Video saved: {video_file}")
    
    # Download audio
    print("\nDownloading audio...")
    audio_file = downloader.download_audio(url, keep_original=args.audio)
    if not audio_file:
        print("Error: Failed to download audio")
        return False
    
    # Create job in database
    job_id = db.create_job(video_id, url, video_title, args.engine)
    
    # Transcribe
    print(f"\nTranscribing with {args.engine}...")
    transcriber = get_transcriber(args.engine, config)
    
    if not transcriber.is_available():
        print(f"Error: {args.engine} is not available. Check configuration.")
        db.update_job_status(job_id, 'failed')
        return False
    
    transcription = transcriber.transcribe(
        audio_file, 
        stream=args.stream,
        return_timestamps=args.timestamp
    )
    
    if not transcription:
        print("Error: Transcription failed")
        db.update_job_status(job_id, 'failed')
        return False
    
    # Save transcription
    safe_title = sanitize_filename(video_title)
    transcript_path = config.TRANSCRIPT_PATH / f"{safe_title}.txt"
    save_text_file(transcription, transcript_path)
    print(f"\nTranscript saved: {transcript_path}")
    
    # Copy to downloads if requested
    if args.downloads:
        download_path = copy_to_downloads(transcript_path, config.DOWNLOADS_PATH)
        if download_path:
            print(f"Copied to: {download_path}")
    
    # Generate summary if requested
    summary_text = None
    if args.summary:
        print("\nGenerating summary...")
        # TODO: Implement summary generation
        summary_text = "Summary generation not yet implemented in modular version"
    
    # Update job status
    db.update_job_status(job_id, 'completed', str(transcript_path), summary_text)
    
    # Clean up temp audio if not keeping
    if not args.audio and audio_file and Path(audio_file).exists():
        try:
            Path(audio_file).unlink()
        except:
            pass
    
    print("\n✅ Transcription completed successfully!")
    return True

def main():
    """Main entry point"""
    
    # Parse arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Initialize configuration
    config = Config()
    
    try:
        # Create necessary directories
        config.create_directories()
        
        # Validate configuration
        config.validate()
        
        # Process URL
        print(f"🎥 Starting transcription: {args.url}")
        print(f"Engine: {args.engine}")
        
        # Check if playlist
        downloader = YouTubeDownloader(config.AUDIO_PATH, config.VIDEO_PATH, config.TEMP_PATH)
        
        if downloader.is_playlist(args.url):
            print("\n🎵 Playlist detected!")
            playlist_items = downloader.get_playlist_items(args.url)
            
            if not playlist_items:
                print("Error: Could not extract playlist items")
                return 1
            
            print(f"Found {len(playlist_items)} videos")
            
            # Process playlist videos
            if args.parallel:
                # TODO: Implement parallel processing
                print(f"Parallel processing with {args.parallel} workers not yet implemented")
            
            # Sequential processing
            success_count = 0
            for i, item in enumerate(playlist_items, 1):
                print(f"\n{'='*60}")
                print(f"Video {i}/{len(playlist_items)}: {item['title']}")
                print(f"{'='*60}")
                
                if process_single_video(item['url'], args, config):
                    success_count += 1
            
            print(f"\n✅ Processed {success_count}/{len(playlist_items)} videos successfully")
            
        else:
            # Single video
            if not process_single_video(args.url, args, config):
                return 1
        
        return 0
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())