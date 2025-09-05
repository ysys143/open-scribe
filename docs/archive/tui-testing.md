# TUI 테스트 가이드

## 1. 테스트 환경 설정

### 1.1 테스트 라이브러리 설치
```bash
# 가상환경 활성화
source .venv/bin/activate

# 테스트 관련 의존성 설치
uv pip install pytest pytest-asyncio pytest-mock textual-dev
```

### 1.2 테스트 디렉토리 구조
```
tests/
├── __init__.py
├── conftest.py                # pytest 설정
├── unit/                      # 단위 테스트
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_database.py
│   └── test_validators.py
├── integration/               # 통합 테스트
│   ├── __init__.py
│   ├── test_screens.py
│   └── test_app_flow.py
└── ui/                        # UI 테스트
    ├── __init__.py
    └── test_user_interactions.py
```

## 2. 단위 테스트

### 2.1 설정 관리자 테스트 (`tests/unit/test_config.py`)
```python
import pytest
import tempfile
import os
from src.tui.utils.config import ConfigManager

@pytest.fixture
def temp_config_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_config_load_default(temp_config_dir):
    """기본 설정 로드 테스트"""
    config_manager = ConfigManager(config_dir=temp_config_dir)
    config = config_manager.load()
    
    assert config["openai_api_key"] == ""
    assert config["default_engine"] == "gpt-4o-mini-transcribe"
    assert config["audio_download_dir"] == "audio"

def test_config_save_load(temp_config_dir):
    """설정 저장 및 로드 테스트"""
    config_manager = ConfigManager(config_dir=temp_config_dir)
    
    # 설정 저장
    test_config = {
        "openai_api_key": "test-key",
        "default_engine": "gpt-4o-transcribe"
    }
    config_manager.save(test_config)
    
    # 설정 로드
    loaded_config = config_manager.load()
    assert loaded_config["openai_api_key"] == "test-key"
    assert loaded_config["default_engine"] == "gpt-4o-transcribe"

def test_api_key_validation():
    """API 키 유효성 검사 테스트"""
    from src.tui.utils.validators import validate_openai_key
    
    assert validate_openai_key("sk-1234567890abcdef") == True
    assert validate_openai_key("invalid-key") == False
    assert validate_openai_key("") == False
```

### 2.2 데이터베이스 테스트 (`tests/unit/test_database.py`)
```python
import pytest
import tempfile
import sqlite3
from src.tui.utils.database import DatabaseManager

@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    yield db_path
    
    # 정리
    import os
    if os.path.exists(db_path):
        os.unlink(db_path)

def test_database_init(temp_db):
    """데이터베이스 초기화 테스트"""
    db_manager = DatabaseManager(temp_db)
    
    # 테이블이 생성되었는지 확인
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='transcriptions'
        """)
        assert cursor.fetchone() is not None

def test_record_operations(temp_db):
    """레코드 CRUD 테스트"""
    db_manager = DatabaseManager(temp_db)
    
    # 레코드 삽입
    record_id = db_manager.insert_record(
        url="https://youtube.com/test",
        title="Test Video",
        engine="gpt-4o-mini-transcribe"
    )
    assert record_id is not None
    
    # 레코드 조회
    records = db_manager.get_records(limit=10)
    assert len(records) == 1
    assert records[0]["url"] == "https://youtube.com/test"
    
    # 레코드 업데이트
    db_manager.update_status(record_id, "completed")
    updated_record = db_manager.get_record_by_id(record_id)
    assert updated_record["status"] == "completed"
    
    # 레코드 삭제
    db_manager.delete_record(record_id)
    records = db_manager.get_records(limit=10)
    assert len(records) == 0
```

## 3. 통합 테스트

### 3.1 화면 통합 테스트 (`tests/integration/test_screens.py`)
```python
import pytest
from textual.app import App
from textual.pilot import Pilot
from src.tui.screens.main_screen import MainScreen

@pytest.mark.asyncio
async def test_main_screen_navigation():
    """메인 화면 네비게이션 테스트"""
    app = App()
    app.install_screen(MainScreen(), name="main")
    
    async with app.run_test() as pilot:
        # 메인 화면으로 이동
        app.push_screen("main")
        await pilot.pause()
        
        # 탭 네비게이션 테스트
        await pilot.press("tab")
        await pilot.pause()
        
        # 설정 화면으로 이동
        await pilot.press("ctrl+s")
        await pilot.pause()
        
        # 현재 화면 확인
        assert isinstance(app.screen, MainScreen)

@pytest.mark.asyncio
async def test_settings_screen_interaction():
    """설정 화면 상호작용 테스트"""
    from src.tui.screens.settings_screen import SettingsScreen
    
    app = App()
    app.install_screen(SettingsScreen(), name="settings")
    
    async with app.run_test() as pilot:
        app.push_screen("settings")
        await pilot.pause()
        
        # API 키 입력 테스트
        api_key_input = app.query_one("#api-key-input")
        await pilot.click(api_key_input)
        await pilot.type("sk-test-key-123")
        await pilot.pause()
        
        # 저장 버튼 클릭
        save_button = app.query_one("#save-button")
        await pilot.click(save_button)
        await pilot.pause()
        
        # 설정이 저장되었는지 확인
        assert api_key_input.value == "sk-test-key-123"
```

### 3.2 애플리케이션 플로우 테스트 (`tests/integration/test_app_flow.py`)
```python
import pytest
from unittest.mock import patch, MagicMock
from src.tui.app import YouTubeTranscriberTUI

@pytest.mark.asyncio
async def test_full_transcription_flow():
    """전체 전사 프로세스 테스트"""
    app = YouTubeTranscriberTUI()
    
    # Mock 전사 엔진
    with patch('src.transcriber.BaseTranscriber') as mock_transcriber:
        mock_instance = MagicMock()
        mock_instance.transcribe.return_value = "Test transcription result"
        mock_transcriber.return_value = mock_instance
        
        async with app.run_test() as pilot:
            # URL 입력
            url_input = app.query_one("#url-input")
            await pilot.click(url_input)
            await pilot.type("https://youtube.com/watch?v=test")
            
            # 전사 시작
            transcribe_button = app.query_one("#transcribe-button")
            await pilot.click(transcribe_button)
            await pilot.pause(2)  # 비동기 작업 대기
            
            # 결과 확인
            result_display = app.query_one("#result-display")
            assert "Test transcription result" in result_display.renderable
```

## 4. UI 테스트

### 4.1 사용자 상호작용 테스트 (`tests/ui/test_user_interactions.py`)
```python
import pytest
from textual.pilot import Pilot
from src.tui.app import YouTubeTranscriberTUI

@pytest.mark.asyncio
async def test_keyboard_shortcuts():
    """키보드 단축키 테스트"""
    app = YouTubeTranscriberTUI()
    
    async with app.run_test() as pilot:
        # Ctrl+Q: 종료
        await pilot.press("ctrl+q")
        assert app.is_running == False

@pytest.mark.asyncio
async def test_input_validation():
    """입력 유효성 검사 테스트"""
    app = YouTubeTranscriberTUI()
    
    async with app.run_test() as pilot:
        # 잘못된 URL 입력
        url_input = app.query_one("#url-input")
        await pilot.click(url_input)
        await pilot.type("invalid-url")
        
        # 전사 시도
        transcribe_button = app.query_one("#transcribe-button")
        await pilot.click(transcribe_button)
        await pilot.pause()
        
        # 오류 메시지 확인
        error_display = app.query_one("#error-display")
        assert "Invalid URL" in str(error_display.renderable)

@pytest.mark.asyncio
async def test_progress_display():
    """진행률 표시 테스트"""
    app = YouTubeTranscriberTUI()
    
    async with app.run_test() as pilot:
        # 진행률 업데이트 시뮬레이션
        progress_bar = app.query_one("#progress-bar")
        
        # 초기 상태
        assert progress_bar.percentage == 0
        
        # 진행률 업데이트
        progress_bar.update(total=100, progress=50)
        await pilot.pause()
        
        assert progress_bar.percentage == 50
```

## 5. 테스트 실행

### 5.1 기본 테스트 실행
```bash
# 모든 테스트 실행
pytest

# 특정 디렉토리 테스트
pytest tests/unit/

# 특정 파일 테스트
pytest tests/unit/test_config.py

# 특정 테스트 함수
pytest tests/unit/test_config.py::test_config_load_default
```

### 5.2 상세 테스트 실행
```bash
# 상세 출력으로 실행
pytest -v

# 커버리지 측정
pytest --cov=src/tui --cov-report=html

# 병렬 실행 (pytest-xdist 설치 필요)
pytest -n auto
```

### 5.3 비동기 테스트 실행
```bash
# asyncio 테스트만 실행
pytest -m asyncio

# 특정 마커로 테스트 실행
pytest -m "not slow"
```

## 6. 테스트 설정 파일

### 6.1 pytest 설정 (`conftest.py`)
```python
import pytest
import asyncio
from unittest.mock import patch

# AsyncIO 이벤트 루프 설정
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# 공통 Mock 설정
@pytest.fixture
def mock_openai_api():
    with patch('openai.OpenAI') as mock:
        yield mock

@pytest.fixture
def mock_config():
    return {
        "openai_api_key": "test-key",
        "default_engine": "gpt-4o-mini-transcribe",
        "audio_download_dir": "test_audio"
    }
```

### 6.2 pytest.ini 설정
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers = 
    asyncio: marks tests as async
    slow: marks tests as slow running
    integration: marks tests as integration tests
```

## 7. 성능 테스트

### 7.1 메모리 사용량 테스트
```python
import pytest
import psutil
import os
from src.tui.app import YouTubeTranscriberTUI

def test_memory_usage():
    """메모리 사용량 테스트"""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # 앱 시작
    app = YouTubeTranscriberTUI()
    
    # 메모리 사용량 측정
    current_memory = process.memory_info().rss
    memory_increase = current_memory - initial_memory
    
    # 메모리 증가량이 100MB 미만이어야 함
    assert memory_increase < 100 * 1024 * 1024
```

### 7.2 응답 시간 테스트
```python
import time
import pytest
from src.tui.utils.database import DatabaseManager

def test_database_response_time():
    """데이터베이스 응답 시간 테스트"""
    db_manager = DatabaseManager(":memory:")
    
    # 대량 데이터 삽입
    start_time = time.time()
    for i in range(1000):
        db_manager.insert_record(
            url=f"https://youtube.com/test{i}",
            title=f"Test Video {i}",
            engine="gpt-4o-mini-transcribe"
        )
    insertion_time = time.time() - start_time
    
    # 삽입 시간이 5초 미만이어야 함
    assert insertion_time < 5.0
    
    # 조회 시간 테스트
    start_time = time.time()
    records = db_manager.get_records(limit=100)
    query_time = time.time() - start_time
    
    # 조회 시간이 1초 미만이어야 함
    assert query_time < 1.0
    assert len(records) == 100
```

## 8. 디버깅 도구

### 8.1 Textual 개발자 도구
```bash
# 개발자 콘솔 실행
textual console

# CSS 실시간 편집
textual run --dev src/tui/app.py

# 디버깅 모드로 실행
python -m src.tui.app --debug
```

### 8.2 로깅 설정
```python
import logging

# 테스트용 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_debug.log'),
        logging.StreamHandler()
    ]
)
```

## 9. CI/CD 통합

### 9.1 GitHub Actions 설정 (`.github/workflows/test.yml`)
```yaml
name: TUI Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install uv
      run: pip install uv
    
    - name: Install dependencies
      run: |
        uv pip install -r requirements.txt
        uv pip install pytest pytest-asyncio pytest-cov
    
    - name: Run tests
      run: pytest --cov=src/tui --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## 10. 테스트 모범 사례

### 10.1 테스트 작성 원칙
- **단일 책임**: 각 테스트는 하나의 기능만 검증
- **독립성**: 테스트 간 의존성 없이 독립적으로 실행 가능
- **반복 가능성**: 동일한 결과를 보장
- **명확한 네이밍**: 테스트 함수명으로 테스트 목적 파악 가능

### 10.2 Mock 사용 가이드
```python
# 외부 API 호출 Mock
@patch('src.transcriber.openai_client.audio.transcriptions.create')
def test_transcription_mock(mock_transcribe):
    mock_transcribe.return_value.text = "Mocked transcription"
    # 테스트 코드...

# 파일 시스템 Mock
@patch('builtins.open', mock_open(read_data="test config"))
def test_config_file_mock():
    # 테스트 코드...
```

### 10.3 비동기 테스트 패턴
```python
@pytest.mark.asyncio
async def test_async_operation():
    # 비동기 작업 테스트
    result = await some_async_function()
    assert result is not None

# Timeout 설정
@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_with_timeout():
    # 10초 타임아웃으로 테스트 실행
    pass
```

이 테스트 가이드를 통해 TUI 구현의 품질과 안정성을 보장할 수 있습니다.