"""Compatibility Config attributes backed solely by the settings.json snapshot."""
from pathlib import Path
from src.core.config.document import load_settings,settings_path
from src.core.providers.models import ASR_MODELS,credential


class _OpenAIKey:
    def __get__(self,instance,owner):return credential('openai')


class Config:
    DATA=load_settings()
    SETTINGS_PATH=settings_path()
    CONFIG_DIR=SETTINGS_PATH.parent
    OPENAI_API_KEY=_OpenAIKey()
    OPENAI_SUMMARY_MODEL=DATA['stages']['summary']['model']
    OPENAI_CORRECT_MODEL=DATA['stages']['correct']['model']
    OPENAI_TRANSLATE_MODEL=DATA['stages']['translate']['model']
    OPENAI_SUMMARY_LANGUAGE=DATA['stages']['summary']['options']['language']
    OPENAI_TRANSLATE_LANGUAGE=DATA['stages']['translate']['options']['language']
    MIN_WORKER=DATA['workers']['min']
    MAX_WORKER=DATA['workers']['max']
    BASE_PATH=Path(DATA['paths']['data'])
    CACHE_DIR=Path(DATA['paths']['cache'])
    AUDIO_PATH=Path(DATA['paths']['audio'])
    VIDEO_PATH=Path(DATA['paths']['video'])
    TRANSCRIPT_PATH=Path(DATA['paths']['transcript'])
    TEMP_PATH=Path(DATA['paths']['temp'])
    DB_PATH=Path(DATA['paths']['database'])
    COPY_TO_PATH=Path(DATA['copy_to_path']) if DATA['copy_to_path'] else None
    DOWNLOADS_PATH=COPY_TO_PATH
    YTDLP_VERSION_CHECK=CACHE_DIR/'.ytdlp_version_check'
    WHISPER_CPP_MODEL=DATA['whisper_cpp']['model_path']
    WHISPER_CPP_EXECUTABLE=DATA['whisper_cpp']['executable']
    ENGINE=DATA['stages']['asr']['model']
    ENABLE_STREAM=DATA['output']['stream']
    COPY_TO_DOWNLOADS=DATA['output']['downloads'] and COPY_TO_PATH is not None
    ENABLE_SUMMARY=DATA['stages']['summary']['enabled']
    VERBOSE=DATA['output']['verbose']
    KEEP_AUDIO=DATA['output']['keep_audio']
    DOWNLOAD_VIDEO=DATA['output']['video']
    GENERATE_SRT=DATA['output']['srt']
    ENABLE_TRANSLATE=DATA['stages']['translate']['enabled']
    INCLUDE_TIMESTAMP=DATA['output']['timestamp']
    COOKIES_BROWSER=DATA['download']['cookies_browser']
    ENABLE_NOTION=DATA['integrations']['notion']['enabled']
    DEBUG=DATA['output']['debug']

    # Engine Aliases
    ENGINE_ALIASES = {
        'high': 'gpt-4o-transcribe',
        'medium': 'gpt-4o-mini-transcribe',
        'whisper-cloud': 'whisper-api',
        'whisper-local': 'whisper-cpp',
        'youtube': 'youtube-transcript-api'
    }

    # Available Engines
    AVAILABLE_ENGINES = list(ASR_MODELS) + [
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
                           "Configure providers.openai.api_key_file in settings.json")
