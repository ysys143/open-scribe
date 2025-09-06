"""메인 메뉴 화면"""

from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Button, Static, Input, Label
from textual.events import Key, Click
from rich.text import Text
from textual.widget import Widget
from textual.app import ComposeResult
from textual.binding import Binding
import subprocess
import os
import sys
import threading
from datetime import datetime
import time
from ...config import Config
from ...database import TranscriptionDatabase
from ...downloader import YouTubeDownloader
from pathlib import Path
import json
from .database import DatabaseScreen
from ..utils.config_manager import ConfigManager
import asyncio


class URLInput(Input):
    """URL 입력을 위한 커스텀 Input 위젯"""
    
    def __init__(self, parent_screen, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_screen = parent_screen
        print(f"DEBUG: URLInput created with parent_screen: {parent_screen}")
    
    def on_key(self, event) -> None:
        """키 이벤트 처리"""
        print(f"DEBUG: URLInput.on_key called, key: {event.key}")
        if event.key == "enter":
            print(f"DEBUG: Enter key pressed in URLInput, value: {self.value}")
            if hasattr(self.parent_screen, 'start_transcription'):
                self.parent_screen.start_transcription()
        else:
            super().on_key(event)
    
    def action_submit(self) -> None:
        """엔터키를 눌렀을 때 호출"""
        print(f"DEBUG: URLInput.action_submit called, value: {self.value}")
        if hasattr(self.parent_screen, 'start_transcription'):
            self.parent_screen.start_transcription()


class MainMenuScreen(Widget):
    """메인 메뉴 화면"""
    
    # 키 이벤트를 직접 받기 위해 포커스 가능하도록 설정
    can_focus = True
    
    BINDINGS = [
        Binding("1", "menu_action('transcribe')", "Transcription", priority=True),
        Binding("2", "menu_action('database')", "Database", priority=True),
        Binding("3", "menu_action('api_keys')", "API Keys", priority=True),
        Binding("4", "menu_action('settings')", "Settings", priority=True),
        Binding("5", "menu_action('monitor')", "Monitoring", priority=True),
        Binding("h", "menu_action('help')", "Help", priority=True),
        Binding("q", "menu_action('quit')", "Quit", priority=True),
        Binding("ㅂ", "menu_action('quit')", "Quit", priority=True),
        Binding("escape", "menu_action('quit')", "Quit", priority=True),
        Binding("up", "handle_up", "Up", priority=True),
        Binding("down", "handle_down", "Down", priority=True),
        Binding("left", "focus_menu", "Menu", priority=True),
        Binding("right", "focus_content", "Content", priority=True),
        Binding("j", "handle_down", "Down (vim)", priority=True),
        Binding("k", "handle_up", "Up (vim)", priority=True),
        Binding("enter", "handle_enter", "Select/Toggle", priority=True),
        Binding("space", "handle_space", "Toggle", priority=True),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu_buttons = []
        self.current_focus = 0
        self.content_area = None
        self.selected_button_id = None
        self.focus_area = "menu"  # "menu" or "content"
        # Store URL input widget
        self.url_input = None
        # Store option states (simple boolean values)
        self.timestamp_enabled = True
        self.summary_enabled = True
        self.translate_enabled = False
        self.video_enabled = False
        self.srt_enabled = False
        self.srt_translate_enabled = False
        self.force_enabled = False
        self.background_enabled = False
        self.selected_engine = "gpt-4o-mini-transcribe"  # default
        # Store option widgets for updating display
        self.option_widgets = {}
        # Current focused option index (for arrow key navigation)
        self.focused_option = 0
        self.total_options = 13  # 8 checkboxes + 5 engines
        # 재처리 확인용 보류 URL
        self._pending_url = None
        # 설정/키 관리자
        self.cfg_manager = ConfigManager()
        self._validating_api_key = False
    
    def compose(self) -> ComposeResult:
        """UI 구성"""
        with Vertical():
            # 상단 제목
            with Vertical(classes="header-section"):
                yield Static("Open-Scribe Youtube Transcriber", classes="title")
                yield Static("(c) Jaesol Shin 2025", classes="subtitle")
            
            # 구분선 (1줄로 통합)
            yield Static("═" * 120, classes="divider-line")
            
            # 하단 메뉴와 콘텐츠 영역
            with Horizontal(classes="main-section"):
                # 왼쪽 메뉴
                with Vertical(classes="menu-section"):
                    with Vertical(classes="menu-buttons"):
                        yield Button("1. Transcribe", id="transcribe", classes="menu-button")
                        yield Button("2. Database", id="database", classes="menu-button")
                        yield Button("3. API Key", id="api_keys", classes="menu-button")
                        yield Button("4. Settings", id="settings", classes="menu-button")
                        yield Button("5. Monitoring", id="monitor", classes="menu-button")
                        yield Button("H. Help", id="help", classes="menu-button")
                        yield Button("Q. Quit", id="quit", classes="menu-button")
                
                # 오른쪽 콘텐츠 영역
                with Vertical(classes="content-area", id="content_area"):
                    yield Static("Select a menu item to view details", classes="content-placeholder")
    
    def on_mount(self) -> None:
        """화면 마운트 시 버튼 리스트 설정 및 첫 번째 버튼에 포커스"""
        # 버튼 순서대로 저장
        button_ids = ["transcribe", "database", "api_keys", "settings", "monitor", "help", "quit"]
        self.menu_buttons = [self.query_one(f"#{btn_id}", Button) for btn_id in button_ids]
        
        # 콘텐츠 영역 저장
        self.content_area = self.query_one("#content_area", Vertical)
        
        # 초기 진입 시 Transcribe 화면을 기본 표시하고 메뉴 강조
        self.current_focus = 0
        self.selected_button_id = "transcribe"
        self.show_transcribe_interface()
        try:
            self.app.set_focus(self)
        except Exception:
            pass
        # 메뉴 강조 클래스 적용
        try:
            for btn in self.menu_buttons:
                btn.remove_class("selected")
            self.menu_buttons[0].add_class("selected")
        except Exception:
            pass
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """버튼 클릭 이벤트 처리"""
        button_id = event.button.id
        
        if button_id == "transcribe":
            # 오른쪽 콘텐츠 영역에 전사 인터페이스 표시
            self.selected_button_id = "transcribe"
            self.show_transcribe_interface()
            self.focus_area = "content"
            # 키 이벤트를 이 위젯이 직접 받도록 포커스 이동
            try:
                self.app.set_focus(self)
            except Exception:
                pass
            self.set_timer(0.01, lambda btn_id="transcribe": self._update_button_selection(btn_id))
        elif button_id == "start_transcribe":
            self.start_transcription()
        elif button_id == "clear_url":
            self.clear_url_input()
            return
        elif button_id == "confirm_yes":
            self._remove_confirm_dialog()
            if self._pending_url:
                self._launch_transcription_process(self._pending_url, force=True)
                self._pending_url = None
            return
        elif button_id == "confirm_no":
            self._remove_confirm_dialog()
            try:
                out = self.content_area.query_one(".transcribe-output", Static)
                out.update("Cancelled by user.")
            except Exception:
                pass
            self._pending_url = None
            return
        elif button_id == "stop_transcribe":
            # 현재는 백그라운드 스레드/프로세스 중지 미구현 - 안내만 표시
            self.app.notify("Stop is not implemented yet", severity="warning")
            return
        elif button_id == "database":
            try:
                self.app.push_screen(DatabaseScreen())
            except Exception:
                self.show_content("Database Management", "Database screen failed to open.")
            self.set_timer(0.01, lambda btn_id="database": self._update_button_selection(btn_id))
        elif button_id == "api_keys":
            self.selected_button_id = "api_keys"
            self.show_api_keys_interface()
            self.focus_area = "content"
            self.set_timer(0.01, lambda btn_id="api_keys": self._update_button_selection(btn_id))
        elif button_id == "settings":
            self.selected_button_id = "settings"
            self.show_settings_interface()
            self.focus_area = "content"
            self.set_timer(0.01, lambda btn_id="settings": self._update_button_selection(btn_id))
        elif button_id == "monitor":
            self.show_content("Monitoring", "Monitoring screen will be implemented in Phase 4.")
            self.set_timer(0.01, lambda btn_id="monitor": self._update_button_selection(btn_id))
        elif button_id == "help":
            self.show_help()
        elif button_id == "quit":
            self.app.exit()
        # API Keys 영역 버튼
        elif button_id == "save_api_key":
            self._save_api_key_inline()
            return
        elif button_id == "validate_api_key":
            self._validate_api_key_inline()
            return
        # Settings 영역 저장
        elif button_id == "settings_save":
            self._save_settings_inline()
            return
    
    def show_help(self) -> None:
        """도움말 표시"""
        self._update_button_selection("help")
        help_text = """YouTube Transcriber TUI Help

Menu Navigation:
- ↑/↓ or K/J: Move menu
- Enter: Select
- 1-5: Direct selection by number
- H: Help, Q: Quit

General Keyboard Shortcuts:
- Ctrl+C: Exit
- F1: Help
- F2: Toggle theme
- Esc: Quit"""
        self.show_content("Help", help_text)
    
    def _update_button_selection(self, selected_id: str) -> None:
        """버튼 선택 상태 업데이트"""
        self.selected_button_id = selected_id
        # 메뉴 강조 클래스 업데이트
        try:
            for btn in self.menu_buttons:
                btn.remove_class("selected")
            mapping = {"transcribe":0,"database":1,"api_keys":2,"settings":3,"monitor":4,"help":5,"quit":6}
            idx = mapping.get(selected_id)
            if idx is not None and 0 <= idx < len(self.menu_buttons):
                self.menu_buttons[idx].add_class("selected")
        except Exception:
            pass
    
    def show_error(self, message: str) -> None:
        """에러 메시지 표시"""
        # 알림 + 섹션 상태라인 모두 갱신 (알림 미표시 환경 대비)
        try:
            self.app.notify(f"✗ {message}", severity="error")
        except Exception:
            pass
        self._update_any_status_lines(f"✗ {message}")
    
    def show_success(self, message: str) -> None:
        """성공 메시지 표시"""
        try:
            self.app.notify(f"✓ {message}", severity="information")
        except Exception:
            pass
        self._update_any_status_lines(f"✓ {message}")

    def _update_any_status_lines(self, text: str) -> None:
        """현재 섹션에 존재하는 상태 라인을 모두 업데이트"""
        try:
            if self.content_area:
                for sid in ("#api_status_line", "#settings_status_line", "#spinner_line"):
                    try:
                        w = self.content_area.query_one(sid, Static)
                        if w:
                            w.update(text)
                    except Exception:
                        pass
        except Exception:
            pass
    
    def show_content(self, title: str, content: str) -> None:
        """콘텐츠 영역에 내용 표시"""
        if self.content_area:
            self.content_area.remove_children()
            self.content_area.mount(Static(title, classes="content-title"))
            self.content_area.mount(Static(content, classes="content-text"))
    
    def show_transcribe_interface(self) -> None:
        """콘텐츠 영역에 전사 인터페이스 표시"""
        if self.content_area:
            # 모든 자식 위젯 제거
            self.content_area.remove_children()
            
            # 제목과 구분선 제거 (단순화)
            
            # 폼 스택 컨테이너 - 모든 요소를 상단부터 세로로 붙임
            form = Vertical(classes="form-stack")
            self.content_area.mount(form)
            
            # URL 입력 섹션
            form.mount(Static("YouTube URL:", classes="options-title"))
            
            # 입력창 컨테이너
            input_container = Horizontal(classes="input-container")
            form.mount(input_container)
            
            # URL 입력창
            self.url_input = Input(
                placeholder="Paste YouTube URL here...",
                classes="url-input",
                id="url_input"
            )
            input_container.mount(self.url_input)
            
            # 액션 바: Output 위로 이동 (Start/Stop/Clear)
            actions = Horizontal(classes="actions-bar")
            form.mount(actions)
            # 상단 강조 제거: 버튼만 3분할로 배치
            actions.mount(Button("Run", id="start_transcribe", variant="primary", classes="action-button"))
            actions.mount(Button("Stop", id="stop_transcribe", variant="warning", classes="warning-button"))
            actions.mount(Button("Clr", id="clear_url", variant="default", classes="utility-button"))
            
            
            # 옵션 섹션 - 텍스트 기반 UI (여백 최소화 타이틀)
            form.mount(Static("", classes="line-spacer"))
            form.mount(Static("Options:", classes="options-title section-gap"))
            
            # 옵션 표시 (체크박스 스타일)
            self.option_widgets['timestamp'] = Button(Text(self._get_option_display(0, "Include timestamps", self.timestamp_enabled)), id="opt_timestamp", classes="content-text option-button")
            self.option_widgets['summary'] = Button(Text(self._get_option_display(1, "Generate AI summary", self.summary_enabled)), id="opt_summary", classes="content-text option-button")
            self.option_widgets['translate'] = Button(Text(self._get_option_display(2, "Translate", self.translate_enabled)), id="opt_translate", classes="content-text option-button")
            self.option_widgets['video'] = Button(Text(self._get_option_display(3, "Download video", self.video_enabled)), id="opt_video", classes="content-text option-button")
            self.option_widgets['srt'] = Button(Text(self._get_option_display(4, "Generate SRT (timestamps)", self.srt_enabled)), id="opt_srt", classes="content-text option-button")
            self.option_widgets['srt_translate'] = Button(Text(self._get_option_display(5, "Translate SRT", self.srt_translate_enabled)), id="opt_srt_translate", classes="content-text option-button")
            self.option_widgets['force'] = Button(Text(self._get_option_display(6, "Force (retry)", self.force_enabled)), id="opt_force", classes="content-text option-button")
            self.option_widgets['background'] = Button(Text(self._get_option_display(7, "Background", self.background_enabled)), id="opt_background", classes="content-text option-button")
            
            form.mount(self.option_widgets['timestamp'])
            form.mount(self.option_widgets['summary'])
            form.mount(self.option_widgets['translate'])
            form.mount(self.option_widgets['video'])
            form.mount(self.option_widgets['srt'])
            form.mount(self.option_widgets['srt_translate'])
            form.mount(self.option_widgets['force'])
            form.mount(self.option_widgets['background'])
            
            # 엔진 선택
            form.mount(Static("", classes="line-spacer"))
            form.mount(Static("Engine:", classes="options-title section-gap"))
            
            self.option_widgets['engine_mini'] = Button(Text(self._get_engine_display(8, "GPT-4o-mini (default, fast)", "gpt-4o-mini-transcribe")), id="eng_mini", classes="content-text option-button")
            self.option_widgets['engine_gpt4o'] = Button(Text(self._get_engine_display(9, "GPT-4o (high quality)", "gpt-4o-transcribe")), id="eng_gpt4o", classes="content-text option-button")
            self.option_widgets['engine_whisper_api'] = Button(Text(self._get_engine_display(10, "Whisper API (OpenAI cloud)", "whisper-api")), id="eng_whisper_api", classes="content-text option-button")
            self.option_widgets['engine_whisper_cpp'] = Button(Text(self._get_engine_display(11, "Whisper-cpp (local)", "whisper-cpp")), id="eng_whisper_cpp", classes="content-text option-button")
            self.option_widgets['engine_youtube'] = Button(Text(self._get_engine_display(12, "YouTube native", "youtube-transcript-api")), id="eng_youtube", classes="content-text option-button")
            
            form.mount(self.option_widgets['engine_mini'])
            form.mount(self.option_widgets['engine_gpt4o'])
            form.mount(self.option_widgets['engine_whisper_api'])
            form.mount(self.option_widgets['engine_whisper_cpp'])
            form.mount(self.option_widgets['engine_youtube'])
            
            # (네비게이션 안내 제거)
            
            # 출력 영역 (액션 바 아래) - 타이틀과 박스 간 여백 최소화
            form.mount(Static("", classes="line-spacer"))
            form.mount(Static("Output:", classes="options-title section-gap"))
            form.mount(Static("─" * 60, classes="divider-line"))
            # 상단 로딩/상태 라인과 스트림 라인(실시간 1줄)
            form.mount(Static("", classes="output-text progress-line", id="spinner_line"))
            form.mount(Static("Ready to transcribe...", classes="transcribe-output content-text", id="stream_line"))
            
            # URL 입력에 포커스
            self.url_input.focus()
            # 초기 포커스 설정
            self.focused_option = 0
            self.update_option_displays()

    def show_api_keys_interface(self) -> None:
        """메인 영역에 API 키 관리 UI 표시 (싱글 페이지)"""
        if not self.content_area:
            return
        self.content_area.remove_children()
        scroller = ScrollableContainer(classes="tab-content", id="api_scroller")
        # 고정 높이 컨테이너 안에서만 스크롤이 동작하도록 명시
        try:
            scroller.styles.height = "1fr"
            scroller.styles.min_height = 0
            scroller.styles.overflow_y = "auto"
        except Exception:
            pass
        self.content_area.mount(scroller)
        form = Vertical(classes="form-stack")
        scroller.mount(form)
        form.mount(Static("API Keys", classes="options-title"))
        form.mount(Static("OPENAI_API_KEY", classes="options-title"))
        # 입력
        key_input_row = Horizontal(classes="input-container")
        form.mount(key_input_row)
        api_input = Input(placeholder="OpenAI API Key (sk-...)", id="openai_key_inline", classes="url-input")
        try:
            from ...config import Config as _Cfg
            api_input.value = _Cfg.OPENAI_API_KEY or ""
        except Exception:
            pass
        key_input_row.mount(api_input)
        # 버튼 바
        actions = Horizontal(classes="actions-bar")
        form.mount(actions)
        actions.mount(Button("Save", id="save_api_key", classes="action-button"))
        actions.mount(Button("Validate", id="validate_api_key", classes="utility-button"))
        actions.mount(Button("Back", id="transcribe", classes="warning-button"))
        # 상태 메시지 위에 빈 줄 추가
        form.mount(Static("", classes="line-spacer"))
        # 상태 (초기 텍스트로 높이 확보)
        form.mount(Static("Status: Ready", id="api_status_line", classes="output-text"))

    def _set_api_status(self, msg: str) -> None:
        try:
            if self.content_area:
                st = self.content_area.query_one("#api_status_line", Static)
                st.update(msg)
                try:
                    st.scroll_visible(animate=False)
                except Exception:
                    pass
        except Exception:
            pass

    def _call_ui(self, func, *args, **kwargs) -> None:
        """백그라운드 스레드에서 안전하게 UI 업데이트 호출"""
        try:
            self.call_from_thread(lambda: func(*args, **kwargs))
        except Exception:
            # fallback: 다음 틱에서 실행
            try:
                self.set_timer(0, lambda: func(*args, **kwargs))
            except Exception:
                pass

    def _end_api_validation(self) -> None:
        """검증 종료 처리"""
        self._validating_api_key = False

    def _save_api_key_inline(self) -> None:
        try:
            val = self.content_area.query_one("#openai_key_inline", Input).value.strip()
            if not val:
                self.show_error("키 값을 입력하세요")
                return
            ok = self.cfg_manager.save_api_key("OpenAI API Key", val)
            if ok:
                try:
                    from dotenv import load_dotenv
                    load_dotenv(override=True)
                except Exception:
                    pass
                self._set_api_status("✓ 저장되었습니다")
                self.show_success("API 키 저장 완료")
            else:
                self._set_api_status("✗ 저장 실패")
                self.show_error("저장 실패")
        except Exception as e:
            self._set_api_status(str(e))
            self.show_error(str(e))

    def _validate_api_key_inline(self) -> None:
        """API 키 검증 (인라인)"""
        if self._validating_api_key:
            return
        
        try:
            val = self.content_area.query_one("#openai_key_inline", Input).value.strip()
            if not val:
                self.show_error("키 값을 입력하세요")
                return
            
            # 검증 시작
            self._set_api_status("◆ 키 검증 중...")
            self.app.notify("API 키 검증 중...", severity="information")
            self._validating_api_key = True
            
            # 스레드로 검증 실행
            import threading
            
            def validate_in_thread():
                ok = False
                err = ""
                
                try:
                    if not val.startswith("sk-") or len(val) <= 20:
                        err = "Invalid key format"  
                    else:
                        import urllib.request
                        import urllib.error
                        req = urllib.request.Request(
                            "https://api.openai.com/v1/models",
                            headers={"Authorization": f"Bearer {val}"}
                        )
                        with urllib.request.urlopen(req, timeout=2) as response:
                            ok = (response.status == 200)
                except urllib.error.HTTPError as e:
                    err = f"HTTP {e.code}"
                except Exception as e:
                    err = str(e)[:30]
                
                # UI 업데이트를 메인 스레드에서 실행
                def update_ui():
                    if ok:
                        self._set_api_status("✓ 키가 유효합니다")
                        self.app.notify("키 검증 성공", severity="information")
                    else:
                        msg = f"✗ 키 검증 실패: {err}" if err else "✗ 키 검증 실패"
                        self._set_api_status(msg)
                        self.app.notify(f"키 검증 실패: {err}" if err else "키 검증 실패", severity="error")
                    self._validating_api_key = False
                
                # 메인 스레드에서 UI 업데이트 실행
                self.app.call_from_thread(update_ui)
            
            # 스레드 시작
            thread = threading.Thread(target=validate_in_thread, daemon=True)
            thread.start()
            
        except Exception as e:
            self._validating_api_key = False
            self.show_error(str(e))

    def show_settings_interface(self) -> None:
        """메인 영역에 Settings UI 표시 (싱글 페이지)"""
        if not self.content_area:
            return
        self.content_area.remove_children()
        scroller = ScrollableContainer(classes="tab-content", id="settings_scroller")
        try:
            scroller.styles.height = "1fr"
            scroller.styles.min_height = 0
            scroller.styles.overflow_y = "auto"
        except Exception:
            pass
        self.content_area.mount(scroller)
        form = Vertical(classes="form-stack")
        scroller.mount(form)
        form.mount(Static("Settings", classes="options-title"))
        # 1) 언어/모델/엔진 (가장 중요)
        form.mount(Static("OPENAI_TRANSLATE_LANGUAGE", classes="options-title"))
        tl = Input(placeholder="Korean / English / Japanese / Chinese / auto", id="set_translate_language", classes="url-input")
        form.mount(tl)
        form.mount(Static("OPENAI_TRANSLATE_MODEL", classes="options-title"))
        tm = Input(placeholder="gpt-5-mini", id="set_translate_model", classes="url-input")
        form.mount(tm)
        form.mount(Static("OPENAI_SUMMARY_LANGUAGE", classes="options-title"))
        sl = Input(placeholder="Korean / English / auto", id="set_summary_language", classes="url-input")
        form.mount(sl)
        form.mount(Static("OPENAI_SUMMARY_MODEL", classes="options-title"))
        sm = Input(placeholder="gpt-5-mini", id="set_summary_model", classes="url-input")
        form.mount(sm)
        form.mount(Static("OPEN_SCRIBE_ENGINE", classes="options-title"))
        eg = Input(placeholder="gpt-4o-mini-transcribe", id="set_engine", classes="url-input")
        form.mount(eg)
        try:
            from ...config import Config as _Cfg
            tl.value = str(_Cfg.OPENAI_TRANSLATE_LANGUAGE)
            tm.value = str(_Cfg.OPENAI_TRANSLATE_MODEL)
            sl.value = str(_Cfg.OPENAI_SUMMARY_LANGUAGE)
            sm.value = str(_Cfg.OPENAI_SUMMARY_MODEL)
            eg.value = str(_Cfg.ENGINE)
        except Exception:
            pass
        # 2) 경로 (자주 쓰는 것)
        form.mount(Static("OPEN_SCRIBE_BASE_PATH", classes="options-title"))
        bp = Input(placeholder="/path/to/base", id="set_base_path", classes="url-input")
        form.mount(bp)
        form.mount(Static("OPEN_SCRIBE_DOWNLOADS_PATH", classes="options-title"))
        dl = Input(placeholder="/path/to/Downloads", id="set_downloads_path", classes="url-input")
        form.mount(dl)
        try:
            from ...config import Config as _Cfg
            bp.value = str(_Cfg.BASE_PATH)
            dl.value = str(_Cfg.DOWNLOADS_PATH)
        except Exception:
            pass
        # 3) 워커 (비기능 설정은 하단)
        form.mount(Static("MIN_WORKER", classes="options-title"))
        min_i = Input(placeholder="MIN_WORKER", id="set_min_worker", classes="url-input")
        form.mount(min_i)
        form.mount(Static("MAX_WORKER", classes="options-title"))
        max_i = Input(placeholder="MAX_WORKER", id="set_max_worker", classes="url-input")
        form.mount(max_i)
        try:
            from ...config import Config as _Cfg
            min_i.value = str(_Cfg.MIN_WORKER)
            max_i.value = str(_Cfg.MAX_WORKER)
        except Exception:
            pass
        # 버튼 바
        actions = Horizontal(classes="actions-bar")
        form.mount(actions)
        actions.mount(Button("Save", id="settings_save", classes="action-button"))
        actions.mount(Button("Back", id="transcribe", classes="warning-button"))
        form.mount(Static("", id="settings_status_line", classes="output-text"))

    def _set_settings_status(self, msg: str) -> None:
        try:
            if self.content_area:
                self.content_area.query_one("#settings_status_line", Static).update(msg)
        except Exception:
            pass

    def _save_settings_inline(self) -> None:
        try:
            # 값 읽기
            min_w = int(self.content_area.query_one("#set_min_worker", Input).value or "1")
            max_w = int(self.content_area.query_one("#set_max_worker", Input).value or "5")
            if min_w < 1 or max_w < 1 or min_w > max_w:
                self.show_error("MIN/MAX 값이 올바르지 않습니다")
                return
            base_path = self.content_area.query_one("#set_base_path", Input).value
            downloads_path = self.content_area.query_one("#set_downloads_path", Input).value
            engine = self.content_area.query_one("#set_engine", Input).value
            translate_lang = self.content_area.query_one("#set_translate_language", Input).value
            translate_model = self.content_area.query_one("#set_translate_model", Input).value
            summary_lang = self.content_area.query_one("#set_summary_language", Input).value
            summary_model = self.content_area.query_one("#set_summary_model", Input).value
            # .env 업데이트
            self.cfg_manager.update_env_file("MIN_WORKER", str(min_w))
            self.cfg_manager.update_env_file("MAX_WORKER", str(max_w))
            if base_path:
                self.cfg_manager.update_env_file("OPEN_SCRIBE_BASE_PATH", base_path)
            if downloads_path:
                self.cfg_manager.update_env_file("OPEN_SCRIBE_DOWNLOADS_PATH", downloads_path)
            if engine:
                self.cfg_manager.update_env_file("OPEN_SCRIBE_ENGINE", engine)
            if translate_lang:
                self.cfg_manager.update_env_file("OPENAI_TRANSLATE_LANGUAGE", translate_lang)
            if translate_model:
                self.cfg_manager.update_env_file("OPENAI_TRANSLATE_MODEL", translate_model)
            if summary_lang:
                self.cfg_manager.update_env_file("OPENAI_SUMMARY_LANGUAGE", summary_lang)
            if summary_model:
                self.cfg_manager.update_env_file("OPENAI_SUMMARY_MODEL", summary_model)
            # 런타임 반영
            try:
                from dotenv import load_dotenv
                load_dotenv(override=True)
            except Exception:
                pass
            self._set_settings_status("✓ 저장되었습니다")
            self.show_success("설정 저장 완료")
        except Exception as e:
            self._set_settings_status(str(e))
            self.show_error(str(e))
    
    def _get_option_display(self, index: int, label: str, enabled: bool) -> str:
        """체크박스 스타일 옵션 표시 생성"""
        checkbox = "[*]" if enabled else "[ ]"
        return f"{checkbox} {label}"
    
    def _get_engine_display(self, index: int, label: str, engine_value: str) -> str:
        """엔진 표시 생성 - 선택시 체크박스 스타일로 표시"""
        checkbox = "[*]" if self.selected_engine == engine_value else "[ ]"
        return f"{checkbox} {label}"
    
    def update_option_displays(self) -> None:
        """모든 옵션 표시 업데이트"""
        if not self.option_widgets:
            return
            
        # 체크박스 업데이트
        if 'timestamp' in self.option_widgets:
            self.option_widgets['timestamp'].label = Text(self._get_option_display(0, "Include timestamps", self.timestamp_enabled))
        if 'summary' in self.option_widgets:
            self.option_widgets['summary'].label = Text(self._get_option_display(1, "Generate AI summary", self.summary_enabled))
        if 'translate' in self.option_widgets:
            self.option_widgets['translate'].label = Text(self._get_option_display(2, "Translate", self.translate_enabled))
        if 'video' in self.option_widgets:
            self.option_widgets['video'].label = Text(self._get_option_display(3, "Download video", self.video_enabled))
        if 'srt' in self.option_widgets:
            self.option_widgets['srt'].label = Text(self._get_option_display(4, "Generate SRT (timestamps)", self.srt_enabled))
        if 'srt_translate' in self.option_widgets:
            self.option_widgets['srt_translate'].label = Text(self._get_option_display(5, "Translate SRT", self.srt_translate_enabled))
        if 'force' in self.option_widgets:
            self.option_widgets['force'].label = Text(self._get_option_display(6, "Force (retry)", self.force_enabled))
        if 'background' in self.option_widgets:
            self.option_widgets['background'].label = Text(self._get_option_display(7, "Background", self.background_enabled))
        
        # 엔진 옵션 업데이트
        if 'engine_mini' in self.option_widgets:
            self.option_widgets['engine_mini'].label = Text(self._get_engine_display(8, "GPT-4o-mini (default, fast)", "gpt-4o-mini-transcribe"))
        if 'engine_gpt4o' in self.option_widgets:
            self.option_widgets['engine_gpt4o'].label = Text(self._get_engine_display(9, "GPT-4o (high quality)", "gpt-4o-transcribe"))
        if 'engine_whisper_api' in self.option_widgets:
            self.option_widgets['engine_whisper_api'].label = Text(self._get_engine_display(10, "Whisper API (OpenAI cloud)", "whisper-api"))
        if 'engine_whisper_cpp' in self.option_widgets:
            self.option_widgets['engine_whisper_cpp'].label = Text(self._get_engine_display(11, "Whisper-cpp (local)", "whisper-cpp"))
        if 'engine_youtube' in self.option_widgets:
            self.option_widgets['engine_youtube'].label = Text(self._get_engine_display(12, "YouTube native", "youtube-transcript-api"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """버튼 클릭 이벤트 처리 (메뉴/옵션/엔진 모두 포함)"""
        button_id = event.button.id
        
        # 메뉴 버튼 처리 (좌측 메뉴 영역의 버튼)
        if button_id in {"transcribe", "database", "api_keys", "settings", "monitor", "help", "quit"}:
            # 좌측 메뉴 클릭 시에도 동일한 동작을 수행
            if button_id == "transcribe":
                self.selected_button_id = "transcribe"
                self.show_transcribe_interface()
                self.focus_area = "content"
                try:
                    self.app.set_focus(self)
                except Exception:
                    pass
                self.set_timer(0.01, lambda btn_id="transcribe": self._update_button_selection(btn_id))
                return
            elif button_id == "database":
                try:
                    self.app.push_screen(DatabaseScreen())
                except Exception:
                    self.show_content("Database Management", "Database screen failed to open.")
                self.set_timer(0.01, lambda btn_id="database": self._update_button_selection(btn_id))
                return
            elif button_id == "api_keys":
                self.selected_button_id = "api_keys"
                self.show_api_keys_interface()
                self.focus_area = "content"
                self.set_timer(0.01, lambda btn_id="api_keys": self._update_button_selection(btn_id))
                return
            elif button_id == "settings":
                self.selected_button_id = "settings"
                self.show_settings_interface()
                self.focus_area = "content"
                self.set_timer(0.01, lambda btn_id="settings": self._update_button_selection(btn_id))
                return
            elif button_id == "monitor":
                self.show_content("Monitoring", "Monitoring screen will be implemented in Phase 4.")
                self.set_timer(0.01, lambda btn_id="monitor": self._update_button_selection(btn_id))
                return
            elif button_id == "help":
                self.show_help()
                return
            elif button_id == "quit":
                self.app.exit()
                return

        # 오른쪽 콘텐츠 내의 버튼 처리
        if button_id == "transcribe":
            self.selected_button_id = "transcribe"
            self.show_transcribe_interface()
            self.focus_area = "content"
            try:
                self.app.set_focus(self)
            except Exception:
                pass
            self.set_timer(0.01, lambda btn_id="transcribe": self._update_button_selection(btn_id))
            return
        elif button_id == "start_transcribe":
            self.start_transcription()
            return
        elif button_id == "clear_url":
            self.clear_url_input()
            return
        elif button_id == "save_api_key":
            self._save_api_key_inline()
            return
        elif button_id == "validate_api_key":
            self._validate_api_key_inline()
            return
        elif button_id == "settings_save":
            self._save_settings_inline()
            return
        # 옵션 토글
        if button_id == 'opt_timestamp':
            self.focused_option = 0
            self.timestamp_enabled = not self.timestamp_enabled
        elif button_id == 'opt_summary':
            self.focused_option = 1
            self.summary_enabled = not self.summary_enabled
        elif button_id == 'opt_translate':
            self.focused_option = 2
            self.translate_enabled = not self.translate_enabled
        elif button_id == 'opt_video':
            self.focused_option = 3
            self.video_enabled = not self.video_enabled
        elif button_id == 'opt_srt':
            self.focused_option = 4
            self.srt_enabled = not self.srt_enabled
        elif button_id == 'opt_srt_translate':
            self.focused_option = 5
            self.srt_translate_enabled = not self.srt_translate_enabled
            if self.srt_translate_enabled:
                self.srt_enabled = True
        elif button_id == 'opt_force':
            self.focused_option = 6
            self.force_enabled = not self.force_enabled
        elif button_id == 'opt_background':
            self.focused_option = 7
            self.background_enabled = not self.background_enabled
        # 엔진 선택
        elif button_id == 'eng_mini':
            self.focused_option = 8
            self.selected_engine = 'gpt-4o-mini-transcribe'
        elif button_id == 'eng_gpt4o':
            self.focused_option = 9
            self.selected_engine = 'gpt-4o-transcribe'
        elif button_id == 'eng_whisper_api':
            self.focused_option = 10
            self.selected_engine = 'whisper-api'
        elif button_id == 'eng_whisper_cpp':
            self.focused_option = 11
            self.selected_engine = 'whisper-cpp'
        elif button_id == 'eng_youtube':
            self.focused_option = 12
            self.selected_engine = 'youtube-transcript-api'
        else:
            return
        self.update_option_displays()
    
    def action_menu_action(self, menu_id: str) -> None:
        """키보드로 메뉴 선택"""
        self._update_button_selection(menu_id)
        
        if menu_id == "transcribe":
            # 오른쪽 콘텐츠 영역에 전사 인터페이스 표시
            self.show_transcribe_interface()
            self.focus_area = "content"
            try:
                self.app.set_focus(self)
            except Exception:
                pass
        elif menu_id == "database":
            try:
                self.app.push_screen(DatabaseScreen())
            except Exception:
                self.show_content("Database Management", "Database screen failed to open.")
        elif menu_id == "api_keys":
            self.selected_button_id = "api_keys"
            self.show_api_keys_interface()
            self.focus_area = "content"
        elif menu_id == "settings":
            self.selected_button_id = "settings"
            self.show_settings_interface()
            self.focus_area = "content"
        elif menu_id == "monitor":
            self.show_content("Monitoring", "Monitoring screen will be implemented in Phase 4.")
        elif menu_id == "help":
            self.show_help()
        elif menu_id == "quit":
            self.app.exit()
    
    def action_press_focused_button(self) -> None:
        """현재 포커스된 버튼 눌러"""
        # 메뉴 영역에 있을 때만 동작하도록 가드
        if self.focus_area != "menu":
            return
        if self.menu_buttons and 0 <= self.current_focus < len(self.menu_buttons):
            # 현재 포커스된 버튼의 ID를 가져와서 직접 액션 실행
            button = self.menu_buttons[self.current_focus]
            button_id = button.id
            self._update_button_selection(button_id)
            
            # 버튼 클릭 이벤트를 시뮬레이션
            if button_id == "transcribe":
                # 오른쪽 콘텐츠 영역에 전사 인터페이스 표시
                self.show_transcribe_interface()
            elif button_id == "database":
                self.show_content("Database Management", "Database management features will be implemented in Phase 4.")
            elif button_id == "api_keys":
                self.show_api_keys_interface()
            elif button_id == "settings":
                self.show_settings_interface()
            elif button_id == "monitor":
                self.show_content("Monitoring", "Monitoring screen will be implemented in Phase 4.")
            elif button_id == "help":
                self.show_help()
            elif button_id == "quit":
                self.app.exit()
    
    def action_navigate_up(self) -> None:
        """위쪽 메뉴로 이동"""
        if self.focus_area != "menu":
            return
        if self.menu_buttons:
            self.current_focus = (self.current_focus - 1) % len(self.menu_buttons)
            self.menu_buttons[self.current_focus].focus()
            self._scroll_to_focused()
    
    def action_navigate_down(self) -> None:
        """아래쪽 메뉴로 이동"""
        if self.focus_area != "menu":
            return
        if self.menu_buttons:
            self.current_focus = (self.current_focus + 1) % len(self.menu_buttons)
            self.menu_buttons[self.current_focus].focus()
            self._scroll_to_focused()
    
    def _scroll_to_focused(self) -> None:
        """현재 포커스된 메뉴 항목이 보이도록 전체 화면 스크롤"""
        if self.menu_buttons and 0 <= self.current_focus < len(self.menu_buttons):
            focused_button = self.menu_buttons[self.current_focus]
            # Textual의 기본 scroll_visible 사용
            focused_button.scroll_visible(animate=True)
    
    def action_focus_menu(self) -> None:
        """메뉴 영역에 포커스"""
        self.focus_area = "menu"
        print(f"DEBUG: Focus changed to menu area")
        if self.menu_buttons and 0 <= self.current_focus < len(self.menu_buttons):
            self.menu_buttons[self.current_focus].focus()
    
    def action_focus_content(self) -> None:
        """콘텐츠 영역에 포커스"""
        self.focus_area = "content"
        print(f"DEBUG: Focus changed to content area")
    
    # 통합 키 액션 (메뉴/콘텐츠 포커스에 따라 분기)
    def action_handle_up(self) -> None:
        if self.focus_area == "menu":
            self.action_navigate_up()
        else:
            if self.focused_option > 0:
                self.focused_option -= 1
                self.update_option_displays()

    def action_handle_down(self) -> None:
        if self.focus_area == "menu":
            self.action_navigate_down()
        else:
            if self.focused_option < self.total_options - 1:
                self.focused_option += 1
                self.update_option_displays()

    def action_handle_enter(self) -> None:
        if self.focus_area == "menu":
            self.action_press_focused_button()
            self.action_focus_content()
        else:
            # 콘텐츠 영역에서는 현재 항목 토글
            self.toggle_current_option()
            self.update_option_displays()

    def action_handle_space(self) -> None:
        if self.focus_area == "content":
            self.toggle_current_option()
    
    
    def start_transcription(self) -> None:
        """전사 시작"""
        self.app.notify("start_transcription called", severity="information")
        try:
            # URL 가져오기
            if not self.url_input:
                self.show_error("URL input not found")
                return
                
            url = self.url_input.value.strip()
            
            if not url:
                self.show_error("Please enter a YouTube URL")
                return
            
            # 선택된 엔진은 이미 self.selected_engine에 저장됨
            
            # 옵션 상태 가져오기
            options_text = []
            if self.timestamp_enabled:
                options_text.append("timestamps")
            if self.summary_enabled:
                options_text.append("summary")
            if self.translate_enabled:
                options_text.append("translation")
            if self.video_enabled:
                options_text.append("video download")
            
            # 출력 영역 업데이트
            output = self.content_area.query_one(".transcribe-output", Static)
            options_str = ", ".join(options_text) if options_text else "none"
            output.update(f"🔄 Starting transcription...\nURL: {url[:50]}...\nEngine: {self.selected_engine}\nOptions: {options_str}")
            
            # Background 모드면 큐에 적재 후 종료
            if self.background_enabled:
                self._enqueue_background_job(url, force=self.force_enabled)
                return
            # 기존 결과 존재 여부 확인 또는 즉시 실행
            self._pending_url = url
            self._precheck_and_maybe_confirm(url)
            
        except Exception as e:
            print(f"DEBUG: Exception occurred: {e}")
            self.show_error(f"Error: {str(e)}")
    
    def clear_url_input(self) -> None:
        """URL 입력 및 모든 옵션 초기화"""
        try:
            # URL 초기화
            if self.url_input:
                self.url_input.value = ""
                self.url_input.focus()
            
            # 옵션 상태 초기화
            self.timestamp_enabled = False
            self.summary_enabled = False
            self.translate_enabled = False
            self.video_enabled = False
            self.selected_engine = "gpt-4o-mini-transcribe"
            self.focused_option = 0
            
            # UI 업데이트
            self.update_option_displays()
            
            # 출력 영역 초기화
            output = self.content_area.query_one(".transcribe-output", Static)
            output.update("Ready to transcribe...")
        except Exception as e:
            print(f"DEBUG: Error in clear_url_input: {e}")
    
    
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Input 위젯에서 엔터키가 눌렸을 때 처리"""
        if event.input.id == "url_input" or "url-input" in event.input.classes:
            # 엔터 입력 후 옵션 영역으로 포커스 이동
            self.focus_area = "content"
            self.focused_option = 0
            self.update_option_displays()
            # 시각적으로 옵션 라인으로 스크롤
            if 'timestamp' in self.option_widgets:
                self.option_widgets['timestamp'].scroll_visible(animate=True)
            # 입력 포커스 해제 및 상위로 포커스 이동
            try:
                self.url_input.blur()
            except Exception:
                pass
            try:
                self.app.set_focus(self)
            except Exception:
                pass
            # 이벤트 전파 중단 (바인딩 충돌 방지)
            try:
                event.stop()
            except Exception:
                pass
            # 바로 전사 시작이 아니라 옵션 선택 가능하도록 종료
    
    def on_key(self, event) -> None:
        """키보드 이벤트 직접 처리"""
        key = event.key
        
        # Transcribe 인터페이스가 활성화된 경우
        if self.selected_button_id == "transcribe" and self.option_widgets and self.focus_area == "content":
            # 단축키만 유지 (s: start, c: clear). 화살표/엔터/스페이스는 바인딩 액션으로 처리
            if key == "s" or key == "S":
                self.start_transcription()
                return
            elif key == "c" or key == "C":
                self.clear_url_input()
                return
        
        # 숫자 키 처리 (메뉴 선택)
        if key == "1":
            self.action_menu_action("transcribe")
        elif key == "2":
            self.action_menu_action("database")
        elif key == "3":
            self.action_menu_action("api_keys")
        elif key == "4":
            self.action_menu_action("settings")
        elif key == "5":
            self.action_menu_action("monitor")
        elif key == "h":
            self.action_menu_action("help")
        elif key == "q" or key == "ㅂ":
            self.action_menu_action("quit")
        elif key == "escape":
            self.action_menu_action("quit")
        # 화살표 키 처리 (메뉴 네비게이션)
        elif key == "up" or key == "k":
            self.action_handle_up()
        elif key == "down" or key == "j":
            self.action_handle_down()
        elif key == "left":
            # 왼쪽 방향키로 메뉴로 복귀
            self.action_focus_menu()
        elif key == "right":
            self.action_focus_content()
        elif key == "enter":
            self.action_handle_enter()
            return
        elif key == "space":
            self.action_handle_space()
            return
        else:
            # 처리되지 않은 키는 부모로 전달
            event.prevent_default = False
    
    def toggle_current_option(self) -> None:
        """현재 포커스된 옵션 토글"""
        if self.focused_option < 8:
            # 체크박스 옵션
            if self.focused_option == 0:
                self.timestamp_enabled = not self.timestamp_enabled
            elif self.focused_option == 1:
                self.summary_enabled = not self.summary_enabled
            elif self.focused_option == 2:
                self.translate_enabled = not self.translate_enabled
            elif self.focused_option == 3:
                self.video_enabled = not self.video_enabled
            elif self.focused_option == 4:
                self.srt_enabled = not self.srt_enabled
            elif self.focused_option == 5:
                # SRT 번역은 SRT 생성이 함께 활성화되어야 함
                self.srt_translate_enabled = not self.srt_translate_enabled
                if self.srt_translate_enabled:
                    self.srt_enabled = True
            elif self.focused_option == 6:
                self.force_enabled = not self.force_enabled
            elif self.focused_option == 7:
                self.background_enabled = not self.background_enabled
        else:
            # 엔진 옵션 (라디오 버튼)
            if self.focused_option == 8:
                self.selected_engine = "gpt-4o-mini-transcribe"
            elif self.focused_option == 9:
                self.selected_engine = "gpt-4o-transcribe"
            elif self.focused_option == 10:
                self.selected_engine = "whisper-api"
            elif self.focused_option == 11:
                self.selected_engine = "whisper-cpp"
            elif self.focused_option == 12:
                self.selected_engine = "youtube-transcript-api"
        
        # UI 업데이트
        self.update_option_displays()

    def _enqueue_background_job(self, url: str, force: bool) -> None:
        """작업을 큐로 등록하고 모니터링 탭에서 관리되도록 한다."""
        try:
            config = Config()
            db = TranscriptionDatabase(config.DB_PATH)
            downloader = YouTubeDownloader(config.AUDIO_PATH, config.VIDEO_PATH, config.TEMP_PATH)
            info = downloader.get_video_info(url)
            if not info:
                self.show_error("Could not extract video information")
                return
            video_id = info.get('id')
            title = info.get('title') or url
            job_id = db.create_job(video_id, url, title, self.selected_engine)
            db.update_job_status(job_id, 'queued')
            # 큐 파일 작성
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            queue_dir = Path(root_dir) / 'queue'
            queue_dir.mkdir(parents=True, exist_ok=True)
            payload = {
                "job_id": job_id,
                "video_id": video_id,
                "url": url,
                "title": title,
                "engine": self.selected_engine,
                "force": force,
                "timestamp": datetime.now().isoformat(timespec='seconds')
            }
            qfile = queue_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{video_id}.json"
            qfile.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
            try:
                out = self.content_area.query_one(".transcribe-output", Static)
                out.update(f"📝 Enqueued background job (ID: {job_id}).\nSee Monitoring for status.")
            except Exception:
                pass
            self.show_success("Job added to queue")
        except Exception as e:
            self.show_error(f"Queue error: {e}")

    def _show_confirm_dialog(self, message: str) -> None:
        """재처리 확인 다이얼로그 표시"""
        try:
            self._remove_confirm_dialog()
            dialog = Vertical(classes="confirmation-dialog", id="confirm_dialog")
            dialog.mount(Static(message))
            buttons = Horizontal(classes="dialog-buttons")
            buttons.mount(Button("Yes", id="confirm_yes", variant="primary"))
            buttons.mount(Button("No", id="confirm_no", variant="default"))
            dialog.mount(buttons)
            self.content_area.mount(dialog)
        except Exception:
            pass

    def _remove_confirm_dialog(self) -> None:
        try:
            dialog = self.content_area.query_one("#confirm_dialog", Vertical)
            dialog.remove()
        except Exception:
            pass

    def _precheck_and_maybe_confirm(self, url: str) -> None:
        """DB와 파일을 확인해 재처리 여부를 묻거나 바로 실행"""
        try:
            config = Config()
            db = TranscriptionDatabase(config.DB_PATH)
            downloader = YouTubeDownloader(config.AUDIO_PATH, config.VIDEO_PATH, config.TEMP_PATH)
            info = downloader.get_video_info(url)
            if not info:
                self._launch_transcription_process(url, force=False)
                return
            video_id = info.get('id')
            existing = db.get_job_progress(video_id, self.selected_engine)
            if existing and existing.get('status') == 'completed' and existing.get('transcription_completed'):
                self._show_confirm_dialog("이미 처리된 영상입니다. 다시 처리하시겠습니까?")
            else:
                self._launch_transcription_process(url, force=False)
        except Exception:
            self._launch_transcription_process(url, force=False)

    def _launch_transcription_process(self, url: str, force: bool = False) -> None:
        """백그라운드 스레드로 전사 프로세스 실행"""
        def run_worker():
            try:
                root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
                main_path = os.path.join(root_dir, "main.py")
                logs_dir = os.path.join(root_dir, "logs")
                os.makedirs(logs_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                log_file_path = os.path.join(logs_dir, f"tui-run-{timestamp}.log")

                args = [sys.executable, main_path, url, "--engine", self.selected_engine]
                if force:
                    args.append("--force")
                if self.timestamp_enabled:
                    args.append("--timestamp")
                if self.summary_enabled:
                    args.append("--summary")
                if self.translate_enabled:
                    args.append("--translate")
                if self.video_enabled:
                    args.append("--video")
                if self.srt_enabled:
                    args.append("--srt")
                if self.srt_translate_enabled:
                    if "--srt" not in args:
                        args.append("--srt")
                    if "--translate" not in args:
                        args.append("--translate")
                env = os.environ.copy()
                env["OPEN_SCRIBE_TUI_LOG"] = log_file_path
                proc = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=root_dir,
                    env=env,
                    bufsize=1,
                )
                try:
                    info_line = self.content_area.query_one("#spinner_line", Static)
                    info_line.update(f"[log] Writing to: {log_file_path}")
                except Exception:
                    pass
                loader_stop = threading.Event()
                def _animate_loader():
                    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
                    i = 0
                    while not loader_stop.is_set():
                        try:
                            spinner = self.content_area.query_one("#spinner_line", Static)
                            spinner.update(f"{frames[i % len(frames)]} Processing...")
                        except Exception:
                            pass
                        i += 1
                        time.sleep(0.08)
                loader_thread = threading.Thread(target=_animate_loader, daemon=True)
                loader_thread.start()
                with open(log_file_path, "a", encoding="utf-8") as log_fp:
                    current_line = ""
                    while True:
                        ch = proc.stdout.read(1)
                        if ch == "" and proc.poll() is not None:
                            break
                        if not ch:
                            continue
                        try:
                            log_fp.write(ch)
                            log_fp.flush()
                        except Exception:
                            pass
                        if ch == "\r":
                            try:
                                out = self.content_area.query_one(".transcribe-output", Static)
                                out.update(current_line.rstrip())
                            except Exception:
                                pass
                            continue
                        if ch == "\n":
                            try:
                                out = self.content_area.query_one(".transcribe-output", Static)
                                out.update(current_line.rstrip())
                            except Exception:
                                pass
                            current_line = ""
                        else:
                            current_line += ch
                proc.wait()
                try:
                    loader_stop.set()
                    loader_thread.join(timeout=0.2)
                except Exception:
                    pass
                if proc.returncode == 0:
                    self.show_success("Transcription finished")
                else:
                    self.show_error(f"Transcription failed (code {proc.returncode}) — see log: {log_file_path}")
            except Exception as e:
                self.show_error(str(e))
        threading.Thread(target=run_worker, daemon=True).start()