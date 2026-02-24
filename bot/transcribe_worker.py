"""
Transcription worker for Cloud Run
Orchestrates the existing src/ modules with cloud-adapted paths
"""

import logging
import asyncio
import os
import random
import shutil
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

# Cloud Run temp paths
CLOUD_TEMP_BASE = Path("/tmp/open-scribe")
CLOUD_AUDIO_PATH = CLOUD_TEMP_BASE / "audio"
CLOUD_VIDEO_PATH = CLOUD_TEMP_BASE / "video"
CLOUD_TRANSCRIPT_PATH = CLOUD_TEMP_BASE / "transcript"
CLOUD_TEMP_PATH = CLOUD_TEMP_BASE / "temp_audio"


@dataclass
class WorkerOptions:
    """Options for transcription processing"""

    engine: str = "gpt-4o-mini-transcribe"
    summary: bool = False
    translate: bool = False
    srt: bool = False
    timestamp: bool = False
    stream: bool = False
    verbose: bool = False


@dataclass
class WorkerResult:
    """Result from transcription processing"""

    success: bool = False
    title: str = ""
    url: str = ""
    video_id: str = ""
    engine: str = ""
    transcript: str = ""
    summary: Optional[str] = None
    srt_content: Optional[str] = None
    translation: Optional[str] = None
    duration: Optional[int] = None
    error: Optional[str] = None
    audio_size_mb: Optional[float] = None


def _refresh_proxy():
    """Fetch a random proxy from Webshare API if configured"""
    api_url = os.getenv("WEBSHARE_PROXY_LIST_URL")
    if not api_url:
        return
    try:
        logger.info("Fetching proxy list from: %s", api_url[:80])
        resp = httpx.get(api_url, timeout=10, follow_redirects=True)
        resp.raise_for_status()
        lines = resp.text.strip().split("\n")
        lines = [line.strip() for line in lines if line.strip()]
        if not lines:
            return
        proxy_line = random.choice(lines)
        parts = proxy_line.split(":")
        if len(parts) == 4:
            ip, port, user, passwd = parts
            os.environ["PROXY_URL"] = f"http://{user}:{passwd}@{ip}:{port}"
            logger.info("Using proxy: %s:%s", ip, port)
    except Exception as e:
        logger.warning("Failed to fetch proxy list: %s", e)


def _setup_cloud_paths():
    """Create necessary temp directories for Cloud Run"""
    for path in [
        CLOUD_AUDIO_PATH,
        CLOUD_VIDEO_PATH,
        CLOUD_TRANSCRIPT_PATH,
        CLOUD_TEMP_PATH,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def _configure_for_cloud():
    """Override Config paths for Cloud Run environment"""
    from src.config import Config

    Config.BASE_PATH = CLOUD_TEMP_BASE
    Config.AUDIO_PATH = CLOUD_AUDIO_PATH
    Config.VIDEO_PATH = CLOUD_VIDEO_PATH
    Config.TRANSCRIPT_PATH = CLOUD_TRANSCRIPT_PATH
    Config.TEMP_PATH = CLOUD_TEMP_PATH
    Config.DOWNLOADS_PATH = CLOUD_TEMP_BASE / "downloads"
    Config.DB_PATH = CLOUD_TEMP_BASE / "jobs.db"
    Config.COPY_TO_DOWNLOADS = False


def _get_transcriber(engine: str):
    """Get the appropriate transcriber for the engine"""
    from src.config import Config

    # Resolve aliases
    engine = Config.ENGINE_ALIASES.get(engine, engine)

    from src.transcribers.openai import (
        WhisperAPITranscriber,
        GPT4OTranscriber,
        GPT4OMiniTranscriber,
    )
    from src.transcribers.youtube import YouTubeTranscriptAPITranscriber

    transcribers = {
        "whisper-api": WhisperAPITranscriber,
        "gpt-4o-transcribe": GPT4OTranscriber,
        "gpt-4o-mini-transcribe": GPT4OMiniTranscriber,
        "youtube-transcript-api": YouTubeTranscriptAPITranscriber,
    }

    transcriber_class = transcribers.get(engine)
    if not transcriber_class:
        raise ValueError(
            f"Unknown engine: {engine}. Available: {list(transcribers.keys())}"
        )

    return transcriber_class(Config)


def _do_transcribe(url: str, options: WorkerOptions) -> WorkerResult:
    """
    Synchronous transcription pipeline.
    Runs in a thread via asyncio.to_thread.
    """
    from src.config import Config
    from src.downloader import YouTubeDownloader
    from src.utils.validators import validate_youtube_url
    from src.utils.file import sanitize_filename

    result = WorkerResult(url=url, engine=options.engine)

    # Refresh proxy from Webshare if configured
    _refresh_proxy()

    # Validate URL
    if not validate_youtube_url(url):
        result.error = "Invalid YouTube URL"
        return result

    # Setup paths
    _setup_cloud_paths()
    _configure_for_cloud()

    # Get video info
    downloader = YouTubeDownloader(CLOUD_AUDIO_PATH, CLOUD_VIDEO_PATH, CLOUD_TEMP_PATH)

    logger.info("Extracting video info for: %s", url)
    video_info = downloader.get_video_info(url)

    # If yt-dlp fails (bot detection), fallback to youtube-transcript-api
    fallback_to_yt_api = False
    if not video_info:
        logger.warning("yt-dlp failed, falling back to youtube-transcript-api")
        fallback_to_yt_api = True
        # Extract video ID from URL for minimal info
        import re
        vid_match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
        video_info = {
            "title": "Unknown",
            "id": vid_match.group(1) if vid_match else "",
            "duration": None,
        }

    result.title = video_info.get("title", "Unknown")
    result.video_id = video_info.get("id", "")
    result.duration = video_info.get("duration")

    logger.info("Video: %s (duration: %ss)", result.title, result.duration)

    # Resolve engine alias
    engine = Config.ENGINE_ALIASES.get(options.engine, options.engine)

    # Force youtube-transcript-api if yt-dlp failed
    if fallback_to_yt_api and engine != "youtube-transcript-api":
        logger.info("Forcing engine: youtube-transcript-api (yt-dlp unavailable)")
        engine = "youtube-transcript-api"

    result.engine = engine

    # Download audio (skip for YouTube Transcript API)
    audio_file = None
    if engine != "youtube-transcript-api":
        logger.info("Downloading audio...")
        audio_file = downloader.download_audio(url)
        if not audio_file:
            # Fallback to youtube-transcript-api on download failure too
            logger.warning("Audio download failed, falling back to youtube-transcript-api")
            engine = "youtube-transcript-api"
            result.engine = engine

    if audio_file:
        # Report audio size
        audio_size = os.path.getsize(audio_file) / (1024 * 1024)
        result.audio_size_mb = round(audio_size, 1)
        logger.info("Audio downloaded: %.1f MB", audio_size)

    # Transcribe
    logger.info("Transcribing with engine: %s", engine)
    transcriber = _get_transcriber(engine)

    if not transcriber.is_available():
        result.error = f"Engine {engine} is not available"
        return result

    if engine == "youtube-transcript-api":
        transcript = transcriber.transcribe(
            url, stream=False, return_timestamps=options.timestamp
        )
    else:
        transcript = transcriber.transcribe(
            audio_file, stream=False, return_timestamps=options.timestamp
        )

    if not transcript or not transcript.strip():
        result.error = "Transcription returned empty result"
        return result

    result.transcript = transcript
    logger.info("Transcription complete: %d characters", len(transcript))

    # Optional: Generate summary
    if options.summary:
        try:
            from src.utils.summary import generate_summary

            logger.info("Generating summary...")
            summary = generate_summary(transcript, verbose=options.verbose)
            if summary:
                result.summary = summary
                logger.info("Summary generated: %d characters", len(summary))
        except Exception as e:
            logger.warning("Summary generation failed: %s", e)

    # Optional: Generate SRT
    if options.srt and options.timestamp:
        try:
            safe_title = sanitize_filename(result.title)
            transcript_path = CLOUD_TRANSCRIPT_PATH / f"{safe_title}.txt"
            transcript_path.write_text(transcript, encoding="utf-8")

            from src.utils.srt_converter import convert_transcript_to_srt

            srt_path = convert_transcript_to_srt(transcript_path)
            if srt_path and srt_path.exists():
                result.srt_content = srt_path.read_text(encoding="utf-8")
                logger.info("SRT generated")
        except Exception as e:
            logger.warning("SRT generation failed: %s", e)

    # Optional: Translation
    if options.translate:
        try:
            from src.utils.translator import SubtitleTranslator

            translator = SubtitleTranslator(Config())
            translated, ok = translator.translate_text(
                transcript, preserve_timestamps=True, verbose=options.verbose
            )
            if ok:
                result.translation = translated
                logger.info("Translation complete")
        except Exception as e:
            logger.warning("Translation failed: %s", e)

    # Cleanup temp files
    try:
        if audio_file and os.path.exists(audio_file):
            os.remove(audio_file)
        # Clean up temp chunks
        if CLOUD_TEMP_PATH.exists():
            shutil.rmtree(CLOUD_TEMP_PATH, ignore_errors=True)
            CLOUD_TEMP_PATH.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning("Cleanup error: %s", e)

    result.success = True
    return result


async def process_url(
    url: str, options: Optional[WorkerOptions] = None
) -> WorkerResult:
    """
    Process a YouTube URL through the transcription pipeline.
    Runs the synchronous pipeline in a thread to avoid blocking.

    Args:
        url: YouTube video URL
        options: Processing options

    Returns:
        WorkerResult with transcription data
    """
    if options is None:
        options = WorkerOptions()

    return await asyncio.to_thread(_do_transcribe, url, options)
