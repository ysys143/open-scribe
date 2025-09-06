"""메인 TUI 애플리케이션"""

from textual.app import App, ComposeResult
from textual.widgets import Header
from textual.containers import ScrollableContainer
from textual.binding import Binding

from .screens.main_menu import MainMenuScreen


class YouTubeTranscriberTUI(App):
    """YouTube Transcriber TUI 메인 애플리케이션"""
    
    CSS = """
    /* --- Theme tokens removed: Textual CSS doesn't support custom properties. */
    Screen { background: #1e1e2e; color: #cdd6f4 }

    .title {
        text-style: bold;
        color: #89b4fa;
        text-align: center;
        margin: 0;
        height: 1;
    }

    .subtitle {
        color: #a6adc8;
        text-align: center;
        margin: 0;
        height: 1;
    }

    .main-scroll {
        height: 100%;
        width: 100%;
        overflow: hidden;
    }

    .header-section {
        height: 10%;
        align: center top;
        margin: 1 0 0 0;
        padding: 0;
    }

    .divider-line {
        width: 100%;
        height: 1;
        color: #45475a;
        text-align: center;
        margin: 0;
        padding: 0;
    }


    .main-section {
        height: 90%;
        min-height: 0;
    }

    .menu-section {
        width: 24;         /* 고정 폭 */
        min-width: 24;
        max-width: 24;
        padding: 0 1;
        margin: 0;
        align: left top;
    }

    .menu-buttons {
        width: 100%;
        height: auto;
        margin: 0;
        padding: 0;
        align: left top;
    }

    .content-area {
        width: 1fr; padding: 0 1 0 1; margin: 0 1;
        border: solid #45475a;
        height: 1fr; min-height: 0; overflow: hidden; /* 내부 컨테이너에서만 스크롤 */
        align: left top; content-align: left top;
    }

    /* content-area 내부 기본 Static 여백 제거 */
    .content-area Static { margin: 0; }
    .content-area Button { margin: 0; }
    .content-area Horizontal { margin: 0; }

    .content-area.focused-area {
        border: solid #f9e2af;
    }

    .content-placeholder {
        text-align: center;
        color: #a6adc8;
        margin: 5 1;
        padding: 1;
    }

    .content-title { text-style: bold; color: #cdd6f4; margin: 1 0 }

    .content-text { color: #cdd6f4; margin: 1 0 }

    /* 섹션 타이틀(Options 등) - 여백 최소화 버전 */
    .options-title {
        color: #cdd6f4;
        margin: 0 0;     /* 위/아래 여백 제거 */
        text-style: bold;
        height: 1;       /* 고정 높이 */
    }

    /* 섹션 사이 간격을 위한 얇은 마진 */
    .section-gap {
        margin: 1 0 0 0;  /* 위쪽으로 1만 부여 */
    }

    .line-spacer {
        height: 1;       /* 한 줄 빈 라인 */
        margin: 0;
        padding: 0;
    }

    .menu-button {
        width: auto;
        min-width: 20;
        max-width: 90%;
        margin: 1 0;
        background: transparent;
        color: #cdd6f4;
        border: none;
        text-align: left;
        padding: 0 1;
        content-align: left top;
    }

    .menu-button:hover {
        background: #45475a;
        color: #f9e2af;
    }

    .menu-button:focus {
        background: #45475a;
    }
    .menu-button.selected {
        background: #45475a;
        color: #f9e2af;
        text-style: bold;
    }
    
    /* Input container styles */
    .input-container {
        width: 100%;
        height: 3;
        margin: 2 0 2 0;   /* 라벨-입력 위/아래 간격 확대 */
        padding: 0;
        align: left top;
    }
    
    .url-input {
        width: 100%;
        margin-right: 0;
    }
    
    .start-btn {
        width: auto;
        min-width: 10;
        background: #89b4fa;
        color: #1e1e2e;
        border: none;
        color: #f9e2af;
        text-style: bold;
    }


    .quit-button {
        background: transparent;
        color: #cdd6f4;
        border: none;
    }

    .quit-button:hover {
        background: #45475a;
        color: #f9e2af;
    }

    .quit-button:focus {
        background: #45475a;
        color: #f9e2af;
        text-style: bold;
    }

    /* Screen titles */
    .screen-title {
        text-style: bold;
        color: #89b4fa;
        text-align: center;
        margin: 1;
        dock: top;
    }

    .section-title {
        text-style: bold;
        color: #f9e2af;
        margin: 1 0;
    }

    /* Transcribe screen */
    .transcribe-container {
        padding: 1;
    }

    .tab-content {
        padding: 1;
        height: 1fr;
        min-height: 0;
        overflow-y: auto;
        scrollbar-size: 1 1;
    }

    .input-group {
        margin-bottom: 1;
    }

    .main-input {
        margin-bottom: 1;
    }

    .checkbox-group {
        margin: 1 0;
    }

    .radio-group {
        margin: 1 0;
    }

    .button-group {
        margin-top: 1;
        align: center middle;
    }

    .option-button {
        background: transparent;
        border: none;
        text-align: left;
        content-align: left top;
        padding: 0 0 0 0;
        width: 100%;
        height: 1;          /* 라인 높이 일정화 */
        margin: 0 0 0 0;    /* 옵션 간 간격 */
    }
    .option-button:hover { background: #3b3b4a }

    .action-button {
        margin: 0 1;
        background: #8bd5a5;
        color: #1e1e2e; min-width: 14; height: 3; min-height: 3;
        border: none;                 /* 기본 보더 제거 */
    }

    .action-button:hover {
        background: #94e2d5;
    }

    .action-button:focus { background: #94e2d5; }

    .utility-button {
        margin: 0 1;
        background: #7aa7f0;          /* 차분한 하늘색 */
        color: #0b1020; min-width: 14; height: 3; min-height: 3;
        border: none; text-style: bold;
    }

    /* 경고: 테두리 제거, 은은한 솔리드 앰버 */
    .warning-button {
        margin: 0 1;
        background: #f59e0b; color: #0f0f10; min-width: 14; height: 3; min-height: 3;
        border: none; text-style: bold;
    }
    .warning-button:hover { background: #fbbf24 }

    /* 치명: 가시성 높은 솔리드 레드 */
    .danger-button {
        margin: 0 1;
        background: #ef4444; color: #0f0f10; min-width: 14; height: 3; min-height: 3;
        border: none; text-style: bold;
    }
    .danger-button:hover { background: #dc2626 }

    .utility-button:hover { background: #6a98e6 }
    .utility-button:focus, .action-button:focus, .warning-button:focus, .danger-button:focus { outline: none }

    /* Bottom action bar & spacer */
    .actions-bar {
        padding: 0;         /* 여백 최소화 */
        background: transparent;  /* 불필요한 배경 제거 */
        border: none;       /* 테두리 없음 */
        align: center top;  /* 중앙 정렬 */
        margin: 2 0 0 0;    /* 입력창 아래 간격 확대 */
        content-align: center middle;
        height: 3;          /* 버튼만 3줄 */
        width: 100%;        /* 전체 너비 사용 */
    }

    /* 액션바 내부 버튼을 동일한 폭/높이로 맞춤 */
    .actions-bar Button {
        width: 1fr;         /* 3분할 균등 폭 */
        min-width: 0;
        height: 3;          /* 버튼 자체 높이 */
        min-height: 3;
        margin: 0;          /* 균등 분할을 위해 여백 제거 */
        content-align: center middle;
        text-style: bold;
        color: #1e1e2e;
    }

    /* 상단 강조 제거로 관련 클래스 미사용 */

    .options-section {
        margin: 0;          /* 액션바 바로 아래에 붙도록 */
        padding: 0;
    }

    /* 폼 전체를 상단에 밀착해서 수직 스택 */
    .form-stack {
        margin: 0;
        padding: 0;
        align: left top;
        content-align: left top;
    }

    /* Input focus styles - remove yellow borders */
    Input { background: transparent; border: none }
    Input:focus { outline: none }

    /* --- Optional theme override (cosmic) --- */
    .theme--cosmic Screen, Screen.theme--cosmic { background:#12141a; color:#f3f6ff }
    .theme--cosmic .content-area, .content-area.theme--cosmic { border: solid #2b303b }
    .theme--cosmic .action-button, .action-button.theme--cosmic { background:#a78bfa; color:#101318 }
    .theme--cosmic .warning-button, .warning-button.theme--cosmic { background:#fb7185; color:#101318 }
    .theme--cosmic .utility-button, .utility-button.theme--cosmic { background:#7dd3fc; color:#101318 }
    .theme--cosmic Input, Input.theme--cosmic { border: solid #a78bfa }
    Select:focus { border: none }
    Checkbox:focus { border: none }
    Switch:focus { border: none }
    Slider:focus { border: none }
    RadioButton:focus { border: none }

    /* Settings screen */
    .settings-container {
        padding: 1;
    }

    .setting-group {
        margin-bottom: 1;
    }

    .switch-group {
        margin: 1 0;
    }

    .settings-actions {
        dock: bottom;
        height: 3;
        background: #313244;
        padding: 1;
        align: center middle;
    }

    .inline-button {
        min-width: 12;
        margin-left: 1;
    }
    
    /* Transcribe screen specific */
    .transcribe-container {
        padding: 1;
        height: 100%;
        overflow-y: auto;
    }

    /* Database screen: 상단 정렬 강제 */
    .db-container {
        padding: 1;
        height: 1fr;            /* 가용 영역을 채움 */
        align: left top;        /* 위쪽 정렬 */
        content-align: left top;
        dock: top;
    }

    .db-container > Horizontal { margin: 0; padding: 0; }
    .db-container Button { margin: 0; }
    /* Database table wrapper and table fill rules */
    #db_table_wrap { height: 1fr; min-height: 0; margin: 0; padding: 0; }
    #db_table_wrap DataTable { height: 100%; margin: 0; dock: top; }
    
    .screen-title {
        text-style: bold;
        color: #89b4fa;
        margin: 0 0 1 0;
    }
    
    .input-group {
        margin: 1 0;
    }
    
    .main-input {
        width: 100%;
        margin: 0;
    }
    
    .checkbox-group {
        margin: 2 0;
        width: 100%;
    }
    
    RadioSet {
        margin: 0;
        padding: 0;
    }
    
    RadioButton {
        margin: 0;
        padding: 0 1;
    }
    
    .output-display {
        border: solid #45475a;
        background: #181825;
        min-height: 10;
        max-height: 30;
        overflow-y: auto;
        margin-top: 0;     /* 위 여백 제거 */
        padding: 1 1 0 1;  /* 하단 패딩 제거 */
    }
    
    .output-placeholder {
        color: #585b70;
        text-align: center;
        margin: 2;
    }
    
    .output-text {
        color: #cdd6f4;
        margin: 0 0 1 0; /* 하단 여백으로 시각적 구분 */
    }
    
    .output-text.success {
        color: #a6e3a1;
    }
    
    .output-text.warning {
        color: #f9e2af;
    }
    
    .output-text.progress-line {
        color: #89b4fa;
    }

    /* Progress widgets */
    .task-progress {
        margin-bottom: 1;
        padding: 1;
        background: #313244;
        border: solid #45475a;
    }

    .task-name {
        text-style: bold;
        color: #f5f5f5;
    }

    .task-bar {
        margin: 1 0;
    }

    .task-status {
        color: #a6adc8;
    }

    .task-time {
        color: #585b70;
        text-align: right;
    }

    .multi-task-progress {
        padding: 1;
    }

    .overall-progress {
        background: #313244;
        padding: 1;
        margin-bottom: 1;
        border: solid #89b4fa;
    }

    .overall-label {
        text-style: bold;
        color: #89b4fa;
    }

    .overall-bar {
        margin: 1 0;
    }

    .overall-status {
        color: #f9e2af;
    }

    .task-list {
        height: auto;
        max-height: 20;
        overflow-y: auto;
    }

    /* Log widget */
    .realtime-log {
        padding: 1;
    }

    .log-display {
        border: solid #45475a;
        background: #181825;
        height: 15;
        margin-top: 1;
    }

    /* Status bar */
    .status-bar {
        dock: bottom;
        height: 1;
        background: #313244;
        padding: 0 1;
    }

    .status-icon {
        width: 3;
    }

    .status-text {
        width: 1fr;
    }

    .progress-info {
        text-align: center;
        color: #a6adc8;
    }

    .time-info {
        text-align: right;
        color: #585b70;
    }

    /* Compact progress */
    .compact-progress {
        margin-bottom: 1;
    }

    .compact-label {
        width: 15;
    }

    .compact-bar {
        width: 1fr;
        margin: 0 1;
    }

    .compact-percent {
        width: 8;
        text-align: right;
    }

    /* Progress bar states */
    .error {
        color: #f38ba8;
    }

    /* Base screen */
    .confirmation-dialog {
        align: center middle;
        background: #313244;
        border: solid #89b4fa;
        padding: 2;
        width: auto;
        max-width: 40;   /* 너무 넓지 않게 조정 */
        min-width: 30;
    }

    .dialog-buttons {
        align: center middle;
        margin-top: 1;
    }
    
    /* Settings container - enable scrolling */
    .settings-container {
        height: 100%;
        max-height: 100%;
        min-height: 0;
        overflow-y: auto;
        scrollbar-size: 1 1;
        padding: 1;
    }
    
    .setting-group {
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "종료", priority=True),
        Binding("f1", "help", "Help"),
        Binding("f2", "toggle_theme", "Toggle Theme"),
        Binding("ctrl+r", "refresh", "새로고침"),
        # Disable command palette (Ctrl+P) and hide from footer
        Binding("ctrl+p", "noop", "", show=False),
    ]
    
    def __init__(self):
        super().__init__()
        self.title = "YouTube Transcriber TUI v2.0"
        self.sub_title = "YouTube Transcription Tool"
        # 테마 상태
        self._themes = [None, "theme--cosmic"]  # 기본테마(None), 코스믹 테마
        self._theme_index = 1  # on_mount에서 적용할 인덱스
    
    def compose(self) -> ComposeResult:
        """UI 구성"""
        yield Header(show_clock=True)
        with ScrollableContainer(classes="main-scroll", id="main_container"):
            yield MainMenuScreen(id="main_screen")
    
    def on_mount(self) -> None:
        """앱 마운트 시 테마 클래스 적용"""
        self._apply_theme(self._themes[self._theme_index])

    def _apply_theme(self, theme: str | None) -> None:
        """테마 클래스 적용/해제 (None이면 기본 테마)"""
        # 기존 테마 클래스 제거
        try:
            self.remove_class("theme--cosmic")
        except Exception:
            pass
        try:
            self.remove_class("theme--neon-gpu")
        except Exception:
            pass
        # 새 테마 적용
        if theme:
            try:
                self.add_class(theme)
            except Exception:
                pass
    
    def action_toggle_theme(self) -> None:
        """테마 토글(F2): 기본↔코스믹 순환"""
        self._theme_index = (self._theme_index + 1) % len(self._themes)
        self._apply_theme(self._themes[self._theme_index])

    # Block command palette explicitly (prevent opening even if other bindings trigger)
    def action_command_palette(self) -> None:  # type: ignore[override]
        return

    def action_noop(self) -> None:
        return
    
    def action_help(self) -> None:
        """도움말 표시"""
        self.notify("F1: 도움말, F2: 테마 변경, Ctrl+R: 새로고침, Ctrl+C: 종료")
    
    def action_refresh(self) -> None:
        """화면 새로고침"""
        if hasattr(self.screen, 'refresh_data'):
            self.screen.refresh_data()
    
    def show_transcribe_screen(self) -> None:
        """전사 화면 표시 - 이제 메인 메뉴 내에서 처리됨"""
        # 메인 메뉴의 transcribe 인터페이스를 사용
        pass
    
    def show_main_menu(self) -> None:
        """메인 메뉴 화면 표시"""
        container = self.query_one("#main_container", ScrollableContainer)
        container.remove_children()
        container.mount(MainMenuScreen(id="main_screen"))


if __name__ == "__main__":
    app = YouTubeTranscriberTUI()
    app.run()