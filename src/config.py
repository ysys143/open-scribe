"""
Configuration management for Open-Scribe
Handles environment variables and application settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Central configuration class for Open-Scribe"""
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_SUMMARY_MODEL = os.getenv('OPENAI_SUMMARY_MODEL', 'gpt-4o-mini')
    
    # Base paths
    BASE_PATH = Path(os.getenv('OPEN_SCRIBE_BASE_PATH', 
                               os.path.expanduser('~/Documents/open-scribe')))
    
    # Specific paths
    AUDIO_PATH = Path(os.getenv('OPEN_SCRIBE_AUDIO_PATH', 
                                BASE_PATH / 'audio'))
    VIDEO_PATH = Path(os.getenv('OPEN_SCRIBE_VIDEO_PATH', 
                                BASE_PATH / 'video'))
    TRANSCRIPT_PATH = Path(os.getenv('OPEN_SCRIBE_TRANSCRIPT_PATH', 
                                     BASE_PATH / 'transcript'))
    TEMP_PATH = Path(os.getenv('OPEN_SCRIBE_TEMP_PATH', 
                               BASE_PATH / 'temp_audio'))
    DOWNLOADS_PATH = Path(os.getenv('OPEN_SCRIBE_DOWNLOADS_PATH', 
                                   os.path.expanduser('~/Downloads')))
    DB_PATH = Path(os.getenv('OPEN_SCRIBE_DB_PATH', 
                             BASE_PATH / 'transcription_jobs.db'))
    
    # Whisper.cpp Configuration
    WHISPER_CPP_MODEL = os.getenv('WHISPER_CPP_MODEL', 
                                  os.path.expanduser('~/whisper.cpp/models/ggml-base.bin'))
    WHISPER_CPP_EXECUTABLE = os.getenv('WHISPER_CPP_EXECUTABLE', 
                                       os.path.expanduser('~/whisper.cpp/build/bin/whisper-cli'))
    
    # Default Options
    DEFAULT_ENGINE = os.getenv('OPEN_SCRIBE_ENGINE', 'gpt-4o-mini-transcribe')
    DEFAULT_STREAM = os.getenv('OPEN_SCRIBE_STREAM', 'true').lower() == 'true'
    DEFAULT_DOWNLOADS = os.getenv('OPEN_SCRIBE_DOWNLOADS', 'true').lower() == 'true'
    DEFAULT_SUMMARY = os.getenv('OPEN_SCRIBE_SUMMARY', 'true').lower() == 'true'
    DEFAULT_VERBOSE = os.getenv('OPEN_SCRIBE_VERBOSE', 'true').lower() == 'true'
    DEFAULT_AUDIO = os.getenv('OPEN_SCRIBE_AUDIO', 'false').lower() == 'true'
    DEFAULT_VIDEO = os.getenv('OPEN_SCRIBE_VIDEO', 'false').lower() == 'true'
    DEFAULT_SRT = os.getenv('OPEN_SCRIBE_SRT', 'false').lower() == 'true'
    DEFAULT_TRANSLATE = os.getenv('OPEN_SCRIBE_TRANSLATE', 'false').lower() == 'true'
    DEFAULT_TIMESTAMP = os.getenv('OPEN_SCRIBE_TIMESTAMP', 'false').lower() == 'true'
    
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
                     cls.TEMP_PATH, cls.BASE_PATH]:
            path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls):
        """Validate configuration and raise errors if critical settings are missing"""
        if not cls.OPENAI_API_KEY and cls.DEFAULT_ENGINE in ['gpt-4o-transcribe', 
                                                               'gpt-4o-mini-transcribe', 
                                                               'whisper-api']:
            raise ValueError("OPENAI_API_KEY is required for selected engine. "
                           "Please set it in your .env file")