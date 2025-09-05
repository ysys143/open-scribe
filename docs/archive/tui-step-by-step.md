# TUI 단계별 구현 가이드

## 사전 준비

### 환경 설정 체크리스트

```bash
# 1. 가상환경 활성화 확인
source .venv/bin/activate
which python  # /path/to/yt-trans/.venv/bin/python 이어야 함

# 2. 현재 설치된 패키지 확인
uv pip list

# 3. 필요한 패키지 설치
uv pip install textual>=0.47.0 rich>=13.7.0 prompt-toolkit>=3.0.0

# 4. 개발 도구 설치 (선택사항)
uv pip install textual-dev

# 5. requirements.txt 업데이트
echo "textual>=0.47.0" >> requirements.txt
echo "rich>=13.7.0" >> requirements.txt
echo "prompt-toolkit>=3.0.0" >> requirements.txt
```

### 디렉토리 구조 준비

```bash
# TUI 관련 디렉토리 생성
mkdir -p src/tui/{screens,widgets,utils,themes}
touch src/tui/__init__.py
touch src/tui/screens/__init__.py
touch src/tui/widgets/__init__.py
touch src/tui/utils/__init__.py
```

## Phase 1: 기본 프레임워크 (Day 1-3)

### Step 1.1: 프로젝트 구조 설정 (30분)

#### 목표
- TUI 모듈의 기본 구조 생성
- 패키지 초기화 파일 설정

#### 작업 내용

1. **`src/tui/__init__.py` 생성**
```python
"""TUI Package for Open-Scribe"""

from .app import OpenScribeTUI

__all__ = ["OpenScribeTUI"]
__version__ = "1.0.0"
```

2. **기본 테마 파일 생성**
```bash
touch src/tui/themes/dark.tcss
touch src/tui/themes/light.tcss
```

#### 완료 기준
- [x] 모든 디렉토리 생성 완료
- [x] `__init__.py` 파일들 생성
- [x] 패키지 import 테스트 성공

**✅ 2025-09-03 완료**

### Step 1.2: Textual 앱 초기화 (1시간)

#### 목표
- 메인 Textual 애플리케이션 클래스 생성
- 기본 설정 및 바인딩 구현

#### 작업 내용

1. **`src/tui/app.py` 생성**
```python
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
        self.dark = not self.dark
    
    def action_help(self) -> None:
        """도움말 표시"""
        self.notify("F1: 도움말, F2: 테마 변경, Ctrl+R: 새로고침, Ctrl+C: 종료")
    
    def action_refresh(self) -> None:
        """화면 새로고침"""
        if hasattr(self.screen, 'refresh_data'):
            self.screen.refresh_data()


if __name__ == "__main__":
    app = OpenScribeTUI()
    app.run()
```

#### 완료 기준
- [x] 앱 클래스 생성 완료
- [x] 기본 바인딩 설정
- [x] 실행 테스트 성공

**✅ 2025-09-03 완료**

#### 테스트 방법
```bash
python -m src.tui.app
```

### Step 1.3: 기본 화면 클래스 및 메인 메뉴 구현 (2시간)

#### 목표
- 모든 화면의 기본 클래스 생성
- 메인 메뉴 화면 구현

#### 작업 내용

1. **`src/tui/screens/base.py` 생성**
```python
"""기본 화면 클래스"""

from textual.screen import Screen
from textual import events
from typing import Any


class BaseScreen(Screen):
    """모든 화면의 기본 클래스"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
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

2. **`src/tui/screens/main_menu.py` 생성**
```python
"""메인 메뉴 화면"""

from textual.containers import Vertical
from textual.widgets import Button, Static
from textual.app import ComposeResult

from .base import BaseScreen


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
            self.show_error("전사 화면은 Phase 3에서 구현됩니다.")
        elif button_id == "database":
            self.show_error("데이터베이스 화면은 Phase 2에서 구현됩니다.")
        elif button_id == "api_keys":
            self.show_error("API 키 관리는 Phase 2에서 구현됩니다.")
        elif button_id == "settings":
            self.show_error("설정 화면은 Phase 2에서 구현됩니다.")
        elif button_id == "monitor":
            self.show_error("모니터링 화면은 Phase 4에서 구현됩니다.")
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

#### 완료 기준
- [x] BaseScreen 클래스 생성
- [x] MainMenuScreen 구현 완료
- [x] 버튼 클릭 이벤트 처리 구현
- [x] 도움말 기능 구현

**✅ 2025-09-03 완료**

### Step 1.4: 기본 CSS 테마 구현 (1시간)

#### 목표
- 기본 다크 테마 스타일 구현
- UI 요소들의 시각적 개선

#### 작업 내용

1. **`src/tui/themes/dark.tcss` 생성**
```css
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
```

#### 완료 기준
- [x] 기본 CSS 테마 생성 (인라인 CSS로 구현)
- [x] 메인 메뉴 스타일링 완료
- [x] 테마 적용 확인

**✅ 2025-09-03 완료** (인라인 CSS 방식으로 구현)

### Step 1.5: 메인 진입점 생성 (30분)

#### 목표
- TUI 실행을 위한 메인 파일 생성
- 실행 옵션 구현

#### 작업 내용

1. **`tui.py` 생성 (프로젝트 루트)**
```python
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

2. **실행 권한 추가**
```bash
chmod +x tui.py
```

#### 완료 기준
- [x] tui.py 파일 생성
- [x] 실행 권한 설정
- [x] 실행 테스트 성공

**✅ 2025-09-03 완료**

#### Phase 1 최종 테스트
```bash
# 1. 기본 실행 테스트
python tui.py

# 2. 모듈로 실행 테스트
python -m src.tui.app

# 3. 개발 모드 실행 (textual-dev 설치 시)
textual run --dev tui:OpenScribeTUI
```

**Phase 1 완료 시 기대 결과:**
- 메인 메뉴가 있는 TUI 애플리케이션 실행
- 키보드 단축키 동작 확인
- 테마 토글 기능 동작
- 각 메뉴 버튼 클릭 시 "Phase X에서 구현" 메시지 출력

## 🎉 Phase 1 완료 상태 (2025-09-03)

### ✅ 성공적으로 구현된 기능들:

1. **기본 프레임워크**: YouTubeTranscriberTUI 앱 클래스
2. **디렉토리 구조**: `src/tui/` 하위 모듈 구조 완성
3. **메인 메뉴**: 7개 기능 버튼 (전사, DB관리, API키, 설정, 모니터링, 도움말, 종료)
4. **스타일링**: 인라인 CSS로 다크 테마 적용
5. **키보드 단축키**: Ctrl+C, F1, F2, Ctrl+R 동작
6. **진입점**: `python tui.py` 실행 가능

### 🔧 실제 구현 변경사항:

- **CSS 방식**: 외부 파일 대신 인라인 CSS 사용 (경로 문제 해결)
- **메뉴 클래스**: BaseScreen 대신 Widget 상속 사용
- **앱 이름**: OpenScribeTUI → YouTubeTranscriberTUI로 변경

### 📝 다음 단계: Phase 2 준비 완료

---

## Phase 2: 핵심 기능 (Day 4-7)

### Step 2.1: 유틸리티 클래스 구현 (2시간)

#### 목표
- ConfigManager 클래스 구현
- DatabaseManager 클래스 구현

#### 작업 내용

1. **`src/tui/utils/config_manager.py` 생성**
```python
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

2. **`src/tui/utils/db_manager.py` 생성**
```python
"""데이터베이스 관리자"""

from typing import List, Dict, Any, Optional
from ...database import TranscriptionDatabase
from ...config import Config
import csv
from datetime import datetime, timedelta


class DatabaseManager:
    """TUI 데이터베이스 관리자"""
    
    def __init__(self):
        self.db = TranscriptionDatabase(Config.DB_PATH)
    
    def get_jobs_filtered(self, search: str = "", status_filter: str = "all", 
                         limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """필터링된 작업 목록 조회"""
        # 기존 database.py의 메서드를 활용하여 구현
        # 실제 구현에서는 database.py를 확장해야 함
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 데이터 조회"""
        # 총 작업 수, 성공률, 엔진별 사용 현황 등
        pass
    
    def export_to_csv(self, search: str = "", status_filter: str = "all") -> str:
        """CSV 파일로 내보내기"""
        # CSV 내보내기 기능 구현
        pass
    
    def cleanup_old_jobs(self, days: int = 30) -> int:
        """오래된 작업 정리"""
        # 지정된 일수보다 오래된 실패 작업 정리
        pass
```

#### 완료 기준
- [ ] ConfigManager 클래스 구현
- [ ] DatabaseManager 클래스 기본 구조 구현
- [ ] 기본 메서드 스텁 생성

### Step 2.2: API 키 관리 화면 구현 (3시간)

#### 목표
- API 키 CRUD 기능이 있는 화면 구현
- 키 마스킹 및 검증 기능

#### 작업 내용

1. **`src/tui/screens/api_keys.py` 생성**
```python
"""API 키 관리 화면"""

from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Static, Input, DataTable
from textual.app import ComposeResult
from textual import on

from .base import BaseScreen
from ..utils.config_manager import ConfigManager


class ApiKeysScreen(BaseScreen):
    """API 키 관리 화면"""
    
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
    
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
    
    @on(Button.Pressed, "#cancel_key")
    def cancel_form(self) -> None:
        """폼 취소"""
        self.query_one("#key_form").display = False
        self.clear_form()
    
    def clear_form(self) -> None:
        """폼 필드 클리어"""
        self.query_one("#key_name", Input).value = ""
        self.query_one("#key_value", Input).value = ""
    
    def refresh_data(self) -> None:
        """데이터 새로고침"""
        self.load_keys()
```

2. **메인 메뉴에서 API 키 화면 연결**

`src/tui/screens/main_menu.py` 업데이트:
```python
# import 추가
from .api_keys import ApiKeysScreen

# on_button_pressed 메서드 수정
elif button_id == "api_keys":
    self.app.push_screen(ApiKeysScreen())
```

#### 완료 기준
- [ ] API 키 목록 표시
- [ ] 키 추가/편집 폼 구현
- [ ] 키 마스킹 기능
- [ ] .env 파일 연동

### Step 2.3: 데이터베이스 관리 화면 구현 (4시간)

#### 목표
- 전사 히스토리 조회 및 관리
- 검색/필터링 기능
- 기본 통계 표시

#### 작업 내용

1. **`src/tui/screens/database.py` 생성**
```python
"""데이터베이스 관리 화면"""

from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Static, Input, DataTable, TabbedContent, TabPane
from textual.app import ComposeResult
from textual import on

from .base import BaseScreen
from ..utils.db_manager import DatabaseManager


class DatabaseScreen(BaseScreen):
    """데이터베이스 관리 화면"""
    
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.current_filter = "all"
        self.search_query = ""
    
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
                    yield Static("📊 통계 화면은 Phase 4에서 구현됩니다.", classes="placeholder")
    
    def on_mount(self) -> None:
        """화면 마운트 시"""
        self.load_history()
    
    def load_history(self) -> None:
        """히스토리 데이터 로드"""
        table = self.query_one("#history_table", DataTable)
        table.clear(columns=True)
        table.add_columns(
            "ID", "제목", "URL", "엔진", "상태", 
            "생성일", "완료일", "파일 크기"
        )
        
        # 임시 테스트 데이터 (실제 구현에서는 db_manager 사용)
        test_data = [
            ["1", "AI 기술의 미래", "youtu.be/abc123", "gpt-4o-mini", "완료", "2025-01-15", "2025-01-15", "2.3MB"],
            ["2", "Python 기초 강의", "youtu.be/def456", "whisper-api", "실패", "2025-01-14", "-", "-"],
        ]
        
        for row in test_data:
            table.add_row(*row)
    
    @on(Button.Pressed, "#search_btn")
    def search_jobs(self) -> None:
        """작업 검색"""
        self.search_query = self.query_one("#search_input", Input).value.strip()
        self.load_history()
        self.show_success(f"'{self.search_query}' 검색 완료")
    
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
        self.show_success(f"필터 적용: {self.current_filter}")
    
    @on(Button.Pressed, "#refresh_btn")
    def refresh_data(self) -> None:
        """데이터 새로고침"""
        self.load_history()
        self.show_success("데이터가 새로고침되었습니다.")
    
    @on(Button.Pressed, "#export_btn")
    def export_data(self) -> None:
        """데이터 내보내기"""
        # 실제 구현에서는 db_manager.export_to_csv() 사용
        self.show_success("CSV 내보내기는 Phase 3에서 구현됩니다.")
```

2. **메인 메뉴에서 데이터베이스 화면 연결**

#### 완료 기준
- [ ] 데이터베이스 히스토리 조회
- [ ] 검색 기능 구현
- [ ] 필터링 기능 구현
- [ ] 탭 구조 구현

### Step 2.4: 설정 관리 화면 구현 (2시간)

#### 목표
- 기본 설정 관리 화면
- 환경 변수 편집 기능

#### 작업 내용

1. **`src/tui/screens/settings.py` 생성**
2. **설정 폼 구현**
3. **환경 변수 연동**

#### 완료 기준
- [ ] 설정 화면 기본 구조
- [ ] 폼 입력 및 저장
- [ ] 설정 유효성 검증

#### Phase 2 최종 테스트
```bash
# 실행 후 다음 기능 테스트:
# 1. API 키 관리 - 키 추가/조회
# 2. 데이터베이스 관리 - 히스토리 조회/검색
# 3. 설정 - 기본값 편집
python tui.py
```

---

## Phase 3: 전사 통합 (Day 8-12)

### Step 3.1: 전사 작업 화면 UI 구현 (3시간)

#### 목표
- 전사 작업을 위한 대화형 UI
- URL 입력, 엔진 선택, 옵션 설정

### Step 3.2: CLI 모듈과 TUI 통합 (4시간)

#### 목표
- 기존 CLI 로직을 TUI에서 호출
- 비동기 작업 처리

### Step 3.3: 실시간 진행률 표시 (3시간)

#### 목표
- 다운로드/전사 진행률 시각화
- 실시간 상태 업데이트

### Step 3.4: 로그 스트리밍 (2시간)

#### 목표
- 실시간 로그 출력
- 색상 및 필터링 기능

---

## Phase 4: 고급 기능 (Day 13-15)

### Step 4.1: 실시간 모니터링 (2시간)

#### 목표
- 시스템 리소스 모니터링
- 현재 작업 상태 표시

### Step 4.2: 통계 대시보드 (2시간)

#### 목표
- 시각적 통계 차트
- 성능 메트릭 표시

### Step 4.3: 테마 시스템 완성 (1시간)

#### 목표
- 라이트 테마 추가
- 테마 전환 기능 완성

## 문제 해결 가이드

### 일반적인 문제들

#### 1. Import 에러
```bash
# 현재 디렉토리에서 실행하고 있는지 확인
pwd  # /path/to/yt-trans 이어야 함

# Python 경로 확인
python -c "import sys; print(sys.path)"
```

#### 2. Textual 관련 에러
```bash
# Textual 버전 확인
uv pip show textual

# 개발 도구로 디버깅
textual console
```

#### 3. CSS 적용 안됨
```bash
# CSS 파일 경로 확인
ls -la src/tui/themes/

# CSS 문법 검증
textual check src/tui/themes/dark.tcss
```

### 성능 최적화 팁

1. **대용량 데이터**: 가상화 테이블 사용
2. **메모리 관리**: 주기적인 가비지 컬렉션
3. **응답성**: 백그라운드 작업을 위한 @work 데코레이터 사용

### 디버깅 도구

```bash
# 실시간 콘솔 디버깅
textual console

# 스크린샷 생성
textual run tui:OpenScribeTUI --screenshot screenshot.svg

# 개발 서버 (핫 리로드)
textual run --dev tui:OpenScribeTUI
```

이제 Phase별로 단계적으로 구현해보시겠습니까?