# Open-Scribe API Reference

## 목차
1. [Transcriber API](#transcriber-api)
2. [Database API](#database-api)
3. [Configuration API](#configuration-api)
4. [Downloader API](#downloader-api)
5. [Processor API](#processor-api)
6. [TUI Event API](#tui-event-api)

## Transcriber API

### BaseTranscriber (Abstract)
모든 전사 엔진의 기본 인터페이스

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseTranscriber(ABC):
    """전사 엔진 추상 클래스"""
    
    @abstractmethod
    def transcribe(
        self, 
        audio_path: str, 
        **kwargs
    ) -> TranscriptionResult:
        """
        오디오 파일을 전사
        
        Args:
            audio_path: 오디오 파일 경로
            **kwargs: 엔진별 추가 옵션
            
        Returns:
            TranscriptionResult: 전사 결과 객체
        """
        pass
    
    @abstractmethod
    def supports_timestamps(self) -> bool:
        """타임스탬프 지원 여부"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """엔진 이름"""
        pass
```

### TranscriptionResult
전사 결과 데이터 클래스

```python
@dataclass
class TranscriptionResult:
    """전사 결과"""
    text: str                          # 전사된 텍스트
    segments: Optional[List[Segment]]  # 타임스탬프 세그먼트
    metadata: Dict[str, Any]           # 메타데이터
    duration: Optional[float]          # 오디오 길이 (초)
    language: Optional[str]            # 감지된 언어
    
@dataclass
class Segment:
    """타임스탬프 세그먼트"""
    start: float    # 시작 시간 (초)
    end: float      # 종료 시간 (초)
    text: str       # 세그먼트 텍스트
    confidence: Optional[float]  # 신뢰도 점수
```

### 엔진별 구현

#### GPT4OTranscriber
```python
class GPT4OTranscriber(BaseTranscriber):
    """GPT-4o 전사 엔진"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: OpenAI API 키 (없으면 환경변수 사용)
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
    
    def transcribe(
        self, 
        audio_path: str,
        prompt: Optional[str] = None,
        language: Optional[str] = None,
        temperature: float = 0.0
    ) -> TranscriptionResult:
        """
        GPT-4o로 오디오 전사
        
        Args:
            audio_path: 오디오 파일 경로
            prompt: 전사 프롬프트
            language: 언어 코드 (예: 'ko', 'en')
            temperature: 생성 온도 (0.0-1.0)
        """
```

#### WhisperAPITranscriber
```python
class WhisperAPITranscriber(BaseTranscriber):
    """Whisper API 전사 엔진"""
    
    def transcribe(
        self,
        audio_path: str,
        response_format: str = "verbose_json",
        timestamp_granularities: List[str] = ["segment"]
    ) -> TranscriptionResult:
        """
        Whisper API로 전사
        
        Args:
            audio_path: 오디오 파일 경로
            response_format: 응답 형식 ('json', 'text', 'verbose_json', 'vtt', 'srt')
            timestamp_granularities: 타임스탬프 단위 (['segment'], ['word'])
        """
```

#### YouTubeTranscriptAPITranscriber
```python
class YouTubeTranscriptAPITranscriber(BaseTranscriber):
    """YouTube 자막 API 전사 엔진"""
    
    def transcribe(
        self,
        video_id: str,
        language_codes: List[str] = ['ko', 'en']
    ) -> TranscriptionResult:
        """
        YouTube 자막 추출
        
        Args:
            video_id: YouTube 비디오 ID
            language_codes: 선호 언어 코드 목록 (우선순위)
        """
```

### 팩토리 함수
```python
def get_transcriber(engine_name: str) -> BaseTranscriber:
    """
    엔진 이름으로 transcriber 인스턴스 생성
    
    Args:
        engine_name: 엔진 이름
        
    Returns:
        BaseTranscriber: 전사 엔진 인스턴스
        
    Raises:
        ValueError: 지원하지 않는 엔진
    
    Examples:
        >>> transcriber = get_transcriber("gpt-4o-mini-transcribe")
        >>> result = transcriber.transcribe("audio.mp3")
    """
```

## Database API

### TranscriptionDatabase
SQLite 데이터베이스 관리 클래스

```python
class TranscriptionDatabase:
    """전사 작업 데이터베이스"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Args:
            db_path: 데이터베이스 파일 경로
        """
    
    def create_job(
        self,
        url: str,
        video_id: str,
        title: str,
        engine: str
    ) -> int:
        """
        새 작업 생성
        
        Returns:
            int: 생성된 작업 ID
        """
    
    def update_job_status(
        self,
        job_id: int,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """작업 상태 업데이트"""
    
    def get_job(self, job_id: int) -> Optional[Dict]:
        """작업 정보 조회"""
    
    def find_existing_transcription(
        self,
        video_id: str,
        engine: Optional[str] = None
    ) -> Optional[Dict]:
        """기존 전사 찾기"""
    
    def search_jobs(
        self,
        query: str,
        status: Optional[str] = None,
        engine: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        작업 검색
        
        Args:
            query: 검색어 (제목, URL)
            status: 상태 필터
            engine: 엔진 필터
            limit: 최대 결과 수
        """
    
    def get_statistics(self) -> Dict:
        """
        통계 정보
        
        Returns:
            Dict: {
                'total_jobs': int,
                'completed': int,
                'failed': int,
                'by_engine': Dict[str, int],
                'by_date': Dict[str, int]
            }
        """
```

### 작업 상태
```python
class JobStatus(Enum):
    """작업 상태 열거형"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

## Configuration API

### Config
설정 관리 클래스

```python
class Config:
    """전역 설정 관리"""
    
    # 경로 설정
    BASE_PATH: str = "~/Documents/open-scribe"
    AUDIO_PATH: str = "{BASE_PATH}/audio"
    TRANSCRIPT_PATH: str = "{BASE_PATH}/transcript"
    VIDEO_PATH: str = "{BASE_PATH}/video"
    DB_PATH: str = "{BASE_PATH}/transcription_jobs.db"
    
    # 기본 옵션
    DEFAULT_ENGINE: str = "gpt-4o-mini-transcribe"
    STREAM_OUTPUT: bool = True
    SAVE_TO_DOWNLOADS: bool = True
    AUTO_SUMMARY: bool = False
    
    # 병렬 처리
    MIN_WORKERS: int = 1
    MAX_WORKERS: int = 5
    
    @classmethod
    def load_from_env(cls) -> None:
        """환경 변수에서 설정 로드"""
    
    @classmethod
    def save_to_file(cls, path: str) -> None:
        """설정을 파일로 저장"""
    
    @classmethod
    def load_from_file(cls, path: str) -> None:
        """파일에서 설정 로드"""
    
    @classmethod
    def get_path(cls, path_type: str) -> Path:
        """
        경로 가져오기 (확장 및 생성)
        
        Args:
            path_type: 'audio', 'transcript', 'video', 'db'
        """
```

### ConfigManager (TUI)
```python
class ConfigManager:
    """TUI 설정 관리"""
    
    def __init__(self, config_path: str = "tui_config.json"):
        """설정 파일 초기화"""
    
    def get(self, key: str, default: Any = None) -> Any:
        """설정 값 가져오기"""
    
    def set(self, key: str, value: Any) -> None:
        """설정 값 설정"""
    
    def save(self) -> None:
        """설정 저장"""
    
    @property
    def theme(self) -> Dict:
        """테마 설정"""
```

## Downloader API

### YouTubeDownloader
YouTube 다운로드 관리

```python
class YouTubeDownloader:
    """YouTube 다운로더"""
    
    def __init__(self):
        """yt-dlp 초기화"""
    
    def download_audio(
        self,
        url: str,
        output_path: str,
        format: str = "mp3",
        quality: str = "128k",
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        오디오 다운로드
        
        Args:
            url: YouTube URL
            output_path: 출력 경로
            format: 오디오 형식
            quality: 오디오 품질
            progress_callback: 진행률 콜백 함수
            
        Returns:
            str: 다운로드된 파일 경로
        """
    
    def download_video(
        self,
        url: str,
        output_path: str,
        quality: str = "best",
        progress_callback: Optional[Callable] = None
    ) -> str:
        """비디오 다운로드"""
    
    def get_video_info(self, url: str) -> Dict:
        """
        비디오 정보 가져오기
        
        Returns:
            Dict: {
                'id': str,
                'title': str,
                'duration': int,
                'uploader': str,
                'upload_date': str,
                'description': str,
                'thumbnail': str
            }
        """
    
    def get_playlist_info(self, url: str) -> List[Dict]:
        """재생목록 정보 가져오기"""
```

## Processor API

### SummaryProcessor
요약 생성 프로세서

```python
class SummaryProcessor:
    """AI 요약 생성"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Args:
            model: 사용할 OpenAI 모델
        """
    
    def generate_summary(
        self,
        text: str,
        language: str = "ko",
        verbose: bool = False,
        max_length: int = 500
    ) -> str:
        """
        텍스트 요약 생성
        
        Args:
            text: 원본 텍스트
            language: 요약 언어
            verbose: 상세 요약 여부
            max_length: 최대 요약 길이
        """
    
    def generate_structured_summary(
        self,
        text: str,
        include_timestamps: bool = True
    ) -> Dict:
        """
        구조화된 요약 생성
        
        Returns:
            Dict: {
                'brief': str,           # 간단 요약
                'key_points': List[str], # 핵심 포인트
                'timeline': List[Dict],  # 타임라인
                'conclusion': str        # 결론
            }
        """
```

### SubtitleProcessor
자막 처리 프로세서

```python
class SubtitleProcessor:
    """자막 생성 및 변환"""
    
    def create_srt(
        self,
        segments: List[Segment],
        output_path: str
    ) -> str:
        """
        SRT 자막 생성
        
        Args:
            segments: 타임스탬프 세그먼트
            output_path: 출력 파일 경로
        """
    
    def create_vtt(
        self,
        segments: List[Segment],
        output_path: str
    ) -> str:
        """WebVTT 자막 생성"""
    
    def merge_short_segments(
        self,
        segments: List[Segment],
        min_duration: float = 2.0
    ) -> List[Segment]:
        """짧은 세그먼트 병합"""
```

### TranslationProcessor
번역 프로세서

```python
class TranslationProcessor:
    """번역 처리"""
    
    def translate(
        self,
        text: str,
        target_language: str = "ko",
        source_language: Optional[str] = None,
        preserve_timestamps: bool = False
    ) -> str:
        """
        텍스트 번역
        
        Args:
            text: 원본 텍스트
            target_language: 대상 언어
            source_language: 소스 언어 (자동 감지)
            preserve_timestamps: 타임스탬프 유지
        """
    
    def detect_language(self, text: str) -> str:
        """언어 감지"""
```

## TUI Event API

### 커스텀 이벤트
```python
from textual.events import Event

class TranscriptionStarted(Event):
    """전사 시작 이벤트"""
    def __init__(self, job_id: int, url: str):
        self.job_id = job_id
        self.url = url

class TranscriptionProgress(Event):
    """전사 진행 이벤트"""
    def __init__(self, job_id: int, progress: float, message: str):
        self.job_id = job_id
        self.progress = progress  # 0.0 - 1.0
        self.message = message

class TranscriptionCompleted(Event):
    """전사 완료 이벤트"""
    def __init__(self, job_id: int, result: TranscriptionResult):
        self.job_id = job_id
        self.result = result

class TranscriptionFailed(Event):
    """전사 실패 이벤트"""
    def __init__(self, job_id: int, error: Exception):
        self.job_id = job_id
        self.error = error
```

### 이벤트 핸들러
```python
class TranscribeScreen(Widget):
    """전사 화면 위젯"""
    
    def on_transcription_started(self, event: TranscriptionStarted):
        """전사 시작 시 호출"""
        self.update_status(f"Started: {event.url}")
    
    def on_transcription_progress(self, event: TranscriptionProgress):
        """진행률 업데이트"""
        self.progress_bar.update(event.progress)
        self.status_label.update(event.message)
    
    def on_transcription_completed(self, event: TranscriptionCompleted):
        """전사 완료 시 호출"""
        self.display_result(event.result)
    
    def on_transcription_failed(self, event: TranscriptionFailed):
        """전사 실패 시 호출"""
        self.show_error(str(event.error))
```

### 이벤트 발행
```python
# 이벤트 발행 예제
async def start_transcription(self, url: str):
    """전사 작업 시작"""
    job_id = self.db.create_job(url, ...)
    
    # 시작 이벤트 발행
    self.post_message(TranscriptionStarted(job_id, url))
    
    try:
        # 진행률 콜백
        def on_progress(percent: float, message: str):
            self.post_message(
                TranscriptionProgress(job_id, percent, message)
            )
        
        # 전사 실행
        result = await self.transcriber.transcribe_async(
            audio_path,
            progress_callback=on_progress
        )
        
        # 완료 이벤트
        self.post_message(TranscriptionCompleted(job_id, result))
        
    except Exception as e:
        # 실패 이벤트
        self.post_message(TranscriptionFailed(job_id, e))
```

## 유틸리티 API

### AudioUtils
```python
class AudioUtils:
    """오디오 유틸리티"""
    
    @staticmethod
    def compress_audio(
        input_path: str,
        output_path: str,
        target_size_mb: float = 25.0
    ) -> str:
        """오디오 압축"""
    
    @staticmethod
    def get_duration(audio_path: str) -> float:
        """오디오 길이 (초)"""
    
    @staticmethod
    def split_audio(
        audio_path: str,
        chunk_duration: float = 300.0
    ) -> List[str]:
        """오디오 분할"""
```

### FileUtils
```python
class FileUtils:
    """파일 유틸리티"""
    
    @staticmethod
    def ensure_directory(path: str) -> Path:
        """디렉토리 생성 (없으면)"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """파일명 정리"""
    
    @staticmethod
    def get_unique_filename(
        directory: str,
        basename: str,
        extension: str
    ) -> str:
        """중복 없는 파일명 생성"""
```

### ProgressTracker
```python
class ProgressTracker:
    """진행률 추적"""
    
    def __init__(self, total: int, callback: Optional[Callable] = None):
        """
        Args:
            total: 전체 작업량
            callback: 진행률 콜백 함수
        """
    
    def update(self, amount: int = 1):
        """진행률 업데이트"""
    
    @property
    def percentage(self) -> float:
        """완료 퍼센트 (0.0-100.0)"""
    
    @property
    def eta(self) -> Optional[timedelta]:
        """예상 완료 시간"""
```

---

최종 업데이트: 2025-09-08