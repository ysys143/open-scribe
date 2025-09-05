# TUI 코드 템플릿 및 스니펫

## 개요

이 문서는 Open-Scribe TUI 개발 시 재사용 가능한 코드 패턴, 템플릿, 스니펫을 제공합니다. 일관성 있고 효율적인 개발을 위해 활용하세요.

## 화면(Screen) 템플릿

### 1. 기본 화면 템플릿

```python
"""[화면명] 화면"""

from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Static, Input, DataTable
from textual.app import ComposeResult
from textual import on

from .base import BaseScreen
from ..utils.config_manager import ConfigManager
from ..utils.db_manager import DatabaseManager


class [ClassName]Screen(BaseScreen):
    """[화면 설명]"""
    
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager()
        # 상태 변수 초기화
        self.current_data = []
    
    def compose(self) -> ComposeResult:
        """UI 구성"""
        with Vertical(classes="[screen-class]"):
            yield Static("🎯 [화면 제목]", classes="screen-title")
            
            # 액션 바
            with Horizontal(classes="action-bar"):
                yield Button("➕ 추가", id="add_btn", variant="primary")
                yield Button("✏️ 편집", id="edit_btn")
                yield Button("🗑️ 삭제", id="delete_btn", variant="error")
                yield Button("🔄 새로고침", id="refresh_btn")
            
            # 메인 콘텐츠
            yield DataTable(id="main_table", classes="main-table")
            
            # 폼 영역 (필요시)
            with Vertical(classes="form-container", id="form_container"):
                yield Static("폼 제목")
                yield Input(placeholder="입력 힌트", id="input_field")
                with Horizontal():
                    yield Button("💾 저장", id="save_btn", variant="success")
                    yield Button("❌ 취소", id="cancel_btn")
    
    def on_mount(self) -> None:
        """화면 마운트 시 초기화"""
        self.load_data()
        self.hide_form()
    
    def load_data(self) -> None:
        """데이터 로드"""
        try:
            # 데이터 로드 로직
            self.current_data = []  # 실제 데이터 로드
            self.update_table()
        except Exception as e:
            self.show_error(f"데이터 로드 실패: {str(e)}")
    
    def update_table(self) -> None:
        """테이블 업데이트"""
        table = self.query_one("#main_table", DataTable)
        table.clear(columns=True)
        table.add_columns("ID", "이름", "상태", "날짜")
        
        for item in self.current_data:
            table.add_row(
                str(item.get("id", "")),
                item.get("name", ""),
                item.get("status", ""),
                item.get("date", "")
            )
    
    @on(Button.Pressed, "#add_btn")
    def show_add_form(self) -> None:
        """추가 폼 표시"""
        self.clear_form()
        self.show_form()
        self.query_one("#input_field").focus()
    
    @on(Button.Pressed, "#save_btn")
    def save_data(self) -> None:
        """데이터 저장"""
        try:
            # 입력 검증
            input_value = self.query_one("#input_field", Input).value.strip()
            if not input_value:
                self.show_error("필수 입력 항목이 누락되었습니다.")
                return
            
            # 저장 로직
            success = self.perform_save(input_value)
            if success:
                self.show_success("저장되었습니다.")
                self.hide_form()
                self.load_data()
            else:
                self.show_error("저장에 실패했습니다.")
                
        except Exception as e:
            self.show_error(f"저장 중 오류: {str(e)}")
    
    @on(Button.Pressed, "#cancel_btn")
    def cancel_form(self) -> None:
        """폼 취소"""
        self.hide_form()
        self.clear_form()
    
    @on(Button.Pressed, "#refresh_btn")
    def refresh_data(self) -> None:
        """데이터 새로고침"""
        self.load_data()
        self.show_success("새로고침 완료")
    
    def perform_save(self, value: str) -> bool:
        """실제 저장 수행 (하위 클래스에서 구현)"""
        # 실제 저장 로직 구현
        return True
    
    def show_form(self) -> None:
        """폼 표시"""
        self.query_one("#form_container").display = True
    
    def hide_form(self) -> None:
        """폼 숨기기"""
        self.query_one("#form_container").display = False
    
    def clear_form(self) -> None:
        """폼 초기화"""
        self.query_one("#input_field", Input).value = ""
```

### 2. 탭 기반 화면 템플릿

```python
"""탭 기반 화면 템플릿"""

from textual.containers import Vertical
from textual.widgets import TabbedContent, TabPane, Static
from textual.app import ComposeResult

from .base import BaseScreen


class TabbedScreen(BaseScreen):
    """탭 기반 화면"""
    
    def compose(self) -> ComposeResult:
        """UI 구성"""
        with Vertical(classes="tabbed-screen"):
            yield Static("📊 탭 화면 제목", classes="screen-title")
            
            with TabbedContent():
                with TabPane("첫 번째 탭", id="tab1"):
                    yield Static("첫 번째 탭 내용")
                    # 탭1 컨텐츠 구현
                
                with TabPane("두 번째 탭", id="tab2"):
                    yield Static("두 번째 탭 내용")
                    # 탭2 컨텐츠 구현
                
                with TabPane("세 번째 탭", id="tab3"):
                    yield Static("세 번째 탭 내용")
                    # 탭3 컨텐츠 구현
    
    def on_mount(self) -> None:
        """마운트 시 초기화"""
        self.load_tab1_data()
    
    def on_tabbed_content_tab_activated(self, event) -> None:
        """탭 활성화 시"""
        if event.tab.id == "tab1":
            self.load_tab1_data()
        elif event.tab.id == "tab2":
            self.load_tab2_data()
        elif event.tab.id == "tab3":
            self.load_tab3_data()
    
    def load_tab1_data(self) -> None:
        """탭1 데이터 로드"""
        pass
    
    def load_tab2_data(self) -> None:
        """탭2 데이터 로드"""
        pass
    
    def load_tab3_data(self) -> None:
        """탭3 데이터 로드"""
        pass
```

### 3. 폼 중심 화면 템플릿

```python
"""폼 중심 화면 템플릿"""

from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Static, Input, Checkbox, RadioSet, RadioButton, Select
from textual.app import ComposeResult
from textual import on

from .base import BaseScreen


class FormScreen(BaseScreen):
    """폼 중심 화면"""
    
    def compose(self) -> ComposeResult:
        """UI 구성"""
        with Vertical(classes="form-screen"):
            yield Static("📝 폼 제목", classes="screen-title")
            
            with Vertical(classes="form-container"):
                # 텍스트 입력
                with Vertical(classes="input-group"):
                    yield Static("📝 텍스트 입력")
                    yield Input(placeholder="텍스트를 입력하세요", id="text_input")
                
                # 선택 박스
                with Vertical(classes="input-group"):
                    yield Static("📋 선택 옵션")
                    yield Select([("옵션1", "option1"), ("옵션2", "option2")], id="select_input")
                
                # 라디오 버튼
                with Vertical(classes="input-group"):
                    yield Static("🔘 단일 선택")
                    with RadioSet(id="radio_input"):
                        yield RadioButton("선택지 1", value="choice1")
                        yield RadioButton("선택지 2", value="choice2", checked=True)
                        yield RadioButton("선택지 3", value="choice3")
                
                # 체크박스들
                with Vertical(classes="input-group"):
                    yield Static("☑️ 다중 선택")
                    with Vertical(classes="checkboxes"):
                        yield Checkbox("옵션 A", id="check_a", value=True)
                        yield Checkbox("옵션 B", id="check_b")
                        yield Checkbox("옵션 C", id="check_c")
                
                # 액션 버튼
                with Horizontal(classes="action-buttons"):
                    yield Button("💾 저장", id="save_btn", variant="primary")
                    yield Button("🔄 초기화", id="reset_btn")
                    yield Button("❌ 취소", id="cancel_btn")
    
    def on_mount(self) -> None:
        """마운트 시 초기화"""
        self.load_form_data()
    
    def load_form_data(self) -> None:
        """폼 데이터 로드"""
        # 기존 설정값 로드 로직
        pass
    
    @on(Button.Pressed, "#save_btn")
    def save_form(self) -> None:
        """폼 저장"""
        try:
            form_data = self.collect_form_data()
            
            # 유효성 검증
            if not self.validate_form_data(form_data):
                return
            
            # 저장 수행
            if self.perform_save(form_data):
                self.show_success("설정이 저장되었습니다.")
            else:
                self.show_error("저장에 실패했습니다.")
                
        except Exception as e:
            self.show_error(f"저장 중 오류: {str(e)}")
    
    def collect_form_data(self) -> dict:
        """폼 데이터 수집"""
        return {
            "text_value": self.query_one("#text_input", Input).value,
            "select_value": self.query_one("#select_input", Select).value,
            "radio_value": self.query_one("#radio_input", RadioSet).pressed_button.value,
            "check_a": self.query_one("#check_a", Checkbox).value,
            "check_b": self.query_one("#check_b", Checkbox).value,
            "check_c": self.query_one("#check_c", Checkbox).value,
        }
    
    def validate_form_data(self, data: dict) -> bool:
        """폼 데이터 유효성 검증"""
        if not data["text_value"].strip():
            self.show_error("텍스트 입력은 필수입니다.")
            return False
        return True
    
    def perform_save(self, data: dict) -> bool:
        """실제 저장 수행"""
        # 저장 로직 구현
        return True
    
    @on(Button.Pressed, "#reset_btn")
    def reset_form(self) -> None:
        """폼 초기화"""
        self.query_one("#text_input", Input).value = ""
        self.query_one("#check_a", Checkbox).value = False
        self.query_one("#check_b", Checkbox).value = False
        self.query_one("#check_c", Checkbox).value = False
        # RadioSet 초기화는 첫 번째 옵션으로
        self.show_success("폼이 초기화되었습니다.")
```

---

## 위젯(Widget) 템플릿

### 1. 사용자 정의 위젯 템플릿

```python
"""사용자 정의 위젯 템플릿"""

from textual.widget import Widget
from textual.reactive import reactive
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, ProgressBar
from textual.app import ComposeResult
from typing import Any


class CustomWidget(Widget):
    """사용자 정의 위젯"""
    
    # 반응형 속성
    data = reactive(None)
    progress = reactive(0.0)
    status = reactive("idle")
    
    def __init__(self, title: str = "Custom Widget", **kwargs):
        super().__init__(**kwargs)
        self.title = title
    
    def compose(self) -> ComposeResult:
        """위젯 구성"""
        with Vertical(classes="custom-widget"):
            yield Static(self.title, classes="widget-title")
            yield Static(id="status_text", classes="status-text")
            yield ProgressBar(id="progress_bar", classes="widget-progress")
            with Horizontal(classes="widget-content"):
                yield Static(id="content_area", classes="content-area")
    
    def watch_data(self, new_data: Any) -> None:
        """데이터 변경 감지"""
        if new_data:
            self.update_content()
    
    def watch_progress(self, new_progress: float) -> None:
        """진행률 변경 감지"""
        progress_bar = self.query_one("#progress_bar", ProgressBar)
        progress_bar.progress = new_progress
    
    def watch_status(self, new_status: str) -> None:
        """상태 변경 감지"""
        status_text = self.query_one("#status_text", Static)
        status_map = {
            "idle": "⏸️ 대기 중",
            "running": "🔄 실행 중",
            "completed": "✅ 완료",
            "error": "❌ 오류"
        }
        status_text.update(status_map.get(new_status, new_status))
    
    def update_content(self) -> None:
        """콘텐츠 업데이트"""
        content_area = self.query_one("#content_area", Static)
        if self.data:
            content_area.update(str(self.data))
        else:
            content_area.update("데이터 없음")
    
    def set_data(self, data: Any) -> None:
        """데이터 설정"""
        self.data = data
    
    def update_progress(self, progress: float, status: str = None) -> None:
        """진행률 및 상태 업데이트"""
        self.progress = max(0.0, min(100.0, progress))
        if status:
            self.status = status
```

### 2. 실시간 모니터링 위젯

```python
"""실시간 모니터링 위젯"""

from textual.widget import Widget
from textual.reactive import reactive
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, ProgressBar
from textual.app import ComposeResult
import psutil
import asyncio


class SystemMonitorWidget(Widget):
    """시스템 리소스 모니터링 위젯"""
    
    cpu_usage = reactive(0.0)
    memory_usage = reactive(0.0)
    disk_usage = reactive(0.0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.monitoring = False
    
    def compose(self) -> ComposeResult:
        """위젯 구성"""
        with Vertical(classes="system-monitor"):
            yield Static("💻 시스템 모니터", classes="monitor-title")
            
            # CPU
            with Horizontal(classes="metric-row"):
                yield Static("CPU:", classes="metric-label")
                yield ProgressBar(id="cpu_bar", classes="metric-bar")
                yield Static(id="cpu_text", classes="metric-text")
            
            # 메모리
            with Horizontal(classes="metric-row"):
                yield Static("Memory:", classes="metric-label")
                yield ProgressBar(id="memory_bar", classes="metric-bar")
                yield Static(id="memory_text", classes="metric-text")
            
            # 디스크
            with Horizontal(classes="metric-row"):
                yield Static("Disk:", classes="metric-label")
                yield ProgressBar(id="disk_bar", classes="metric-bar")
                yield Static(id="disk_text", classes="metric-text")
    
    def on_mount(self) -> None:
        """마운트 시 모니터링 시작"""
        self.start_monitoring()
    
    def start_monitoring(self) -> None:
        """모니터링 시작"""
        if not self.monitoring:
            self.monitoring = True
            self.set_timer(1.0, self.update_metrics)
    
    def stop_monitoring(self) -> None:
        """모니터링 중지"""
        self.monitoring = False
    
    async def update_metrics(self) -> None:
        """메트릭 업데이트"""
        if not self.monitoring:
            return
        
        try:
            # 시스템 메트릭 수집
            self.cpu_usage = psutil.cpu_percent(interval=None)
            
            memory = psutil.virtual_memory()
            self.memory_usage = memory.percent
            
            disk = psutil.disk_usage('/')
            self.disk_usage = (disk.used / disk.total) * 100
            
            # 다음 업데이트 스케줄링
            if self.monitoring:
                self.set_timer(1.0, self.update_metrics)
                
        except Exception:
            # 에러 발생 시 모니터링 중지
            self.stop_monitoring()
    
    def watch_cpu_usage(self, value: float) -> None:
        """CPU 사용률 업데이트"""
        self.query_one("#cpu_bar", ProgressBar).progress = value
        self.query_one("#cpu_text", Static).update(f"{value:.1f}%")
    
    def watch_memory_usage(self, value: float) -> None:
        """메모리 사용률 업데이트"""
        self.query_one("#memory_bar", ProgressBar).progress = value
        self.query_one("#memory_text", Static).update(f"{value:.1f}%")
    
    def watch_disk_usage(self, value: float) -> None:
        """디스크 사용률 업데이트"""
        self.query_one("#disk_bar", ProgressBar).progress = value
        self.query_one("#disk_text", Static).update(f"{value:.1f}%")
```

### 3. 통계 차트 위젯

```python
"""통계 차트 위젯"""

from textual.widget import Widget
from textual.reactive import reactive
from textual.containers import Vertical, Horizontal
from textual.widgets import Static
from textual.app import ComposeResult
from typing import Dict, List, Any


class StatisticsChartWidget(Widget):
    """통계 차트 위젯"""
    
    data = reactive({})
    
    def __init__(self, title: str = "통계", **kwargs):
        super().__init__(**kwargs)
        self.title = title
    
    def compose(self) -> ComposeResult:
        """위젯 구성"""
        with Vertical(classes="statistics-chart"):
            yield Static(self.title, classes="chart-title")
            yield Static(id="chart_content", classes="chart-content")
            yield Static(id="legend", classes="chart-legend")
    
    def watch_data(self, new_data: Dict[str, Any]) -> None:
        """데이터 변경 시 차트 업데이트"""
        if new_data:
            self.update_chart()
    
    def update_chart(self) -> None:
        """차트 업데이트"""
        if not self.data:
            return
        
        chart_content = self.query_one("#chart_content", Static)
        legend = self.query_one("#legend", Static)
        
        # 간단한 수평 바 차트 생성
        chart_lines = []
        legend_lines = []
        
        # 데이터 정규화
        max_value = max(self.data.values()) if self.data.values() else 1
        
        for label, value in self.data.items():
            # 바 길이 계산 (최대 20칸)
            bar_length = int((value / max_value) * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            
            # 퍼센트 계산
            percentage = (value / sum(self.data.values())) * 100 if sum(self.data.values()) > 0 else 0
            
            chart_lines.append(f"{label:<15} {bar} {percentage:5.1f}%")
            legend_lines.append(f"• {label}: {value}")
        
        chart_content.update("\n".join(chart_lines))
        legend.update("\n".join(legend_lines))
    
    def set_data(self, data: Dict[str, Any]) -> None:
        """데이터 설정"""
        self.data = data
```

---

## 유틸리티 템플릿

### 1. 설정 관리자 템플릿

```python
"""설정 관리자 템플릿"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class BaseConfigManager:
    """기본 설정 관리자"""
    
    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.config_cache = {}
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """설정 로드"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config_cache = json.load(f)
            else:
                self.config_cache = self.get_default_config()
        except Exception as e:
            print(f"설정 로드 실패: {e}")
            self.config_cache = self.get_default_config()
        
        return self.config_cache
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """설정 저장"""
        try:
            data_to_save = config or self.config_cache
            
            # 백업 생성
            self.create_backup()
            
            # 메타데이터 추가
            data_to_save["_metadata"] = {
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            # 디렉토리 생성
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 파일 저장
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
            
            self.config_cache = data_to_save
            return True
            
        except Exception as e:
            print(f"설정 저장 실패: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """설정값 조회"""
        return self.config_cache.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """설정값 설정"""
        self.config_cache[key] = value
    
    def update(self, updates: Dict[str, Any]) -> None:
        """설정 일괄 업데이트"""
        self.config_cache.update(updates)
    
    def reset_to_defaults(self) -> None:
        """기본값으로 리셋"""
        self.config_cache = self.get_default_config()
    
    def create_backup(self) -> None:
        """설정 백업 생성"""
        if self.config_file.exists():
            backup_file = self.config_file.with_suffix(
                f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            try:
                import shutil
                shutil.copy2(self.config_file, backup_file)
            except Exception:
                pass  # 백업 실패는 무시
    
    def get_default_config(self) -> Dict[str, Any]:
        """기본 설정 반환 (하위 클래스에서 구현)"""
        return {}
```

### 2. 데이터베이스 접근 템플릿

```python
"""데이터베이스 접근 템플릿"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager


class DatabaseAccessTemplate:
    """데이터베이스 접근 템플릿"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self) -> None:
        """데이터베이스 초기화"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self.get_connection() as conn:
            self.create_tables(conn)
    
    @contextmanager
    def get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 반환
        try:
            yield conn
        finally:
            conn.close()
    
    def create_tables(self, conn: sqlite3.Connection) -> None:
        """테이블 생성 (하위 클래스에서 구현)"""
        pass
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """쿼리 실행 (SELECT용)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """업데이트 쿼리 실행"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """배치 업데이트"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount
    
    def get_paginated(self, base_query: str, params: tuple = (), 
                     page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """페이지네이션 지원 조회"""
        offset = (page - 1) * per_page
        
        # 전체 개수 조회
        count_query = f"SELECT COUNT(*) as total FROM ({base_query})"
        count_result = self.execute_query(count_query, params)
        total = count_result[0]["total"]
        
        # 페이지 데이터 조회
        paginated_query = f"{base_query} LIMIT {per_page} OFFSET {offset}"
        data = self.execute_query(paginated_query, params)
        
        return {
            "data": data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
```

### 3. 비동기 작업 템플릿

```python
"""비동기 작업 템플릿"""

from textual import work
from typing import Callable, Any, Optional
import asyncio


class AsyncTaskTemplate:
    """비동기 작업 템플릿"""
    
    def __init__(self, progress_callback: Optional[Callable] = None,
                 log_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.cancelled = False
    
    def log(self, message: str) -> None:
        """로그 출력"""
        if self.log_callback:
            self.log_callback(message)
    
    def update_progress(self, step: str, percent: float, eta: str = "") -> None:
        """진행률 업데이트"""
        if self.progress_callback:
            self.progress_callback(step, percent, eta)
    
    def cancel(self) -> None:
        """작업 취소"""
        self.cancelled = True
    
    @work(exclusive=True)
    async def run_task(self, *args, **kwargs) -> Any:
        """비동기 작업 실행 템플릿"""
        try:
            self.log("작업을 시작합니다...")
            self.update_progress("시작", 0.0)
            
            result = await self.perform_task(*args, **kwargs)
            
            if not self.cancelled:
                self.log("작업이 완료되었습니다.")
                self.update_progress("완료", 100.0)
                return result
            else:
                self.log("작업이 취소되었습니다.")
                return None
                
        except Exception as e:
            self.log(f"작업 중 오류 발생: {str(e)}")
            self.update_progress("오류", 0.0)
            raise e
    
    async def perform_task(self, *args, **kwargs) -> Any:
        """실제 작업 수행 (하위 클래스에서 구현)"""
        # 예제: 단계별 작업
        steps = ["준비", "처리", "완료"]
        for i, step in enumerate(steps):
            if self.cancelled:
                break
            
            self.log(f"{step} 단계 시작...")
            self.update_progress(step, (i + 1) / len(steps) * 100)
            
            # 실제 작업 수행
            await asyncio.sleep(1)  # 실제 작업으로 교체
            
            self.log(f"{step} 단계 완료")
        
        return "작업 결과"
```

---

## CSS 템플릿

### 1. 기본 컴포넌트 스타일

```css
/* 기본 컴포넌트 스타일 템플릿 */

/* 화면 레이아웃 */
.screen-title {
    text-style: bold;
    color: #f5c2e7;
    margin: 1;
    dock: top;
}

.action-bar {
    height: auto;
    margin: 0 0 1 0;
    align: left middle;
}

.form-container {
    margin: 1;
    padding: 1;
    border: solid #6c7086;
    background: #181825;
}

.input-group {
    margin: 0 0 1 0;
}

/* 테이블 스타일 */
.main-table {
    background: #181825;
    color: #cdd6f4;
    margin: 1 0;
}

.main-table > .datatable--header {
    background: #313244;
    color: #f5c2e7;
    text-style: bold;
}

.main-table > .datatable--cursor {
    background: #45475a;
}

.main-table > .datatable--hover {
    background: #585b70;
}

/* 버튼 스타일 */
Button {
    background: #313244;
    color: #f5f5f5;
    border: solid #89b4fa;
    margin: 0 1 0 0;
}

Button:hover {
    background: #89b4fa;
    color: #1e1e2e;
}

Button.primary {
    background: #a6e3a1;
    color: #1e1e2e;
    border: solid #a6e3a1;
}

Button.primary:hover {
    background: #94e2d5;
}

Button.error {
    background: #f38ba8;
    color: #1e1e2e;
    border: solid #f38ba8;
}

Button.error:hover {
    background: #eba0ac;
}

Button.success {
    background: #a6e3a1;
    color: #1e1e2e;
    border: solid #a6e3a1;
}

Button.warning {
    background: #fab387;
    color: #1e1e2e;
    border: solid #fab387;
}

/* 입력 필드 */
Input {
    background: #313244;
    color: #cdd6f4;
    border: solid #6c7086;
}

Input:focus {
    border: solid #89b4fa;
}

/* 체크박스 그리드 */
.checkboxes {
    layout: grid;
    grid-size: 2 4;
    grid-gutter: 1;
    margin: 1 0;
}

/* 진행률 바 */
ProgressBar > .bar--bar {
    color: #a6e3a1;
}

ProgressBar > .bar--percentage {
    color: #f5c2e7;
}

/* 탭 스타일 */
Tab {
    background: #313244;
    color: #a6adc8;
}

Tab.-active {
    background: #89b4fa;
    color: #1e1e2e;
}

/* 로그 출력 */
Log {
    background: #181825;
    color: #cdd6f4;
    border: solid #6c7086;
}
```

### 2. 반응형 레이아웃 CSS

```css
/* 반응형 레이아웃 CSS */

/* 작은 화면 (< 80 컬럼) */
Screen {
    &.small {
        .action-bar {
            layout: vertical;
        }
        
        .checkboxes {
            grid-size: 1;
        }
        
        .input-group {
            margin: 0 0 2 0;
        }
    }
}

/* 중간 화면 (80-120 컬럼) */
Screen {
    &.medium {
        .main-table {
            max-height: 20;
        }
        
        .form-container {
            max-width: 60;
        }
    }
}

/* 큰 화면 (> 120 컬럼) */
Screen {
    &.large {
        .main-content {
            layout: grid;
            grid-size: 2;
            grid-gutter: 2;
        }
        
        .side-panel {
            dock: right;
            width: 30;
        }
    }
}
```

---

## 테스트 템플릿

### 1. 단위 테스트 템플릿

```python
"""단위 테스트 템플릿"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import json

# 테스트할 클래스 import
from src.tui.utils.config_manager import ConfigManager


class TestConfigManager:
    """ConfigManager 테스트"""
    
    @pytest.fixture
    def temp_config_file(self):
        """임시 설정 파일"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {"test_key": "test_value"}
            json.dump(config_data, f)
            yield Path(f.name)
        
        # 정리
        Path(f.name).unlink(missing_ok=True)
    
    @pytest.fixture
    def config_manager(self, temp_config_file):
        """ConfigManager 인스턴스"""
        return ConfigManager(temp_config_file)
    
    def test_load_config(self, config_manager):
        """설정 로드 테스트"""
        config = config_manager.load_config()
        assert "test_key" in config
        assert config["test_key"] == "test_value"
    
    def test_save_config(self, config_manager):
        """설정 저장 테스트"""
        new_config = {"new_key": "new_value"}
        result = config_manager.save_config(new_config)
        
        assert result is True
        assert config_manager.get("new_key") == "new_value"
    
    def test_get_default_value(self, config_manager):
        """기본값 조회 테스트"""
        value = config_manager.get("nonexistent_key", "default")
        assert value == "default"
    
    def test_set_value(self, config_manager):
        """값 설정 테스트"""
        config_manager.set("new_key", "new_value")
        assert config_manager.get("new_key") == "new_value"
    
    @patch('src.tui.utils.config_manager.datetime')
    def test_backup_creation(self, mock_datetime, config_manager):
        """백업 생성 테스트"""
        mock_datetime.now.return_value.strftime.return_value = "20250103_120000"
        
        with patch('shutil.copy2') as mock_copy:
            config_manager.create_backup()
            mock_copy.assert_called_once()
```

### 2. UI 테스트 템플릿

```python
"""UI 테스트 템플릿"""

import pytest
from textual.app import App
from textual.testing import AppPilot

from src.tui.screens.api_keys import ApiKeysScreen


@pytest.fixture
async def api_keys_screen():
    """API 키 화면 테스트 픽스처"""
    app = App()
    screen = ApiKeysScreen()
    async with AppPilot(app) as pilot:
        app.push_screen(screen)
        yield pilot, screen


class TestApiKeysScreen:
    """API 키 화면 테스트"""
    
    async def test_initial_render(self, api_keys_screen):
        """초기 렌더링 테스트"""
        pilot, screen = api_keys_screen
        
        # 제목이 렌더링되는지 확인
        assert pilot.app.query_one(".screen-title").renderable.plain == "🔑 API 키 관리"
        
        # 테이블이 존재하는지 확인
        assert pilot.app.query_one("#keys_table") is not None
    
    async def test_add_key_form(self, api_keys_screen):
        """키 추가 폼 테스트"""
        pilot, screen = api_keys_screen
        
        # 추가 버튼 클릭
        await pilot.click("#add_key")
        
        # 폼이 표시되는지 확인
        form = pilot.app.query_one("#key_form")
        assert form.display
        
        # 입력 필드가 포커스되는지 확인
        name_input = pilot.app.query_one("#key_name")
        assert name_input.has_focus
    
    async def test_key_validation(self, api_keys_screen):
        """키 유효성 검증 테스트"""
        pilot, screen = api_keys_screen
        
        # 빈 폼으로 저장 시도
        await pilot.click("#add_key")
        await pilot.click("#save_key")
        
        # 에러 메시지가 표시되는지 확인 (실제로는 notify 호출 확인)
        # 이 부분은 mock을 사용하여 테스트해야 함
```

이러한 템플릿들을 활용하여 일관성 있고 효율적인 TUI 개발을 진행하세요!