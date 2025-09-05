# TUI 구현 가이드

## 준비 사항

### 필요 패키지 설치

```bash
# 가상환경 활성화
source .venv/bin/activate

# 필요한 패키지 설치 (uv pip 사용)
uv pip install textual>=0.47.0 rich>=13.7.0 prompt-toolkit>=3.0.0

# requirements.txt 업데이트
echo "textual>=0.47.0" >> requirements.txt
echo "rich>=13.7.0" >> requirements.txt
echo "prompt-toolkit>=3.0.0" >> requirements.txt
```

### 개발 환경 설정

```bash
# Textual 개발 도구 설치 (선택사항)
uv pip install textual-dev

# CSS 자동 재로드를 위한 감시 명령
textual run --dev src.tui.app:OpenScribeTUI
```

## Phase 1: 기본 프레임워크 설정

### 1.1 메인 애플리케이션 생성

```python
# src/tui/__init__.py
"""TUI Package for Open-Scribe"""

from .app import OpenScribeTUI

__all__ = ["OpenScribeTUI"]
```

```python
# src/tui/app.py
"""메인 TUI 애플리케이션"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.binding import Binding

from .screens.main_menu import MainMenuScreen


class OpenScribeTUI(App):
    """Open-Scribe TUI 메인 애플리케이션"""
    
    CSS_PATH = "themes/dark.tcss"
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "종료", priority=True),
        Binding("f1", "help", "도움말"),
        Binding("f2", "toggle_theme", "테마 변경"),
        Binding("ctrl+r", "refresh", "새로고침"),
    ]
    
    def __init__(self):
        super().__init__()
        self.title = "Open-Scribe TUI v2.0"
        self.sub_title = "YouTube Transcription Tool"
    
    def compose(self) -> ComposeResult:
        """UI 구성"""
        yield Header(show_clock=True)
        yield MainMenuScreen()
        yield Footer()
    
    def action_toggle_theme(self) -> None:
        """테마 토글"""
        if self.dark:
            self.theme = "light"
        else:
            self.theme = "dark"
    
    def action_help(self) -> None:
        """도움말 표시"""
        self.push_screen("help")
    
    def action_refresh(self) -> None:
        """화면 새로고침"""
        if hasattr(self.screen, 'refresh_data'):
            self.screen.refresh_data()


if __name__ == "__main__":
    app = OpenScribeTUI()
    app.run()
```

### 1.2 기본 화면 클래스 생성

```python
# src/tui/screens/base.py
"""기본 화면 클래스"""

from textual.screen import Screen
from textual import events
from typing import Any

from ..utils.config_manager import ConfigManager
from ..utils.db_manager import DatabaseManager


class BaseScreen(Screen):
    """모든 화면의 기본 클래스"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager()
    
    def on_key(self, event: events.Key) -> None:
        """공통 키 이벤트 처리"""
        if event.key == "escape":
            self.app.pop_screen()
        elif event.key == "f5":
            self.refresh_data()
    
    def refresh_data(self) -> None:
        """데이터 새로고침 (하위 클래스에서 구현)"""
        pass
    
    def show_error(self, message: str) -> None:
        """에러 메시지 표시"""
        self.notify(f"❌ {message}", severity="error")
    
    def show_success(self, message: str) -> None:
        """성공 메시지 표시"""
        self.notify(f"✅ {message}", severity="information")
```

### 1.3 메인 메뉴 화면 구현

```python
# src/tui/screens/main_menu.py
"""메인 메뉴 화면"""

from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Static
from textual.app import ComposeResult

from .base import BaseScreen
from .transcribe import TranscribeScreen
from .database import DatabaseScreen
from .api_keys import ApiKeysScreen
from .settings import SettingsScreen
from .monitor import MonitorScreen


class MainMenuScreen(BaseScreen):
    """메인 메뉴 화면"""
    
    def compose(self) -> ComposeResult:
        """UI 구성"""
        with Vertical(classes="main-menu"):
            yield Static("🎥 Open-Scribe TUI", classes="title")
            yield Static("YouTube 전사 도구", classes="subtitle")
            
            with Vertical(classes="menu-buttons"):
                yield Button("🎬 새 전사 작업", id="transcribe", classes="menu-button")
                yield Button("📊 데이터베이스 관리", id="database", classes="menu-button")
                yield Button("🔑 API 키 관리", id="api_keys", classes="menu-button")
                yield Button("⚙️ 설정", id="settings", classes="menu-button")
                yield Button("📈 실시간 모니터링", id="monitor", classes="menu-button")
                yield Button("❓ 도움말", id="help", classes="menu-button")
                yield Button("🚪 종료", id="quit", classes="menu-button quit-button")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """버튼 클릭 이벤트 처리"""
        button_id = event.button.id
        
        if button_id == "transcribe":
            self.app.push_screen(TranscribeScreen())
        elif button_id == "database":
            self.app.push_screen(DatabaseScreen())
        elif button_id == "api_keys":
            self.app.push_screen(ApiKeysScreen())
        elif button_id == "settings":
            self.app.push_screen(SettingsScreen())
        elif button_id == "monitor":
            self.app.push_screen(MonitorScreen())
        elif button_id == "help":
            self.show_help()
        elif button_id == "quit":
            self.app.exit()
    
    def show_help(self) -> None:
        """도움말 표시"""
        help_text = """
        Open-Scribe TUI 도움말
        
        키보드 단축키:
        - Ctrl+C: 종료
        - F1: 도움말
        - F2: 테마 변경
        - F5: 새로고침
        - Esc: 이전 화면
        
        각 화면에서 Tab/Shift+Tab으로 요소 간 이동 가능
        """
        self.notify(help_text, title="도움말", timeout=10)
```

## Phase 2: 핵심 기능 구현

### 2.1 API 키 관리 화면

```python
# src/tui/screens/api_keys.py
"""API 키 관리 화면"""

from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Static, Input, DataTable
from textual.app import ComposeResult
from textual import on

from .base import BaseScreen
from ..widgets.dialogs import ConfirmDialog


class ApiKeysScreen(BaseScreen):
    """API 키 관리 화면"""
    
    def compose(self) -> ComposeResult:
        """UI 구성"""
        with Vertical(classes="api-keys-screen"):
            yield Static("🔑 API 키 관리", classes="screen-title")
            
            with Horizontal(classes="action-bar"):
                yield Button("➕ 키 추가", id="add_key", variant="primary")
                yield Button("✏️ 키 수정", id="edit_key")
                yield Button("🗑️ 키 삭제", id="delete_key", variant="error")
                yield Button("✅ 키 검증", id="validate_key")
            
            yield DataTable(id="keys_table", classes="keys-table")
            
            with Vertical(classes="key-form", id="key_form"):
                yield Static("키 정보")
                yield Input(placeholder="키 이름 (예: OpenAI API Key)", id="key_name")
                yield Input(
                    placeholder="API 키 값 (sk-...)",
                    password=True,
                    id="key_value"
                )
                with Horizontal():
                    yield Button("💾 저장", id="save_key", variant="success")
                    yield Button("❌ 취소", id="cancel_key")
    
    def on_mount(self) -> None:
        """화면 마운트 시"""
        self.load_keys()
        self.query_one("#key_form").display = False
    
    def load_keys(self) -> None:
        """키 목록 로드"""
        table = self.query_one("#keys_table", DataTable)
        table.clear(columns=True)
        table.add_columns("이름", "키 (마스킹)", "상태", "마지막 검증")
        
        keys = self.config_manager.get_api_keys()
        for key_info in keys:
            masked_key = self.mask_api_key(key_info.get("value", ""))
            table.add_row(
                key_info.get("name", ""),
                masked_key,
                key_info.get("status", "미검증"),
                key_info.get("last_validated", "없음")
            )
    
    def mask_api_key(self, key: str) -> str:
        """API 키 마스킹"""
        if len(key) < 10:
            return "*" * len(key)
        return f"{key[:6]}...{key[-4:]}"
    
    @on(Button.Pressed, "#add_key")
    def show_add_form(self) -> None:
        """키 추가 폼 표시"""
        self.clear_form()
        self.query_one("#key_form").display = True
        self.query_one("#key_name").focus()
    
    @on(Button.Pressed, "#save_key")
    def save_key(self) -> None:
        """키 저장"""
        name = self.query_one("#key_name", Input).value.strip()
        value = self.query_one("#key_value", Input).value.strip()
        
        if not name or not value:
            self.show_error("이름과 키 값을 모두 입력해주세요.")
            return
        
        try:
            success = self.config_manager.save_api_key(name, value)
            if success:
                self.show_success(f"키 '{name}'이 저장되었습니다.")
                self.query_one("#key_form").display = False
                self.load_keys()
            else:
                self.show_error("키 저장에 실패했습니다.")
        except Exception as e:
            self.show_error(f"저장 중 오류: {str(e)}")
    
    @on(Button.Pressed, "#validate_key")
    def validate_selected_key(self) -> None:
        """선택된 키 검증"""
        table = self.query_one("#keys_table", DataTable)
        if table.cursor_row < 0:
            self.show_error("검증할 키를 선택해주세요.")
            return
        
        # 백그라운드에서 키 검증 실행
        self.validate_key_async(table.cursor_row)
    
    @self.work(exclusive=True)
    async def validate_key_async(self, row_index: int) -> None:
        """비동기 키 검증"""
        try:
            keys = self.config_manager.get_api_keys()
            if row_index < len(keys):
                key_info = keys[row_index]
                is_valid = await self.config_manager.validate_api_key_async(
                    key_info.get("value", "")
                )
                
                if is_valid:
                    self.show_success("키가 유효합니다.")
                else:
                    self.show_error("키가 유효하지 않습니다.")
                
                self.load_keys()  # 테이블 새로고침
        except Exception as e:
            self.show_error(f"검증 중 오류: {str(e)}")
    
    def clear_form(self) -> None:
        """폼 필드 클리어"""
        self.query_one("#key_name", Input).value = ""
        self.query_one("#key_value", Input).value = ""
```

### 2.2 데이터베이스 관리 화면

```python
# src/tui/screens/database.py
"""데이터베이스 관리 화면"""

from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Static, Input, DataTable, TabbedContent, TabPane
from textual.app import ComposeResult
from textual import on

from .base import BaseScreen
from ..widgets.charts import StatisticsWidget


class DatabaseScreen(BaseScreen):
    """데이터베이스 관리 화면"""
    
    def compose(self) -> ComposeResult:
        """UI 구성"""
        with Vertical(classes="database-screen"):
            yield Static("📊 데이터베이스 관리", classes="screen-title")
            
            with TabbedContent():
                with TabPane("히스토리", id="history_tab"):
                    with Horizontal(classes="search-bar"):
                        yield Input(placeholder="검색어 입력...", id="search_input")
                        yield Button("🔍 검색", id="search_btn")
                        yield Button("🔄 새로고침", id="refresh_btn")
                        yield Button("📤 내보내기", id="export_btn")
                    
                    with Horizontal(classes="filter-bar"):
                        yield Button("전체", id="filter_all", classes="filter-btn active")
                        yield Button("성공", id="filter_success", classes="filter-btn")
                        yield Button("실패", id="filter_failed", classes="filter-btn")
                        yield Button("진행중", id="filter_running", classes="filter-btn")
                    
                    yield DataTable(id="history_table", classes="history-table")
                
                with TabPane("통계", id="stats_tab"):
                    yield StatisticsWidget(id="statistics")
                
                with TabPane("관리", id="manage_tab"):
                    with Vertical(classes="manage-actions"):
                        yield Button("🗑️ 오래된 작업 정리", id="cleanup_old")
                        yield Button("📊 데이터베이스 최적화", id="optimize_db")
                        yield Button("🔧 스키마 업그레이드", id="upgrade_schema")
                        yield Button("💾 백업 생성", id="create_backup")
    
    def on_mount(self) -> None:
        """화면 마운트 시"""
        self.current_filter = "all"
        self.search_query = ""
        self.load_history()
        self.load_statistics()
    
    def load_history(self) -> None:
        """히스토리 데이터 로드"""
        table = self.query_one("#history_table", DataTable)
        table.clear(columns=True)
        table.add_columns(
            "ID", "제목", "URL", "엔진", "상태", 
            "생성일", "완료일", "파일 크기"
        )
        
        # 페이지네이션 적용 (100개씩)
        jobs = self.db_manager.get_jobs_filtered(
            search=self.search_query,
            status_filter=self.current_filter,
            limit=100
        )
        
        for job in jobs:
            table.add_row(
                str(job.get("id", "")),
                job.get("title", "")[:50] + "..." if len(job.get("title", "")) > 50 else job.get("title", ""),
                job.get("url", "")[:30] + "..." if len(job.get("url", "")) > 30 else job.get("url", ""),
                job.get("engine", ""),
                job.get("status", ""),
                job.get("created_at", ""),
                job.get("completed_at", ""),
                self.format_file_size(job.get("file_size", 0))
            )
    
    def load_statistics(self) -> None:
        """통계 데이터 로드"""
        stats_widget = self.query_one("#statistics", StatisticsWidget)
        stats_data = self.db_manager.get_statistics()
        stats_widget.update_data(stats_data)
    
    @on(Button.Pressed, "#search_btn")
    def search_jobs(self) -> None:
        """작업 검색"""
        self.search_query = self.query_one("#search_input", Input).value.strip()
        self.load_history()
    
    @on(Button.Pressed, ".filter-btn")
    def filter_jobs(self, event: Button.Pressed) -> None:
        """필터 적용"""
        # 이전 활성 필터 제거
        for btn in self.query(".filter-btn"):
            btn.remove_class("active")
        
        # 새 필터 활성화
        event.button.add_class("active")
        
        filter_map = {
            "filter_all": "all",
            "filter_success": "completed",
            "filter_failed": "failed",
            "filter_running": "running"
        }
        
        self.current_filter = filter_map.get(event.button.id, "all")
        self.load_history()
    
    @on(Button.Pressed, "#export_btn")
    def export_data(self) -> None:
        """데이터 내보내기"""
        try:
            export_path = self.db_manager.export_to_csv(
                search=self.search_query,
                status_filter=self.current_filter
            )
            self.show_success(f"데이터가 {export_path}에 내보내졌습니다.")
        except Exception as e:
            self.show_error(f"내보내기 실패: {str(e)}")
    
    @on(Button.Pressed, "#cleanup_old")
    def cleanup_old_jobs(self) -> None:
        """오래된 작업 정리"""
        try:
            count = self.db_manager.cleanup_old_jobs(days=30)
            self.show_success(f"{count}개의 오래된 작업을 정리했습니다.")
            self.load_history()
            self.load_statistics()
        except Exception as e:
            self.show_error(f"정리 실패: {str(e)}")
    
    def format_file_size(self, size_bytes: int) -> str:
        """파일 크기 포맷팅"""
        if size_bytes == 0:
            return "0B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.1f}TB"
    
    def refresh_data(self) -> None:
        """데이터 새로고침"""
        self.load_history()
        self.load_statistics()
```

## Phase 3: 전사 통합

### 3.1 전사 작업 화면

```python
# src/tui/screens/transcribe.py
"""전사 작업 화면"""

from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Button, Static, Input, RadioSet, RadioButton, Checkbox, Log
from textual.app import ComposeResult
from textual import on, work

from .base import BaseScreen
from ..widgets.progress import TranscriptionProgressWidget


class TranscribeScreen(BaseScreen):
    """전사 작업 화면"""
    
    def compose(self) -> ComposeResult:
        """UI 구성"""
        with Vertical(classes="transcribe-screen"):
            yield Static("🎬 새 전사 작업", classes="screen-title")
            
            with Container(classes="form-container"):
                # URL 입력
                with Container(classes="input-group"):
                    yield Static("📺 YouTube URL")
                    yield Input(
                        placeholder="https://www.youtube.com/watch?v=...",
                        id="url_input"
                    )
                
                # 엔진 선택
                with Container(classes="input-group"):
                    yield Static("🔧 전사 엔진")
                    with RadioSet(id="engine_select"):
                        yield RadioButton("GPT-4o-transcribe (고품질)", value="gpt-4o-transcribe")
                        yield RadioButton(
                            "GPT-4o-mini-transcribe (기본)", 
                            value="gpt-4o-mini-transcribe", 
                            checked=True
                        )
                        yield RadioButton("Whisper API", value="whisper-api")
                        yield RadioButton("Whisper.cpp (로컬)", value="whisper-cpp")
                        yield RadioButton("YouTube Transcript API", value="youtube-transcript-api")
                
                # 옵션 선택
                with Container(classes="input-group"):
                    yield Static("⚙️ 옵션")
                    with Container(classes="checkboxes"):
                        yield Checkbox("요약 생성", id="summary_check", value=True)
                        yield Checkbox("상세 요약", id="verbose_check")
                        yield Checkbox("한국어 번역", id="translate_check")
                        yield Checkbox("SRT 자막 생성", id="srt_check")
                        yield Checkbox("비디오 다운로드", id="video_check")
                        yield Checkbox("오디오 보관", id="audio_check")
                        yield Checkbox("타임스탬프 포함", id="timestamp_check")
                        yield Checkbox("실시간 스트리밍", id="stream_check", value=True)
                
                # 실행 버튼
                with Horizontal(classes="action-buttons"):
                    yield Button("🚀 전사 시작", id="start_btn", variant="primary")
                    yield Button("⏹️ 중지", id="stop_btn", variant="error", disabled=True)
                    yield Button("🔄 재시작", id="restart_btn", disabled=True)
            
            # 진행률 표시
            yield TranscriptionProgressWidget(id="progress_widget")
            
            # 로그 출력
            yield Log(id="transcription_log", classes="log-output")
    
    @on(Button.Pressed, "#start_btn")
    def start_transcription(self) -> None:
        """전사 작업 시작"""
        url = self.query_one("#url_input", Input).value.strip()
        if not url:
            self.show_error("YouTube URL을 입력해주세요.")
            return
        
        if not self.validate_youtube_url(url):
            self.show_error("유효한 YouTube URL이 아닙니다.")
            return
        
        # 설정 수집
        config = self.collect_transcription_config()
        
        # UI 상태 변경
        self.toggle_transcription_ui(running=True)
        
        # 백그라운드에서 전사 실행
        self.run_transcription(url, config)
    
    def collect_transcription_config(self) -> dict:
        """전사 설정 수집"""
        engine = self.query_one("#engine_select", RadioSet).pressed_button.value
        
        return {
            "engine": engine,
            "summary": self.query_one("#summary_check", Checkbox).value,
            "verbose": self.query_one("#verbose_check", Checkbox).value,
            "translate": self.query_one("#translate_check", Checkbox).value,
            "srt": self.query_one("#srt_check", Checkbox).value,
            "video": self.query_one("#video_check", Checkbox).value,
            "audio": self.query_one("#audio_check", Checkbox).value,
            "timestamp": self.query_one("#timestamp_check", Checkbox).value,
            "stream": self.query_one("#stream_check", Checkbox).value,
        }
    
    @work(exclusive=True)
    async def run_transcription(self, url: str, config: dict) -> None:
        """비동기 전사 실행"""
        log = self.query_one("#transcription_log", Log)
        progress = self.query_one("#progress_widget", TranscriptionProgressWidget)
        
        try:
            log.write("🚀 전사 작업을 시작합니다...")
            progress.start_progress()
            
            # 여기서 기존 CLI 로직과 통합
            from ...cli import process_video
            
            result = await process_video(
                url=url,
                config=config,
                progress_callback=self.update_progress,
                log_callback=self.log_message
            )
            
            if result:
                log.write("✅ 전사가 완료되었습니다!")
                self.show_success("전사 작업이 성공적으로 완료되었습니다.")
            else:
                log.write("❌ 전사가 실패했습니다.")
                self.show_error("전사 작업에 실패했습니다.")
                
        except Exception as e:
            log.write(f"❌ 오류 발생: {str(e)}")
            self.show_error(f"전사 중 오류: {str(e)}")
        
        finally:
            self.toggle_transcription_ui(running=False)
            progress.complete_progress()
    
    def update_progress(self, step: str, percent: float, eta: str = "") -> None:
        """진행률 업데이트"""
        progress = self.query_one("#progress_widget", TranscriptionProgressWidget)
        progress.update(step, percent, eta)
    
    def log_message(self, message: str) -> None:
        """로그 메시지 출력"""
        log = self.query_one("#transcription_log", Log)
        log.write(message)
    
    def toggle_transcription_ui(self, running: bool) -> None:
        """전사 실행 상태에 따른 UI 토글"""
        self.query_one("#start_btn").disabled = running
        self.query_one("#stop_btn").disabled = not running
        self.query_one("#url_input").disabled = running
        self.query_one("#engine_select").disabled = running
    
    def validate_youtube_url(self, url: str) -> bool:
        """YouTube URL 유효성 검증"""
        youtube_patterns = [
            r'youtube\.com/watch\?v=',
            r'youtu\.be/',
            r'youtube\.com/playlist\?list=',
        ]
        
        import re
        for pattern in youtube_patterns:
            if re.search(pattern, url):
                return True
        return False
```

## Phase 4: 유틸리티 및 위젯

### 4.1 설정 관리자

```python
# src/tui/utils/config_manager.py
"""설정 관리자"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

from ...config import Config


class ConfigManager:
    """TUI 설정 관리자"""
    
    def __init__(self):
        self.config_file = Config.BASE_PATH / "tui_config.json"
        self.env_file = Path(".env")
    
    def get_api_keys(self) -> List[Dict[str, Any]]:
        """저장된 API 키 목록 조회"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("api_keys", [])
            return []
        except Exception:
            return []
    
    def save_api_key(self, name: str, value: str) -> bool:
        """API 키 저장"""
        try:
            # .env 파일에 저장
            self.update_env_file(name.upper().replace(" ", "_"), value)
            
            # 설정 파일에 메타데이터 저장
            config_data = self.load_config_file()
            api_keys = config_data.get("api_keys", [])
            
            # 기존 키 업데이트 또는 새 키 추가
            key_updated = False
            for key_info in api_keys:
                if key_info.get("name") == name:
                    key_info.update({
                        "value": value,
                        "updated_at": datetime.now().isoformat(),
                        "status": "미검증"
                    })
                    key_updated = True
                    break
            
            if not key_updated:
                api_keys.append({
                    "name": name,
                    "value": value,
                    "created_at": datetime.now().isoformat(),
                    "status": "미검증"
                })
            
            config_data["api_keys"] = api_keys
            self.save_config_file(config_data)
            return True
            
        except Exception:
            return False
    
    async def validate_api_key_async(self, api_key: str) -> bool:
        """비동기 API 키 검증"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            
            # 간단한 API 호출로 키 유효성 검증
            await client.models.list()
            return True
            
        except Exception:
            return False
    
    def update_env_file(self, key: str, value: str) -> None:
        """환경 변수 파일 업데이트"""
        lines = []
        key_found = False
        
        if self.env_file.exists():
            with open(self.env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # 기존 키 업데이트
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                key_found = True
                break
        
        # 새 키 추가
        if not key_found:
            lines.append(f"{key}={value}\n")
        
        # 파일 저장
        with open(self.env_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    def load_config_file(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}
    
    def save_config_file(self, data: Dict[str, Any]) -> None:
        """설정 파일 저장"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
```

## 테마 및 스타일링

### 4.2 CSS 테마 파일

```css
/* src/tui/themes/dark.tcss */

/* 전역 스타일 */
Screen {
    background: #1e1e2e;
    color: #cdd6f4;
}

.title {
    text-style: bold;
    color: #89b4fa;
    text-align: center;
    margin: 1;
}

.subtitle {
    color: #a6adc8;
    text-align: center;
    margin-bottom: 1;
}

.screen-title {
    text-style: bold;
    color: #f5c2e7;
    margin: 1;
    dock: top;
}

/* 메인 메뉴 */
.main-menu {
    align: center middle;
    margin: 2;
}

.menu-buttons {
    width: 40;
    height: auto;
    margin: 1;
}

.menu-button {
    width: 100%;
    margin: 0 0 1 0;
    background: #313244;
    color: #f5f5f5;
    border: solid #89b4fa;
}

.menu-button:hover {
    background: #89b4fa;
    color: #1e1e2e;
}

.quit-button {
    border: solid #f38ba8;
    color: #f38ba8;
}

.quit-button:hover {
    background: #f38ba8;
    color: #1e1e2e;
}

/* 폼 스타일 */
.form-container {
    margin: 1;
    padding: 1;
    border: solid #6c7086;
}

.input-group {
    margin: 0 0 1 0;
}

.checkboxes {
    layout: grid;
    grid-size: 2 4;
    grid-gutter: 1;
    margin: 1 0;
}

/* 테이블 스타일 */
DataTable {
    background: #181825;
    color: #cdd6f4;
}

DataTable > .datatable--header {
    background: #313244;
    color: #f5c2e7;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: #45475a;
}

/* 버튼 변형 */
Button.primary {
    background: #a6e3a1;
    color: #1e1e2e;
    border: solid #a6e3a1;
}

Button.error {
    background: #f38ba8;
    color: #1e1e2e;
    border: solid #f38ba8;
}

Button.success {
    background: #a6e3a1;
    color: #1e1e2e;
    border: solid #a6e3a1;
}

/* 진행률 바 */
.progress-bar {
    height: 3;
    margin: 1 0;
}

ProgressBar > .bar--bar {
    color: #a6e3a1;
}

ProgressBar > .bar--percentage {
    color: #f5c2e7;
}

/* 로그 출력 */
.log-output {
    height: 20;
    border: solid #6c7086;
    margin: 1 0;
}

Log {
    background: #181825;
    color: #cdd6f4;
}

/* 탭 */
TabbedContent {
    margin: 1;
}

Tab {
    background: #313244;
    color: #a6adc8;
}

Tab.-active {
    background: #89b4fa;
    color: #1e1e2e;
}

/* 필터 버튼 */
.filter-btn {
    margin: 0 1 0 0;
    background: #313244;
    color: #a6adc8;
}

.filter-btn.active {
    background: #89b4fa;
    color: #1e1e2e;
}
```

## 실행 및 테스트

### 4.3 메인 진입점 생성

```python
# tui.py (프로젝트 루트)
#!/usr/bin/env python3
"""
Open-Scribe TUI 진입점
"""

import sys
from pathlib import Path

# src 경로 추가
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.tui.app import OpenScribeTUI

if __name__ == "__main__":
    app = OpenScribeTUI()
    app.run()
```

### 4.4 실행 방법

```bash
# 직접 실행
python tui.py

# 또는 scribe 명령어에 --tui 옵션 추가 (scribe.zsh 수정 필요)
scribe --tui

# 개발 모드로 실행 (CSS 자동 재로드)
textual run --dev tui:OpenScribeTUI
```

### 4.5 테스트 방법

```bash
# 개발 도구를 사용한 디버깅
textual console

# 스크린샷 생성
textual run tui:OpenScribeTUI --screenshot screenshot.svg

# CSS 검증
textual check src/tui/themes/dark.tcss
```

이제 단계별로 구현해보시겠습니까?