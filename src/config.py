"""
Configuration management for Open-Scribe
Handles environment variables and application settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv


def _resolve_dir(explicit_env: str, xdg_env: str, xdg_default: str) -> Path:
    """XDG Base Directory 규칙으로 디렉토리를 해석한다.

    우선순위:
      1) 앱 전용 override 환경변수(explicit_env) — 그대로 사용
      2) XDG base 환경변수(xdg_env) — 그 아래 'open-scribe' 하위
      3) 기본값(xdg_default)
    """
    explicit = os.environ.get(explicit_env)
    if explicit:
        return Path(os.path.expanduser(explicit))
    base = os.environ.get(xdg_env)
    if base:
        return Path(base) / "open-scribe"
    return Path(os.path.expanduser(xdg_default))


# XDG Base Directory 기반 경로
CONFIG_DIR = _resolve_dir("OPEN_SCRIBE_CONFIG_DIR", "XDG_CONFIG_HOME", "~/.config/open-scribe")
DATA_DIR = _resolve_dir("OPEN_SCRIBE_DATA_DIR", "XDG_DATA_HOME", "~/.local/share/open-scribe")
CACHE_DIR = _resolve_dir("OPEN_SCRIBE_CACHE_DIR", "XDG_CACHE_HOME", "~/.cache/open-scribe")

# 환경변수 로드: XDG config의 .env를 우선 적용하고,
# 이어서 현재 디렉토리의 .env로 보충한다(레포에서 직접 실행하는 개발 편의).
# load_dotenv는 기본적으로 기존 값을 덮어쓰지 않으므로 config가 우선된다.
load_dotenv(CONFIG_DIR / ".env")
load_dotenv()

class Config:
    """Central configuration class for Open-Scribe"""
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_SUMMARY_MODEL = os.getenv('OPENAI_SUMMARY_MODEL', 'gpt-5-mini')
    OPENAI_SUMMARY_LANGUAGE = os.getenv('OPENAI_SUMMARY_LANGUAGE', 'auto')
    OPENAI_CORRECT_MODEL = os.getenv('OPENAI_CORRECT_MODEL', 'gpt-5-mini')
    OPENAI_TRANSLATE_MODEL = os.getenv('OPENAI_TRANSLATE_MODEL', 'gpt-5-mini')
    OPENAI_TRANSLATE_LANGUAGE = os.getenv('OPENAI_TRANSLATE_LANGUAGE', 'Korean')
    
    # Worker Configuration
    MIN_WORKER = int(os.getenv('MIN_WORKER', '1'))
    MAX_WORKER = int(os.getenv('MAX_WORKER', '5'))
    
    # Base paths (XDG data dir 기준; OPEN_SCRIBE_BASE_PATH로 override 가능)
    BASE_PATH = Path(os.getenv('OPEN_SCRIBE_BASE_PATH') or DATA_DIR)
    
    # Specific paths: compose from BASE_PATH, allow overrides if defined
    AUDIO_PATH = Path(os.getenv('OPEN_SCRIBE_AUDIO_PATH') or (BASE_PATH / 'audio'))
    VIDEO_PATH = Path(os.getenv('OPEN_SCRIBE_VIDEO_PATH') or (BASE_PATH / 'video'))
    TRANSCRIPT_PATH = Path(os.getenv('OPEN_SCRIBE_TRANSCRIPT_PATH') or (BASE_PATH / 'transcript'))
    TEMP_PATH = Path(os.getenv('OPEN_SCRIBE_TEMP_PATH') or (BASE_PATH / 'temp_audio'))
    DOWNLOADS_PATH = Path(os.getenv('OPEN_SCRIBE_DOWNLOADS_PATH', 
                                   os.path.expanduser('~/Downloads')))
    DB_PATH = Path(os.getenv('OPEN_SCRIBE_DB_PATH') or (BASE_PATH / 'transcription_jobs.db'))

    # XDG 디렉토리 (클래스에서도 접근 가능하게 노출)
    CONFIG_DIR = CONFIG_DIR
    CACHE_DIR = CACHE_DIR
    # 런타임 캐시 파일
    YTDLP_VERSION_CHECK = CACHE_DIR / '.ytdlp_version_check'
    
    # Whisper.cpp Configuration
    WHISPER_CPP_MODEL = os.getenv('WHISPER_CPP_MODEL', 
                                  str(Path(__file__).parent.parent / 'whisper.cpp/models/ggml-large-v3.bin'))
    WHISPER_CPP_EXECUTABLE = os.getenv('WHISPER_CPP_EXECUTABLE', 
                                       str(Path(__file__).parent.parent / 'whisper.cpp/build/bin/whisper-cli'))
    
    # Options Configuration
    ENGINE = os.getenv('OPEN_SCRIBE_ENGINE', 'gpt-4o-mini-transcribe')
    ENABLE_STREAM = os.getenv('OPEN_SCRIBE_STREAM', 'true').lower() == 'true'
    COPY_TO_DOWNLOADS = os.getenv('OPEN_SCRIBE_DOWNLOADS', 'true').lower() == 'true'
    ENABLE_SUMMARY = os.getenv('OPEN_SCRIBE_SUMMARY', 'true').lower() == 'true'
    VERBOSE = os.getenv('OPEN_SCRIBE_VERBOSE', 'true').lower() == 'true'
    KEEP_AUDIO = os.getenv('OPEN_SCRIBE_AUDIO', 'false').lower() == 'true'
    DOWNLOAD_VIDEO = os.getenv('OPEN_SCRIBE_VIDEO', 'false').lower() == 'true'
    GENERATE_SRT = os.getenv('OPEN_SCRIBE_SRT', 'false').lower() == 'true'
    ENABLE_TRANSLATE = os.getenv('OPEN_SCRIBE_TRANSLATE', 'false').lower() == 'true'
    INCLUDE_TIMESTAMP = os.getenv('OPEN_SCRIBE_TIMESTAMP', 'false').lower() == 'true'
    COOKIES_BROWSER = os.getenv('OPEN_SCRIBE_COOKIES_BROWSER', '')
    ENABLE_NOTION = os.getenv('OPEN_SCRIBE_NOTION', 'false').lower() == 'true'


    # Debug Configuration
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'


    # Engine Aliases
    ENGINE_ALIASES = {
        'high': 'gpt-4o-transcribe',
        'medium': 'gpt-4o-mini-transcribe',
        'whisper-cloud': 'whisper-api',
        'whisper-local': 'whisper-cpp',
        'youtube': 'youtube-transcript-api'
    }
    
    # Available Engines
    AVAILABLE_ENGINES = [
        'gpt-4o-transcribe',
        'gpt-4o-mini-transcribe', 
        'whisper-api',
        'whisper-cpp',
        'youtube-transcript-api'
    ]
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist"""
        for path in [cls.AUDIO_PATH, cls.VIDEO_PATH, cls.TRANSCRIPT_PATH,
                     cls.TEMP_PATH, cls.BASE_PATH, cls.CACHE_DIR]:
            path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls):
        """Validate configuration and raise errors if critical settings are missing"""
        if not cls.OPENAI_API_KEY and cls.ENGINE in ['gpt-4o-transcribe', 
                                                       'gpt-4o-mini-transcribe', 
                                                       'whisper-api']:
            raise ValueError("OPENAI_API_KEY is required for selected engine. "
                           "Please set it in your .env file")