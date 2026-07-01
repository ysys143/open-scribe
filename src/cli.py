"""
Command-line interface for Open-Scribe
"""

import argparse
import os
import sys
from pathlib import Path

from .config import Config
from .database import TranscriptionDatabase
from .downloader import YouTubeDownloader
from .transcribers.openai import WhisperAPITranscriber, GPT4OTranscriber, GPT4OMiniTranscriber
from .transcribers.youtube import YouTubeTranscriptAPITranscriber
from .transcribers.whisper_cpp import WhisperCppTranscriber
from .utils.validators import validate_youtube_url, is_local_audio_file
from .utils.file import sanitize_filename, save_text_file, copy_to_downloads
from .utils.summary import generate_summary, format_summary_output
from .utils.srt_converter import convert_transcript_to_srt
from .utils.translator import SubtitleTranslator
from . import notion

def create_argument_parser():
    """Create and configure argument parser"""
    
    parser = argparse.ArgumentParser(
        prog='open-scribe',
        description='Open-Scribe: YouTube Video Transcription Tool',
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
    
    parser.add_argument('input', nargs='?', default=None,
                        help='YouTube video/playlist URL or local audio file path')

    parser.add_argument(
        '--update-key',
        action='store_true',
        help='OPENAI_API_KEY를 대화형으로 안전하게 교체하고 종료 (입력은 화면에 표시되지 않음)'
    )
    
    parser.add_argument(
        '--engine', '-e',
        default=Config.ENGINE,
        choices=Config.AVAILABLE_ENGINES,
        help=f'Transcription engine (default: {Config.ENGINE})'
    )
    
    parser.add_argument(
        '--stream', '-s',
        action='store_true',
        default=Config.ENABLE_STREAM,
        help=f'Stream transcription output (default: {Config.ENABLE_STREAM})'
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
        default=Config.COPY_TO_DOWNLOADS,
        help=f'Copy to Downloads folder (default: {Config.COPY_TO_DOWNLOADS})'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        default=Config.ENABLE_SUMMARY,
        help=f'Generate AI summary (default: {Config.ENABLE_SUMMARY})'
    )
    parser.add_argument(
        '--no-summary',
        action='store_false',
        dest='summary',
        help='Disable AI summary'
    )

    parser.add_argument(
        '--translate',
        action='store_true',
        default=Config.ENABLE_TRANSLATE,
        help=f'Translate transcript/SRT (default: {Config.ENABLE_TRANSLATE})'
    )
    parser.add_argument(
        '--no-translate',
        action='store_false',
        dest='translate',
        help='Disable translation'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        default=Config.VERBOSE,
        help=f'Verbose output (default: {Config.VERBOSE})'
    )
    
    parser.add_argument(
        '--timestamp', '-t',
        action='store_true',
        default=Config.INCLUDE_TIMESTAMP,
        help=f'Include timestamps (default: {Config.INCLUDE_TIMESTAMP})'
    )
    parser.add_argument(
        '--no-timestamp',
        action='store_false',
        dest='timestamp',
        help='Disable timestamps'
    )

    parser.add_argument(
        '--srt',
        action='store_true',
        default=Config.GENERATE_SRT,
        help=f'Generate SRT subtitles (default: {Config.GENERATE_SRT})'
    )
    parser.add_argument(
        '--no-srt',
        action='store_false',
        dest='srt',
        help='Disable SRT generation'
    )
    
    parser.add_argument(
        '--audio',
        action='store_true',
        default=Config.KEEP_AUDIO,
        help=f'Keep audio file (default: {Config.KEEP_AUDIO})'
    )
    
    parser.add_argument(
        '--video',
        action='store_true',
        default=Config.DOWNLOAD_VIDEO,
        help=f'Download video (default: {Config.DOWNLOAD_VIDEO})'
    )
    parser.add_argument(
        '--no-video',
        action='store_false',
        dest='video',
        help='Do not download video'
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


def update_api_key() -> int:
    """OPENAI_API_KEY를 대화형으로 안전하게 교체한다.

    - getpass로 입력받아 화면/셸 히스토리에 키가 남지 않는다.
    - XDG 설정(~/.config/open-scribe/.env)의 OPENAI_API_KEY 라인만 교체하고
      나머지 설정은 보존한다. .env.gcloud가 있으면 함께 교체할지 묻는다.
    """
    import getpass

    config_dir = Config.CONFIG_DIR
    env_local = config_dir / ".env"
    env_cloud = config_dir / ".env.gcloud"

    if not env_local.exists():
        config_dir.mkdir(parents=True, exist_ok=True)
        env_local.write_text("")
        os.chmod(env_local, 0o600)
        print(f"[INFO] 설정 파일을 생성했습니다: {env_local}")

    targets = [env_local]
    if env_cloud.exists():
        ans = input(f"클라우드 설정({env_cloud.name})도 함께 교체할까요? [y/N] ").strip().lower()
        if ans == "y":
            targets.append(env_cloud)

    key = getpass.getpass("새 OPENAI_API_KEY 입력 (화면에 표시되지 않음): ").strip()
    if not key:
        print("입력이 없어 취소했습니다.")
        return 1
    if not key.startswith("sk-"):
        ans = input("입력값이 'sk-'로 시작하지 않습니다. 계속할까요? [y/N] ").strip().lower()
        if ans != "y":
            print("취소했습니다.")
            return 1

    for path in targets:
        lines = path.read_text().splitlines() if path.exists() else []
        replaced = False
        for i, line in enumerate(lines):
            if line.strip().startswith("OPENAI_API_KEY="):
                lines[i] = f"OPENAI_API_KEY={key}"
                replaced = True
        if not replaced:
            lines.append(f"OPENAI_API_KEY={key}")
        path.write_text("\n".join(lines) + "\n")
        os.chmod(path, 0o600)
        print(f"[OK] 교체 완료: {path}" + ("" if replaced else "  (키가 없어 새로 추가함)"))

    # 현재 프로세스에도 즉시 반영 (재실행 없이 이어지는 작업이 새 키를 인식하도록)
    os.environ["OPENAI_API_KEY"] = key
    Config.OPENAI_API_KEY = key

    print("\n완료했습니다. 키는 화면/히스토리에 남지 않았습니다.")
    print("이전 키는 https://platform.openai.com/api-keys 에서 폐기(revoke)하세요.")
    if env_cloud in targets:
        print("클라우드 반영: bash deploy.sh 를 재실행하세요.")
    return 0


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
        'youtube-transcript-api': YouTubeTranscriptAPITranscriber,
        'whisper-cpp': WhisperCppTranscriber,
    }
    
    transcriber_class = transcribers.get(engine)
    if not transcriber_class:
        raise ValueError(f"Unknown engine: {engine}")
    
    return transcriber_class(config)

def process_single_video(input_path: str, args, config: Config) -> bool:
    """
    Process a single video or local audio file
    
    Args:
        input_path: Video URL or local audio file path
        args: Command line arguments
        config: Configuration object
        
    Returns:
        bool: True if successful
    """
    # Check if input is a local audio file
    is_local_file = is_local_audio_file(input_path)
    
    if is_local_file:
        # For local files, disable certain options
        args.audio = False
        args.video = False
        args.srt = False
        print(f"Local audio file detected: {input_path}")
    else:
        # Validate URL for YouTube videos
        if not validate_youtube_url(input_path):
            print(f"Error: Invalid YouTube URL or audio file: {input_path}")
            return False
    
    # Initialize components
    db = TranscriptionDatabase(config.DB_PATH)
    
    if is_local_file:
        # For local files, create basic info
        file_path = Path(input_path)
        video_id = f"local_{file_path.stem}"
        video_title = file_path.stem
        print(f"Title: {video_title}")
        print(f"File: {input_path}")
    else:
        # For YouTube videos, get video info
        downloader = YouTubeDownloader(config.AUDIO_PATH, config.VIDEO_PATH, config.TEMP_PATH, cookies_browser=config.COOKIES_BROWSER)
        print("\nExtracting video information...")
        video_info = downloader.get_video_info(input_path)
        if not video_info:
            print("Error: Could not extract video information")
            return False
        
        video_id = video_info['id']
        video_title = video_info['title']
        print(f"Title: {video_title}")
        print(f"Duration: {video_info['duration']} seconds")
        print(f"Uploader: {video_info['uploader']}")
    
    # Check for existing job and progress
    existing_job = db.get_job_progress(video_id, args.engine)
    job_id = None
    
    if existing_job:
        job_id = existing_job['id']
        if not args.force:
            print("\n[DB] Checking existing progress...")
            # If fully completed, just return
            if existing_job['status'] == 'completed' and existing_job['transcription_completed']:
                print(f"[OK] Transcription already completed: {existing_job['transcript_path']}")
                if not args.summary or existing_job['summary_completed']:
                    print("[OK] All requested tasks already completed")
                    return True
    else:
        # Create new job
        job_id = db.create_job(video_id, input_path, video_title, args.engine)
    
    # Handle audio file
    audio_file = None
    if is_local_file:
        # For local files, use the file directly
        audio_file = input_path
        print(f"\n[OK] Using local audio file: {audio_file}")
        # Update download status
        db.update_download_status(job_id, True, audio_file)
    else:
        # For YouTube videos, download if needed
        if args.video:
            print("\nDownloading video...")
            video_file = downloader.download_video(input_path)
            if video_file:
                print(f"Video saved: {video_file}")
        
        # Download audio (skip for YouTube Transcript API)
        if args.engine != 'youtube-transcript-api':
            if existing_job and existing_job.get('download_completed') and not args.force:
                if existing_job.get('download_path') and Path(existing_job['download_path']).exists():
                    print("\n[OK] Download already completed (using cached file)")
                    audio_file = existing_job['download_path']
                else:
                    print("\n[WARNING] Previous download missing, re-downloading...")
            
            if not audio_file:
                print("\nDownloading audio...")
                audio_file = downloader.download_audio(input_path, keep_original=args.audio)
                if not audio_file:
                    print("Error: Failed to download audio")
                    db.update_job_status(job_id, 'failed')
                    return False
                # Update download status
                db.update_download_status(job_id, True, audio_file)
        else:
            print("\n[OK] Skipping audio download (using YouTube Transcript API)")
    
    # Transcribe (check if already transcribed)
    transcription = None
    transcript_path = None
    safe_title = sanitize_filename(video_title)
    
    if existing_job and existing_job.get('transcription_completed') and not args.force:
        if existing_job.get('transcript_path') and Path(existing_job['transcript_path']).exists():
            print("\n[OK] Transcription already completed (using cached result)")
            transcript_path = Path(existing_job['transcript_path'])
            transcription = transcript_path.read_text(encoding='utf-8')
        else:
            print("\n[WARNING] Previous transcription missing, re-transcribing...")
    
    if not transcription:
        print(f"\nTranscribing with {args.engine}...")
        transcriber = get_transcriber(args.engine, config)
        
        if not transcriber.is_available():
            print(f"Error: {args.engine} is not available. Check configuration.")
            db.update_job_status(job_id, 'failed')
            return False
        
        # YouTube Transcript API uses URL directly, not audio file
        if args.engine == 'youtube-transcript-api':
            if is_local_file:
                print("Error: YouTube Transcript API cannot be used with local files")
                db.update_job_status(job_id, 'failed')
                return False
            transcription = transcriber.transcribe(
                input_path,  # Pass URL directly for YouTube API
                stream=args.stream,
                return_timestamps=args.timestamp
            )
        else:
            transcription = transcriber.transcribe(
                audio_file, 
                stream=args.stream,
                return_timestamps=args.timestamp
            )
        
        if not transcription or not transcription.strip():  # Check for empty transcription
            print("Error: Transcription failed")
            db.update_job_status(job_id, 'failed')
            return False
        
        # Save transcription
        transcript_path = config.TRANSCRIPT_PATH / f"{safe_title}.txt"
        save_text_file(transcription, transcript_path)
        print(f"\nTranscript saved: {transcript_path}")
        
        # Update transcription status
        db.update_transcription_status(job_id, True, str(transcript_path))
    
    # Generate summary if requested
    summary_text = None
    if args.summary:
        if existing_job and existing_job.get('summary_completed') and not args.force:
            print("\n[OK] Summary already generated")
            summary_text = existing_job.get('summary')
        else:
            print("\n[SUMMARY] Generating summary...")
            summary_text = generate_summary(transcription, verbose=args.verbose)
            if summary_text:
                # Save summary to file
                summary_path = config.TRANSCRIPT_PATH / f"{safe_title}_summary.txt"
                formatted_summary = format_summary_output(summary_text, video_title)
                save_text_file(formatted_summary, summary_path)
                print(f"Summary saved: {summary_path}")
                
                # Copy to downloads if requested
                if args.downloads:
                    summary_download = copy_to_downloads(summary_path, config.DOWNLOADS_PATH)
                    if summary_download:
                        print(f"Summary copied to: {summary_download}")
                
                db.update_summary_status(job_id, True, summary_text)
            else:
                print("Warning: Summary generation failed")
                db.update_summary_status(job_id, False, None)
    
    # Generate SRT if requested
    srt_path = None
    if args.srt and transcript_path:
        try:
            print("\n[SRT] Generating SRT subtitles...")
            srt_path = convert_transcript_to_srt(transcript_path)
            print(f"SRT saved: {srt_path}")
            try:
                db.update_srt_status(job_id, True, str(srt_path))
            except Exception:
                pass
            if args.downloads:
                srt_download = copy_to_downloads(srt_path, config.DOWNLOADS_PATH)
                if srt_download:
                    print(f"SRT copied to: {srt_download}")
        except Exception as e:
            print(f"Warning: Failed to generate SRT: {e}")

    # Translate if requested (transcript and/or SRT)
    if args.translate:
        try:
            translator = SubtitleTranslator(config)
            # Prefer SRT translation when available
            if srt_path and srt_path.exists():
                print("\n[TRANSLATE] Translating SRT...")
                translated_srt, ok = translator.translate_srt(srt_path.read_text(encoding='utf-8'), verbose=args.verbose)
                if ok:
                    srt_ko_path = srt_path.with_name(f"{srt_path.stem}.ko.srt")
                    save_text_file(translated_srt, srt_ko_path)
                    print(f"Translated SRT saved: {srt_ko_path}")
                    if args.downloads:
                        srt_ko_download = copy_to_downloads(srt_ko_path, config.DOWNLOADS_PATH)
                        if srt_ko_download:
                            print(f"Translated SRT copied to: {srt_ko_download}")
            else:
                print("\n[TRANSLATE] Translating transcript...")
                translated_text, ok = translator.translate_text(transcription, preserve_timestamps=True, verbose=args.verbose)
                if ok:
                    ko_path = config.TRANSCRIPT_PATH / f"{safe_title}.ko.txt"
                    save_text_file(translated_text, ko_path)
                    print(f"Translated transcript saved: {ko_path}")
                    if args.downloads:
                        ko_download = copy_to_downloads(ko_path, config.DOWNLOADS_PATH)
                        if ko_download:
                            print(f"Translated transcript copied to: {ko_download}")
        except Exception as e:
            print(f"Warning: Translation failed: {e}")

    # Copy transcript to downloads if requested (after summary/SRT so files are together)
    if args.downloads and transcript_path:
        download_path = copy_to_downloads(transcript_path, config.DOWNLOADS_PATH)
        if download_path:
            print(f"\nTranscript copied to: {download_path}")
    
    # Save to Notion if configured
    if transcription and transcription.strip() and notion.is_configured():
        print("\n[NOTION] Saving to Notion...")
        from .utils.keywords import extract_keywords
        keyword_source = summary_text or transcription
        print("[NOTION] Extracting keywords...")
        keywords = extract_keywords(keyword_source)
        if keywords:
            print(f"[NOTION] Keywords: {', '.join(keywords)}")

        srt_text = None
        if srt_path and srt_path.exists():
            srt_text = srt_path.read_text(encoding='utf-8')
        duration = video_info.get('duration') if not is_local_file and video_info else None
        from datetime import datetime
        page_id = notion.save_to_notion(
            title=video_title,
            url=input_path,
            engine=args.engine,
            transcript=transcription,
            summary=summary_text,
            srt=srt_text,
            duration=duration,
            keywords=keywords,
            created_at=datetime.now().strftime("%Y-%m-%d"),
        )
        if page_id:
            print(f"[NOTION] Saved: https://notion.so/{page_id.replace('-', '')}")
        else:
            print("[NOTION] Failed to save (check NOTION_API_KEY and NOTION_DATABASE_ID)")

    # Update overall job status
    if transcription and transcription.strip():  # Check for non-empty transcription
        db.update_job_status(job_id, 'completed', str(transcript_path), summary_text)

    # Clean up temp audio if not keeping
    if not args.audio and audio_file and Path(audio_file).exists():
        try:
            Path(audio_file).unlink()
        except OSError:
            pass
    
    # Only show success message if transcription actually succeeded
    if transcription and transcription.strip():  # Check for non-empty transcription
        print("\n[SUCCESS] Transcription completed successfully!")
        return True
    else:
        print("\n[ERROR] Transcription failed!")
        return False

def main():
    """Main entry point"""
    
    # Parse arguments
    parser = create_argument_parser()
    args = parser.parse_args()

    # 설정 유틸리티: API 키 교체 후 종료
    if args.update_key:
        return update_api_key()

    # 전사에는 input이 필요하다
    if not args.input:
        parser.error("input(YouTube URL 또는 로컬 오디오 경로)이 필요합니다. "
                     "API 키만 교체하려면 --update-key 를 사용하세요.")

    # Initialize configuration
    config = Config()

    # 첫 실행: API 엔진인데 키가 없고 대화형 터미널이면 대화형으로 키를 설정한다.
    # (비대화형 환경(CI/파이프)에서는 아래 validate()가 기존처럼 명확한 에러를 낸다)
    needs_api_key = args.engine in ('gpt-4o-transcribe', 'gpt-4o-mini-transcribe', 'whisper-api')
    if needs_api_key and not Config.OPENAI_API_KEY and sys.stdin.isatty():
        print("\n[SETUP] OPENAI_API_KEY가 설정되어 있지 않습니다. 지금 설정합니다.")
        print("발급: https://platform.openai.com/api-keys\n")
        rc = update_api_key()
        if rc != 0:
            return rc

    try:
        # Create necessary directories
        config.create_directories()
        
        # Validate configuration
        config.validate()
        
        # Process input
        print(f"[START] Starting transcription: {args.input}")
        print(f"Engine: {args.engine}")
        
        # Check if input is a local file
        if is_local_audio_file(args.input):
            # Process local file
            if not process_single_video(args.input, args, config):
                return 1
        else:
            # Check if playlist
            downloader = YouTubeDownloader(config.AUDIO_PATH, config.VIDEO_PATH, config.TEMP_PATH, cookies_browser=config.COOKIES_BROWSER)
            
            if downloader.is_playlist(args.input):
                print("\n[PLAYLIST] Playlist detected!")
                playlist_items = downloader.get_playlist_items(args.input)
            
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
                
                print(f"\n[COMPLETE] Processed {success_count}/{len(playlist_items)} videos successfully")
                
            else:
                # Single video
                if not process_single_video(args.input, args, config):
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