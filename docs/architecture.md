# Open-Scribe v2.0 시스템 아키텍처

## 목차
1. [시스템 개요](#시스템-개요)
2. [멀티 인터페이스 아키텍처](#멀티-인터페이스-아키텍처)
3. [전사 엔진 플러그인 시스템](#전사-엔진-플러그인-시스템)
4. [데이터 처리 파이프라인](#데이터-처리-파이프라인)
5. [데이터베이스 설계](#데이터베이스-설계)
6. [백그라운드 작업 처리](#백그라운드-작업-처리)
7. [이벤트 시스템](#이벤트-시스템)

## 시스템 개요

Open-Scribe v2.0은 모듈화된 아키텍처를 채택하여 확장성과 유지보수성을 극대화한 YouTube 전사 도구입니다.

```
┌─────────────────────────────────────────────────────────┐
│                     User Interfaces                      │
├─────────────┬────────────────┬──────────────────────────┤
│     CLI     │      TUI       │     Shell (Zsh)          │
│  (main.py)  │   (tui.py)     │   (scribe.zsh)          │
└─────────────┴────────────────┴──────────────────────────┘
                         │
┌─────────────────────────────────────────────────────────┐
│                    Core Engine                           │
├─────────────────────────────────────────────────────────┤
│  Config │ Database │ Downloader │ Transcribers │ Utils  │
└─────────────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────────┐
│                  External Services                       │
├─────────────────────────────────────────────────────────┤
│  OpenAI API │ YouTube API │ whisper.cpp │ yt-dlp        │
└─────────────────────────────────────────────────────────┘
```

## 멀티 인터페이스 아키텍처

### 1. CLI 인터페이스 (`src/cli.py`)
전통적인 명령줄 인터페이스로 스크립팅과 자동화에 최적화:

```python
# 주요 컴포넌트
- ArgumentParser: 명령줄 인자 파싱
- ConfigManager: 설정 관리
- TranscriptionOrchestrator: 전사 작업 조정
```

### 2. TUI 인터페이스 (`src/tui/`)
Textual 프레임워크 기반의 현대적인 터미널 UI:

```python
# 화면 구조
src/tui/
├── app.py                 # 메인 애플리케이션 클래스
├── screens/
│   ├── main_menu.py      # 메인 메뉴 (F1-F5 네비게이션)
│   ├── database.py        # 데이터베이스 브라우저
│   ├── monitor.py         # 작업 모니터링
│   ├── transcribe_screen.py # 전사 실행 화면
│   └── settings.py        # 설정 관리
└── widgets/
    └── progress.py        # 커스텀 진행률 위젯
```

#### TUI 라우팅 시스템
```python
# app.py의 화면 전환 로직
def show_transcribe_screen(self):
    self.push_screen(TranscribeScreen())

def show_database_screen(self):
    self.push_screen(DatabaseScreen())
```

### 3. Shell 통합 (`scribe.zsh`)
Zsh 자동완성과 alias를 제공하는 셸 래퍼:
- 자동완성 지원
- 히스토리 관리
- 별칭 설정

## 전사 엔진 플러그인 시스템

### 추상 기본 클래스 (`src/transcribers/base.py`)
```python
class BaseTranscriber(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str, **kwargs) -> TranscriptionResult:
        """전사 실행 인터페이스"""
        pass
    
    @abstractmethod
    def supports_timestamps(self) -> bool:
        """타임스탬프 지원 여부"""
        pass
```

### 구현된 엔진들

#### 1. OpenAI 엔진 (`src/transcribers/openai.py`)
- **GPT4OTranscriber**: GPT-4o 모델 사용 (고품질)
- **GPT4OMiniTranscriber**: GPT-4o-mini 모델 사용 (균형)
- **WhisperAPITranscriber**: Whisper API 사용

#### 2. YouTube 자막 엔진 (`src/transcribers/youtube.py`)
- **YouTubeTranscriptAPITranscriber**: YouTube 네이티브 자막 추출
- 가장 빠른 처리 속도
- 자막이 있는 경우에만 사용 가능

#### 3. 로컬 엔진 (`src/transcribers/whisper_cpp.py`)
- **WhisperCppTranscriber**: whisper.cpp 로컬 실행
- 오프라인 작업 가능
- GPU 가속 지원

### 엔진 팩토리 패턴
```python
# src/transcribers/__init__.py
def get_transcriber(engine_name: str) -> BaseTranscriber:
    """엔진 이름으로 적절한 transcriber 인스턴스 반환"""
    engine_map = {
        'gpt-4o-transcribe': GPT4OTranscriber,
        'gpt-4o-mini-transcribe': GPT4OMiniTranscriber,
        'whisper-api': WhisperAPITranscriber,
        'whisper-cpp': WhisperCppTranscriber,
        'youtube-transcript-api': YouTubeTranscriptAPITranscriber,
    }
    return engine_map[engine_name]()
```

## 데이터 처리 파이프라인

### 전체 처리 흐름
```
1. URL 입력
   └─> URL 검증 (validators.py)
       └─> 비디오 ID 추출
   
2. 데이터베이스 체크
   └─> 중복 확인 (database.py)
       └─> 기존 전사 재사용 또는 새 작업 생성
   
3. 엔진 선택
   └─> 사용자 지정 또는 자동 선택
       └─> Fallback 로직 적용
   
4. 다운로드 (필요시)
   └─> yt-dlp로 오디오 추출 (downloader.py)
       └─> 압축 필요시 처리 (audio.py)
   
5. 전사 실행
   └─> 선택된 엔진으로 처리
       └─> 타임스탬프 처리 (지원시)
   
6. 후처리
   └─> 요약 생성 (summary.py)
       └─> 번역 처리 (translator.py)
       └─> SRT 생성 (subtitle.py)
   
7. 저장
   └─> 파일 시스템 저장 (file.py)
       └─> 데이터베이스 업데이트
```

### 병렬 처리 시스템
```python
# 동적 워커 계산
class WorkerCalculator:
    def calculate_optimal_workers(self):
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        return min(
            max(MIN_WORKER, cpu_count // 2),
            MAX_WORKER
        )
```

## 데이터베이스 설계

### SQLite 스키마
```sql
CREATE TABLE transcription_jobs (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL,
    video_id TEXT,
    title TEXT,
    engine TEXT,
    status TEXT DEFAULT 'pending',
    transcript_path TEXT,
    audio_path TEXT,
    summary TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSON
);

CREATE INDEX idx_video_id ON transcription_jobs(video_id);
CREATE INDEX idx_status ON transcription_jobs(status);
CREATE INDEX idx_created_at ON transcription_jobs(created_at);
```

### 상태 관리
```python
class JobStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
```

## 백그라운드 작업 처리

### 작업 큐 시스템
```python
class BackgroundJobManager:
    def __init__(self):
        self.job_queue = Queue()
        self.workers = []
        self.active_jobs = {}
    
    def submit_job(self, job: TranscriptionJob):
        """작업 큐에 추가"""
        self.job_queue.put(job)
        self.start_worker_if_needed()
    
    def monitor_jobs(self):
        """실시간 작업 모니터링"""
        return self.active_jobs.values()
```

### TUI 작업 모니터 (`src/tui/screens/monitor.py`)
```python
class JobMonitorScreen(BaseScreen):
    def compose(self):
        # 실시간 작업 상태 표시
        yield DataTable(id="job_table")
        yield ProgressBar(id="progress")
    
    @work(exclusive=True, thread=True)
    def update_job_status(self):
        """백그라운드에서 작업 상태 업데이트"""
        while self.monitoring:
            jobs = self.db_manager.get_active_jobs()
            self.update_table(jobs)
            time.sleep(1)
```

## 이벤트 시스템

### TUI 이벤트 처리
```python
# Textual 이벤트 시스템 활용
class TranscribeScreen(Widget):
    def on_button_pressed(self, event: Button.Pressed):
        """버튼 클릭 이벤트 처리"""
        if event.button.id == "start_button":
            self.start_transcription()
    
    def on_input_submitted(self, event: Input.Submitted):
        """입력 완료 이벤트 처리"""
        if event.input.id == "url_input":
            self.validate_and_process_url(event.value)
```

### 커스텀 이벤트
```python
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

## 성능 최적화

### 1. 메모리 관리
- 스트리밍 처리로 대용량 파일 지원
- 청크 단위 처리로 메모리 사용량 최소화
- 자동 가비지 컬렉션 트리거

### 2. 네트워크 최적화
- 연결 풀링 사용
- 재시도 로직 (지수 백오프)
- 타임아웃 관리

### 3. 파일 시스템 최적화
- 비동기 I/O 활용
- 임시 파일 자동 정리
- 압축을 통한 저장 공간 절약

## 확장 포인트

### 새로운 전사 엔진 추가
1. `BaseTranscriber` 상속
2. `transcribe()` 메서드 구현
3. 엔진 팩토리에 등록

### 새로운 UI 화면 추가
1. `BaseScreen` 상속 (TUI)
2. `compose()` 메서드로 UI 구성
3. 라우팅 로직 추가

### 새로운 후처리기 추가
1. `processors/` 디렉토리에 모듈 추가
2. 파이프라인에 통합
3. 설정 옵션 추가

---

최종 업데이트: 2025-09-08